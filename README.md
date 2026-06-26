# BA Jira Agent

A LangChain ReAct agent that acts as a Business Analyst (BA) Assistant. It reads a mock Jira
export (JSON), summarizes tickets, filters by status/priority/assignee/sprint, searches
descriptions, and calculates backlog metrics — all through natural language queries powered
by the DeepSeek LLM.

Built as a learning project for understanding AI agent architecture: tools, ReAct reasoning
loop, LLM integration, and conversational CLI interaction.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   run.py                        │
│         CLI entry point (single + REPL)         │
└──────────────┬──────────────────────────────────┘
               │ imports executor
               ▼
┌─────────────────────────────────────────────────┐
│                  agent.py                       │
│   ┌───────────────────────────────────────────┐ │
│   │  ChatOpenAI (deepseek-chat)               │ │
│   │  + ReAct prompt (hwchase17/react)         │ │
│   │  + AgentExecutor (max_iterations=10)      │ │
│   └──────────────┬────────────────────────────┘ │
│                  │ uses tools                   │
└──────────────────┼──────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────┐
│                  tools.py                       │
│  ┌─────────────┐  ┌──────────────┐             │
│  │ load_tickets │  │filter_tickets│             │
│  │   (all 20)   │  │(field, value)│             │
│  └─────────────┘  └──────────────┘             │
│  ┌──────────────┐ ┌──────────────────┐         │
│  │search_tickets│ │calculate_metrics │         │
│  │   (keyword)  │ │ (summary/breakdown)        │
│  └──────────────┘ └──────────────────┘         │
│              │                                  │
│              ▼                                  │
│     data/jira_export.json                       │
│        (20 mock tickets)                        │
└─────────────────────────────────────────────────┘
```

**Data flow:** The user asks a question in `run.py` → `agent.py` passes it to the ReAct
agent → the LLM decides which `tool` to call → the tool reads `data/jira_export.json` and
returns results → the LLM synthesizes a structured answer → printed to the terminal.

---

## Setup

### 1. Prerequisites
- Python 3.13+ (`/usr/local/bin/python3`)
- A [DeepSeek API key](https://platform.deepseek.com/api_keys)

### 2. Install dependencies
```bash
cd ~/Documents/Pythonproject/Touseef_Project_Work/learning-ai-agents/ba-jira-agent/
pip install -r requirements.txt
```

### 3. Configure API key
```bash
cp .env.example .env
# Edit .env and add your real DeepSeek API key:
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## How to Run

### Single Query
Pass your question as a command-line argument:
```bash
python3 run.py "Summarize all open bugs in Sprint 24"
```

### Interactive Mode (REPL)
Run without arguments to enter an interactive conversation loop. Type your queries and
press Enter. Press `Ctrl+C` to exit.
```bash
python3 run.py
```

---

## Example Queries

| Query | What It Asks |
|-------|--------------|
| `"Summarize all open bugs in Sprint 24"` | List all bug-type tickets that are open and in Sprint 24 |
| `"Which tickets are unassigned?"` | Find tickets with no assignee |
| `"What is the total story points in the backlog?"` | Sum all story points across the backlog |
| `"Show me all Highest priority tickets"` | Filter tickets by Highest priority |
| `"Calculate sprint velocity metrics"` | Compute velocity/throughput metrics per sprint |

---

## Project Files

```
ba-jira-agent/
├── data/
│   └── jira_export.json       # 20 mock Jira tickets (pre-created)
├── tools.py                   # 4 @tool functions (load, filter, search, metrics)
├── agent.py                   # ReAct agent + AgentExecutor setup
├── run.py                     # CLI: single query mode + interactive REPL
├── requirements.txt           # Python dependencies
├── .env.example               # API key template
└── README.md                  # This file
```

---

## How It Works

1. **Tools layer** (`tools.py`) — Four `@tool`-decorated functions that read from
   `data/jira_export.json`. Each returns formatted text (strings) so the LLM can
   understand them. Tools cover loading, filtering, searching, and metrics calculation.

2. **Agent layer** (`agent.py`) — Wires up `ChatOpenAI` pointed at DeepSeek's API,
   pulls the standard ReAct prompt from LangChain Hub, and wraps everything in an
   `AgentExecutor`. The system prompt instructs the LLM to act as a BA Assistant.

3. **CLI layer** (`run.py`) — Provides two ways to interact: a one-shot mode where
   you pass a query as an argument, and an interactive REPL where you can ask
   multiple questions in a session.

The ReAct loop works as follows: the LLM receives your question → it outputs a
**Thought** ("I need to check unassigned tickets") → an **Action** ("call
calculate_metrics") → the tool runs and returns an **Observation** → the LLM
iterates if needed → finally produces a human-readable **Answer**.
