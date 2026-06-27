"""Tests for tool behaviour in Jira (live) data-source mode."""

import pytest

import tools


@pytest.fixture(autouse=True)
def reset_tools():
    """Reset tool data-source config between tests."""
    tools.configure_tools("mock", None)
    yield
    tools.configure_tools("mock", None)


def test_configure_tools_switches_to_jira():
    tools.configure_tools("jira", {"jira_url": "https://example.atlassian.net", "pat": "tok", "email": "a@b.com"})
    # configure_tools should complete without error
    assert True


def test_load_tickets_jira_mode(monkeypatch):
    """When data source is jira, tools produce output from live data."""
    mock_tickets = [
        {
            "key": "BA-1", "summary": "Test", "type": "Bug", "priority": "High",
            "status": "Open", "assignee": None, "story_points": 3,
            "sprint": "Sprint 1", "labels": [], "created": "", "description": "",
        }
    ]
    monkeypatch.setattr(tools, "_load_all_tickets", lambda: mock_tickets)
    tools.configure_tools("jira", {"jira_url": "https://e.a.net", "pat": "t", "email": "a@b.com"})
    result = tools.load_tickets.invoke({})
    assert "BA-1" in result
    assert "Total tickets: 1" in result


def test_filter_tickets_jira_mode(monkeypatch):
    """When data source is jira, filter_tickets works on live data."""
    mock_tickets = [
        {
            "key": "BA-1", "summary": "Test bug", "type": "Bug", "priority": "High",
            "status": "Open", "assignee": "Asha", "story_points": 3,
            "sprint": "Sprint 1", "labels": [], "created": "", "description": "",
        }
    ]
    monkeypatch.setattr(tools, "_load_all_tickets", lambda: mock_tickets)
    tools.configure_tools("jira", {"jira_url": "https://e.a.net", "pat": "t", "email": "a@b.com"})
    result = tools.filter_tickets.invoke({"field": "assignee", "value": "Asha"})
    assert "BA-1" in result


def test_search_tickets_jira_mode(monkeypatch):
    """When data source is jira, search_tickets works on live data."""
    mock_tickets = [
        {
            "key": "BA-1", "summary": "Performance fix", "type": "Bug", "priority": "High",
            "status": "Open", "assignee": None, "story_points": 5,
            "sprint": None, "labels": [], "created": "", "description": "Improve latency",
        }
    ]
    monkeypatch.setattr(tools, "_load_all_tickets", lambda: mock_tickets)
    tools.configure_tools("jira", {"jira_url": "https://e.a.net", "pat": "t", "email": "a@b.com"})
    result = tools.search_tickets.invoke({"query": "Performance"})
    assert "BA-1" in result


def test_calculate_metrics_jira_mode(monkeypatch):
    """When data source is jira, calculate_metrics works on live data."""
    mock_tickets = [
        {
            "key": "BA-1", "summary": "Bug 1", "type": "Bug", "priority": "High",
            "status": "Open", "assignee": "Asha", "story_points": 5,
            "sprint": "Sprint 1", "labels": [], "created": "", "description": "",
        },
        {
            "key": "BA-2", "summary": "Story 1", "type": "Story", "priority": "Medium",
            "status": "Done", "assignee": None, "story_points": 3,
            "sprint": "Sprint 1", "labels": [], "created": "", "description": "",
        },
    ]
    monkeypatch.setattr(tools, "_load_all_tickets", lambda: mock_tickets)
    tools.configure_tools("jira", {"jira_url": "https://e.a.net", "pat": "t", "email": "a@b.com"})
    result = tools.calculate_metrics.invoke({"metric_type": "summary"})
    assert "Total Tickets:        2" in result
    assert "Total Story Points:   8" in result
    assert "Unassigned Tickets:   1" in result
