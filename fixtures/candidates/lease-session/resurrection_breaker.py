#!/usr/bin/env python3
"""Negative candidate: late completion wrongly resurrects an expired lease."""

from __future__ import annotations

import json
import sys


state = "available"
holder = request = token = None


def observe() -> dict:
    if state == "held":
        return {"state": state, "holder": holder, "request": request, "token": token}
    return {"state": state}


def receive(message: dict) -> dict:
    global state, holder, request, token
    operation = message.get("op")
    if state == "expired" and operation == "complete":
        state = "completed"  # intentional resurrection defect
        return {"status": "completed"}
    if state in {"completed", "expired"}:
        return {"status": "terminal", "state": state}
    if state == "available" and operation == "acquire":
        state, holder, request, token = "held", message.get("client"), message.get("request"), "t1"
        return {"status": "granted", "token": token}
    if operation == "acquire":
        if message.get("client") == holder and message.get("request") == request:
            return {"status": "granted", "token": token}
        return {"status": "busy"}
    if operation == "renew":
        return {"status": "renewed"} if message.get("token") == token else {"status": "denied"}
    if operation == "complete":
        if message.get("token") != token:
            return {"status": "denied"}
        state = "completed"
        return {"status": "completed"}
    if operation == "expire":
        state = "expired"
        return {"status": "expired"}
    return {"status": "denied"}


for raw in sys.stdin:
    try:
        message = json.loads(raw)
        response = {"output": receive(message), "state": observe()}
    except Exception as error:  # pragma: no cover - process boundary
        response = {"error": type(error).__name__}
    print(json.dumps(response, sort_keys=True, separators=(",", ":")), flush=True)
