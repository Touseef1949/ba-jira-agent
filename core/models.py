"""
Shared dataclasses for the BA Jira Agent.

Provides immutable data structures for tickets, agent results,
and dashboard metrics used across the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Ticket:
    """Immutable representation of a single Jira ticket."""

    key: str
    summary: str
    type: str
    priority: str
    status: str
    assignee: str | None = None
    story_points: int = 0
    sprint: str = ""
    labels: list[str] = field(default_factory=list)
    created: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        """Construct a Ticket from a dictionary (e.g., from jira_export.json)."""
        return cls(
            key=data.get("key", ""),
            summary=data.get("summary", ""),
            type=data.get("type", ""),
            priority=data.get("priority", ""),
            status=data.get("status", ""),
            assignee=data.get("assignee"),
            story_points=data.get("story_points", 0) or 0,
            sprint=data.get("sprint", ""),
            labels=data.get("labels", []),
            created=data.get("created", ""),
            description=data.get("description", ""),
        )


@dataclass(frozen=True)
class AgentResult:
    """Result of an agent query: final answer plus ReAct trace."""

    answer: str
    trace: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class DashboardMetrics:
    """Summary metrics for the backlog dashboard cards."""

    total: int = 0
    total_sp: int = 0
    unassigned: int = 0
    open_bugs: int = 0


@dataclass(frozen=True)
class TraceEntry:
    """A single step in the ReAct agent trace."""

    role: str
    content: str
