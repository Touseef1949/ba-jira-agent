---
name: sprint-health-report
description: Produce a full backlog health report — totals, priority/status/sprint breakdowns, and flagged risks (unassigned high-priority work, open bugs, overloaded sprints). Use for "how healthy is the backlog", "give me a health report", or broad triage questions.
when_to_use: The user asks for an overall picture of the backlog or sprint health, a "health check", a "full report", or wants risks surfaced across the whole backlog rather than a single filtered slice.
command: /sprint-health
---

# Sprint Health Report

Produce a complete, decision-ready health report on the Jira backlog. Do not answer from memory — always pull fresh data with the tools below.

## Procedure

1. Call `calculate_metrics("all")` to get totals, story points, and the priority / status / sprint (velocity) breakdowns in one shot.
2. Call `filter_tickets("status", "Open")` and `filter_tickets("type", "Bug")` to isolate open work and bugs.
3. Call `filter_tickets("assignee", "unassigned")` to find work with no owner.
4. Cross-reference: any ticket that is **both** high-priority (Highest/High) **and** unassigned is a top risk. Any sprint whose story points are well above the others is an overload risk.

## Output format

Return the report in this structure:

- **Snapshot** — total tickets, total story points, unassigned count, open-bug count (one line each).
- **By priority / status / sprint** — compact tables from the metrics.
- **🚩 Risks** — a bulleted list, most severe first. Each risk names the ticket key(s), why it's a risk, and a one-line recommended action (assign, split, de-scope, escalate).
- **Recommended next actions** — 2–4 concrete, prioritized steps for the PO.

Keep it skimmable. Lead with the risks, not the raw counts.
