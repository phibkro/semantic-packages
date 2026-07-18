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

import hashlib
import json
import math
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

_DECLARATIONS: Tuple[str, ...] = (
    "pop-empty",
    "pop-push",
    "persistence",
    "stack-effects",
)

_SPECIFICATION_REFERENCE = ("specification", "stack", "0.1.0")
_SPECIFICATION_SHA256 = "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1"
_PROFILE_REFERENCE = ("realizationProfile", "stack-default", "0.1.0")
_PROFILE_SHA256 = "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb"
_CAMPAIGN_ALGORITHM = "stack-conformance-campaign"
_CAMPAIGN_ALGORITHM_VERSION = "1"
_CAMPAIGN_SEED = 20260718


@dataclass(frozen=True)
class RecordInput:
    reference: Tuple[str, str, str]
    sha256: str


@dataclass(frozen=True)
class EventContract:
    forbidden: Tuple[str, ...]
    optional: Tuple[str, ...]
    default: str


@dataclass(frozen=True)
class PlanStep:
    op: str
    source: Optional[str] = None
    bind: Optional[str] = None
    value: Optional[int] = None


@dataclass(frozen=True)
class PlannedObservation:
    declaration_id: str
    binding: str
    top_first: Tuple[int, ...]


@dataclass(frozen=True)
class ConformanceCase:
    case_id: str
    origin: str
    steps: Tuple[PlanStep, ...]
    observations: Tuple[PlannedObservation, ...]


def _canonical_value(value: Any) -> Any:
    """Return the JSON value used for stable plan and case provenance."""
    if isinstance(value, RecordInput):
        return {"reference": list(value.reference), "sha256": value.sha256}
    if isinstance(value, EventContract):
        return {
            "default": value.default,
            "forbidden": list(value.forbidden),
            "optional": list(value.optional),
        }
    if isinstance(value, PlanStep):
        result: Dict[str, Any] = {"op": value.op}
        if value.source is not None:
            result["source"] = value.source
        if value.bind is not None:
            result["bind"] = value.bind
        if value.value is not None:
            result["value"] = value.value
        return result
    if isinstance(value, PlannedObservation):
        return {
            "binding": value.binding,
            "declaration_id": value.declaration_id,
            "top_first": list(value.top_first),
        }
    if isinstance(value, ConformanceCase):
        return {
            "case_id": value.case_id,
            "observations": [_canonical_value(item) for item in value.observations],
            "origin": value.origin,
            "steps": [_canonical_value(item) for item in value.steps],
        }
    if isinstance(value, StackConformancePlan):
        return {
            "algorithm": value.algorithm,
            "algorithm_version": value.algorithm_version,
            "cases": [_canonical_value(item) for item in value.cases],
            "element_domain": list(value.element_domain),
            "event_contract": _canonical_value(value.event_contract),
            "max_depth": value.max_depth,
            "max_history": value.max_history,
            "observation_limit": value.observation_limit,
            "profile": _canonical_value(value.profile),
            "seed": value.seed,
            "specification": _canonical_value(value.specification),
            "timeout_seconds": value.timeout_seconds,
        }
    raise TypeError(f"no canonical JSON form for {type(value).__name__}")


@dataclass(frozen=True)
class StackConformancePlan:
    specification: RecordInput
    profile: RecordInput
    element_domain: Tuple[int, ...]
    max_depth: int
    max_history: int
    observation_limit: int
    algorithm: str
    algorithm_version: str
    seed: int
    timeout_seconds: float
    event_contract: EventContract
    cases: Tuple[ConformanceCase, ...]

    def canonical_json(self) -> str:
        return json.dumps(
            _canonical_value(self),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CaseObservation:
    case_id: str
    declaration_id: str
    result: str
    expected_top_first: Tuple[int, ...]
    observed_top_first: Tuple[int, ...]
    causes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DeclarationOutcome:
    declaration_id: str
    result: str
    causes: Tuple[str, ...] = ()


def _case(
    case_id: str,
    origin: str,
    steps: Sequence[PlanStep],
    declaration_id: str,
    binding: str,
    top_first: Sequence[int],
) -> ConformanceCase:
    return ConformanceCase(
        case_id=case_id,
        origin=origin,
        steps=tuple(steps),
        observations=(
            PlannedObservation(declaration_id, binding, tuple(top_first)),
        ),
    )


def _generated_mixed_case(seed: int, max_depth: int, max_history: int) -> ConformanceCase:
    """Generate a reproducible bounded history without relying on host RNG details."""
    steps: List[PlanStep] = [PlanStep("empty", bind="g0")]
    current = "g0"
    state: Tuple[int, ...] = ()
    word = seed & 0xFFFFFFFF
    next_binding = 1

    # Reach the profile boundary first, then retain that logical state while the
    # remainder of the history mixes pushes and pops. This makes depth coverage a
    # planned observation rather than an incidental transient.
    while len(state) < max_depth and len(steps) < max_history:
        word = (1664525 * word + 1013904223) & 0xFFFFFFFF
        value = (word % 5) - 2
        binding = f"g{next_binding}"
        next_binding += 1
        steps.append(PlanStep("push", source=current, bind=binding, value=value))
        state = (value,) + state
        current = binding

    observed_binding = current
    observed_state = state
    while len(steps) < max_history:
        word = (1664525 * word + 1013904223) & 0xFFFFFFFF
        choose_push = ((word >> 16) & 1) == 0
        if not state:
            choose_push = True
        elif len(state) >= max_depth:
            choose_push = False

        if choose_push:
            value = (word % 5) - 2
            binding = f"g{next_binding}"
            next_binding += 1
            steps.append(PlanStep("push", source=current, bind=binding, value=value))
            state = (value,) + state
            current = binding
        else:
            binding = f"g{next_binding}"
            next_binding += 1
            steps.append(PlanStep("pop", source=current, bind=binding))
            state = state[1:]
            current = binding

    return _case(
        f"generated-mixed-{seed}-v1",
        "generated",
        steps,
        "pop-push",
        observed_binding,
        observed_state,
    )


def default_stack_conformance_plan() -> StackConformancePlan:
    depth_steps: List[PlanStep] = [PlanStep("empty", bind="d0")]
    depth_values: Tuple[int, ...] = ()
    source = "d0"
    for index, value in enumerate((-2, -1, 0, 1, 2, -2, 1, 0), start=1):
        binding = f"d{index}"
        depth_steps.append(PlanStep("push", source=source, bind=binding, value=value))
        depth_values = (value,) + depth_values
        source = binding

    seed = _CAMPAIGN_SEED
    cases = (
        _case(
            "curated-pop-empty-v1",
            "curated",
            (PlanStep("empty", bind="empty"), PlanStep("pop", source="empty")),
            "pop-empty",
            "empty",
            (),
        ),
        _case(
            "curated-pop-push-v1",
            "curated",
            (
                PlanStep("empty", bind="base"),
                PlanStep("push", source="base", bind="one", value=2),
                PlanStep("pop", source="one", bind="remainder"),
            ),
            "pop-push",
            "remainder",
            (),
        ),
        _case(
            "curated-depth-eight-repeated-v1",
            "curated",
            depth_steps,
            "pop-push",
            source,
            depth_values,
        ),
        ConformanceCase(
            case_id="curated-retained-source-push-v1",
            origin="curated",
            steps=(
                PlanStep("empty", bind="root"),
                PlanStep("push", source="root", bind="source", value=1),
                PlanStep("push", source="source", bind="derived", value=2),
            ),
            observations=(
                PlannedObservation("persistence", "root", ()),
                PlannedObservation("persistence", "source", (1,)),
            ),
        ),
        ConformanceCase(
            case_id="curated-retained-source-pop-v1",
            origin="curated",
            steps=(
                PlanStep("empty", bind="root"),
                PlanStep("push", source="root", bind="one", value=1),
                PlanStep("push", source="one", bind="source", value=2),
                PlanStep("pop", source="source", bind="remainder"),
            ),
            observations=(
                PlannedObservation("persistence", "root", ()),
                PlannedObservation("persistence", "one", (1,)),
                PlannedObservation("persistence", "source", (2, 1)),
            ),
        ),
        _case(
            "curated-stack-effects-v1",
            "curated",
            (PlanStep("empty", bind="effect_state"),),
            "stack-effects",
            "effect_state",
            (),
        ),
        _generated_mixed_case(seed, 8, 32),
    )
    plan = StackConformancePlan(
        specification=RecordInput(
            _SPECIFICATION_REFERENCE,
            _SPECIFICATION_SHA256,
        ),
        profile=RecordInput(
            _PROFILE_REFERENCE,
            _PROFILE_SHA256,
        ),
        element_domain=(-2, -1, 0, 1, 2),
        max_depth=8,
        max_history=32,
        observation_limit=9,
        algorithm=_CAMPAIGN_ALGORITHM,
        algorithm_version=_CAMPAIGN_ALGORITHM_VERSION,
        seed=seed,
        timeout_seconds=0.20,
        event_contract=EventContract(("io.*",), ("debug.emit",), "unspecified"),
        cases=cases,
    )
    validate_stack_conformance_plan(plan)
    return plan


def _valid_binding(binding: Any) -> bool:
    if not isinstance(binding, str) or not binding:
        return False
    return binding[0].islower() and all(
        character.islower() or character.isdigit() or character == "_"
        for character in binding
    )


def validate_stack_conformance_plan(plan: StackConformancePlan) -> None:
    if not isinstance(plan, StackConformancePlan):
        raise ValueError("plan must be a StackConformancePlan")
    if (
        plan.algorithm != _CAMPAIGN_ALGORITHM
        or plan.algorithm_version != _CAMPAIGN_ALGORITHM_VERSION
    ):
        raise ValueError("algorithm and version must match the tracer campaign")
    if plan.specification != RecordInput(
        _SPECIFICATION_REFERENCE, _SPECIFICATION_SHA256
    ):
        raise ValueError("specification input must match the canonical tracer record")
    if plan.profile != RecordInput(_PROFILE_REFERENCE, _PROFILE_SHA256):
        raise ValueError("profile input must match the canonical tracer record")
    if (
        isinstance(plan.max_depth, bool)
        or not isinstance(plan.max_depth, int)
        or isinstance(plan.max_history, bool)
        or not isinstance(plan.max_history, int)
        or plan.max_depth < 1
        or plan.max_history < 1
    ):
        raise ValueError("plan bounds must be positive")
    if (
        isinstance(plan.observation_limit, bool)
        or not isinstance(plan.observation_limit, int)
        or plan.observation_limit < plan.max_depth + 1
    ):
        raise ValueError("observation limit must exceed maximum depth")
    if (
        isinstance(plan.timeout_seconds, bool)
        or not isinstance(plan.timeout_seconds, (int, float))
        or not math.isfinite(plan.timeout_seconds)
        or plan.timeout_seconds <= 0
    ):
        raise ValueError("timeout must be positive")
    if not plan.element_domain or any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in plan.element_domain
    ):
        raise ValueError("element domain must contain JSON integers")
    if len(set(plan.element_domain)) != len(plan.element_domain):
        raise ValueError("element domain values must be unique")
    if not plan.algorithm or not plan.algorithm_version or isinstance(plan.seed, bool):
        raise ValueError("algorithm, version, and integer seed are required")
    if not isinstance(plan.seed, int):
        raise ValueError("algorithm seed must be an integer")
    for record_input in (plan.specification, plan.profile):
        if (
            len(record_input.reference) != 3
            or any(not isinstance(item, str) or not item for item in record_input.reference)
            or len(record_input.sha256) != 64
            or any(character not in "0123456789abcdef" for character in record_input.sha256)
        ):
            raise ValueError("record input reference and sha256 must be exact")
    if plan.event_contract.default != "unspecified":
        raise ValueError("event contract default must be unspecified")
    event_patterns = plan.event_contract.forbidden + plan.event_contract.optional
    if any(not isinstance(item, str) or not item for item in event_patterns):
        raise ValueError("event patterns must be nonempty strings")

    if not plan.cases:
        raise ValueError("plan must contain cases")
    case_ids: set[str] = set()
    for case in plan.cases:
        if (
            not isinstance(case.case_id, str)
            or not case.case_id
            or case.case_id in case_ids
        ):
            raise ValueError("case IDs must be nonempty and unique")
        case_ids.add(case.case_id)
        if case.origin not in ("curated", "generated"):
            raise ValueError("case origin must be curated or generated")
        if not case.steps or len(case.steps) > plan.max_history:
            raise ValueError("case history exceeds plan bounds")

        bindings: Dict[str, Tuple[int, ...]] = {}
        for step in case.steps:
            if step.op == "empty":
                if step.source is not None or step.value is not None or step.bind is None:
                    raise ValueError("empty operation shape is invalid")
                state: Tuple[int, ...] = ()
            elif step.op == "push":
                if (
                    not _valid_binding(step.source)
                    or step.source not in bindings
                    or step.bind is None
                    or step.value not in plan.element_domain
                    or isinstance(step.value, bool)
                ):
                    raise ValueError("push operation has an unknown binding or value")
                state = (step.value,) + bindings[step.source]  # type: ignore[operator]
            elif step.op == "pop":
                if (
                    not _valid_binding(step.source)
                    or step.source not in bindings
                    or step.value is not None
                ):
                    raise ValueError("pop operation has an unknown binding")
                source_state = bindings[step.source]
                if source_state:
                    if step.bind is None:
                        raise ValueError("nonempty pop must bind its remainder")
                    state = source_state[1:]
                else:
                    if step.bind is not None:
                        raise ValueError("empty pop cannot bind a remainder")
                    continue
            else:
                raise ValueError("operation must be empty, push, or pop")

            if not _valid_binding(step.bind):
                raise ValueError("binding names must be logical lowercase identifiers")
            assert step.bind is not None
            if step.bind in bindings:
                raise ValueError("binding names must be unique within a case")
            if len(state) > plan.max_depth:
                raise ValueError("case depth exceeds plan bounds")
            bindings[step.bind] = state

        if not case.observations:
            raise ValueError("each case needs at least one observation")
        observation_keys: set[Tuple[str, str]] = set()
        for observation in case.observations:
            if observation.declaration_id not in _DECLARATIONS:
                raise ValueError("observation declaration is unknown")
            if observation.binding not in bindings:
                raise ValueError("observation references an unknown binding")
            observation_key = (observation.declaration_id, observation.binding)
            if observation_key in observation_keys:
                raise ValueError("duplicate case observation")
            observation_keys.add(observation_key)
            if tuple(observation.top_first) != bindings[observation.binding]:
                raise ValueError("observation disagrees with derived logical state")
            if len(observation.top_first) + 1 > plan.observation_limit:
                raise ValueError("observation exceeds plan limit")

    generated = tuple(case for case in plan.cases if case.origin == "generated")
    expected_generated = (
        _generated_mixed_case(plan.seed, plan.max_depth, plan.max_history),
    )
    if generated != expected_generated:
        raise ValueError("generated cases do not match seed, algorithm, and bounds")


def _unique(items: Sequence[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def summarize_stack_conformance(
    observations: Sequence[CaseObservation],
    *,
    events: Sequence[Tuple[str, str]] = (),
    execution_causes: Sequence[str] = (),
    assumptions: Sequence[str] = ASSUMPTIONS,
    exclusions: Sequence[str] = EXCLUSIONS,
    stderr: bytes = b"",
    plan_sha256: Optional[str] = None,
) -> ConformanceReport:
    retained_observations = tuple(observations)
    retained_events = tuple(events)
    outcomes: List[DeclarationOutcome] = []
    semantic_causes: List[str] = []
    for declaration_id in _DECLARATIONS:
        selected = tuple(
            item for item in retained_observations if item.declaration_id == declaration_id
        )
        causes = [cause for item in selected for cause in item.causes]
        if declaration_id == "stack-effects" and any(
            disposition == "forbidden" for _name, disposition in retained_events
        ):
            causes.append("FORBIDDEN_EVENT")
        unique_causes = _unique(causes)
        semantic_causes.extend(unique_causes)
        if unique_causes or any(item.result == "challenges" for item in selected):
            result = "challenges"
        elif selected and all(item.result == "supports" for item in selected):
            result = "supports"
        else:
            result = "inconclusive"
        outcomes.append(DeclarationOutcome(declaration_id, result, unique_causes))

    execution = _unique(tuple(execution_causes))
    causes = _unique(execution + tuple(semantic_causes))
    if execution:
        result = "error"
    elif any(item.result == "challenges" for item in outcomes):
        result = "challenges"
    elif all(item.result == "supports" for item in outcomes):
        result = "supports"
    else:
        result = "inconclusive"
    return ConformanceReport(
        result=result,
        causes=causes,
        events=retained_events,
        assumptions=tuple(assumptions),
        exclusions=tuple(exclusions),
        stderr=stderr,
        observations=retained_observations,
        declaration_outcomes=tuple(outcomes),
        plan_sha256=plan_sha256,
    )


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
    observations: Tuple[CaseObservation, ...] = ()
    declaration_outcomes: Tuple[DeclarationOutcome, ...] = ()
    plan_sha256: Optional[str] = None


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
        event_contract: Optional[EventContract] = None,
    ) -> None:
        self.values = tuple(values)
        self.max_depth = max_depth
        self.max_history = max_history
        self.observation_limit = observation_limit
        self.timeout_seconds = timeout_seconds
        self.event_contract = event_contract

        self.causes: List[str] = []
        self.events: List[Tuple[str, str]] = []
        self.campaign_observations: List[CaseObservation] = []
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
            disposition = self._event_disposition(name)
            self.events.append((name, disposition))
            if disposition == "forbidden":
                self.add_cause("FORBIDDEN_EVENT")

    def _event_disposition(self, name: str) -> str:
        contract = self.event_contract
        if contract is None:
            return _classify_event(name)
        for pattern in contract.forbidden:
            if pattern.endswith(".*"):
                prefix = pattern[:-1]
                if name.startswith(prefix) and len(name) > len(prefix):
                    return "forbidden"
            elif name == pattern:
                return "forbidden"
        for pattern in contract.optional:
            if pattern.endswith(".*"):
                prefix = pattern[:-1]
                if name.startswith(prefix) and len(name) > len(prefix):
                    return "optional"
            elif name == pattern:
                return "optional"
        return contract.default

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

    def _observe_expected(
        self, handle: str, expected: Tuple[int, ...]
    ) -> Tuple[Tuple[int, ...], str]:
        """Observe one plan-owned finite state and retain why traversal stopped."""
        obtained: List[int] = []
        current = handle
        for _expected_value in expected:
            tag, value, remainder = self._pop(current)
            if tag == "none":
                return tuple(obtained), "early-none"
            assert value is not None and remainder is not None
            obtained.append(value)
            current = remainder
        tag, value, _remainder = self._pop(current)
        if tag == "none":
            return tuple(obtained), "complete"
        assert value is not None
        obtained.append(value)
        return tuple(obtained), "nonempty-tail"

    def _record_campaign_observation(
        self,
        *,
        case_id: str,
        declaration_id: str,
        result: str,
        expected: Tuple[int, ...],
        observed: Tuple[int, ...],
        causes: Sequence[str] = (),
    ) -> None:
        self.campaign_observations.append(
            CaseObservation(
                case_id=case_id,
                declaration_id=declaration_id,
                result=result,
                expected_top_first=expected,
                observed_top_first=observed,
                causes=_unique(causes),
            )
        )

    def run_campaign(self, plan: StackConformancePlan) -> Tuple[CaseObservation, ...]:
        """Execute logical histories while keeping all adapter tokens opaque."""
        self.campaign_observations = []
        for case in plan.cases:
            handles: Dict[str, Optional[str]] = {}
            states: Dict[str, Tuple[int, ...]] = {}
            persistence_baselines: Dict[str, Tuple[Tuple[int, ...], str]] = {}
            for step in case.steps:
                for planned in case.observations:
                    baseline_handle = handles.get(planned.binding)
                    if (
                        planned.declaration_id == "persistence"
                        and step.source == planned.binding
                        and baseline_handle is not None
                        and planned.binding not in persistence_baselines
                    ):
                        persistence_baselines[planned.binding] = self._observe_expected(
                            baseline_handle, planned.top_first
                        )
                if step.op == "empty":
                    assert step.bind is not None
                    handles[step.bind] = self._empty()
                    states[step.bind] = ()
                elif step.op == "push":
                    assert step.source is not None and step.bind is not None
                    assert step.value is not None
                    source_handle = handles.get(step.source)
                    handles[step.bind] = (
                        self._push(source_handle, step.value)
                        if source_handle is not None
                        else None
                    )
                    states[step.bind] = (step.value,) + states[step.source]
                else:
                    assert step.op == "pop" and step.source is not None
                    expected_source = states[step.source]
                    source_handle = handles.get(step.source)
                    if source_handle is None:
                        if expected_source:
                            assert step.bind is not None
                            handles[step.bind] = None
                            states[step.bind] = expected_source[1:]
                        continue
                    tag, value, remainder = self._pop(source_handle)
                    if not expected_source:
                        if tag != "none":
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-empty",
                                result="challenges",
                                expected=(),
                                observed=(() if value is None else (value,)),
                                causes=("POP_EMPTY",),
                            )
                    elif tag != "some" or remainder is None:
                        assert step.bind is not None
                        handles[step.bind] = None
                        states[step.bind] = expected_source[1:]
                        self._record_campaign_observation(
                            case_id=case.case_id,
                            declaration_id="pop-push",
                            result="challenges",
                            expected=(expected_source[0],),
                            observed=(),
                            causes=("POP_PUSH_VALUE",),
                        )
                    else:
                        if value != expected_source[0]:
                            assert value is not None
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-push",
                                result="challenges",
                                expected=(expected_source[0],),
                                observed=(value,),
                                causes=("POP_PUSH_VALUE",),
                            )
                        assert step.bind is not None
                        handles[step.bind] = remainder
                        expected_remainder = expected_source[1:]
                        states[step.bind] = expected_remainder
                        observed_remainder, remainder_status = self._observe_expected(
                            remainder, expected_remainder
                        )
                        if (
                            remainder_status == "nonempty-tail"
                            and observed_remainder[:-1] == expected_remainder
                        ):
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-empty",
                                result="challenges",
                                expected=(),
                                observed=(observed_remainder[-1],),
                                causes=("POP_EMPTY",),
                            )
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-push",
                                result="inconclusive",
                                expected=expected_remainder,
                                observed=observed_remainder,
                            )
                        elif (
                            remainder_status != "complete"
                            or observed_remainder != expected_remainder
                        ):
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-push",
                                result="challenges",
                                expected=expected_remainder,
                                observed=observed_remainder,
                                causes=("POP_PUSH_REMAINDER",),
                            )

            for planned in case.observations:
                causes: List[str] = []
                result = "supports"
                planned_handle = handles.get(planned.binding)
                if planned_handle is None:
                    observed: Tuple[int, ...] = ()
                    result = "inconclusive"
                elif planned.declaration_id == "stack-effects":
                    # Effect evidence is the event trace already retained from every
                    # invocation; Stack-state traversal cannot challenge this concern.
                    observed = planned.top_first
                elif planned.declaration_id == "persistence":
                    observed, status = self._observe_expected(
                        planned_handle, planned.top_first
                    )
                    baseline = persistence_baselines.get(planned.binding)
                    if baseline is None or baseline[1] != "complete":
                        result = "inconclusive"
                    elif status != "complete" or observed != baseline[0]:
                        causes.append("RETAINED_HANDLE_CHANGED")
                else:
                    observed, status = self._observe_expected(
                        planned_handle, planned.top_first
                    )
                    if (
                        status == "nonempty-tail"
                        and observed[:-1] == planned.top_first
                    ):
                        if planned.declaration_id == "pop-empty":
                            causes.append("POP_EMPTY")
                        else:
                            result = "inconclusive"
                            self._record_campaign_observation(
                                case_id=case.case_id,
                                declaration_id="pop-empty",
                                result="challenges",
                                expected=(),
                                observed=(observed[-1],),
                                causes=("POP_EMPTY",),
                            )
                    elif status == "early-none" or observed != planned.top_first:
                        pop_bindings = {
                            step.bind for step in case.steps if step.op == "pop"
                        }
                        if planned.binding in pop_bindings:
                            causes.append("POP_PUSH_REMAINDER")
                        else:
                            causes.append("OBSERVATION_ORDER")
                unique_causes = _unique(causes)
                if unique_causes:
                    result = "challenges"
                self._record_campaign_observation(
                    case_id=case.case_id,
                    declaration_id=planned.declaration_id,
                    result=result,
                    expected=planned.top_first,
                    observed=observed,
                    causes=unique_causes,
                )
        return tuple(self.campaign_observations)

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
    values: Optional[Sequence[int]] = None,
    max_depth: Optional[int] = None,
    max_history: Optional[int] = None,
    observation_limit: Optional[int] = None,
    timeout_seconds: Optional[float] = None,
    plan: Optional[StackConformancePlan] = None,
) -> ConformanceReport:
    if plan is not None:
        if any(
            item is not None
            for item in (
                values,
                max_depth,
                max_history,
                observation_limit,
                timeout_seconds,
            )
        ):
            raise ValueError("plan cannot be combined with legacy campaign arguments")
        validate_stack_conformance_plan(plan)
        if plan != default_stack_conformance_plan():
            raise ValueError("evidence execution requires the exact default campaign plan")
        runner = _Runner(
            values=plan.element_domain,
            max_depth=plan.max_depth,
            max_history=plan.max_history,
            observation_limit=plan.observation_limit,
            timeout_seconds=plan.timeout_seconds,
            event_contract=plan.event_contract,
        )
        execution_causes: List[str] = []
        observations: Tuple[CaseObservation, ...] = ()
        started = True
        try:
            runner.start(command)
        except OSError:
            execution_causes.append("PROCESS_START")
            started = False

        if started:
            try:
                try:
                    observations = runner.run_campaign(plan)
                except _AdapterError as error:
                    execution_causes.append(error.cause)
                    observations = tuple(runner.campaign_observations)
            finally:
                closure_cause = runner.close()
                if closure_cause is not None:
                    execution_causes.append(closure_cause)

        return summarize_stack_conformance(
            observations,
            events=runner.events,
            execution_causes=execution_causes,
            stderr=runner.stderr,
            plan_sha256=plan.sha256,
        )

    if any(
        item is None
        for item in (values, max_depth, max_history, observation_limit, timeout_seconds)
    ):
        raise TypeError("legacy campaign arguments are required when plan is absent")
    assert values is not None
    assert max_depth is not None
    assert max_history is not None
    assert observation_limit is not None
    assert timeout_seconds is not None
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
