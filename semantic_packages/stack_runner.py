"""Tracer-scoped Stack conformance runner for ``stack-runner-json-v1``.

This module owns the semantic oracle described in ``docs/design/adapter-protocol.md``:
it derives expected top-first traces from operations it issues itself, using plain
Python values, and never imports a Realization's Stack operations. The child adapter
is opaque; only its protocol responses are observed.

Runner classifications (see the adapter-protocol table):

- a malformed/short-framed transport, a sequence mismatch, extra stdout, a timeout, a
  nonzero process exit, or an adapter error response to a valid request is an
  execution ``error``, not a semantic counterexample;
- a well-formed response that violates an observation (wrong empty-pop, wrong
  pop_push value/remainder, wrong top-first order, a changed retained handle, an
  observation that never terminates, or a forbidden reported event) ``challenges``
  the Specification;
- a clean bounded run ``supports`` it, subject to the explicit assumptions and
  exclusions every report carries.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

ASSUMPTIONS: Tuple[str, ...] = ("adapter-faithfulness", "adapter-event-completeness")
EXCLUSIONS: Tuple[str, ...] = ("adapter-external-effects", "realization-steps")

# The Stack effect contract frozen in specs/stack.pspec: forbidden io.*, optional
# debug.emit, default unspecified. The tracer hardcodes this rather than parsing the
# still-illustrative .pspec surface syntax.
_OPTIONAL_EXACT_EVENT = "debug.emit"
_FORBIDDEN_PREFIX = "io."


def _classify_event(name: str) -> str:
    if name == _OPTIONAL_EXACT_EVENT:
        return "optional"
    if name.startswith(_FORBIDDEN_PREFIX) and name != _FORBIDDEN_PREFIX:
        return "forbidden"
    return "unspecified"


@dataclass(frozen=True)
class ConformanceReport:
    result: str
    causes: Tuple[str, ...]
    events: Tuple[Tuple[str, str], ...]
    assumptions: Tuple[str, ...]
    exclusions: Tuple[str, ...]
    stderr: bytes = b""


class _AdapterError(Exception):
    def __init__(self, cause: str) -> None:
        super().__init__(cause)
        self.cause = cause


class _LineReader:
    """Reads LF-delimited lines from a raw fd, exposing whether more is already waiting."""

    def __init__(self, fd: int, chunk_size: int = 65536) -> None:
        self._fd = fd
        self._chunk_size = chunk_size
        self._buffer = b""
        self._eof = False

    def read_line(self, timeout: float) -> Optional[bytes]:
        deadline = time.monotonic() + timeout
        while b"\n" not in self._buffer:
            if self._eof:
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            ready, _, _ = select.select([self._fd], [], [], remaining)
            if not ready:
                raise TimeoutError
            chunk = os.read(self._fd, self._chunk_size)
            if chunk == b"":
                self._eof = True
                continue
            self._buffer += chunk
        line, _, self._buffer = self._buffer.partition(b"\n")
        return line

    def has_pending(self) -> bool:
        if self._buffer:
            return True
        if self._eof:
            return False
        ready, _, _ = select.select([self._fd], [], [], 0)
        return bool(ready)


class _Runner:
    """Owns the child session transport and the fixed protocol-level check plan."""

    def __init__(
        self,
        *,
        values: Sequence[int],
        max_depth: int,
        max_history: int,
        observation_limit: int,
        timeout_seconds: float,
    ) -> None:
        self.values = tuple(values)
        self.max_depth = max_depth
        self.max_history = max_history
        self.observation_limit = observation_limit
        self.timeout_seconds = timeout_seconds

        self.causes: List[str] = []
        self.events: List[Tuple[str, str]] = []
        self.stderr: bytes = b""
        self._retained: List[Tuple[str, Tuple[int, ...]]] = []

        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[_LineReader] = None
        self._seq = 0
        self._stderr_thread: Optional[threading.Thread] = None
        self._stderr_chunks: List[bytes] = []

    def add_cause(self, cause: str) -> None:
        if cause not in self.causes:
            self.causes.append(cause)

    # -- transport -----------------------------------------------------

    def start(self, command: Sequence[str]) -> None:
        command_list = list(command)
        if not command_list:
            raise OSError("empty command sequence")
        self._proc = subprocess.Popen(
            command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert self._proc.stdout is not None
        self._reader = _LineReader(self._proc.stdout.fileno())
        self._start_stderr_drain()

    def _start_stderr_drain(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stderr is not None

        def _drain() -> None:
            try:
                while True:
                    chunk = proc.stderr.read(65536)
                    if not chunk:
                        break
                    self._stderr_chunks.append(chunk)
            except (OSError, ValueError):
                pass

        self._stderr_thread = threading.Thread(target=_drain, daemon=True)
        self._stderr_thread.start()

    def close(self) -> Optional[str]:
        """Ends the session and returns a closure cause, if the lifecycle was unclean.

        Closes stdin, then inspects stdout through EOF and the process exit status
        against one coherent teardown deadline: an unread stdout line after the final
        response is ``EXTRA_STDOUT``, a nonzero exit is ``PROCESS_EXIT``, and failing to
        reach a clean EOF/exit within the deadline is ``TIMEOUT``. The child is always
        terminated/killed afterward so no process remains, regardless of this cause.
        """
        proc = self._proc
        if proc is None:
            return None
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
        except OSError:
            pass

        deadline = time.monotonic() + self.timeout_seconds
        try:
            closure_cause = self._await_clean_exit(deadline)
        finally:
            self._ensure_terminated()
            try:
                if proc.stderr is not None:
                    proc.stderr.close()
            except OSError:
                pass
            if self._stderr_thread is not None:
                self._stderr_thread.join(timeout=1.0)
            self.stderr = b"".join(self._stderr_chunks)
            try:
                if proc.stdout is not None:
                    proc.stdout.close()
            except OSError:
                pass
        return closure_cause

    def _await_clean_exit(self, deadline: float) -> Optional[str]:
        """Reads any post-EOF stdout and the exit status against ``deadline``."""
        assert self._reader is not None
        try:
            line = self._reader.read_line(deadline - time.monotonic())
        except TimeoutError:
            return "TIMEOUT"
        if line is not None:
            return "EXTRA_STDOUT"
        if self._reader.has_pending():
            # EOF reached with a nonempty, LF-less remainder: unterminated extra
            # output, not a clean close.
            return "EXTRA_STDOUT"

        proc = self._proc
        assert proc is not None
        try:
            returncode = proc.wait(timeout=max(deadline - time.monotonic(), 0.0))
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        return "PROCESS_EXIT" if returncode != 0 else None

    def _ensure_terminated(self) -> None:
        """Terminates a still-alive child after ``_await_clean_exit`` has already

        spent the one semantic teardown deadline: no further full wait before
        signalling, just terminate immediately, one bounded cleanup grace, then
        kill/wait.
        """
        proc = self._proc
        assert proc is not None
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def _classify_exit(self) -> str:
        proc = self._proc
        assert proc is not None
        try:
            returncode = proc.wait(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            returncode = None
        if returncode not in (0, None):
            return "PROCESS_EXIT"
        return "UNEXPECTED_EOF"

    def _send(self, payload: Dict[str, Any]) -> None:
        proc = self._proc
        assert proc is not None and proc.stdin is not None
        data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            proc.stdin.write(data)
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise _AdapterError(self._classify_exit())

    def _validate_envelope(self, response: Any, expected_seq: int) -> Dict[str, Any]:
        if not isinstance(response, dict):
            raise _AdapterError("RESPONSE_SHAPE")
        status = response.get("status")
        if status == "ok":
            if set(response) != {"seq", "status", "result", "events"}:
                raise _AdapterError("RESPONSE_SHAPE")
        elif status == "error":
            if set(response) != {"seq", "status", "error", "events"}:
                raise _AdapterError("RESPONSE_SHAPE")
            error = response.get("error")
            if (
                not isinstance(error, dict)
                or set(error) != {"code", "message"}
                or not isinstance(error.get("code"), str)
                or not error["code"]
                or not isinstance(error.get("message"), str)
                or not error["message"]
            ):
                raise _AdapterError("RESPONSE_SHAPE")
        else:
            raise _AdapterError("RESPONSE_SHAPE")

        seq = response.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq != expected_seq:
            raise _AdapterError("SEQUENCE_MISMATCH")

        events = response.get("events")
        if not isinstance(events, list) or any(not isinstance(e, str) or not e for e in events):
            raise _AdapterError("RESPONSE_SHAPE")
        return response

    def _receive(self, expected_seq: int) -> Dict[str, Any]:
        assert self._reader is not None
        try:
            line = self._reader.read_line(self.timeout_seconds)
        except TimeoutError:
            raise _AdapterError("TIMEOUT")
        if line is None:
            raise _AdapterError(self._classify_exit())
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            raise _AdapterError("RESPONSE_ENCODING")
        try:
            response = json.loads(text)
        except json.JSONDecodeError:
            raise _AdapterError("RESPONSE_JSON")
        envelope = self._validate_envelope(response, expected_seq)
        if self._reader.has_pending():
            raise _AdapterError("EXTRA_STDOUT")
        return envelope

    def _validate_result_shape(self, op: str, result: Any) -> None:
        if op in ("empty", "push"):
            if (
                not isinstance(result, dict)
                or set(result) != {"stack"}
                or not isinstance(result["stack"], str)
                or not result["stack"]
            ):
                raise _AdapterError("RESPONSE_SHAPE")
            return
        if not isinstance(result, dict):
            raise _AdapterError("RESPONSE_SHAPE")
        tag = result.get("tag")
        if tag == "none":
            if set(result) != {"tag"}:
                raise _AdapterError("RESPONSE_SHAPE")
        elif tag == "some":
            if (
                set(result) != {"tag", "value", "remainder"}
                or isinstance(result.get("value"), bool)
                or not isinstance(result.get("value"), int)
                or not isinstance(result.get("remainder"), str)
                or not result["remainder"]
            ):
                raise _AdapterError("RESPONSE_SHAPE")
        else:
            raise _AdapterError("RESPONSE_SHAPE")

    def _record_events(self, events: Sequence[str]) -> None:
        for name in events:
            disposition = _classify_event(name)
            self.events.append((name, disposition))
            if disposition == "forbidden":
                self.add_cause("FORBIDDEN_EVENT")

    def _call(self, op: str, args: Dict[str, Any]) -> Dict[str, Any]:
        seq = self._seq
        self._send({"seq": seq, "op": op, "args": args})
        response = self._receive(seq)
        self._seq += 1
        self._record_events(response["events"])
        if response["status"] == "error":
            raise _AdapterError("ADAPTER_ERROR")
        result = response["result"]
        self._validate_result_shape(op, result)
        return result

    # -- Stack primitives ------------------------------------------------

    def _empty(self) -> str:
        return self._call("empty", {})["stack"]

    def _push(self, handle: str, value: int) -> str:
        return self._call("push", {"stack": handle, "value": value})["stack"]

    def _pop(self, handle: str) -> Tuple[str, Optional[int], Optional[str]]:
        result = self._call("pop", {"stack": handle})
        if result["tag"] == "none":
            return "none", None, None
        return "some", result["value"], result["remainder"]

    # -- observation and checks ------------------------------------------

    def _observe_raw(self, handle: str, expected: Tuple[int, ...], cause: str) -> bool:
        """Pops ``handle`` to exhaustion (bounded), comparing against ``expected``.

        Returns True if the traversal terminated within the observation bound.
        """
        obtained: List[int] = []
        current = handle
        for _ in range(self.observation_limit):
            tag, value, remainder = self._pop(current)
            if tag == "none":
                if tuple(obtained) != expected:
                    self.add_cause(cause)
                return True
            obtained.append(value)  # type: ignore[arg-type]
            current = remainder  # type: ignore[assignment]
        self.add_cause("OBSERVATION_LIMIT")
        return False

    def recheck_retained(self) -> None:
        for handle, expected in list(self._retained):
            self._observe_raw(handle, expected, "RETAINED_HANDLE_CHANGED")

    def check_pop_empty(self, handle: str) -> None:
        tag, _value, _remainder = self._pop(handle)
        if tag != "none":
            self.add_cause("POP_EMPTY")
            return
        self._retained.append((handle, ()))

    def check_pop_push(
        self, handle: str, expected_value: int, expected_remainder: Tuple[int, ...]
    ) -> None:
        tag, value, remainder = self._pop(handle)
        if tag != "some" or remainder is None:
            self.add_cause("POP_PUSH_VALUE")
            return
        if value != expected_value:
            self.add_cause("POP_PUSH_VALUE")
        if self._observe_raw(remainder, expected_remainder, "POP_PUSH_REMAINDER"):
            self._retained.append((remainder, expected_remainder))

    def observe_and_check(self, handle: str, expected: Tuple[int, ...], cause: str) -> None:
        if self._observe_raw(handle, expected, cause):
            self._retained.append((handle, expected))

    def run_plan(self) -> None:
        depth = max(0, min(self.max_depth, self.max_history, len(self.values)))

        handle = self._empty()
        self.check_pop_empty(handle)

        sequence: Tuple[int, ...] = ()
        for index in range(depth):
            value = self.values[index]
            next_handle = self._push(handle, value)
            self.recheck_retained()

            next_sequence = (value,) + sequence
            self._retained.append((next_handle, next_sequence))

            self.check_pop_push(next_handle, value, sequence)
            self.recheck_retained()

            handle, sequence = next_handle, next_sequence

        if depth > 0:
            self.observe_and_check(handle, sequence, "OBSERVATION_ORDER")


def run_stack_conformance(
    command: Sequence[str],
    *,
    values: Sequence[int],
    max_depth: int,
    max_history: int,
    observation_limit: int,
    timeout_seconds: float,
) -> ConformanceReport:
    runner = _Runner(
        values=values,
        max_depth=max_depth,
        max_history=max_history,
        observation_limit=observation_limit,
        timeout_seconds=timeout_seconds,
    )
    errored = False
    started = True
    try:
        runner.start(command)
    except OSError:
        runner.add_cause("PROCESS_START")
        errored = True
        started = False

    if started:
        try:
            try:
                runner.run_plan()
            except _AdapterError as error:
                runner.add_cause(error.cause)
                errored = True
        finally:
            closure_cause = runner.close()
            if closure_cause is not None:
                runner.add_cause(closure_cause)
                errored = True

    if errored:
        result = "error"
    elif runner.causes:
        result = "challenges"
    else:
        result = "supports"

    return ConformanceReport(
        result=result,
        causes=tuple(runner.causes),
        events=tuple(runner.events),
        assumptions=ASSUMPTIONS,
        exclusions=EXCLUSIONS,
        stderr=runner.stderr,
    )
