"""Tests for the Jira auth service."""

from unittest.mock import patch

import pytest

from services import auth_service
from services.jira_client import JiraAPIError


def test_validate_jira_connection_success():
    with patch("services.auth_service.jira_client.validate_pat", return_value={
        "valid": True, "user": "Asha Rao", "error": ""
    }):
        result = auth_service.validate_jira_connection("example.atlassian.net", "token", "a@example.com")
    assert result["connected"] is True
    assert result["user"] == "Asha Rao"


def test_validate_jira_connection_invalid_pat():
    with patch("services.auth_service.jira_client.validate_pat", return_value={
        "valid": False, "user": None, "error": "Unauthorized"
    }):
        result = auth_service.validate_jira_connection("https://example.atlassian.net", "bad", "a@example.com")
    assert result["connected"] is False
    assert "Unauthorized" in result["error"]


def test_validate_jira_connection_bad_url():
    result = auth_service.validate_jira_connection("not-a-valid-url", "token", "a@example.com")
    assert result["connected"] is False
    assert "valid" in result["error"].lower()


def test_validate_jira_connection_url_normalization():
    with patch("services.auth_service.jira_client.validate_pat", return_value={
        "valid": True, "user": "Asha", "error": ""
    }) as mock_validate:
        result = auth_service.validate_jira_connection("example.atlassian.net", "token", "a@example.com")
    assert result["connected"] is True
    # URL should have been normalized with https:// prefix
    normalized_url = mock_validate.call_args[0][0]
    assert normalized_url.startswith("https://")


def test_mask_pat_standard():
    assert auth_service.mask_pat("abcdefghijklmnop") == "abcd********mnop"


def test_mask_pat_short():
    assert auth_service.mask_pat("abc") == "***"


def test_mask_pat_empty():
    assert auth_service.mask_pat("") == ""
