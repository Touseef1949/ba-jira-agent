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
