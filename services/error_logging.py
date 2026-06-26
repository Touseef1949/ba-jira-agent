"""
Structured JSONL error logging for the BA Jira Agent.

Logs errors to logs/errors.jsonl with timestamp, module, message, and context.
Includes latency tracking for agent operations.
"""

import json
import logging
import os
import traceback
from collections import deque
from datetime import datetime, timezone
from statistics import median

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "errors.jsonl")

_logger = logging.getLogger("ba_jira_agent")

# ── Latency tracking ───────────────────────────────────────────────────────────
# Circular buffer of the last 100 latency samples, keyed by operation name.
# Each entry: {"operation": str, "latency_ms": float, "timestamp": str}
_MAX_LATENCY_SAMPLES = 100
_latency_buffer: deque[dict] = deque(maxlen=_MAX_LATENCY_SAMPLES)


def log_error(
    module: str,
    message: str,
    exc_info: bool = False,
    context: dict | None = None,
    latency_ms: float | None = None,
) -> None:
    """
    Log an error as a structured JSON line.

    Args:
        module: Name of the module reporting the error (e.g. 'agent', 'data').
        message: Error description.
        exc_info: If True, include full traceback.
        context: Optional extra metadata about the error.
        latency_ms: Optional latency in ms from the operation that failed.
    """
    entry: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": module,
        "message": message,
    }

    if exc_info:
        entry["traceback"] = traceback.format_exc()

    if context:
        entry["context"] = context

    if latency_ms is not None:
        entry["latency_ms"] = latency_ms

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Best-effort logging

    _logger.error(f"[{module}] {message}")


def log_latency(operation: str, latency_ms: float) -> None:
    """
    Record an operation's latency for statistics tracking.

    Keeps the last 100 samples per operation in a circular buffer.

    Args:
        operation: Name of the operation (e.g. 'run_agent_query').
        latency_ms: Latency in milliseconds.
    """
    entry = {
        "operation": operation,
        "latency_ms": latency_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _latency_buffer.append(entry)


def get_latency_stats(operation: str | None = None) -> dict:
    """
    Compute p50, p95, p99 latency statistics from the last 100 calls.

    Args:
        operation: Optional filter — only return stats for this operation.
                   If None, returns stats across all operations.

    Returns:
        dict with keys:
            - samples (int): Number of samples available.
            - p50_ms (float or None): 50th percentile latency.
            - p95_ms (float or None): 95th percentile latency.
            - p99_ms (float or None): 99th percentile latency.
            - min_ms (float or None): Minimum observed latency.
            - max_ms (float or None): Maximum observed latency.
            - operation (str or None): Operation name if filtered.
    """
    if operation:
        values = sorted(
            e["latency_ms"] for e in _latency_buffer
            if e["operation"] == operation
        )
    else:
        values = sorted(e["latency_ms"] for e in _latency_buffer)

    n = len(values)
    if n == 0:
        return {
            "samples": 0,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "min_ms": None,
            "max_ms": None,
            "operation": operation,
        }

    def _percentile(sorted_vals: list[float], pct: float) -> float:
        """Compute a percentile from a sorted list of values."""
        if not sorted_vals:
            return 0.0
        k = (len(sorted_vals) - 1) * (pct / 100.0)
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_vals):
            return sorted_vals[f] + c * (sorted_vals[f + 1] - sorted_vals[f])
        return sorted_vals[f]

    return {
        "samples": n,
        "p50_ms": round(_percentile(values, 50), 1),
        "p95_ms": round(_percentile(values, 95), 1),
        "p99_ms": round(_percentile(values, 99), 1),
        "min_ms": round(values[0], 1),
        "max_ms": round(values[-1], 1),
        "operation": operation,
    }


def get_recent_errors(limit: int = 20) -> list[dict]:
    """
    Read the most recent errors from the JSONL log file.

    Args:
        limit: Maximum number of error entries to return.

    Returns:
        List of error dicts, most recent first.
    """
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        errors = [json.loads(line) for line in lines if line.strip()]
        return list(reversed(errors[-limit:]))
    except (OSError, json.JSONDecodeError):
        return []
