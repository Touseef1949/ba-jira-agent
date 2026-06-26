"""
Integration / unit tests for services/agent_service.py.

Tests cover get_all_tickets, get_metrics, and run_agent_query.
The run_agent_query tests mock agent.invoke — no real API calls.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from services.agent_service import get_all_tickets, get_metrics, run_agent_query


# ── get_all_tickets ────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.integration
def test_get_all_tickets_returns_list():
    """get_all_tickets should return a list."""
    tickets = get_all_tickets()
    assert isinstance(tickets, list)


@pytest.mark.integration
def test_get_all_tickets_has_20():
    """get_all_tickets should return all 20 tickets."""
    tickets = get_all_tickets()
    assert len(tickets) == 20


# ── get_metrics ────────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.integration
def test_get_metrics_returns_dict():
    """get_metrics should return a dict with expected keys."""
    metrics = get_metrics()
    assert isinstance(metrics, dict)
    assert "total" in metrics
    assert "total_sp" in metrics
    assert "unassigned" in metrics
    assert "open_bugs" in metrics


@pytest.mark.integration
def test_get_metrics_values_correct():
    """get_metrics should return correct values for the mock data."""
    metrics = get_metrics()
    assert metrics["total"] == 20
    assert metrics["total_sp"] == 105
    assert metrics["unassigned"] == 12
    assert metrics["open_bugs"] == 8


# ── run_agent_query (MOCKED — no real API calls) ──────────────────────────────

@pytest.mark.smoke
@pytest.mark.integration
def test_run_agent_query_returns_answer(mock_agent):
    """run_agent_query should return answer + trace from the agent."""
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("Show me all bugs")

    assert "answer" in result
    assert "trace" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert isinstance(result["trace"], list)
    assert len(result["trace"]) > 0
    # The mock returns "I found 20 tickets in the backlog."
    assert "20 tickets" in result["answer"]
    mock_agent.invoke.assert_called_once()


@pytest.mark.integration
def test_run_agent_query_trace_has_roles(mock_agent):
    """Trace entries should have role and content keys."""
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("test query")

    trace = result["trace"]
    for entry in trace:
        assert "role" in entry
        assert "content" in entry


# ── run_agent_query — invalid query ────────────────────────────────────────────

@pytest.mark.unit
def test_run_agent_query_rejects_invalid_query(mock_agent):
    """run_agent_query should return error for invalid queries without calling agent."""
    from services.logic import validate_query
    # Empty string is invalid
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("")
    assert "Invalid query" in result["answer"]
    assert result["trace"][0]["role"] == "error"
    mock_agent.invoke.assert_not_called()


@pytest.mark.unit
def test_run_agent_query_rejects_too_long_query(mock_agent):
    """run_agent_query should reject queries exceeding max length (3000)."""
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("x" * 3001)
    assert "Invalid query" in result["answer"]
    mock_agent.invoke.assert_not_called()


# ── run_agent_query — dict-type final message ──────────────────────────────────

@pytest.mark.unit
def test_run_agent_query_dict_final_message():
    """run_agent_query should extract content from dict-type final message."""
    mock_dict_result = {
        "messages": [
            {"role": "user", "content": "test"},
            {"role": "ai", "content": "Response from dict"},
        ]
    }
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = mock_dict_result
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("test query")
    assert result["answer"] == "Response from dict"


# ── run_agent_query — message without .content ─────────────────────────────────

@pytest.mark.unit
def test_run_agent_query_message_without_content():
    """run_agent_query should stringify message without .content attribute."""
    mock_msg = object()
    mock_result = {"messages": [mock_msg]}
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = mock_result
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("test query")
    assert "answer" in result
    assert "trace" in result


# ── run_agent_query — exception handler ────────────────────────────────────────

@pytest.mark.unit
def test_run_agent_query_exception_handler():
    """run_agent_query should catch exceptions and return error response."""
    mock_agent = MagicMock()
    mock_agent.invoke.side_effect = RuntimeError("API connection failed")
    with patch("services.agent_service._agent", mock_agent):
        result = run_agent_query("test query")
    assert "Agent error" in result["answer"]
    assert result["trace"][0]["role"] == "error"
    assert "API connection failed" in result["trace"][0]["content"]


# ── get_all_tickets — file error ───────────────────────────────────────────────

@pytest.mark.unit
def test_get_all_tickets_file_read_error():
    """get_all_tickets should return empty list on file read error."""
    with patch("builtins.open", side_effect=FileNotFoundError("no such file")):
        with patch("services.agent_service.log_error") as mock_log:
            result = get_all_tickets()
    assert result == []
    mock_log.assert_called_once()


# ── get_metrics — exception ────────────────────────────────────────────────────

@pytest.mark.unit
def test_get_metrics_exception_handler():
    """get_metrics should return zero-filled dict on exception."""
    with patch("services.agent_service.get_all_tickets",
               side_effect=RuntimeError("data unavailable")):
        with patch("services.agent_service.log_error") as mock_log:
            result = get_metrics()
    assert result == {"total": 0, "total_sp": 0, "unassigned": 0, "open_bugs": 0}
    mock_log.assert_called_once()
