"""Streamlit AppTest coverage for the live Jira toggle."""

import os
import services
import sys
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

APP_PATH = os.path.join(PROJECT_DIR, "app.py")


def _mock_agent_service():
    mock_module = MagicMock()
    mock_module.get_metrics.return_value = {
        "total": 1,
        "total_sp": 3,
        "unassigned": 0,
        "open_bugs": 1,
    }
    mock_module.get_all_tickets.return_value = [
        {
            "key": "BA-1",
            "summary": "Test bug",
            "type": "Bug",
            "priority": "High",
            "status": "Open",
            "assignee": "Asha",
            "story_points": 3,
            "sprint": "Sprint 1",
            "labels": [],
            "created": "2026-06-20",
            "description": "Test description",
        }
    ]
    mock_module.run_agent_query.return_value = {
        "answer": "Jira mode answer",
        "trace": [{"role": "ai", "content": "Jira mode answer"}],
    }
    return mock_module


def _mock_auth_service(connected=True):
    mock_module = MagicMock()
    if connected:
        mock_module.validate_jira_connection.return_value = {
            "connected": True,
            "user": "Asha Rao",
            "error": "",
        }
    else:
        mock_module.validate_jira_connection.return_value = {
            "connected": False,
            "user": "",
            "error": "Unauthorized",
        }
    mock_module.mask_pat.side_effect = lambda pat: "toke****cret" if pat else ""
    return mock_module


def _run_app(agent_service=None, auth_service=None):
    from streamlit.testing.v1 import AppTest

    agent_service = agent_service or _mock_agent_service()
    auth_service = auth_service or _mock_auth_service()
    at = AppTest.from_file(APP_PATH)
    _rerun(at, agent_service, auth_service)
    return at, agent_service, auth_service


def _rerun(at, agent_service, auth_service):
    with patch.dict(
        "sys.modules",
        {
            "services.agent_service": agent_service,
            "services.auth_service": auth_service,
        },
    ), patch.object(services, "auth_service", auth_service, create=True):
        at.run(timeout=10)
    return at, agent_service, auth_service


def test_toggle_defaults_off():
    at, _, _ = _run_app()
    assert not at.exception
    assert at.session_state["use_live_jira"] is False


def test_toggle_shows_jira_fields_when_on():
    at, agent_service, auth_service = _run_app()
    at.toggle(key="use_live_jira").set_value(True)
    _rerun(at, agent_service, auth_service)
    assert at.text_input(key="jira_url")
    assert at.text_input(key="jira_email")
    assert at.text_input(key="jira_pat")


def test_jira_fields_hidden_when_toggle_off():
    at, _, _ = _run_app()
    assert len(at.text_input) == 0


def test_test_connection_success_shows_green_badge():
    at, agent_service, auth = _run_app(auth_service=_mock_auth_service(connected=True))
    at.toggle(key="use_live_jira").set_value(True)
    _rerun(at, agent_service, auth)
    at.text_input(key="jira_url").set_value("example.atlassian.net")
    at.text_input(key="jira_email").set_value("a@example.com")
    at.text_input(key="jira_pat").set_value("tokensecret")
    at.button(key="test_jira_connection").click()
    _rerun(at, agent_service, auth)
    assert auth.validate_jira_connection.called
    assert at.session_state["jira_config"]["pat"] == "tokensecret"
    assert any("Connected as Asha Rao" in str(s.value) for s in at.success)


def test_test_connection_failure_shows_error():
    at, agent_service, auth = _run_app(auth_service=_mock_auth_service(connected=False))
    at.toggle(key="use_live_jira").set_value(True)
    _rerun(at, agent_service, auth)
    at.text_input(key="jira_url").set_value("example.atlassian.net")
    at.text_input(key="jira_email").set_value("a@example.com")
    at.text_input(key="jira_pat").set_value("badtoken")
    at.button(key="test_jira_connection").click()
    _rerun(at, agent_service, auth)
    assert auth.validate_jira_connection.called
    assert at.session_state["jira_config"] is None
    assert any("Unauthorized" in str(e.value) for e in at.error)


def test_metrics_load_from_mock_when_toggle_off():
    _, agent_service, _ = _run_app()
    kwargs = agent_service.get_metrics.call_args.kwargs
    assert kwargs["data_source"] == "mock"
    assert kwargs["jira_config"] is None


def test_metrics_load_from_jira_when_toggle_on_connected():
    at, agent_service, _ = _run_app()
    at.session_state["jira_config"] = {
        "jira_url": "https://example.atlassian.net",
        "email": "a@example.com",
        "pat": "tokensecret",
    }
    at.session_state["jira_connection_user"] = "Asha Rao"
    at.toggle(key="use_live_jira").set_value(True)
    _rerun(at, agent_service, _)
    kwargs = agent_service.get_metrics.call_args.kwargs
    assert kwargs["data_source"] == "jira"
    assert kwargs["jira_config"]["email"] == "a@example.com"


def test_query_submit_with_jira_mode():
    at, agent_service, _ = _run_app()
    at.session_state["jira_config"] = {
        "jira_url": "https://example.atlassian.net",
        "email": "a@example.com",
        "pat": "tokensecret",
    }
    at.session_state["jira_connection_user"] = "Asha Rao"
    at.toggle(key="use_live_jira").set_value(True)
    _rerun(at, agent_service, _)
    at.text_area(key="query_input").set_value("Show open bugs")
    _rerun(at, agent_service, _)
    at.button[7].click()
    _rerun(at, agent_service, _)
    kwargs = agent_service.run_agent_query.call_args.kwargs
    assert kwargs["data_source"] == "jira"
    assert kwargs["jira_config"]["pat"] == "tokensecret"
