"""
Tests for core/config.py and services/error_logging.py.
Closes coverage gaps on the config module (0% → 80%+) and error_logging (35% → 70%+).
"""

import os
import json
import tempfile
from unittest.mock import patch

import pytest

from core.config import (
    APP_TITLE,
    APP_ICON,
    LLM_MODEL,
    LLM_BASE_URL,
    DEEPSEEK_API_KEY,
    safe_secret,
)


@pytest.mark.unit
class TestConfig:
    """Tests for core/config.py constants and safe_secret helper."""

    def test_app_title_is_set(self):
        assert APP_TITLE == "BA Jira Agent"

    def test_app_icon_is_set(self):
        assert APP_ICON == "🤖"

    def test_llm_model_default(self):
        assert LLM_MODEL == "deepseek-chat"

    def test_llm_base_url_default(self):
        assert LLM_BASE_URL == "https://api.deepseek.com/v1"

    def test_deepseek_api_key_is_string(self):
        assert isinstance(DEEPSEEK_API_KEY, str)

    def test_safe_secret_short_value(self):
        result = safe_secret("ab")
        assert result == "ab***"

    def test_safe_secret_empty(self):
        assert safe_secret("") == "<not set>"

    def test_safe_secret_long_key(self):
        result = safe_secret("sk-abc...i789")
        assert result.startswith("sk-a")
        assert result.endswith("i789")
        assert "***" in result

    def test_safe_secret_custom_visible(self):
        result = safe_secret("abcdefghijklmnop", visible_chars=3)
        assert result.startswith("abc")
        assert result.endswith("nop")
        assert "***" in result

    def test_prompt_injection_guard_exists(self):
        from core.config import PROMPT_INJECTION_GUARD
        assert isinstance(PROMPT_INJECTION_GUARD, list)
        assert len(PROMPT_INJECTION_GUARD) >= 5


@pytest.mark.unit
class TestErrorLogging:
    """Tests for services/error_logging.py."""

    def test_log_error_creates_file(self):
        """log_error should create a log file and write a JSON line."""
        from services.error_logging import log_error

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("services.error_logging.LOG_DIR", tmpdir):
                with patch("services.error_logging.LOG_FILE",
                           os.path.join(tmpdir, "errors.jsonl")):
                    log_error("test", "Test error message", context={"key": "value"})

            log_files = [f for f in os.listdir(tmpdir) if f.endswith(".jsonl")]
            assert len(log_files) > 0

            log_path = os.path.join(tmpdir, log_files[0])
            with open(log_path) as f:
                line = f.readline()
                data = json.loads(line)
                assert data["module"] == "test"
                assert data["message"] == "Test error message"

    def test_get_recent_errors_returns_list(self):
        """get_recent_errors should return a list."""
        from services.error_logging import get_recent_errors
        result = get_recent_errors(limit=5)
        assert isinstance(result, list)

    def test_log_latency_exists(self):
        """log_latency function should exist."""
        from services.error_logging import log_latency
        assert callable(log_latency)

    def test_log_latency_writes(self):
        """log_latency should write latency data to the in-memory buffer."""
        from services.error_logging import log_latency, get_latency_stats

        # Clear the buffer by reading current state, then call log_latency
        log_latency("agent_query", 1234.5)
        log_latency("agent_query", 500.0)

        stats = get_latency_stats("agent_query")
        assert stats["samples"] >= 2
        assert stats["operation"] == "agent_query"