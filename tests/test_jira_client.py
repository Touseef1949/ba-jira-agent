"""Tests for the Jira Cloud REST API client."""

from unittest.mock import patch

import pytest
import requests

from services import jira_client


class MockResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


def sample_issue(**field_overrides):
    fields = {
        "summary": "Add checkout flow",
        "issuetype": {"name": "Story"},
        "priority": {"name": "High"},
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Asha Rao"},
        "customfield_10016": 5,
        "customfield_10020": [{"name": "Sprint 42"}],
        "labels": ["checkout"],
        "created": "2026-06-20T10:00:00.000+0000",
        "description": {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Build payment screen."}]}],
        },
    }
    fields.update(field_overrides)
    return {"key": "BA-123", "fields": fields}


def test_map_jira_issue_to_ticket_standard_issue():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue())
    assert ticket["key"] == "BA-123"
    assert ticket["summary"] == "Add checkout flow"
    assert ticket["type"] == "Story"
    assert ticket["priority"] == "High"
    assert ticket["status"] == "In Progress"
    assert ticket["assignee"] == "Asha Rao"
    assert ticket["story_points"] == 5
    assert ticket["sprint"] == "Sprint 42"
    assert ticket["labels"] == ["checkout"]
    assert "payment screen" in ticket["description"]


def test_map_jira_issue_to_ticket_null_assignee():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue(assignee=None))
    assert ticket["assignee"] is None


def test_map_jira_issue_to_ticket_missing_priority():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue(priority=None))
    assert ticket["priority"] == "Medium"


def test_map_jira_issue_to_ticket_epic_type():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue(issuetype={"name": "Epic"}))
    assert ticket["type"] == "Epic"


def test_map_jira_issue_to_ticket_subtask():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue(issuetype={"name": "Sub-task"}))
    assert ticket["type"] == "Sub-task"


def test_map_jira_issue_to_ticket_empty_sprint():
    ticket = jira_client.map_jira_issue_to_ticket(sample_issue(customfield_10020=[]))
    assert ticket["sprint"] is None


def test_validate_pat_success():
    with patch("services.jira_client.requests.get", return_value=MockResponse(payload={"displayName": "Asha"})):
        result = jira_client.validate_pat("https://example.atlassian.net", "token", "a@example.com")
    assert result == {"valid": True, "user": "Asha", "error": ""}


def test_validate_pat_unauthorized():
    with patch("services.jira_client.requests.get", return_value=MockResponse(status_code=401)):
        result = jira_client.validate_pat("https://example.atlassian.net", "bad", "a@example.com")
    assert result["valid"] is False
    assert "Unauthorized" in result["error"]


def test_validate_pat_network_error():
    with patch("services.jira_client.requests.get", side_effect=requests.ConnectionError("offline")):
        result = jira_client.validate_pat("https://example.atlassian.net", "token", "a@example.com")
    assert result["valid"] is False
    assert "Network error" in result["error"]


def test_fetch_issues_empty_results():
    with patch("services.jira_client.requests.get", return_value=MockResponse(payload={"issues": []})):
        issues = jira_client.fetch_issues("https://example.atlassian.net", "token", "a@example.com")
    assert issues == []


def test_fetch_issues_with_jql():
    response = MockResponse(payload={"issues": [{"key": "BA-1"}]})
    with patch("services.jira_client.requests.get", return_value=response) as mock_get:
        issues = jira_client.fetch_issues(
            "https://example.atlassian.net",
            "token",
            "a@example.com",
            jql="project = BA",
            max_results=10,
            start_at=5,
        )
    assert issues == [{"key": "BA-1"}]
    assert mock_get.call_args.kwargs["params"] == {
        "jql": "project = BA",
        "maxResults": 10,
        "startAt": 5,
    }


def test_fetch_issue_by_key():
    with patch("services.jira_client.requests.get", return_value=MockResponse(payload={"key": "BA-1"})):
        issue = jira_client.fetch_issue("https://example.atlassian.net", "token", "a@example.com", "BA-1")
    assert issue == {"key": "BA-1"}
