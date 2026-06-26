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
