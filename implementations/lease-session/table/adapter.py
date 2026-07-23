#!/usr/bin/env python3
"""Table-oriented retry-safe lease-session candidate."""

from __future__ import annotations

import json
import sys


session = {"state": "available"}


def snapshot() -> dict:
    if session["state"] == "held":
        return {
            "state": "held",
            "holder": session["holder"],
            "request": session["request"],
            "token": session["token"],
        }
    return {"state": session["state"]}


def terminal() -> dict:
    return {"status": "terminal", "state": session["state"]}


def apply(message: dict) -> dict:
    state = session["state"]
    operation = message.get("op")
    if state in {"completed", "expired"}:
        return terminal()
    if state == "available":
        if operation != "acquire":
            return {"status": "denied"}
        session.update(
            state="held",
            holder=message.get("client"),
            request=message.get("request"),
            token="t1",
        )
        return {"status": "granted", "token": "t1"}

    handlers = {
        "acquire": lambda: (
            {"status": "granted", "token": session["token"]}
            if message.get("client") == session["holder"]
            and message.get("request") == session["request"]
            else {"status": "busy"}
        ),
        "renew": lambda: (
            {"status": "renewed"}
            if message.get("token") == session["token"]
            else {"status": "denied"}
        ),
        "complete": lambda: complete(message.get("token")),
        "expire": expire,
    }
    handler = handlers.get(operation)
    return handler() if handler is not None else {"status": "denied"}


def complete(token: object) -> dict:
    if token != session["token"]:
        return {"status": "denied"}
    session.clear()
    session["state"] = "completed"
    return {"status": "completed"}


def expire() -> dict:
    session.clear()
    session["state"] = "expired"
    return {"status": "expired"}


for raw in sys.stdin:
    try:
        message = json.loads(raw)
        output = apply(message)
        response = {"output": output, "state": snapshot()}
    except Exception as error:  # pragma: no cover - process boundary
        response = {"error": type(error).__name__}
    print(json.dumps(response, sort_keys=True, separators=(",", ":")), flush=True)
