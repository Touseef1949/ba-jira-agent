"""
Structured JSONL error logging for the BA Jira Agent.

Logs errors to logs/errors.jsonl with timestamp, module, message, and context.
"""

import json
import logging
import os
import traceback
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "errors.jsonl")

_logger = logging.getLogger("ba_jira_agent")


def log_error(
    module: str,
    message: str,
    exc_info: bool = False,
    context: dict | None = None,
) -> None:
    """
    Log an error as a structured JSON line.

    Args:
        module: Name of the module reporting the error (e.g. 'agent', 'data').
        message: Error description.
        exc_info: If True, include full traceback.
        context: Optional extra metadata about the error.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": module,
        "message": message,
    }

    if exc_info:
        entry["traceback"] = traceback.format_exc()

    if context:
        entry["context"] = context

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Best-effort logging

    _logger.error(f"[{module}] {message}")
