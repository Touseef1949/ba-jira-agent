# BA Jira Agent — Operations Runbook

## Architecture Overview

```
ba-jira-agent/
├── app.py                    # Streamlit web UI (entry point)
├── agent.py                  # LangGraph ReAct agent (DeepSeek LLM)
├── tools.py                  # 4 @tool functions for Jira data
├── run.py                    # CLI runner for the agent
├── core/
│   └── config.py             # Config constants, safe_secret helper
├── services/
│   ├── agent_service.py      # Agent invocation wrapper (UI ↔ agent)
│   └── error_logging.py      # Structured JSONL error logging
├── data/
│   └── jira_export.json      # 20 mock Jira tickets
├── tests/                    # Test suite (pytest)
├── .streamlit/
│   └── config.toml           # Streamlit theme config
├── Dockerfile                # HF Spaces deployment
├── requirements.txt          # Python dependencies
└── RUNBOOK.md                # This file
```

### Data Flow

```
User Query → app.py (Streamlit)
    → services/agent_service.py (run_agent_query)
        → agent.py (LangGraph ReAct agent)
            → tools.py (4 @tool functions)
                → data/jira_export.json
            ← tool results
        ← agent answer + trace
    ← {"answer": str, "trace": [...]}
→ app.py renders results
```

### Components

| Component | Role |
|-----------|------|
| **Streamlit UI** (`app.py`) | Web interface with hero card, query input, results, trace, ticket table, metrics |
| **Agent Service** (`services/agent_service.py`) | Thin wrapper that invokes the LangGraph agent and normalizes output |
| **LangGraph Agent** (`agent.py`) | ReAct agent backed by DeepSeek Chat API with 4 custom tools |
| **Tools** (`tools.py`) | `load_tickets`, `filter_tickets`, `search_tickets`, `calculate_metrics` |
| **Error Logging** (`services/error_logging.py`) | JSONL log at `logs/errors.jsonl` with timestamps, types, and tracebacks |
| **Config** (`core/config.py`) | Centralized constants, env loading, and the `safe_secret()` helper |

## Local Development

### Prerequisites

- Python 3.11+ (recommended: 3.13)
- DeepSeek API key

### Setup

```bash
cd ~/Documents/Pythonproject/Touseef_Project_Work/learning-ai-agents/ba-jira-agent/

# Create virtual environment (recommended)
/usr/local/bin/python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY
```

### Running Locally

```bash
# Streamlit web app (main entry point)
streamlit run app.py

# CLI runner (direct agent invocation, no UI)
python run.py "Show me all open bugs"
```

The Streamlit app starts at `http://localhost:8503`.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Specific test file
pytest tests/test_tools.py -v
```

## Deployment: HuggingFace Spaces

### Step 1: Create a Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose **Streamlit** as the SDK
3. Select any CPU instance (the agent calls DeepSeek API, no GPU needed)
4. Choose **Public** or **Private**

### Step 2: Push Code

```bash
# Clone the Space repo
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# Copy project files (excluding .venv, __pycache__, logs/, .env)
cp -r /path/to/ba-jira-agent/{app.py,agent.py,tools.py,run.py,core,services,data,.streamlit,Dockerfile,requirements.txt} .

# Commit and push
git add .
git commit -m "Deploy BA Jira Agent"
git push origin main
```

### Step 3: Set Secrets

In your Space settings → **Repository Secrets**, add:

| Secret Name | Description |
|-------------|-------------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key (starts with `sk-`) |

The `agent.py` file loads from `.env` for local dev and from environment variables for Spaces — no code changes needed.

> **Note for Docker-based Spaces:** When using the Dockerfile, HF Spaces injects secrets as environment variables automatically. The `dotenv` fallback means local `.env` works and Spaces secrets work — both are supported.

### Step 4: Verify

Visit `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME` and confirm:
- The hero card renders with correct styling
- The metrics dashboard shows numbers from the mock dataset
- The ticket table displays all 20 tickets
- Querying the agent returns a reasoned response

## Secrets Management

### Local Development

Secrets go in `.env` (gitignored — never committed):

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Loaded by both `agent.py` and `core/config.py` via `python-dotenv`.

### HF Spaces

Secrets go in **Space Settings → Repository Secrets**. HF Spaces injects them as environment variables at runtime. No `.env` file needed on Spaces.

### safe_secret Helper

For logging or displaying API key info safely:

```python
from core.config import safe_secret
print(safe_secret("sk-abc123def456ghi789"))  # "sk-a***i789"
```

## Troubleshooting

### "DEEPSEEK_API_KEY not found"

- **Local:** Ensure `.env` exists and contains the key
- **HF Spaces:** Add the secret in Space Settings
- Verify with: `python -c "from core.config import DEEPSEEK_API_KEY; print(bool(DEEPSEEK_API_KEY))"`

### Agent hangs or times out

- Agent queries take 10–30 seconds (multiple tool calls + LLM roundtrips)
- Check `logs/errors.jsonl` for any logged errors
- Verify DeepSeek API is accessible: `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models`

### Streamlit styling not applying

- The CSS is loaded inline via `st.markdown(..., unsafe_allow_html=True)`
- Hard-refresh the browser (Cmd+Shift+R)
- Clear Streamlit cache: `streamlit cache clear`

### Error logs

Errors are written to `logs/errors.jsonl` (one JSON object per line):

```json
{"timestamp": "2026-06-26T12:00:00+00:00", "type": "agent", "message": "...", "traceback": "..."}
```

View recent errors:
```bash
python -c "from services.error_logging import get_recent_errors; import json; [print(json.dumps(e, indent=2)) for e in get_recent_errors()]"
```

## Monitoring

- **Streamlit logs:** Check the HF Spaces build logs and app logs in the Space UI
- **Error logs:** `logs/errors.jsonl` is append-only, rotated manually
- **Agent performance:** Each agent invocation is timed; check the Streamlit spinner duration
- **API usage:** Monitor DeepSeek dashboard for token consumption

## Maintenance

### Updating mock data

Edit `data/jira_export.json` — it's a JSON array of ticket objects. Each ticket has fields: `key`, `summary`, `type`, `priority`, `status`, `assignee`, `story_points`, `sprint`, `labels`, `created`, `description`.

### Adding new tools

1. Add a new `@tool` function in `tools.py`
2. Register it in `agent.py`'s `tools` list
3. The agent automatically discovers and uses it

### Updating dependencies

```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.lock  # optional lock file
```
