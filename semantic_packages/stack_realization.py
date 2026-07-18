"""An independent reference Stack[A] Realization.

This is a small persistent representation (an immutable singly linked list) used
only behind ``stack_adapter``. ``stack_runner`` never imports this module: its
expected top-first traces are tracked independently so a shared implementation
can never become the harness's own oracle.
"""

from __future__ import annotations

from typing import Optional, Tuple


class _Node:
    __slots__ = ("value", "rest")

    def __init__(self, value: int, rest: "Optional[_Node]") -> None:
        self.value = value
        self.rest = rest


Stack = Optional[_Node]


def empty() -> Stack:
    return None


def push(stack: Stack, value: int) -> Stack:
    return _Node(value, stack)


def pop(stack: Stack) -> Optional[Tuple[int, Stack]]:
    if stack is None:
        return None
    return stack.value, stack.rest
