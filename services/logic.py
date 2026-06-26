"""
Pure business-logic functions for the BA Jira Agent.

All functions are side-effect-free: they take data as parameters,
return computed values, and never touch files, I/O, or Streamlit state.
"""

from __future__ import annotations

import re

from core.config import PROMPT_INJECTION_GUARD
from core.models import DashboardMetrics
from services.error_logging import log_error


# ── Query validation ──────────────────────────────────────────────────────────

MAX_QUERY_LENGTH = 3000

# SQL-injection-like patterns (complement PROMPT_INJECTION_GUARD from config)
_SQL_PATTERNS = [
    r"drop\s+table",
    r"delete\s+from",
    r"exec\s*\(",
]


def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate a user-submitted agent query.

    Checks for emptiness, excessive length (>3000 chars), SQL-injection
    patterns, and prompt-injection / jailbreak signatures from
    PROMPT_INJECTION_GUARD in core.config.

    Returns:
        (valid, reason) — True and "" if valid, otherwise
        False and a human-readable reason.
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."

    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters."

    # Check SQL-injection-like patterns
    for pattern in _SQL_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains suspicious patterns."

    # Check prompt-injection / jailbreak signatures
    for rule_name, pattern in PROMPT_INJECTION_GUARD:
        if pattern.search(query):
            log_error(
                "prompt_injection",
                f"Blocked suspicious query matching rule '{rule_name}'",
                context={"query_preview": query[:200]},
            )
            return (
                False,
                f"Query contains suspicious patterns (rule: {rule_name}). "
                "Please rephrase your request.",
            )

    return True, ""


# ── Metrics computation ───────────────────────────────────────────────────────


def compute_metrics(tickets: list) -> DashboardMetrics:
    """
    Compute summary dashboard metrics from a list of ticket dicts.

    Args:
        tickets: List of ticket dictionaries (as loaded from jira_export.json).

    Returns:
        DashboardMetrics with total, total_sp, unassigned, and open_bugs.
    """
    total = len(tickets)
    total_sp = sum(t.get("story_points", 0) or 0 for t in tickets)
    unassigned = sum(1 for t in tickets if not t.get("assignee"))
    open_bugs = sum(
        1
        for t in tickets
        if t.get("type") == "Bug" and t.get("status") == "Open"
    )

    return DashboardMetrics(
        total=total,
        total_sp=total_sp,
        unassigned=unassigned,
        open_bugs=open_bugs,
    )


# ── Trace formatting ──────────────────────────────────────────────────────────


def format_trace_for_display(trace: list[dict]) -> str:
    """
    Format a ReAct agent trace as a human-readable string.

    Args:
        trace: List of dicts, each with at least 'role' and 'content' keys.

    Returns:
        Multi-line string suitable for display in a code block or log.
    """
    if not trace:
        return "(empty trace)"

    lines: list[str] = []
    for i, entry in enumerate(trace):
        role = entry.get("role", "unknown")
        content = entry.get("content", "")

        if len(content) > 500:
            content = content[:500] + "... (truncated)"

        lines.append(f"[{role.upper()}]")
        lines.append(content)

        tool_calls = entry.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name", "unknown")
                args = tc.get("args", {})
                lines.append(f"  -> tool call: {name}({args})")

        if i < len(trace) - 1:
            lines.append("-" * 40)

    return "\n".join(lines)


# ── API key masking ──────────────────────────────────────────────────────────


def mask_api_key(key: str) -> str:
    """Mask an API key, showing only first 4 and last 4 characters."""
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"