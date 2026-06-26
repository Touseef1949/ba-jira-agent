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

## Health Monitoring

A standalone health-check script is available at `scripts/health_monitor.py`:

```bash
# Check the production HF Space
python scripts/health_monitor.py

# Check local dev server
python scripts/health_monitor.py --local

# Check a custom URL
python scripts/health_monitor.py --url https://my-custom-deploy.com
```

The script outputs JSON on stdout and exits 0 for healthy, 1 for unhealthy:

```json
{"status": "healthy", "latency_ms": 245.3, "timestamp": "2026-06-26T12:00:00+00:00"}
```

### Load Testing

Locust load tests are at `tests/load/locustfile.py`. They test only non-LLM endpoints (health/GUI — no agent invocation).

```bash
# Install locust (one time)
pip install locust

# Headless run against HF Space
locust -f tests/load/locustfile.py --host=https://tshaik1990-ba-jira-agent.hf.space \
    --headless -u 10 -t 60s

# Headless run against local dev
locust -f tests/load/locustfile.py --host=http://localhost:8503 \
    --headless -u 10 -t 60s

# Interactive web UI mode (open http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://localhost:8503
```

### Latency Statistics

Latency is tracked per agent invocation via `services/error_logging.py`:

```python
from services.error_logging import get_latency_stats, log_latency

# View latency stats across all operations
stats = get_latency_stats()
print(stats)
# {"samples": 15, "p50_ms": 12000, "p95_ms": 24500, "p99_ms": 31000, ...}

# View stats for a specific operation
stats = get_latency_stats("run_agent_query")
```

## Incident Response

### What to check when agent returns errors

1. **Verify API key** — Check `DEEPSEEK_API_KEY` is set and valid:
   ```bash
   python -c "from core.config import DEEPSEEK_API_KEY; print('Set' if DEEPSEEK_API_KEY else 'MISSING')"
   ```

2. **Check error logs** — The most recent errors are in `logs/errors.jsonl`:
   ```bash
   # View last 20 errors as pretty JSON
   python -c "
   from services.error_logging import get_recent_errors
   import json
   for e in get_recent_errors(20):
       print(json.dumps(e, indent=2))
   "
   ```

3. **Check API availability** — Verify DeepSeek API is reachable:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" \
     -H "Authorization: Bearer $DEEPS...EY" \
     https://api.deepseek.com/v1/models
   ```
   Expected: HTTP 200.

4. **Check agent latency** — If responses are slow, inspect latency stats:
   ```bash
   python -c "from services.error_logging import get_latency_stats; print(get_latency_stats('run_agent_query'))"
   ```
   Typical `run_agent_query` latency: 5–30 seconds depending on tool calls and query complexity.

5. **Check data integrity** — Verify the Jira export file is valid:
   ```bash
   python -c "
   import json
   with open('data/jira_export.json') as f:
       data = json.load(f)
   print(f'{len(data)} tickets loaded OK')
   "
   ```
   Expected: 20 tickets loaded.

6. **Check Streamlit app health**:
   ```bash
   python scripts/health_monitor.py --local
   ```

### Common error patterns and resolutions

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| `DEEPSEEK_API_KEY not found` | Missing `.env` or HF secret | Create `.env` with key, or add secret in HF Space Settings |
| `Connection refused` on local | Streamlit not running | `streamlit run app.py` |
| Agent times out (30s+) | DeepSeek API slow or tool loop | Check API status at status.deepseek.com; restart with fresh query |
| `No output returned by the agent` | Empty LLM response | Check `logs/errors.jsonl` for tracebacks; try simpler query |
| `jira_export.json` not found | Data file missing | Restore from git: `git checkout data/jira_export.json` |
| HTTP 502/503 on HF Space | Space is sleeping or crashed | Visit Space page to wake it; check HF Space logs in Settings |
| Metrics show zeros | Data file corrupted or missing | Validate JSON: `python -m json.tool data/jira_export.json > /dev/null` |

### How to view recent errors

**From the command line:**
```bash
python -c "
from services.error_logging import get_recent_errors
import json
for e in get_recent_errors():
    print(json.dumps(e, indent=2))
"
```

**From the error log file directly:**
```bash
tail -20 logs/errors.jsonl | python -m json.tool --no-ensure-ascii
```

**From a running app (Python REPL):**
```python
from services.error_logging import get_recent_errors, get_latency_stats
errors = get_recent_errors(limit=10)
stats = get_latency_stats("run_agent_query")
```

### Rollback procedure

**Option 1: Git revert (recommended)**
```bash
cd ~/Documents/Pythonproject/Touseef_Project_Work/learning-ai-agents/ba-jira-agent/

# View recent commits
git log --oneline -10

# Revert to a known-good commit
git revert <bad-commit-hash>
git push origin main
```

**Option 2: Git reset (force rollback)**
```bash
# Hard reset to a known-good commit (destroys local changes)
git reset --hard <known-good-commit-hash>
git push --force origin main
```
⚠️ Use `--force` only as a last resort — it rewrites remote history.

**Option 3: Roll back specific files**
```bash
# Restore a file to a previous state
git checkout <known-good-commit-hash> -- path/to/file.py

# Example: restore agent.py
git checkout HEAD~1 -- agent.py
```

**Post-rollback verification:**
```bash
# Run tests
pytest tests/ -v

# Health check
python scripts/health_monitor.py --local

# Verify the app starts
streamlit run app.py --server.headless true &
sleep 5
python scripts/health_monitor.py --local
kill %1
```

### Known limitations

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| **Mock data only** — `data/jira_export.json` is static; no live Jira API integration | Tickets are fixed at 20; no real-time updates | Replace `tools.py` tool functions with Jira REST API calls for live data |
| **DeepSeek API dependency** — Agent requires internet access and a valid API key | Agent is unavailable if DeepSeek is down or key expires | Monitor DeepSeek status page; keep a backup API key |
| **Single-user agent** — No session isolation; concurrent users share the same agent instance | Responses may interleave under high concurrency | Deploy with multiple replicas; add session management |
| **No authentication** — App has no login; anyone with the URL can query the agent | Sensitive Jira data could be exposed | Add HF Space auth or OAuth proxy in front of the app |
| **Memory-less agent** — Each query is independent; no conversation history | Cannot ask follow-up questions contextually | Implement LangGraph checkpointing with a persistent store |
| **HF Space cold starts** — Space sleeps after inactivity (~48h on free tier) | First request after idle period takes 30–60 seconds to wake | Use a paid HF Space tier; set up a cron health check ping every 15 minutes |
| **Large responses truncated** — Trace view truncates at 2000 chars per message | Long tool outputs may be clipped in the UI | Expand trace view limit in `app.py`; use the CLI runner for full output |
| **No structured error codes** — Errors are free-text only | Hard to programmatically classify failures | Extend `log_error` to accept an `error_code` enum |
