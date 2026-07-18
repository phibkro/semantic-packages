#!/usr/bin/env python3
"""Table-driven child adapters for the stack-runner-json-v1 test oracle.

This is test data, not a Realization.  It intentionally uses a tiny list-backed
model so that runner tests do not import or share product Stack operations.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any


MODE = sys.argv[1] if len(sys.argv) > 1 else "reference"
MODE_ARGUMENTS = sys.argv[2:]

PUSH_MUTATIONS = {
    "destructive-push": "every-source-new-handle",
    "destructive-push-nonempty": "nonempty-source-same-handle",
}
IMMEDIATE_EXTRA_STDOUT = {
    "extra-stdout": '{"extra":true}\n',
    "extra-stdout-unterminated": '{"extra":true}',
}
POST_EOF_ACTIONS = {
    "eof-marker": "marker",
    "eof-nonzero": "nonzero",
    "eof-timeout": "ignore-term-and-wait",
    "eof-extra-stdout": "extra-stdout",
}
STDERR_PAYLOADS = {
    "stderr-bytes": b"adapter diagnostic: \xff\x00\n",
}


class FakeStackAdapter:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.next_handle = 0
        self.states: dict[str, list[int]] = {}
        self.interned: dict[tuple[int, ...], str] = {}

    def _new_handle(self, values: list[int]) -> str:
        key = tuple(values)
        if self.mode == "interned" and key in self.interned:
            return self.interned[key]

        handle = f"opaque-{self.next_handle}"
        self.next_handle += 1
        self.states[handle] = list(values)
        if self.mode == "interned":
            self.interned[key] = handle
        return handle

    def _events(self) -> list[str]:
        if self.mode == "optional-event":
            return ["debug.emit"]
        if self.mode == "forbidden-event":
            return ["io.read"]
        if self.mode == "unspecified-event":
            return ["custom.audit"]
        if self.mode == "ordered-events":
            return ["debug.emit", "custom.audit"]
        return []

    def _error(self, seq: int, code: str, message: str) -> dict[str, Any]:
        return {
            "seq": seq,
            "status": "error",
            "error": {"code": code, "message": message},
            "events": self._events(),
        }

    def _validate_request(self, request: Any, expected_seq: int) -> dict[str, Any] | None:
        if not isinstance(request, dict) or set(request) != {"seq", "op", "args"}:
            return self._error(expected_seq, "bad-request-shape", "request keys differ")
        if request["seq"] != expected_seq or isinstance(request["seq"], bool):
            return self._error(expected_seq, "bad-request-seq", "sequence is not monotonic")
        if request["op"] not in {"empty", "push", "pop"}:
            return self._error(expected_seq, "bad-request-op", "operation is not selected")
        args = request["args"]
        if not isinstance(args, dict):
            return self._error(expected_seq, "bad-request-args", "args is not an object")
        expected_keys = {
            "empty": set(),
            "push": {"stack", "value"},
            "pop": {"stack"},
        }[request["op"]]
        if set(args) != expected_keys:
            return self._error(expected_seq, "bad-request-args", "operation args differ")
        if request["op"] in {"push", "pop"}:
            stack = args.get("stack")
            if not isinstance(stack, str) or not stack or stack not in self.states:
                return self._error(expected_seq, "unknown-handle", "handle is not live")
        if request["op"] == "push":
            value = args.get("value")
            if isinstance(value, bool) or not isinstance(value, int) or value not in range(-2, 3):
                return self._error(expected_seq, "bad-element", "value is outside profile")
        return None

    def respond(self, request: dict[str, Any], expected_seq: int) -> dict[str, Any] | None:
        request_error = self._validate_request(request, expected_seq)
        if request_error is not None:
            return request_error

        seq = request["seq"]
        if self.mode == "early-eof":
            return None
        if self.mode == "timeout":
            time.sleep(10)
        if self.mode == "nonzero-exit":
            raise SystemExit(7)
        if self.mode == "status-error":
            return self._error(seq, "adapter-error", "intentional adapter failure")

        op = request["op"]
        args = request["args"]
        if op == "empty":
            stack = self._new_handle([])
            result: dict[str, Any] = {"stack": stack}
        elif op == "push":
            source = args["stack"]
            value = args["value"]
            mutation = PUSH_MUTATIONS.get(self.mode)
            if mutation == "every-source-new-handle":
                self.states[source].insert(0, value)
                stack = self._new_handle(self.states[source])
            elif mutation == "nonempty-source-same-handle" and self.states[source]:
                self.states[source].insert(0, value)
                stack = source
            else:
                stack = self._new_handle([value, *self.states[source]])
            result = {"stack": stack}
        else:
            source = args["stack"]
            values = self.states[source]
            if self.mode == "nonterminating-observation":
                result = {"tag": "some", "value": 0, "remainder": source}
            elif not values:
                if self.mode == "wrong-empty":
                    result = {"tag": "some", "value": 0, "remainder": source}
                else:
                    result = {"tag": "none"}
            else:
                if self.mode in {"bottom-first", "shallow-liar"} and len(values) >= 2:
                    value = values[-1]
                    remainder_values = values[:-1]
                else:
                    value = values[0]
                    remainder_values = values[1:]
                if self.mode == "wrong-value":
                    value += 1
                if self.mode == "destructive-pop":
                    self.states[source][:] = remainder_values
                if self.mode == "wrong-remainder" and len(values) >= 2:
                    remainder_values = []
                remainder = self._new_handle(remainder_values)
                result = {"tag": "some", "value": value, "remainder": remainder}

        response: dict[str, Any] = {
            "seq": seq,
            "status": "ok",
            "result": result,
            "events": self._events(),
        }
        if self.mode == "wrong-seq":
            response["seq"] = seq + 1
        if self.mode == "malformed-shape":
            response.pop("events")
        return response


def write_response(response: dict[str, Any]) -> None:
    if MODE == "malformed-json":
        sys.stdout.write("this-is-not-json\n")
    elif MODE == "malformed-utf8":
        sys.stdout.buffer.write(b"\xff\n")
    else:
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
        extra = IMMEDIATE_EXTRA_STDOUT.get(MODE)
        if extra is not None:
            sys.stdout.write(extra)
    sys.stdout.flush()


def main() -> int:
    stderr_payload = STDERR_PAYLOADS.get(MODE)
    if stderr_payload is not None:
        sys.stderr.buffer.write(stderr_payload)
        sys.stderr.buffer.flush()

    adapter = FakeStackAdapter(MODE)
    expected_seq = 0
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Malformed client requests are outside v1, but a stable error makes a
            # runner-side request-shape bug visible rather than hanging the fixture.
            write_response(adapter._error(expected_seq, "bad-request-json", "invalid JSON"))
            expected_seq += 1
            continue
        response = adapter.respond(request, expected_seq)
        if response is None:
            return 0
        write_response(response)
        expected_seq += 1

    eof_action = POST_EOF_ACTIONS.get(MODE)
    if eof_action == "marker":
        if len(MODE_ARGUMENTS) != 1:
            return 9
        Path(MODE_ARGUMENTS[0]).write_text("stdin-closed\n", encoding="utf-8")
    elif eof_action == "nonzero":
        return 7
    elif eof_action == "ignore-term-and-wait":
        if len(MODE_ARGUMENTS) != 1:
            return 9
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        Path(MODE_ARGUMENTS[0]).write_text(str(os.getpid()) + "\n", encoding="ascii")
        while True:
            time.sleep(10)
    elif eof_action == "extra-stdout":
        sys.stdout.write('{"extra":true}\n')
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
