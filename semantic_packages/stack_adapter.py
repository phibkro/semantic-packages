#!/usr/bin/env python3
"""Reference ``stack-runner-json-v1`` child adapter.

Speaks the tracer protocol described in ``docs/design/adapter-protocol.md`` over
stdin/stdout: one UTF-8, LF-delimited JSON request per response, in lockstep, until
the harness closes stdin. The Stack Realization behind this adapter lives in
``stack_realization`` and is opaque to the conformance runner.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict

from semantic_packages import stack_realization as realization


class _Session:
    def __init__(self) -> None:
        self._next_handle = 0
        self._stacks: Dict[str, realization.Stack] = {}

    def _new_handle(self, stack: realization.Stack) -> str:
        handle = f"h{self._next_handle}"
        self._next_handle += 1
        self._stacks[handle] = stack
        return handle

    def empty(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {"stack": self._new_handle(realization.empty())}

    def push(self, args: Dict[str, Any]) -> Dict[str, Any]:
        stack = self._stacks[args["stack"]]
        return {"stack": self._new_handle(realization.push(stack, args["value"]))}

    def pop(self, args: Dict[str, Any]) -> Dict[str, Any]:
        stack = self._stacks[args["stack"]]
        popped = realization.pop(stack)
        if popped is None:
            return {"tag": "none"}
        value, remainder = popped
        return {"tag": "some", "value": value, "remainder": self._new_handle(remainder)}


_OPERATIONS: Dict[str, Callable[[_Session, Dict[str, Any]], Dict[str, Any]]] = {
    "empty": _Session.empty,
    "push": _Session.push,
    "pop": _Session.pop,
}


def _error(seq: int, code: str, message: str) -> Dict[str, Any]:
    return {"seq": seq, "status": "error", "error": {"code": code, "message": message}, "events": []}


def _handle_request(session: _Session, request: Dict[str, Any], seq: int) -> Dict[str, Any]:
    operation = _OPERATIONS.get(request.get("op"))
    if operation is None:
        return _error(seq, "bad-request-op", f"unsupported operation {request.get('op')!r}")
    try:
        result = operation(session, request.get("args", {}))
    except (KeyError, TypeError) as error:
        return _error(seq, "bad-request-args", str(error))
    return {"seq": seq, "status": "ok", "result": result, "events": []}


def main() -> int:
    session = _Session()
    seq = 0
    for line in sys.stdin.buffer:
        request = json.loads(line)
        response = _handle_request(session, request, seq)
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
        sys.stdout.flush()
        seq += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
