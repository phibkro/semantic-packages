#!/usr/bin/env python3
"""Hostile test double for ``ordered-map-runner-json-v1``.

This fixture implements protocol responses only. It is not a candidate Realization.
It may produce ephemeral runner reports for hostile controls, but must never enter a
retained candidate report, manifest, Claim, Evidence, review, or acceptance input.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any


MODE = sys.argv[1] if len(sys.argv) > 1 else "reference"
ARGUMENT = sys.argv[2] if len(sys.argv) > 2 else None


class Session:
    def __init__(self) -> None:
        self.next_handle = 0
        self.maps: dict[str, tuple[tuple[str, int], ...]] = {}

    def store(self, entries: tuple[tuple[str, int], ...]) -> str:
        if MODE == "interned":
            for handle, retained in self.maps.items():
                if retained == entries:
                    return handle
        if MODE == "arbitrary-handles":
            handle = f" map token/{self.next_handle}:☃ "
        else:
            handle = f"opaque-{self.next_handle * 17 + 3}"
        self.next_handle += 1
        self.maps[handle] = entries
        return handle


def classify(key: str) -> str:
    return key.lower()


def events() -> list[str]:
    if MODE == "optional-event":
        return ["debug.emit"]
    if MODE == "forbidden-event":
        return ["io.read"]
    if MODE == "unspecified-event":
        return ["network.send"]
    if MODE == "ordered-events":
        return ["debug.emit", "network.send"]
    if MODE == "nonmatching-io-boundary":
        return ["io", "io."]
    if MODE == "long-forbidden-event":
        return ["io.read.deep"]
    if MODE in {"empty-event", "invalid-event-container"}:
        return [""]
    if MODE == "adapter-error-forbidden":
        return ["io.read"]
    return []


def error(seq: int, code: str, message: str) -> dict[str, Any]:
    return {
        "seq": seq,
        "status": "error",
        "error": {"code": code, "message": message},
        "events": events(),
    }


def validate_request(request: Any, seq: int) -> str | None:
    if not isinstance(request, dict) or set(request) != {"seq", "op", "args"}:
        return "request members"
    if type(request["seq"]) is not int or request["seq"] != seq:
        return "sequence"
    if not isinstance(request["op"], str) or not isinstance(request["args"], dict):
        return "sequence or args"
    op = request["op"]
    expected = {
        "empty": set(),
        "put": {"map", "key", "value"},
        "lookup": {"map", "key"},
        "entries": {"map"},
    }
    if op not in expected or set(request["args"]) != expected[op]:
        return "operation args"
    args = request["args"]
    if op in {"put", "lookup", "entries"} and (
        not isinstance(args["map"], str) or not args["map"]
    ):
        return "map handle"
    if op in {"put", "lookup"} and args["key"] not in {
        "A", "a", "B", "b", "C", "c"
    }:
        return "key domain"
    if op == "put" and (
        type(args["value"]) is not int or args["value"] not in {-2, -1, 0, 1, 2}
    ):
        return "value domain"
    return None


def respond(session: Session, request: dict[str, Any], seq: int) -> dict[str, Any]:
    if problem := validate_request(request, seq):
        return error(seq, "bad-request", problem)
    if MODE in {
        "status-error",
        "adapter-error-forbidden",
        "empty-error-code",
        "empty-error-message",
        "numeric-error-code",
        "numeric-error-message",
        "extra-error-member",
        "error-top-level-extra",
    }:
        response = error(seq, "controlled-error", "adapter rejected a valid request")
        if MODE == "empty-error-code":
            response["error"]["code"] = ""
        elif MODE == "empty-error-message":
            response["error"]["message"] = ""
        elif MODE == "numeric-error-code":
            response["error"]["code"] = 7
        elif MODE == "numeric-error-message":
            response["error"]["message"] = 7
        elif MODE == "extra-error-member":
            response["error"]["extra"] = True
        elif MODE == "error-top-level-extra":
            response["extra"] = True
        return response

    op = request["op"]
    args = request["args"]
    if op == "empty":
        result: Any = {"map": session.store(())}
    elif op == "put":
        source = session.maps[args["map"]]
        token = classify(args["key"])
        position = next(
            (index for index, (item, _value) in enumerate(source) if item == token),
            None,
        )
        updated = list(source)
        if position is None:
            updated.append((token, args["value"]))
        elif MODE in {"reorder-existing", "reorder-existing-nonzero"}:
            updated.pop(position)
            updated.append((token, args["value"]))
        else:
            updated[position] = (token, args["value"])
        retained = tuple(updated)
        if MODE == "destructive-new" and position is None and len(source) == 1:
            session.maps[args["map"]] = retained
        if MODE == "destructive-existing" and position is not None and len(source) == 2:
            session.maps[args["map"]] = retained
        result = {"map": session.store(retained)}
    elif op == "lookup":
        source = session.maps[args["map"]]
        token = classify(args["key"])
        found = next((value for item, value in source if item == token), None)
        if MODE == "wrong-empty" and not source:
            result = {"tag": "some", "value": 0}
        elif MODE == "wrong-same" and len(source) == 1 and found is not None:
            result = {"tag": "some", "value": found + 1}
        elif MODE == "wrong-other" and len(source) == 2 and found is not None:
            result = {"tag": "some", "value": found + 1}
        elif found is None:
            result = {"tag": "none"}
        else:
            result = {"tag": "some", "value": found}
    else:
        source = session.maps[args["map"]]
        visible = source
        if MODE == "wrong-append" and len(source) == 3:
            visible = tuple(reversed(source))
        result = {
            "entries": [
                {"class": token, "value": value} for token, value in visible
            ]
        }
    if MODE == "empty-handle" and op in {"empty", "put"}:
        result = {"map": ""}
    elif MODE == "numeric-handle" and op in {"empty", "put"}:
        result = {"map": 7}
    elif MODE == "put-empty-handle" and op == "put":
        result = {"map": ""}
    elif MODE == "extra-result-member":
        result["extra"] = True
    elif MODE == "put-extra-result" and op == "put":
        result["extra"] = True
    elif MODE == "lookup-extra-result" and op == "lookup":
        result["extra"] = True
    elif MODE == "invalid-lookup-tag" and op == "lookup":
        result = {"tag": "unknown"}
    elif MODE == "lookup-bool-value" and op == "lookup":
        result = {"tag": "some", "value": True}
    elif MODE == "lookup-some-missing-value" and op == "lookup":
        result = {"tag": "some"}
    elif MODE == "lookup-none-extra-value" and op == "lookup":
        result = {"tag": "none", "value": 1}
    elif MODE == "invalid-entry-class" and op == "entries":
        result = {"entries": [{"class": "z", "value": 1}]}
    elif MODE == "entry-extra-member" and op == "entries":
        result = {"entries": [{"class": "a", "value": 1, "extra": True}]}
    elif MODE == "invalid-entry-value" and op == "entries":
        result = {"entries": [{"class": "a", "value": True}]}
    elif MODE == "entries-not-list" and op == "entries":
        result = {"entries": {}}
    elif MODE == "entries-result-extra" and op == "entries":
        result["extra"] = True
    response = {"seq": seq, "status": "ok", "result": result, "events": events()}
    if MODE == "invalid-event-container":
        response["events"] = "debug.emit"
    elif MODE == "nonstring-event":
        response["events"] = [7]
    if MODE == "unknown-status":
        response["status"] = "maybe"
    if MODE == "top-level-extra":
        response["extra"] = True
    if MODE == "both-result-error":
        response["error"] = {"code": "also-error", "message": "both branches"}
    return response


def write_response(response: dict[str, Any], seq: int) -> None:
    if MODE == "malformed-json":
        sys.stdout.write("{ malformed\n")
    elif MODE == "malformed-utf8":
        sys.stdout.buffer.write(b"\xff\n")
    elif MODE == "malformed-shape":
        sys.stdout.write(json.dumps({"seq": seq, "status": "ok"}) + "\n")
    elif MODE == "duplicate-member":
        sys.stdout.write(
            f'{{"seq":{seq},"seq":{seq},"status":"ok","result":{{}},"events":[]}}\n'
        )
    elif MODE == "nonstandard-number":
        sys.stdout.write(
            f'{{"seq":{seq},"status":"ok","result":{{"map":NaN}},"events":[]}}\n'
        )
    elif MODE == "bool-seq":
        response["seq"] = False
        sys.stdout.write(json.dumps(response) + "\n")
    elif MODE == "wrong-seq":
        response["seq"] = seq + 1
        sys.stdout.write(json.dumps(response) + "\n")
    else:
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    session = Session()
    seq = 0
    if MODE == "start-marker" and ARGUMENT is not None:
        with open(ARGUMENT, "w", encoding="utf-8") as stream:
            stream.write("adapter-started\n")
    if MODE == "output-before-request":
        sys.stdout.write("{}\n")
        sys.stdout.flush()
    if MODE == "stderr-bytes":
        sys.stderr.buffer.write(b"ordered-map diagnostic: \xff\x00\n")
        sys.stderr.buffer.flush()
    for line in sys.stdin.buffer:
        if MODE == "early-eof":
            return 0
        if MODE == "timeout":
            if ARGUMENT is not None:
                with open(ARGUMENT, "w", encoding="ascii") as stream:
                    stream.write(str(os.getpid()))
            time.sleep(2)
        request = json.loads(line)
        if MODE == "request-journal" and ARGUMENT is not None:
            with open(ARGUMENT, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(request, separators=(",", ":")) + "\n")
        response = respond(session, request, seq)
        write_response(response, seq)
        if MODE == "extra-stdout":
            sys.stdout.write("{}\n")
            sys.stdout.flush()
        seq += 1

    if MODE == "eof-marker":
        with open(ARGUMENT, "w", encoding="utf-8") as stream:
            stream.write("stdin-closed\n")
    elif MODE == "eof-timeout":
        with open(ARGUMENT, "w", encoding="ascii") as stream:
            stream.write(str(os.getpid()))
        time.sleep(2)
    elif MODE == "eof-extra-stdout":
        sys.stdout.write("{}\n")
        sys.stdout.flush()
    if MODE in {"nonzero-exit", "eof-nonzero", "reorder-existing-nonzero"}:
        return 7
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
