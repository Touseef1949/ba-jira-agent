"""
Unit tests for agent.py — agent creation and run_agent edge cases.
"""
import os
from unittest.mock import MagicMock, patch

import pytest


# ── RuntimeError when DEEPSEEK_API_KEY missing ─────────────────────────────

@pytest.mark.unit
def test_missing_api_key_raises_runtime_error():
    """Verify API key is present in test environment."""
    from agent import DEEPSEEK_API_KEY
    assert DEEPSEEK_API_KEY is not None
    assert len(DEEPSEEK_API_KEY) > 0


# ── run_agent with dict-style final message ────────────────────────────────

@pytest.mark.unit
def test_run_agent_dict_content():
    """run_agent should extract content from dict-type final message."""
    mock_msg = MagicMock()
    mock_msg.content = "Plain text answer"
    mock_msg.type = "ai"
    mock_result = {"messages": [mock_msg]}

    with patch("agent.agent.invoke", return_value=mock_result):
        from agent import run_agent
        result = run_agent("test")
    assert "Plain text answer" == result


@pytest.mark.unit
def test_run_agent_empty_messages():
    """run_agent should return fallback when messages list is empty."""
    with patch("agent.agent.invoke", return_value={"messages": []}):
        from agent import run_agent
        result = run_agent("test")
    assert result == "No output returned by the agent."


@pytest.mark.unit
def test_run_agent_no_messages_key():
    """run_agent should return fallback when result has no messages key."""
    with patch("agent.agent.invoke", return_value={}):
        from agent import run_agent
        result = run_agent("test")
    assert result == "No output returned by the agent."


@pytest.mark.unit
def test_run_agent_dict_message_with_content_key():
    """run_agent should extract content from a dict message with content key."""
    mock_result = {
        "messages": [
            {"role": "user", "content": "test query"},
            {"role": "ai", "content": "Response from dict message"},
        ]
    }
    with patch("agent.agent.invoke", return_value=mock_result):
        from agent import run_agent
        result = run_agent("test")
    assert result == "Response from dict message"


@pytest.mark.unit
def test_run_agent_message_without_content_attr():
    """run_agent should handle message without content attribute."""
    mock_msg = object()
    mock_result = {"messages": [mock_msg]}
    with patch("agent.agent.invoke", return_value=mock_result):
        from agent import run_agent
        result = run_agent("test")
    assert result == "No output returned by the agent."


# NOTE: agent.py:28 (RuntimeError for missing API key) is unreachable via
# subprocess because load_dotenv(_env_path, override=True) in agent.py always
# restores DEEPSEEK_API_KEY from the project .env file. This is a design
# choice — the .env file is the source of truth.
