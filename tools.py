"""
BA Jira Agent Tools — LangChain @tool functions for mock Jira data analysis.
All tools read from data/jira_export.json and return formatted string output.
"""

import json
import os
from collections import Counter

from langchain.tools import tool

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "jira_export.json")


def _load_all_tickets():
    """Helper: load and return all tickets from the JSON file."""
    with open(DATA_PATH, "r") as f:
        return json.load(f)


@tool
def load_tickets() -> str:
    """
    Load all Jira tickets from the mock data export (data/jira_export.json).
    Returns all fields for every ticket: key, summary, type, priority, status,
    assignee, story_points, sprint, labels, created, and description.
    Use this tool when you need to see the full backlog or a comprehensive listing.
    """
    tickets = _load_all_tickets()
    # Return each ticket as a compact single-line dict for LLM readability
    output_lines = [f"Total tickets: {len(tickets)}\n"]
    for t in tickets:
        output_lines.append(
            f"  {t['key']} | {t['type']} | {t['priority']} | {t['status']} | "
            f"assignee={t['assignee'] or 'unassigned'} | "
            f"SP={t['story_points']} | sprint={t['sprint']} | "
            f"summary: {t['summary']}"
        )
    return "\n".join(output_lines)


@tool
def filter_tickets(field: str, value: str) -> str:
    """
    Filter tickets by a specific field and value.
    Supported fields: status, priority, assignee, sprint, type.
    Value matching is case-insensitive. Returns each matching ticket with key,
    summary, type, priority, status, assignee, story_points, and sprint.
    Use this when you need tickets matching a particular criterion
    (e.g., all 'Open' tickets, all 'Bug' type, all tickets in 'Sprint 24').
    """
    valid_fields = {"status", "priority", "assignee", "sprint", "type"}
    if field not in valid_fields:
        return (
            f"Error: field '{field}' is not supported. "
            f"Valid fields: {', '.join(sorted(valid_fields))}"
        )

    tickets = _load_all_tickets()
    value_lower = value.lower()
    results = []

    for t in tickets:
        # Handle assignee which can be null
        field_value = t.get(field)
        if field_value is None:
            field_value_str = "unassigned" if field == "assignee" else ""
        else:
            field_value_str = str(field_value)

        if value_lower in field_value_str.lower():
            results.append(t)

    if not results:
        return f"No tickets found where {field} matches '{value}'."

    output_lines = [
        f"Found {len(results)} ticket(s) where {field} matches '{value}':\n"
    ]
    for t in results:
        output_lines.append(
            f"  {t['key']} | {t['type']} | {t['priority']} | {t['status']} | "
            f"assignee={t['assignee'] or 'unassigned'} | "
            f"SP={t['story_points']} | sprint={t['sprint']} | "
            f"summary: {t['summary']}"
        )
    return "\n".join(output_lines)


@tool
def search_tickets(query: str) -> str:
    """
    Search tickets by keyword across summary and description fields.
    Case-insensitive search. Returns matching ticket keys, summaries, and
    the matching context (where the keyword was found).
    Use this for open-ended searching (e.g., find all tickets mentioning 'Slack'
    or 'CORS') when you don't know the exact field value to filter on.
    """
    tickets = _load_all_tickets()
    query_lower = query.lower()
    results = []

    for t in tickets:
        summary_text = t.get("summary", "")
        description_text = t.get("description", "")
        combined = summary_text + " " + description_text

        if query_lower in combined.lower():
            # Determine where the match occurred
            where = []
            if query_lower in summary_text.lower():
                where.append("summary")
            if query_lower in description_text.lower():
                where.append("description")
            results.append((t, where))

    if not results:
        return f"No tickets found matching search query '{query}'."

    output_lines = [
        f"Found {len(results)} ticket(s) matching '{query}':\n"
    ]
    for t, where in results:
        output_lines.append(
            f"  {t['key']} | {t['type']} | {t['priority']} | {t['status']} | "
            f"assignee={t['assignee'] or 'unassigned'} | sprint={t['sprint']} | "
            f"matched in: {', '.join(where)}\n"
            f"    summary: {t['summary']}"
        )
    return "\n".join(output_lines)


@tool
def calculate_metrics(metric_type: str = "all") -> str:
    """
    Calculate backlog metrics from the Jira tickets.
    Accepted metric_type values:
      - "summary"     : total tickets, total story points, unassigned count
      - "priority"    : ticket counts grouped by priority level
      - "status"      : ticket counts grouped by status
      - "sprint"      : ticket counts and story points per sprint, plus velocity
      - "all"         : all of the above in one report (default)
    Use this for sprint planning, velocity analysis, and backlog health checks.
    """
    valid_types = {"summary", "priority", "status", "sprint", "all"}
    mt = metric_type.lower() if metric_type else "all"

    if mt not in valid_types:
        return (
            f"Error: metric_type '{metric_type}' is not supported. "
            f"Valid types: {', '.join(sorted(valid_types))}"
        )

    tickets = _load_all_tickets()
    output_parts = []

    if mt in ("summary", "all"):
        total = len(tickets)
        total_sp = sum(t.get("story_points", 0) for t in tickets)
        unassigned = sum(1 for t in tickets if t.get("assignee") is None)
        # Count by type
        type_counts = Counter(t.get("type", "Unknown") for t in tickets)

        output_parts.append("=== BACKLOG SUMMARY ===")
        output_parts.append(f"Total Tickets:        {total}")
        output_parts.append(f"Total Story Points:   {total_sp}")
        output_parts.append(f"Unassigned Tickets:   {unassigned}")
        output_parts.append(f"By Type:")
        for typ, count in type_counts.most_common():
            output_parts.append(f"  {typ}: {count}")

    if mt in ("priority", "all"):
        priority_counts = Counter(t.get("priority", "Unknown") for t in tickets)
        priority_order = ["Highest", "High", "Medium", "Low"]

        output_parts.append("\n=== BY PRIORITY ===")
        for p in priority_order:
            count = priority_counts.get(p, 0)
            output_parts.append(f"  {p}: {count}")
        # Any priority not in the standard order
        for p, count in priority_counts.items():
            if p not in priority_order:
                output_parts.append(f"  {p}: {count}")

    if mt in ("status", "all"):
        status_counts = Counter(t.get("status", "Unknown") for t in tickets)

        output_parts.append("\n=== BY STATUS ===")
        for s, count in status_counts.most_common():
            output_parts.append(f"  {s}: {count}")

    if mt in ("sprint", "all"):
        # Group by sprint: count tickets and sum story points
        sprint_data = {}
        for t in tickets:
            sprint = t.get("sprint", "Unknown")
            if sprint not in sprint_data:
                sprint_data[sprint] = {"ticket_count": 0, "story_points": 0}
            sprint_data[sprint]["ticket_count"] += 1
            sprint_data[sprint]["story_points"] += t.get("story_points", 0)

        # Sort sprints alphabetically
        output_parts.append("\n=== BY SPRINT (Velocity) ===")
        for sprint in sorted(sprint_data.keys()):
            d = sprint_data[sprint]
            output_parts.append(
                f"  {sprint}: {d['ticket_count']} tickets, "
                f"{d['story_points']} story points"
            )

    return "\n".join(output_parts)
