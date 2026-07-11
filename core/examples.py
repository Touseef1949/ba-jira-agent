"""Curated prompts that demonstrate the BA agent's skills and tools together."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuidedExample:
    """A UI example with an explicit, inspectable execution route."""

    title: str
    outcome: str
    prompt: str
    skills: tuple[str, ...]
    tools: tuple[str, ...]


GUIDED_EXAMPLES: tuple[GuidedExample, ...] = (
    GuidedExample(
        title="Sprint health check",
        outcome="Assess scope, delivery risk, blockers, and recommended actions.",
        prompt=(
            "Create a sprint health report for Sprint 24. Analyze status mix, open bugs, "
            "blocked work, and story-point progress, then recommend the top three actions."
        ),
        skills=("sprint-health-report",),
        tools=("load_skill", "filter_tickets", "calculate_metrics"),
    ),
    GuidedExample(
        title="Unassigned risk triage",
        outcome="Prioritize ownerless work by urgency and business impact.",
        prompt=(
            "Run an unassigned risk triage for Sprint 24. Rank unassigned tickets by "
            "priority and delivery risk, and suggest the role that should own each one."
        ),
        skills=("unassigned-risk-triage",),
        tools=("load_skill", "filter_tickets", "search_tickets"),
    ),
    GuidedExample(
        title="Velocity forecast",
        outcome="Use historical sprint metrics and the bundled forecasting tool.",
        prompt=(
            "Forecast the next sprint's likely velocity from all completed sprint data. "
            "Show the historical values, explain the estimate, and flag planning risks."
        ),
        skills=("velocity-forecast",),
        tools=("load_skill", "calculate_metrics", "use_skill_tool"),
    ),
    GuidedExample(
        title="Stand-up briefing",
        outcome="Turn current ticket state into a concise team briefing.",
        prompt=(
            "Prepare today's stand-up summary for Sprint 24. Group completed, in-progress, "
            "blocked, and unassigned work, then call out items that need attention today."
        ),
        skills=("standup-summary",),
        tools=("load_skill", "filter_tickets", "search_tickets"),
    ),
    GuidedExample(
        title="Delivery risk review",
        outcome="Combine sprint health with focused ownership-risk triage.",
        prompt=(
            "Perform a delivery risk review for Sprint 24 using both the sprint health report "
            "and unassigned risk triage skills. Quantify the backlog risks, identify the five "
            "most urgent tickets, and produce an owner/action plan."
        ),
        skills=("sprint-health-report", "unassigned-risk-triage"),
        tools=("load_skill", "filter_tickets", "calculate_metrics"),
    ),
    GuidedExample(
        title="Next-sprint planning pack",
        outcome="Combine delivery health and velocity evidence into a planning recommendation.",
        prompt=(
            "Build a next-sprint planning pack using the sprint health report and velocity "
            "forecast skills. Compare Sprint 24 health with historical velocity, recommend a "
            "story-point commitment, and list assumptions and risks."
        ),
        skills=("sprint-health-report", "velocity-forecast"),
        tools=("load_skill", "calculate_metrics", "use_skill_tool"),
    ),
)


QUICK_TOOL_EXAMPLES: tuple[str, ...] = (
    "Show me all open bugs in Sprint 24",
    "What's the total story points across all tickets?",
    "Search for tickets related to performance",
    "Show me unassigned tickets",
)
