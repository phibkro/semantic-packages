"""Plan-driven OrderedMap conformance runner for ``ordered-map-runner-json-v1``.

The runner authenticates and captures the reviewed plan once, then treats the child
adapter as an opaque process.  A well-framed observation that disagrees with the plan
challenges only the declarations attached to that observation.  Framing, lifecycle,
and adapter failures are execution errors and never become semantic counterexamples.

This module produces an ephemeral conformance fact.  It does not construct Claims,
Evidence, reviews, manifests, registration authority, or acceptance decisions.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from semantic_packages import ordered_map_contract


ASSUMPTIONS: tuple[str, ...] = (
    "adapter-faithfulness",
    "adapter-event-completeness",
)
EXCLUSIONS: tuple[str, ...] = (
    "adapter-external-effects",
    "realization-steps",
)


@dataclass(frozen=True)
class DeclarationOutcome:
    declaration_id: str
    observation_count: int
    result: str
    causes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    request_count: int
    declarations: tuple[DeclarationOutcome, ...]


@dataclass(frozen=True)
class EventOutcome:
    seq: int
    case_id: str
    operation: str
    event: str
    disposition: str


@dataclass(frozen=True)
class ConformanceReport:
    result: str
    causes: tuple[str, ...]
    plan_sha256: Optional[str]
    declarations: tuple[DeclarationOutcome, ...]
    cases: tuple[CaseOutcome, ...]
    events: tuple[EventOutcome, ...]
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]
    stderr: bytes = b""


@dataclass
class _MutableDeclaration:
    declaration_id: str
    observation_count: int = 0
    challenged: bool = False
    causes: tuple[str, ...] = ()

    def observe(self, *, supports: bool, cause: Optional[str] = None) -> None:
        self.observation_count += 1
        if not supports:
            self.challenged = True
            if cause is not None and cause not in self.causes:
                self.causes += (cause,)

    def freeze(self, *, execution_error: bool = False) -> DeclarationOutcome:
        if self.challenged:
            result = "challenges"
            causes = self.causes
        elif execution_error:
            result = "supports" if self.observation_count else "inconclusive"
            causes: tuple[str, ...] = ()
        elif self.observation_count:
            result = "supports"
            causes = ()
        else:
            result = "inconclusive"
            causes = ()
        return DeclarationOutcome(
            self.declaration_id,
            self.observation_count,
            result,
            causes,
        )


@dataclass
class _MutableCase:
    case_id: str
    request_count: int
    declarations: list[_MutableDeclaration]

    def freeze(self, *, execution_error: bool = False) -> CaseOutcome:
        return CaseOutcome(
            self.case_id,
            self.request_count,
            tuple(item.freeze(execution_error=execution_error) for item in self.declarations),
        )


class _ProtocolFailure(Exception):
    def __init__(self, cause: str) -> None:
        super().__init__(cause)
        self.cause = cause


class _DuplicateMember(ValueError):
    pass


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMember(key)
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {value}")


def _snapshot(value: Any) -> Any:
    """Detach a captured plan value while exercising its complete access path."""

    if isinstance(value, Mapping):
        return {key: _snapshot(value[key]) for key in value}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_snapshot(value[index]) for index in range(len(value)))
    return value


def _unique(items: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


class _LineReader:
    """Bounded LF-framed reader retaining bytes already received from the child."""

    def __init__(self, fd: int) -> None:
        self._fd = fd
        self._buffer = b""
        self._eof = False

    def _read_available(self, timeout: float) -> None:
        if self._eof:
            return
        ready, _, _ = select.select([self._fd], [], [], max(timeout, 0.0))
        if not ready:
            return
        chunk = os.read(self._fd, 65536)
        if chunk:
            self._buffer += chunk
        else:
            self._eof = True

    def has_output(self, timeout: float = 0.0) -> bool:
        if self._buffer:
            return True
        self._read_available(timeout)
        return bool(self._buffer)

    def read_line(self, timeout: float) -> Optional[bytes]:
        deadline = time.monotonic() + timeout
        while b"\n" not in self._buffer:
            if self._eof:
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            self._read_available(remaining)
        line, _, self._buffer = self._buffer.partition(b"\n")
        return line

    @property
    def has_remainder(self) -> bool:
        return bool(self._buffer)


class _Session:
    """One strict request/response child session driven by captured plan steps."""

    def __init__(
        self,
        *,
        response_timeout: float,
        exit_timeout: float,
        event_contract: Mapping[str, Any],
        allowed_values: Sequence[int],
        allowed_classes: Sequence[str],
    ) -> None:
        self.response_timeout = response_timeout
        self.exit_timeout = exit_timeout
        self.event_contract = event_contract
        self.allowed_values = tuple(allowed_values)
        self.allowed_classes = tuple(allowed_classes)
        self.events: list[EventOutcome] = []
        self.stderr = b""

        self._proc: Optional[subprocess.Popen[bytes]] = None
        self._reader: Optional[_LineReader] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._stderr_chunks: list[bytes] = []
        self._completed_responses = 0

    def start(self, command: Sequence[str]) -> None:
        command_list = list(command)
        if not command_list:
            raise OSError("empty command")
        self._proc = subprocess.Popen(
            command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        assert self._proc.stdout is not None
        self._reader = _LineReader(self._proc.stdout.fileno())
        self._start_stderr_drain()

    def _start_stderr_drain(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stderr is not None

        def drain() -> None:
            try:
                while True:
                    chunk = proc.stderr.read(65536)
                    if not chunk:
                        return
                    self._stderr_chunks.append(chunk)
            except (OSError, ValueError):
                return

        self._stderr_thread = threading.Thread(target=drain, daemon=True)
        self._stderr_thread.start()

    def _classify_exit(self) -> str:
        proc = self._proc
        assert proc is not None
        try:
            returncode = proc.wait(timeout=self.exit_timeout)
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        return "PROCESS_EXIT" if returncode != 0 else "UNEXPECTED_EOF"

    def _ensure_terminated(self) -> None:
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        # Response and clean-exit handling have already consumed their two
        # plan-owned deadlines.  This is cleanup signal grace, not a third semantic
        # timeout; leave deterministic margin beneath the campaign's total bound.
        signal_grace = min(self.exit_timeout / 4, 0.05)
        try:
            proc.wait(timeout=signal_grace)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def close(self) -> Optional[str]:
        proc = self._proc
        if proc is None:
            return None
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
        except OSError:
            pass

        deadline = time.monotonic() + self.exit_timeout
        closure_cause: Optional[str] = None
        try:
            assert self._reader is not None
            try:
                line = self._reader.read_line(max(deadline - time.monotonic(), 0.0))
            except TimeoutError:
                closure_cause = "TIMEOUT"
            else:
                if line is not None or self._reader.has_remainder:
                    closure_cause = "EXTRA_STDOUT"
                else:
                    try:
                        returncode = proc.wait(
                            timeout=max(deadline - time.monotonic(), 0.0)
                        )
                    except subprocess.TimeoutExpired:
                        closure_cause = "TIMEOUT"
                    else:
                        if returncode != 0:
                            closure_cause = "PROCESS_EXIT"
        finally:
            self._ensure_terminated()
            signal_grace = min(self.exit_timeout / 4, 0.05)
            if self._stderr_thread is not None:
                self._stderr_thread.join(timeout=signal_grace)
            try:
                if proc.stderr is not None:
                    proc.stderr.close()
            except OSError:
                pass
            self.stderr = b"".join(self._stderr_chunks)
            try:
                if proc.stdout is not None:
                    proc.stdout.close()
            except OSError:
                pass
        return closure_cause

    def _before_request(self) -> None:
        assert self._reader is not None
        # Give an eager child one short scheduling turn before the first request.
        # Later checks are immediate and occur before every subsequent write.
        grace = min(self.response_timeout / 10, 0.02) if self._completed_responses == 0 else 0.0
        if self._reader.has_output(grace):
            cause = "UNEXPECTED_OUTPUT" if self._completed_responses == 0 else "EXTRA_STDOUT"
            raise _ProtocolFailure(cause)

    def _write_request(self, request: Mapping[str, Any]) -> None:
        proc = self._proc
        assert proc is not None and proc.stdin is not None
        payload = (json.dumps(request, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            proc.stdin.write(payload)
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise _ProtocolFailure(self._classify_exit())

    def _read_response(self, expected_seq: int) -> dict[str, Any]:
        assert self._reader is not None
        try:
            line = self._reader.read_line(self.response_timeout)
        except TimeoutError:
            raise _ProtocolFailure("TIMEOUT")
        if line is None:
            raise _ProtocolFailure(self._classify_exit())
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            raise _ProtocolFailure("RESPONSE_ENCODING")
        try:
            response = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_members,
                parse_constant=_reject_nonstandard_constant,
            )
        except _DuplicateMember:
            raise _ProtocolFailure("RESPONSE_DUPLICATE_MEMBER")
        except (json.JSONDecodeError, ValueError):
            raise _ProtocolFailure("RESPONSE_JSON")
        try:
            self._validate_envelope(response, expected_seq)
        except _ProtocolFailure as error:
            # A child can race the short startup observation window: its unsolicited
            # frame becomes the first read after our request, followed by the actual
            # response.  Before any completed response or next write, distinguish that
            # queued two-frame violation from a single malformed response.
            if (
                self._completed_responses == 0
                and error.cause == "RESPONSE_SHAPE"
                and self._reader.has_output(min(self.response_timeout / 2, 0.10))
            ):
                raise _ProtocolFailure("UNEXPECTED_OUTPUT")
            raise
        self._completed_responses += 1
        # Buffered bytes are unambiguously a second response before another request.
        if self._reader.has_output(0.0):
            raise _ProtocolFailure("EXTRA_STDOUT")
        return response

    @staticmethod
    def _validate_envelope(response: Any, expected_seq: int) -> None:
        if not isinstance(response, dict):
            raise _ProtocolFailure("RESPONSE_SHAPE")
        status = response.get("status")
        if status == "ok":
            if set(response) != {"seq", "status", "result", "events"}:
                raise _ProtocolFailure("RESPONSE_SHAPE")
        elif status == "error":
            if set(response) != {"seq", "status", "error", "events"}:
                raise _ProtocolFailure("RESPONSE_SHAPE")
            error = response.get("error")
            if (
                not isinstance(error, dict)
                or set(error) != {"code", "message"}
                or not isinstance(error.get("code"), str)
                or not error["code"]
                or not isinstance(error.get("message"), str)
                or not error["message"]
            ):
                raise _ProtocolFailure("RESPONSE_SHAPE")
        else:
            raise _ProtocolFailure("RESPONSE_SHAPE")

        seq = response.get("seq")
        if type(seq) is not int:
            raise _ProtocolFailure("RESPONSE_SHAPE")
        if seq != expected_seq:
            raise _ProtocolFailure("SEQUENCE_MISMATCH")
        events = response.get("events")
        if (
            not isinstance(events, list)
            or any(not isinstance(event, str) or not event for event in events)
        ):
            raise _ProtocolFailure("RESPONSE_SHAPE")

    def _validate_result(self, op: str, result: Any) -> None:
        if not isinstance(result, dict):
            raise _ProtocolFailure("RESPONSE_SHAPE")
        if op in {"empty", "put"}:
            if (
                set(result) != {"map"}
                or not isinstance(result.get("map"), str)
                or not result["map"]
            ):
                raise _ProtocolFailure("RESPONSE_SHAPE")
            return
        if op == "lookup":
            tag = result.get("tag")
            if tag == "none":
                if set(result) != {"tag"}:
                    raise _ProtocolFailure("RESPONSE_SHAPE")
                return
            if tag == "some":
                value = result.get("value")
                if (
                    set(result) != {"tag", "value"}
                    or type(value) is not int
                    or value not in self.allowed_values
                ):
                    raise _ProtocolFailure("RESPONSE_SHAPE")
                return
            raise _ProtocolFailure("RESPONSE_SHAPE")
        if op == "entries":
            if set(result) != {"entries"} or not isinstance(result["entries"], list):
                raise _ProtocolFailure("RESPONSE_SHAPE")
            for entry in result["entries"]:
                if (
                    not isinstance(entry, dict)
                    or set(entry) != {"class", "value"}
                    or entry.get("class") not in self.allowed_classes
                    or type(entry.get("value")) is not int
                    or entry["value"] not in self.allowed_values
                ):
                    raise _ProtocolFailure("RESPONSE_SHAPE")
            return
        raise _ProtocolFailure("RESPONSE_SHAPE")

    def _event_disposition(self, event: str) -> str:
        for disposition in ("forbidden", "optional"):
            for pattern in self.event_contract[disposition]:
                if pattern.endswith(".*"):
                    prefix = pattern[:-1]
                    if event.startswith(prefix) and len(event) > len(prefix):
                        return disposition
                elif event == pattern:
                    return disposition
        return self.event_contract["default"]

    def invoke(
        self,
        *,
        seq: int,
        case_id: str,
        op: str,
        args: Mapping[str, Any],
    ) -> dict[str, Any]:
        # The order is the protocol invariant: inspect pending output, write exactly
        # one request, then read and validate exactly its one response.
        self._before_request()
        self._write_request({"seq": seq, "op": op, "args": dict(args)})
        response = self._read_response(seq)
        for event in response["events"]:
            self.events.append(
                EventOutcome(
                    seq,
                    case_id,
                    op,
                    event,
                    self._event_disposition(event),
                )
            )
        if response["status"] == "error":
            raise _ProtocolFailure("ADAPTER_ERROR")
        result = response["result"]
        self._validate_result(op, result)
        return result


def _case_declaration_ids(case: Mapping[str, Any]) -> tuple[str, ...]:
    ids: list[str] = []
    for step in case["steps"]:
        for declaration_id in step.get("declarations", ()):
            if declaration_id not in ids:
                ids.append(declaration_id)
    for step in case["steps"]:
        declaration_id = step["effectDeclaration"]
        if declaration_id not in ids:
            ids.append(declaration_id)
    return tuple(ids)


def _report_for_plan_failure() -> ConformanceReport:
    return ConformanceReport(
        result="error",
        causes=("PLAN_AUTHORITY",),
        plan_sha256=None,
        declarations=(),
        cases=(),
        events=(),
        assumptions=ASSUMPTIONS,
        exclusions=EXCLUSIONS,
    )


def run_ordered_map_conformance(command):
    """Run the one authenticated OrderedMap campaign against ``command``."""

    captured = ordered_map_contract.inspect_conformance_plan()
    if not captured.ok or captured.document is None or captured.canonical_sha256 is None:
        return _report_for_plan_failure()

    document = _snapshot(captured.document)
    plan_sha256 = captured.canonical_sha256
    cases = document["cases"]
    bounds = document["bounds"]
    domains = document["domains"]
    session = _Session(
        response_timeout=bounds["responseTimeoutSeconds"],
        exit_timeout=bounds["exitTimeoutSeconds"],
        event_contract=document["eventContract"],
        allowed_values=domains["values"],
        allowed_classes=domains["classTokens"],
    )

    mutable_cases = [
        _MutableCase(
            case["id"],
            len(case["steps"]),
            [_MutableDeclaration(item) for item in _case_declaration_ids(case)],
        )
        for case in cases
    ]
    global_declarations: dict[str, _MutableDeclaration] = {}
    for case in mutable_cases:
        for outcome in case.declarations:
            global_declarations.setdefault(
                outcome.declaration_id,
                _MutableDeclaration(outcome.declaration_id),
            )

    execution_causes: list[str] = []
    seq = 0
    try:
        try:
            session.start(command)
        except (OSError, TypeError, ValueError):
            execution_causes.append("PROCESS_START")
        else:
            try:
                for case, mutable_case in zip(cases, mutable_cases):
                    bindings: dict[str, str] = {}
                    case_declarations = {
                        item.declaration_id: item for item in mutable_case.declarations
                    }
                    for step in case["steps"]:
                        op = step["op"]
                        if op == "empty":
                            args: dict[str, Any] = {}
                        elif op == "put":
                            args = {
                                "map": bindings[step["source"]],
                                "key": step["key"],
                                "value": step["value"],
                            }
                        elif op == "lookup":
                            args = {
                                "map": bindings[step["source"]],
                                "key": step["key"],
                            }
                        else:
                            args = {"map": bindings[step["source"]]}

                        result = session.invoke(
                            seq=seq,
                            case_id=case["id"],
                            op=op,
                            args=args,
                        )
                        if "bind" in step:
                            bindings[step["bind"]] = result["map"]

                        for declaration_id in step.get("declarations", ()):
                            if op == "entries":
                                supports = result["entries"] == list(step["expected"])
                            else:
                                supports = result == step["expected"]
                            cause = None if supports else "OBSERVATION_MISMATCH"
                            case_declarations[declaration_id].observe(
                                supports=supports,
                                cause=cause,
                            )
                            global_declarations[declaration_id].observe(
                                supports=supports,
                                cause=cause,
                            )

                        effect_id = step["effectDeclaration"]
                        step_events = [item for item in session.events if item.seq == seq]
                        effect_supports = not any(
                            item.disposition == "forbidden" for item in step_events
                        )
                        effect_cause = None if effect_supports else "FORBIDDEN_EVENT"
                        case_declarations[effect_id].observe(
                            supports=effect_supports,
                            cause=effect_cause,
                        )
                        global_declarations[effect_id].observe(
                            supports=effect_supports,
                            cause=effect_cause,
                        )
                        seq += 1
            except _ProtocolFailure as error:
                execution_causes.append(error.cause)
    finally:
        closure_cause = session.close()
        if closure_cause is not None:
            execution_causes.append(closure_cause)

    execution = _unique(execution_causes)
    execution_error = bool(execution)
    declarations = tuple(
        item.freeze(execution_error=execution_error)
        for item in global_declarations.values()
    )
    frozen_cases = tuple(
        item.freeze(execution_error=execution_error) for item in mutable_cases
    )
    if execution_error:
        result = "error"
        causes = execution
    elif any(item.result == "challenges" for item in declarations):
        result = "challenges"
        causes = _unique(cause for item in declarations for cause in item.causes)
    elif declarations and all(item.result == "supports" for item in declarations):
        result = "supports"
        causes = ()
    else:
        result = "inconclusive"
        causes = ()
    return ConformanceReport(
        result=result,
        causes=causes,
        plan_sha256=plan_sha256,
        declarations=declarations,
        cases=frozen_cases,
        events=tuple(session.events),
        assumptions=ASSUMPTIONS,
        exclusions=EXCLUSIONS,
        stderr=session.stderr,
    )
