# AGENT.md — BA Jira Agent Project Memory

Persistent context for the BA Jira Agent. This file is always injected into the
agent's system prompt (the `CLAUDE.md` analogue). Keep it short and factual —
team conventions the agent should honor in every answer.

## Team roster

- **Priya Sharma** — Frontend
- **Rahul Verma** — Backend
- **Arjun Nair** — Platform / DevOps
- **Sneha Reddy** — QA / Full-stack
- Unassigned work is an ownership gap and should always be surfaced.

## Sprint cadence

- Two-week sprints, numbered sequentially (currently Sprint 23 → Sprint 27).
- Sprint 24 is the active sprint; earlier sprints are treated as delivered.

## Priority conventions

- Priority ladder: **Highest > High > Medium > Low**.
- Any **Highest** or **High** priority item that is unassigned is a top risk and
  must be called out first in any triage or health report.
- Open bugs are counted separately from stories when reporting backlog health.

## Definition of done

- A ticket is "done" only when status is **Resolved**.
- `Open`, `To Do`, and `In Progress` all count as outstanding work.

## Reporting style

- Lead with risks and recommended actions, not raw counts.
- Never invent tickets, assignees, story points, or capacity — report only what
  the tools return. State assumptions explicitly when forecasting.
