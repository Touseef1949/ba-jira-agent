---
name: unassigned-risk-triage
description: Find all unassigned tickets and quantify the story points at risk, then rank what needs an owner first. Use for "what's unassigned", "story points at risk", "what has no owner", or ownership-gap questions.
when_to_use: The user wants a full triage or risk analysis of unassigned work with a prioritized assignment plan. Do NOT use for a plain count ("how many unassigned?") — answer that directly with the data tools.
command: /unassigned
---

# Unassigned Risk Triage

Surface the ownership gap in the backlog and turn it into a prioritized assignment list.

## Procedure

1. Call `filter_tickets("assignee", "unassigned")` to get every ticket with no owner.
2. Call `calculate_metrics("summary")` to anchor the unassigned count and total story points against the whole backlog.
3. Sum the story points of the unassigned tickets — this is the **story points at risk**.
4. Rank the unassigned tickets by priority (Highest → Low), then by story points within each priority band.

## Output format

- **Headline** — "N unassigned tickets, X story points at risk (Y% of backlog SP)."
- **Assign first** — a short table of the highest-priority unassigned tickets: key, priority, story points, summary.
- **The rest** — remaining unassigned tickets, one line each.
- **Recommendation** — which 2–3 tickets to assign this sprint and why (priority × size × risk).

Do not invent assignees or capacity; only state what the data shows.
