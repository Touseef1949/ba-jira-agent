# BA Jira Agent — Streamlit Web App Build Spec

## Project
Wrap the existing LangChain ReAct agent (ba-jira-agent) in a Streamlit web UI matching the BA Assistant design system. Deploy to HuggingFace Spaces.

## Location
~/Documents/Pythonproject/Touseef_Project_Work/learning-ai-agents/ba-jira-agent/

## Existing Files (DO NOT MODIFY)
- tools.py — 4 @tool functions (load_tickets, filter_tickets, search_tickets, calculate_metrics)
- agent.py — LangGraph create_react_agent + DeepSeek + run_agent(query)
- data/jira_export.json — 20 mock Jira tickets
- .env — DEEPSEEK_API_KEY

## New Files to Create
1. app.py — Streamlit web app
2. core/config.py — Config constants and safe_secret helper
3. services/agent_service.py — Agent invocation wrapper (separates logic from UI)
4. services/error_logging.py — Structured JSONL error logging
5. tests/test_tools.py — Unit tests for 4 tools
6. tests/test_agent_service.py — Integration test for agent service
7. tests/test_app.py — Streamlit AppTest smoke test
8. tests/conftest.py — Shared fixtures
9. requirements.txt — Updated with streamlit + test deps
10. Dockerfile — HF Spaces deployment
11. .streamlit/config.toml — Streamlit theme config
12. RUNBOOK.md — Ops runbook

## UI Design (MUST MATCH BA Assistant)

### CSS Variables (exact same as BA Assistant)
```css
:root {
  --accent: #1DB954;
  --accent-dark: #169a45;
  --accent-light: #1ED760;
  --text: #1A1A1A;
  --muted: #4A4A4A;
  --muted-2: #8A8A8A;
  --border: #E8E8E8;
  --border-strong: #D0D0D0;
  --bg: #FFFFFF;
  --bg-2: #FAFAFA;
  --panel-soft: #F5F5F5;
  --panel-softer: #F0F0F0;
  --shadow: 0 1px 3px rgba(29,185,84,0.04), 0 1px 2px rgba(0,0,0,0.03);
  --shadow-lg: 0 4px 12px rgba(29,185,84,0.06), 0 2px 4px rgba(0,0,0,0.04);
  --radius-xl: 20px;
  --radius-lg: 14px;
  --radius-md: 10px;
  --radius-sm: 8px;
  --amber: #FFA000;
  --red: #E53935;
  --blue: #2563EB;
  --violet: #7C3AED;
  --font-sans: 'Outfit', sans-serif;
}
```

### Font
```css
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: var(--font-sans) !important; }
```

### Must-Override Streamlit Defaults
```css
header[data-testid="stHeader"] { display: none !important; }
.stRadio div, .stCheckbox div, .stToggle div { background: var(--bg) !important; }
.stButton button:active { transform: scale(0.98) !important; }
```

### Layout
- page_title="BA Jira Agent", page_icon="🤖", layout="wide", initial_sidebar_state="expanded"
- Sidebar: Brand card (logo + "BA Jira Agent" + description), "About" section, example queries
- Main area: Hero card with eyebrow, title, subtitle, workflow chips
- Query input: st.text_area for natural language query
- Submit button (accent green)
- Results area: Agent answer rendered as markdown
- Agent thought process: Expander showing ReAct Thought/Action/Observation trace
- Ticket data table: st.dataframe showing the mock Jira tickets
- Metrics dashboard: 4 metric cards (Total Tickets, Total SP, Unassigned, Open Bugs)

### Hero Card Pattern (same as BA Assistant)
```html
<div class="hero-card">
  <div class="hero-eyebrow">LANGCHAIN REACT AGENT</div>
  <h1 class="hero-title">BA Jira Agent</h1>
  <p class="hero-subtitle">AI agent that analyzes Jira backlogs — reasons, calls tools, and produces structured summaries.</p>
  <div class="hero-chip-row">
    <span>DeepSeek LLM</span>
    <span>4 Custom Tools</span>
    <span>ReAct Pattern</span>
    <span>LangGraph</span>
  </div>
</div>
```

## app.py Architecture
```python
# Imports
import streamlit as st
from services.agent_service import run_agent_query, get_agent_trace
from tools import load_tickets, filter_tickets, search_tickets, calculate_metrics
import json

# Page config
st.set_page_config(page_title="BA Jira Agent", page_icon="🤖", layout="wide")

# CSS (inline, same as BA Assistant)
st.markdown(CARD_CSS, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Brand card
    # About section
    # Example queries (clickable buttons)

# Main area
# Hero card
# Query input (text_area)
# Submit button
# Results (markdown)
# Agent trace (expander)
# Ticket data table
# Metric cards

# Error handling: try/except around agent invocation, show friendly error
```

## services/agent_service.py
```python
from agent import run_agent, agent
from tools import load_tickets, filter_tickets, search_tickets, calculate_metrics
import json

def run_agent_query(query: str) -> dict:
    """Run the agent and return answer + trace."""
    # Invoke agent
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    # Extract final answer
    messages = result.get("messages", [])
    answer = messages[-1].content if messages else "No output"
    # Extract all messages as trace
    trace = []
    for msg in messages:
        trace.append({
            "role": getattr(msg, "type", "unknown"),
            "content": msg.content if hasattr(msg, "content") else str(msg),
        })
    return {"answer": answer, "trace": trace}

def get_all_tickets() -> list:
    """Load all tickets for display."""
    with open("data/jira_export.json") as f:
        return json.load(f)

def get_metrics() -> dict:
    """Calculate metrics for dashboard cards."""
    tickets = get_all_tickets()
    return {
        "total": len(tickets),
        "total_sp": sum(t.get("story_points", 0) for t in tickets),
        "unassigned": sum(1 for t in tickets if not t.get("assignee")),
        "open_bugs": sum(1 for t in tickets if t.get("type") == "Bug" and t.get("status") == "Open"),
    }
```

## Test Requirements (production-grade)

### tests/test_tools.py (unit tests — at least 8)
- test_load_tickets_returns_string
- test_load_tickets_has_all_20
- test_filter_tickets_by_status
- test_filter_tickets_by_priority
- test_filter_tickets_unassigned
- test_search_tickets_finds_match
- test_search_tickets_no_match
- test_calculate_metrics_summary
- test_calculate_metrics_all
- test_calculate_metrics_invalid_type

### tests/test_agent_service.py (integration — at least 3)
- test_get_all_tickets
- test_get_metrics
- test_run_agent_query_returns_answer (mock the agent.invoke)

### tests/test_app.py (AppTest smoke — at least 3)
- test_app_renders_title
- test_app_renders_hero
- test_app_renders_query_input

## requirements.txt
```
streamlit>=1.40.0
langchain>=0.3.0
langchain-openai>=0.2.0
langgraph>=0.2.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-cov>=5.0.0
```

## Dockerfile (HF Spaces)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8503
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]
```

## .streamlit/config.toml
```toml
[theme]
base = "light"
primaryColor = "#1DB954"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#FAFAFA"
textColor = "#1A1A1A"
font = "sans serif"
```

## IMPORTANT NOTES
- Use /usr/local/bin/python3 (NOT anaconda)
- DeepSeek API key loaded from .env via dotenv (NOT st.secrets for local dev)
- For HF Spaces: key goes in Spaces Secrets as DEEPSEEK_API_KEY
- Agent invocation can take 10-30 seconds — show a spinner
- The ReAct trace should be in an expander (not shown by default)
- Mobile responsive (max-width: 640px media query)
- No dark mode — light theme only (matching BA Assistant)
- All CSS inline in app.py (same pattern as BA Assistant)