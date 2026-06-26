"""
Streamlit AppTest smoke tests for app.py.

Uses streamlit.testing.v1.AppTest with mocked agent_service
to avoid real API calls during test runs.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is importable
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


def _make_mock_agent_service():
    """Build a mock replacement for services.agent_service."""
    mock_module = MagicMock()
    mock_module.get_all_tickets.return_value = [
        {
            "key": "BA-101",
            "summary": "Test ticket",
            "type": "Bug",
            "priority": "Highest",
            "status": "Open",
            "assignee": "Alice",
            "story_points": 3,
            "sprint": "Sprint 24",
            "labels": [],
            "created": "2026-06-20",
            "description": "A test bug.",
        }
    ]
    mock_module.get_metrics.return_value = {
        "total": 1,
        "total_sp": 3,
        "unassigned": 0,
        "open_bugs": 1,
    }
    mock_module.run_agent_query.return_value = {
        "answer": "Mock agent answer.",
        "trace": [
            {"role": "ai", "content": "Mock agent answer."},
        ],
    }
    return mock_module


@pytest.fixture
def mock_agent_service_module():
    """Return a MagicMock that replaces services.agent_service in sys.modules."""
    return _make_mock_agent_service()


class TestAppSmoke:
    """Smoke tests that verify the Streamlit app renders without crashing."""

    @pytest.mark.smoke
    def test_app_renders_without_error(self, mock_agent_service_module):
        """The app should run to completion without exceptions."""
        from streamlit.testing.v1 import AppTest

        app_path = os.path.join(PROJECT_DIR, "app.py")

        with patch.dict(
            "sys.modules",
            {"services.agent_service": mock_agent_service_module},
        ):
            at = AppTest.from_file(app_path)

        at.run()
        assert not at.exception

    @pytest.mark.smoke
    def test_app_has_title(self, mock_agent_service_module):
        """The app should render the BA Jira Agent title in the hero card."""
        from streamlit.testing.v1 import AppTest

        app_path = os.path.join(PROJECT_DIR, "app.py")

        with patch.dict(
            "sys.modules",
            {"services.agent_service": mock_agent_service_module},
        ):
            at = AppTest.from_file(app_path)

        at.run()
        assert not at.exception

        # Title is rendered via st.markdown (HTML hero card), not st.title
        markdown_texts = [str(m.value) for m in at.markdown]
        assert any("BA Jira Agent" in t for t in markdown_texts), "Title not found in markdown"

    @pytest.mark.smoke
    def test_app_has_query_input(self, mock_agent_service_module):
        """The app should have a text_area for the query input."""
        from streamlit.testing.v1 import AppTest

        app_path = os.path.join(PROJECT_DIR, "app.py")

        with patch.dict(
            "sys.modules",
            {"services.agent_service": mock_agent_service_module},
        ):
            at = AppTest.from_file(app_path)

        at.run()
        assert not at.exception
        assert at.text_area("query_input")