"""
Shared fixtures for the BA Jira Agent test suite.

Provides:
  - ticket_data : loads the 20 mock Jira tickets from data/jira_export.json
  - mock_agent  : a MagicMock that patches agent.invoke for agent_service tests
"""


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "smoke: smoke tests (fast, critical path)"
    )
    config.addinivalue_line(
        "markers", "unit: unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests requiring file I/O or fixtures"
    )
    config.addinivalue_line(
        "markers", "regression: regression tests verifying consistency across runs"
    )

import json
import os
from unittest.mock import MagicMock, patch

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
DATA_PATH = os.path.join(PROJECT_DIR, "data", "jira_export.json")


@pytest.fixture(scope="session")
def ticket_data():
    """Load and return the full list of 20 mock Jira tickets."""
    with open(DATA_PATH, "r") as f:
        return json.load(f)


@pytest.fixture
def mock_agent():
    """
    Return a MagicMock that stands in for agent.invoke.

    The default return value emulates a simple agent response:
      {"messages": [MockMessage("I found 20 tickets.")]}
    """
    mock_msg = MagicMock()
    mock_msg.content = "I found 20 tickets in the backlog."
    mock_msg.type = "ai"

    mock_result = {"messages": [mock_msg]}

    agent_mock = MagicMock()
    agent_mock.invoke.return_value = mock_result
    return agent_mock
