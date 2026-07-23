#!/usr/bin/env python3
"""Object-state retry-safe lease-session candidate."""

from __future__ import annotations

import json
import sys


class LeaseSession:
    def __init__(self) -> None:
        self.phase = "available"
        self.owner: str | None = None
        self.request: str | None = None
        self.token: str | None = None

    def observe(self) -> dict:
        if self.phase != "held":
            return {"state": self.phase}
        return {
            "state": "held",
            "holder": self.owner,
            "request": self.request,
            "token": self.token,
        }

    def receive(self, message: dict) -> dict:
        if self.phase == "completed" or self.phase == "expired":
            return {"status": "terminal", "state": self.phase}
        operation = message.get("op")
        if operation == "acquire":
            return self.acquire(message.get("client"), message.get("request"))
        if operation == "renew":
            return self.renew(message.get("token"))
        if operation == "complete":
            return self.complete(message.get("token"))
        if operation == "expire":
            return self.expire()
        return {"status": "denied"}

    def acquire(self, client: object, request: object) -> dict:
        if self.phase == "available":
            self.phase = "held"
            self.owner = str(client)
            self.request = str(request)
            self.token = "t1"
            return {"status": "granted", "token": self.token}
        if client == self.owner and request == self.request:
            return {"status": "granted", "token": self.token}
        return {"status": "busy"}

    def renew(self, token: object) -> dict:
        return {"status": "renewed"} if token == self.token else {"status": "denied"}

    def complete(self, token: object) -> dict:
        if token != self.token:
            return {"status": "denied"}
        self.phase = "completed"
        self.owner = self.request = self.token = None
        return {"status": "completed"}

    def expire(self) -> dict:
        if self.phase != "held":
            return {"status": "denied"}
        self.phase = "expired"
        self.owner = self.request = self.token = None
        return {"status": "expired"}


session = LeaseSession()
for raw in sys.stdin:
    try:
        message = json.loads(raw)
        response = {"output": session.receive(message), "state": session.observe()}
    except Exception as error:  # pragma: no cover - process boundary
        response = {"error": type(error).__name__}
    print(json.dumps(response, sort_keys=True, separators=(",", ":")), flush=True)
