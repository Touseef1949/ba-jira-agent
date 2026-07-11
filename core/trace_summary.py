"""Helpers for presenting an agent trace without exposing raw reasoning text."""

from __future__ import annotations


def summarize_tool_calls(trace: list[dict] | None) -> list[dict]:
    """Return ordered, de-duplicated tool calls from a serialized agent trace."""
    calls: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for message in trace or []:
        for tool_call in message.get("tool_calls", []) or []:
            name = str(tool_call.get("name", "unknown"))
            args = tool_call.get("args", {}) or {}
            skill_name = str(args.get("skill_name", "")) if isinstance(args, dict) else ""
            identity = (name, skill_name)
            if identity in seen:
                continue
            seen.add(identity)
            calls.append({"name": name, "skill_name": skill_name})

    return calls
