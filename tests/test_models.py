"""
Tests for core/models.py dataclasses and services/logic.py pure functions.
"""

import pytest
from dataclasses import FrozenInstanceError

from core.models import Ticket, AgentResult, DashboardMetrics, TraceEntry
from services.logic import validate_query, compute_metrics, format_trace_for_display, mask_api_key


# ── Model Tests ────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_ticket_creation_from_dict():
    """Ticket.from_dict should create a Ticket from a dict."""
    data = {"key": "BA-1", "summary": "Test", "type": "Bug", "priority": "High",
            "status": "Open", "assignee": "Alice", "story_points": 5, "sprint": "Sprint 1"}
    ticket = Ticket.from_dict(data)
    assert ticket.key == "BA-1"
    assert ticket.summary == "Test"
    assert ticket.assignee == "Alice"
    assert ticket.story_points == 5


@pytest.mark.smoke
@pytest.mark.unit
def test_ticket_immutable():
    """Ticket should be frozen — mutation raises FrozenInstanceError."""
    ticket = Ticket(key="BA-1", summary="Test", type="Bug", priority="High",
                    status="Open", sprint="Sprint 1")
    with pytest.raises(FrozenInstanceError):
        ticket.key = "BA-2"


@pytest.mark.unit
def test_agent_result_creation():
    """AgentResult should store answer and trace."""
    result = AgentResult(answer="All done", trace=[{"role": "ai", "content": "done"}])
    assert result.answer == "All done"
    assert len(result.trace) == 1


@pytest.mark.unit
def test_dashboard_metrics_values():
    """DashboardMetrics should store correct values."""
    metrics = DashboardMetrics(total=20, total_sp=105, unassigned=12, open_bugs=8)
    assert metrics.total == 20
    assert metrics.total_sp == 105
    assert metrics.unassigned == 12
    assert metrics.open_bugs == 8


@pytest.mark.unit
def test_dashboard_metrics_immutable():
    """DashboardMetrics should be frozen."""
    metrics = DashboardMetrics(total=20)
    with pytest.raises(FrozenInstanceError):
        metrics.total = 99


@pytest.mark.unit
def test_trace_entry_creation():
    """TraceEntry should store role and content."""
    entry = TraceEntry(role="ai", content="I will now search...")
    assert entry.role == "ai"
    assert entry.content == "I will now search..."


# ── Logic Tests ────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_validate_query_rejects_empty():
    is_valid, reason = validate_query("   ")
    assert not is_valid
    assert "empty" in reason.lower()


@pytest.mark.unit
def test_validate_query_rejects_too_long():
    is_valid, reason = validate_query("A" * 3001)
    assert not is_valid
    assert "exceed" in reason.lower()


@pytest.mark.unit
def test_validate_query_accepts_valid():
    is_valid, reason = validate_query("Show me all open bugs in Sprint 24")
    assert is_valid
    assert reason == ""


@pytest.mark.unit
def test_validate_query_suspicious_pattern():
    is_valid, reason = validate_query("DROP TABLE users; --")
    assert not is_valid
    assert "suspicious" in reason.lower()


@pytest.mark.unit
def test_compute_metrics_with_sample_data():
    """compute_metrics should return correct metrics from ticket dicts."""
    tickets = [
        {"key": "BA-1", "type": "Bug", "priority": "High", "status": "Open", "sprint": "S1", "story_points": 3},
        {"key": "BA-2", "type": "Bug", "priority": "Medium", "status": "Open", "sprint": "S1", "story_points": 5},
        {"key": "BA-3", "type": "Story", "priority": "Low", "status": "To Do", "sprint": "S2", "story_points": 8, "assignee": "Alice"},
    ]
    metrics = compute_metrics(tickets)
    assert metrics.total == 3
    assert metrics.total_sp == 16
    assert metrics.unassigned == 2
    assert metrics.open_bugs == 2


@pytest.mark.unit
def test_format_trace_for_display():
    """format_trace_for_display should produce readable output from dict entries."""
    trace = [
        {"role": "human", "content": "Show me bugs"},
        {"role": "ai", "content": "I found 3 bugs"},
    ]
    output = format_trace_for_display(trace)
    assert "[HUMAN]" in output
    assert "[AI]" in output
    assert "Show me bugs" in output
    assert "I found 3 bugs" in output


@pytest.mark.unit
def test_mask_api_key():
    key = "sk-abc123def456ghi789"
    masked = mask_api_key(key)
    assert masked.startswith("sk-a")
    assert masked.endswith("i789")
    assert "*" * (len(key) - 8) in masked
    assert len(masked) == len(key)