"""
Core configuration constants and helpers for BA Jira Agent.

Loads environment variables from the project .env file and provides
a safe_secret helper for masking sensitive values in logs/display.
"""

import os

from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

# ── API Keys ──────────────────────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_DIR, "data")
JIRA_EXPORT_PATH = os.path.join(DATA_DIR, "jira_export.json")
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")

# ── LLM Config ────────────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# ── App Config ────────────────────────────────────────────────────────────────
APP_TITLE = "BA Jira Agent"
APP_ICON = "🤖"
APP_PORT = int(os.getenv("APP_PORT", "8503"))

# ── Prompt Injection Guard ───────────────────────────────────────────────────
# Compiled regex patterns for detecting common prompt injection / jailbreak
# attempts. Used by agent_service.py to reject malicious queries before they
# reach the LLM.
import re as _re

PROMPT_INJECTION_GUARD: list[tuple[str, _re.Pattern]] = [
    (
        "ignore_previous_instructions",
        _re.compile(
            r"(ignore|forget|disregard)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|directives?)",
            _re.IGNORECASE,
        ),
    ),
    (
        "system_prompt_leak",
        _re.compile(
            r"(reveal|show|print|display|output|tell\s+me)\s+(me\s+)?(your\s+)?(system\s+)?(prompt|instructions?|directives?|rules?)",
            _re.IGNORECASE,
        ),
    ),
    (
        "role_override",
        _re.compile(
            r"(you\s+are\s+now|act\s+as|pretend\s+you\s+are|you\s+are\s+a)\s+(DAN|jailbreak|evil|unfiltered|unrestricted)",
            _re.IGNORECASE,
        ),
    ),
    (
        "delimiter_attack",
        _re.compile(
            r"_{3,}|={3,}|-{3,}|\]{3,}|\[{3,}|<\|.*?\|>",
        ),
    ),
    (
        "encoding_obfuscation",
        _re.compile(
            r"(base64|rot13|decode|encode)\s*\(?\s*['\"].*?['\"]\s*\)?",
            _re.IGNORECASE,
        ),
    ),
    (
        "nested_prompt",
        _re.compile(
            r"\[system\]|\[/system\]|\[assistant\]|\[/assistant\]|\[user\]|\[/user\]",
            _re.IGNORECASE,
        ),
    ),
    (
        "system_override",
        _re.compile(
            r"(?<!\[)system\s*:\s*",
            _re.IGNORECASE,
        ),
    ),
]


def safe_secret(value: str, visible_chars: int = 4) -> str:
    """
    Mask a secret value for safe display in logs or UI.

    Args:
        value: The secret string to mask.
        visible_chars: Number of characters to show at start and end.

    Returns:
        A masked string like 'sk-a***b12c'.
    """
    if not value:
        return "<not set>"
    if len(value) <= visible_chars * 2:
        return value[:visible_chars] + "***"
    return value[:visible_chars] + "***" + value[-visible_chars:]
