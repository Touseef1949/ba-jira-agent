---
title: BA Jira Agent
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# BA Jira Agent

A LangChain ReAct agent that analyzes Jira backlogs — reasons about which tool to call, executes it, observes results, and produces structured summaries.

## Features
- 4 custom LangChain data tools (load, filter, search, metrics)
- **Skill layer (Claude-Code-style)** — reusable BA playbooks in `skills/*/SKILL.md`, surfaced to the agent as a name+description catalog and loaded on demand via the `load_skill` tool (progressive disclosure, visible in the ReAct trace)
- **Slash commands** — `/sprint-health`, `/velocity`, `/unassigned`, `/standup` launch a skill directly from the UI or query box
- **Project memory** — `AGENT.md` (the `CLAUDE.md` analogue) is always injected: team roster, sprint cadence, definition-of-done, priority conventions
- **Subagents** — `spawn_subagent(skill, task)` delegates a self-contained analysis to a specialist sub-agent scoped to one skill (Claude Code's Task-tool pattern)
- **Per-skill bundled tools** — a skill can ship `skills/<slug>/tools.py`; those tools are revealed only after `load_skill` and run via `use_skill_tool(skill, tool)` (e.g. `velocity-forecast` bundles `forecast_next_sprint`)
- DeepSeek LLM via OpenAI-compatible API (`deepseek-v4-flash`)
- LangGraph ReAct orchestration
- 20 mock Jira tickets (bugs, stories, epics)
- Streamlit web UI matching BA Assistant design system
- Test suite: unit, integration, smoke/AppTest + a dedicated skill-layer suite (`tests/test_skills.py`)

## Architecture

**A progressive-disclosure _Agent Skills_ layer on a ReAct core** — the same shape
Claude Code uses. It composes four well-known patterns:

- **ReAct-style tool loop** (Reason → Act → Observe) through LangChain's
  `create_agent` API as the base agent loop.
- **Agent Skills with progressive disclosure** — only each skill's *name + description*
  sits in the prompt; the full procedure is fetched on demand via `load_skill`.
- **Orchestrator–workers** — the agent delegates a self-contained sub-task to a
  single-skill specialist via `spawn_subagent` (Claude Code's Task-tool pattern).
- **Project memory** — `AGENT.md` (the `CLAUDE.md` analogue) is always injected.

```text
        user query    "/velocity"   "give me a health report"   "how many bugs?"
             |
             v
   +--------------------------------------------------------------------------+
   |  Streamlit UI  (app.py)                                                  |
   |  /slash launchers    .    Skills panel    .    ReAct trace viewer        |
   +--------------------------------------------------------------------------+
               |  expand_slash_command()      ( /velocity -> run the skill )
               v
   +--------------------------------------------------------------------------+
   |  agent_service.run_agent_query()       validate . trace . latency        |
   +--------------------------------------------------------------------------+
               |
               v
   +--------------------------------------------------------------------------+
   |  ReAct Agent    .    LangGraph  +  DeepSeek                              |
   |                                                                          |
   |  SYSTEM PROMPT =  base persona                                           |
   |                 + AGENT.md project memory          <- always injected    |
   |                 + SKILL CATALOG (name + one-line desc)   <- cheap        |
   |                                                                          |
   |     loop:    Think -->  Act -->  Observe  -->  (repeat until answer)     |
   +--------------------------------------------------------------------------+
      |
      +-- data tools --->  load_tickets . filter_tickets . search_tickets .
      |                    calculate_metrics   -->  jira_export.json / live Jira
      |
      +-- skill tools -->  load_skill(name) -------->  SkillRegistry (core/skills.py)
      |                    use_skill_tool(skill,tool)     scans skills/*/
      |                          |
      |                          v
      |                    skills/<slug>/SKILL.md    procedure      (loaded on demand)
      |                    skills/<slug>/tools.py    bundled tools  (optional)
      |
      +-- delegate ----->  spawn_subagent(skill, task)
                           `-->  fresh ReAct loop scoped to ONE skill + data tools
```

## Skill layer

A *skill* is a folder under `skills/` with a `SKILL.md` file: YAML frontmatter
(`name`, `description`, `when_to_use`, `command`) plus a markdown **procedure**.
Only the name + description enter the system prompt; the agent calls `load_skill`
to pull a skill's full procedure when a query matches it, then follows it using the
data tools. Add a new skill by dropping a new `skills/<slug>/SKILL.md` — no code
change required.

Shipped skills: `sprint-health-report`, `unassigned-risk-triage`,
`velocity-forecast`, `standup-summary`.

A skill may also ship **bundled tools** (`skills/<slug>/tools.py`) and be run as a
**subagent**. Skills are gated to report/analysis intent — narrow factual questions
("how many unassigned?") are answered directly by the data tools, no skill loaded.

## Tech Stack
- Python 3.13
- LangChain 1.3.x + LangGraph
- DeepSeek API (`deepseek-v4-flash`)
- Streamlit
