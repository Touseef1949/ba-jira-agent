"""Authentication helpers for Jira Cloud live connections."""

from __future__ import annotations

from urllib.parse import urlparse

from services import jira_client


def _normalize_url(jira_url: str) -> str:
    url = (jira_url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def validate_jira_connection(jira_url: str, pat: str, email: str) -> dict:
    """
    Normalize and validate a Jira Cloud connection using an email and API token.

    Args:
        jira_url: Base Jira URL supplied by the user.
        pat: Jira API token.
        email: Jira account email.

    Returns:
        A dictionary with `connected`, `user`, and `error` keys.
    """
    normalized_url = _normalize_url(jira_url)
    parsed = urlparse(normalized_url)
    if not normalized_url or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"connected": False, "user": "", "error": "Enter a valid Jira URL."}
    if not email or not email.strip():
        return {"connected": False, "user": "", "error": "Enter the Jira account email."}
    if not pat:
        return {"connected": False, "user": "", "error": "Enter a Jira API token."}

    result = jira_client.validate_pat(normalized_url, pat, email.strip())
    if result.get("valid"):
        return {"connected": True, "user": result.get("user") or "Jira user", "error": ""}
    return {"connected": False, "user": "", "error": result.get("error") or "Connection failed."}


def mask_pat(pat: str) -> str:
    """
    Mask a Jira API token for safe UI display.

    Args:
        pat: Raw API token.

    Returns:
        A masked token showing only the first four and last four characters.
    """
    if not pat:
        return ""
    if len(pat) <= 8:
        return "*" * len(pat)
    return f"{pat[:4]}{'*' * (len(pat) - 8)}{pat[-4:]}"
