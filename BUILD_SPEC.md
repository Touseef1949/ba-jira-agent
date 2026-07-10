# BA Jira Agent — Build Spec

## Project
A LangChain ReAct agent that reads a mock Jira export (JSON), summarizes tickets, and prioritizes the backlog.

## Location
~/Documents/Pythonproject/Touseef_Project_Work/learning-ai-agents/ba-jira-agent/

## Stack
- Python 3.13 (/usr/local/bin/python3)
- LangChain (langchain, langchain-openai)
- DeepSeek API (model: deepseek-v4-flash, base_url: https://api.deepseek.com/v1)
- Mock Jira data already at data/jira_export.json (20 tickets)

## Agent Tools (4 tools)
1. `load_tickets()` — Loads all tickets from data/jira_export.json. Returns list of ticket dicts.
2. `filter_tickets(field, value)` — Filters tickets by any field (status, priority, assignee, sprint, type). Returns matching tickets.
3. `search_tickets(query)` — Simple keyword search across summary + description fields. Returns matching tickets.
4. `calculate_metrics(metric_type)` — Computes backlog metrics: total_tickets, by_priority, by_status, unassigned_count, total_story_points, velocity_by_sprint.

## Agent Behavior
- Uses create_react_agent from langchain.agents
- LLM: ChatOpenAI with DeepSeek base_url
- ReAct prompt template (hwchase17/react from langchain hub)
- AgentExecutor with verbose=True, max_iterations=10
- System prompt: "You are a BA Assistant AI agent. You help Product Owners analyze Jira backlogs. You have tools to load tickets, filter them, search them, and calculate metrics. Always use tools to get data before answering. Provide structured, actionable summaries."

## File Structure
```
ba-jira-agent/
├── data/
│   └── jira_export.json       # ALREADY CREATED — 20 mock tickets
├── tools.py                   # 4 @tool functions
├── agent.py                   # Agent + AgentExecutor setup
├── run.py                     # CLI entry point (interactive + single query)
├── requirements.txt           # langchain, langchain-openai, python-dotenv
├── .env.example               # DEEPSEEK_API_KEY=your-key-here
└── README.md                  # How to run, what it does
```

## requirements.txt
```
langchain>=0.3.0
langchain-openai>=0.2.0
langchainhub>=0.1.1
python-dotenv>=1.0.0
```

## tools.py — Detailed
Each tool must be decorated with @tool from langchain.tools. Include docstrings (the LLM reads these to decide which tool to call).

1. load_tickets(): Returns JSON string of all tickets with key, summary, type, priority, status, assignee, story_points, sprint.
2. filter_tickets(field: str, value: str): field can be "status", "priority", "assignee", "sprint", "type". Returns matching tickets as formatted text.
3. search_tickets(query: str): Case-insensitive search in summary + description. Returns matching ticket keys + summaries.
4. calculate_metrics(metric_type: str): metric_type can be "summary", "priority", "status", "sprint", "all". Returns formatted metrics text.

## agent.py — Detailed
- Load DEEPSEEK_API_KEY from .env via dotenv
- Create ChatOpenAI(model="deepseek-v4-flash", base_url="https://api.deepseek.com/v1", temperature=0)
- Pull ReAct prompt from langchain hub: hub.pull("hwchase17/react")
- Create agent: create_react_agent(llm, tools, prompt)
- Create executor: AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10, handle_parsing_errors=True)
- Export `executor` and `run_agent(query)` function

## run.py — Detailed
- Import executor from agent.py
- Support two modes:
  1. Single query: `python run.py "Summarize all bugs in Sprint 24"`
  2. Interactive: `python run.py` (no args) — REPL loop, type queries, Ctrl+C to exit
- Print Thought/Action/Observation verbose output (already handled by verbose=True)
- Print final answer with formatting

## .env.example
```
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

## README.md
- Project description (what it does, why)
- Architecture diagram (ASCII)
- Setup instructions (pip install, .env setup)
- How to run (single query + interactive mode)
- Example queries:
  - "Summarize all open bugs in Sprint 24"
  - "Which tickets are unassigned?"
  - "What is the total story points in the backlog?"
  - "Show me all Highest priority tickets"
  - "Calculate sprint velocity metrics"

## IMPORTANT
- Use /usr/local/bin/python3 (NOT anaconda python)
- The .env file must be loaded from the project directory
- All tool functions must return strings (not dicts) — the LLM needs readable text
- Tool docstrings must be clear — the LLM decides which tool to call based on them
- handle_parsing_errors=True on AgentExecutor — DeepSeek may occasionally format ReAct output incorrectly

## Skill Layer (added)

Claude-Code-style skills sit on top of the existing ReAct runtime — no runtime swap.

- `skills/<slug>/SKILL.md` — YAML frontmatter (`name`, `description`, `when_to_use`, `command`) + markdown procedure body.
- `core/skills.py::SkillRegistry` — discovers skills, parses frontmatter (pyyaml), exposes `catalog()`, `get_body()`, `resolve_command()`, `expand_slash_command()`.
- `tools.py::load_skill(skill_name)` — returns a skill's full procedure on demand (progressive disclosure) and surfaces the skill's bundled tools if any.
- `tools.py::use_skill_tool(skill, tool, arg)` — dispatches to a skill's bundled `tools.py` functions (revealed only after load_skill).
- `tools.py::spawn_subagent(skill, task)` — runs a fresh single-skill ReAct sub-agent (data tools only, no recursion) and returns its result. Lazy-imports `agent.llm` to avoid an import cycle.
- `core/skills.py::SkillRegistry` — discovers skills, parses frontmatter (pyyaml), exposes `catalog()`, `get_body()`, `resolve_command()`, `expand_slash_command()`, `get_skill_tools()`, `has_tools()`.
- `agent.py::build_system_prompt()` — composes base persona + `AGENT.md` project memory + the skill catalog. `SYSTEM_PROMPT` is built from it at import. Skills are gated to report/analysis intent; narrow factual questions are answered directly by the data tools.
- `core/project_memory.py::load_project_memory()` — injects `AGENT.md` (the `CLAUDE.md` analogue) when present.
- `app.py` — 🧩 Skills sidebar panel + `/command` launcher buttons; slash input is expanded via `SkillRegistry.expand_slash_command()` before `run_agent_query`.
- Agent tool set (7): the 4 data tools + `load_skill`, `use_skill_tool`, `spawn_subagent`.

Add a skill by creating `skills/<slug>/SKILL.md` (optionally `skills/<slug>/tools.py` for bundled tools) — no core code change needed. Tests live in `tests/test_skills.py`.