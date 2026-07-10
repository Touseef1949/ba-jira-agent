---
name: standup-summary
description: Build a per-assignee workload digest — who owns what, how many tickets, and how many story points each — ready to read out in a standup. Use for "who is working on what", "workload per person", "how much does Priya have", or standup-prep questions.
when_to_use: The user wants a standup-ready workload digest across the whole team (everyone's load, balance flags). Do NOT use for a single-person lookup ("which tickets are Priya's?") — answer that directly with filter_tickets.
command: /standup
---

# Standup Summary

Produce a per-assignee workload digest a Scrum Master can read straight into a standup.

## Procedure

1. Call `load_tickets()` to get the full backlog with assignees and story points.
2. If the user named a specific person, call `filter_tickets("assignee", "<name>")` to scope to them. Known assignees: Priya Sharma, Rahul Verma, Arjun Nair, Sneha Reddy (plus unassigned).
3. Group tickets by assignee. For each person, count tickets and sum story points; note their highest-priority in-flight item.
4. Flag imbalance: anyone carrying a lot more story points than the others, and the unassigned bucket.

## Output format

- **Per person** — one block each: name, ticket count, total story points, and their top in-progress item (key + summary).
- **Unassigned** — count and story points, called out separately.
- **Balance note** — one line flagging over/under-loaded people, if any.

Keep each person to 2–3 lines. Only report assignees who actually have tickets in the data.
