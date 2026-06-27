"""Jira Cloud REST API v3 client helpers."""

from __future__ import annotations

import base64
from typing import Any

import requests

from core.jira_config import DEFAULT_JQL, JIRA_API_VERSION, JIRA_MAX_RESULTS


class JiraAPIError(Exception):
    """Raised when a Jira API request fails in a recoverable, user-facing way."""


def _normalize_jira_url(jira_url: str) -> str:
    url = (jira_url or "").strip()
    return url.rstrip("/")


def _auth_headers(email: str, pat: str) -> dict[str, str]:
    token = base64.b64encode(f"{email}:{pat}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _error_from_response(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    messages = payload.get("errorMessages") or []
    errors = payload.get("errors") or {}
    if messages:
        return "; ".join(str(m) for m in messages)
    if errors:
        return "; ".join(f"{k}: {v}" for k, v in errors.items())
    if response.status_code == 401:
        return "Unauthorized. Check the Jira email and API token."
    if response.status_code == 403:
        return "Forbidden. The Jira account does not have permission for this resource."
    if response.status_code == 404:
        return "Not found. Check the Jira URL or issue key."
    if response.status_code == 429:
        return "Jira rate limit exceeded. Try again later."
    return response.text or f"Jira API request failed with status {response.status_code}."


def _raise_for_jira_response(response: requests.Response, action: str) -> None:
    if response.status_code < 400:
        return
    raise JiraAPIError(f"{action} failed: {_error_from_response(response)}")


def validate_pat(jira_url: str, pat: str, email: str) -> dict:
    """
    Validate Jira Cloud credentials against the `/myself` endpoint.

    Args:
        jira_url: Base Jira Cloud URL, such as https://example.atlassian.net.
        pat: Jira API token.
        email: Jira account email used with the token.

    Returns:
        A dictionary with `valid`, `user`, and `error` keys.
    """
    url = f"{_normalize_jira_url(jira_url)}/rest/api/{JIRA_API_VERSION}/myself"
    try:
        response = requests.get(url, headers=_auth_headers(email, pat), timeout=15)
    except requests.RequestException as exc:
        return {"valid": False, "user": None, "error": f"Network error: {exc}"}

    if response.status_code == 200:
        try:
            data = response.json()
        except ValueError:
            return {"valid": False, "user": None, "error": "Invalid JSON response from Jira."}
        user = data.get("displayName") or data.get("emailAddress") or data.get("accountId")
        return {"valid": True, "user": user or "Jira user", "error": ""}

    return {"valid": False, "user": None, "error": _error_from_response(response)}


def fetch_issues(
    jira_url: str,
    pat: str,
    email: str,
    jql: str = "",
    max_results: int = JIRA_MAX_RESULTS,
    start_at: int = 0,
) -> list[dict]:
    """
    Fetch Jira issues using the Jira Cloud search endpoint.

    Args:
        jira_url: Base Jira Cloud URL.
        pat: Jira API token.
        email: Jira account email.
        jql: Jira Query Language filter. Defaults to newest created issues.
        max_results: Maximum issues to fetch.
        start_at: Zero-based Jira pagination offset.

    Returns:
        The `issues` list from the Jira API response.

    Raises:
        JiraAPIError: If Jira rejects the request or the network call fails.
    """
    url = f"{_normalize_jira_url(jira_url)}/rest/api/{JIRA_API_VERSION}/search"
    params = {
        "jql": jql or DEFAULT_JQL,
        "maxResults": max_results,
        "startAt": start_at,
    }
    try:
        response = requests.get(url, headers=_auth_headers(email, pat), params=params, timeout=30)
    except requests.RequestException as exc:
        raise JiraAPIError(f"Fetch issues failed: Network error: {exc}") from exc

    _raise_for_jira_response(response, "Fetch issues")
    try:
        data = response.json()
    except ValueError as exc:
        raise JiraAPIError("Fetch issues failed: Invalid JSON response from Jira.") from exc
    return data.get("issues", [])


def fetch_issue(jira_url: str, pat: str, email: str, issue_key: str) -> dict:
    """
    Fetch a single Jira issue by key.

    Args:
        jira_url: Base Jira Cloud URL.
        pat: Jira API token.
        email: Jira account email.
        issue_key: Jira issue key, such as BA-101.

    Returns:
        The Jira issue dictionary.

    Raises:
        JiraAPIError: If Jira rejects the request or the network call fails.
    """
    key = (issue_key or "").strip()
    url = f"{_normalize_jira_url(jira_url)}/rest/api/{JIRA_API_VERSION}/issue/{key}"
    try:
        response = requests.get(url, headers=_auth_headers(email, pat), timeout=30)
    except requests.RequestException as exc:
        raise JiraAPIError(f"Fetch issue {key} failed: Network error: {exc}") from exc

    _raise_for_jira_response(response, f"Fetch issue {key}")
    try:
        return response.json()
    except ValueError as exc:
        raise JiraAPIError(f"Fetch issue {key} failed: Invalid JSON response from Jira.") from exc


def _extract_text_from_adf(node: Any) -> str:
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(part for part in (_extract_text_from_adf(item) for item in node) if part).strip()
    if not isinstance(node, dict):
        return ""

    pieces: list[str] = []
    text = node.get("text")
    if text:
        pieces.append(str(text))
    content = node.get("content")
    if content:
        nested = _extract_text_from_adf(content)
        if nested:
            pieces.append(nested)
    return " ".join(pieces).strip()


def _extract_sprint_name(fields: dict) -> str | None:
    for key, value in fields.items():
        if "sprint" not in key.lower() and key != "customfield_10020":
            continue
        if not value:
            continue
        if isinstance(value, dict):
            name = value.get("name")
            if name:
                return str(name)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and item.get("name"):
                    return str(item["name"])
                if isinstance(item, str):
                    marker = "name="
                    if marker in item:
                        return item.split(marker, 1)[1].split(",", 1)[0].rstrip("]")
                    return item
        if isinstance(value, str):
            return value
    return None


def map_jira_issue_to_ticket(issue: dict) -> dict:
    """
    Normalize a Jira issue dictionary into the app's internal ticket format.

    Args:
        issue: Raw Jira issue dictionary from the REST API.

    Returns:
        A normalized ticket dictionary used by tools, metrics, and the UI.
    """
    fields = issue.get("fields") or {}
    priority = fields.get("priority") or {}
    assignee = fields.get("assignee") or {}
    issue_type = fields.get("issuetype") or {}
    status = fields.get("status") or {}

    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary") or "",
        "type": issue_type.get("name") or "Unknown",
        "priority": priority.get("name") if priority else "Medium",
        "status": status.get("name") or "Unknown",
        "assignee": assignee.get("displayName") if assignee else None,
        "story_points": fields.get("customfield_10016") or 0,
        "sprint": _extract_sprint_name(fields),
        "labels": fields.get("labels") or [],
        "created": fields.get("created") or "",
        "description": _extract_text_from_adf(fields.get("description")),
    }
