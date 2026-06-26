"""
BA Jira Agent — Streamlit Web App.

LangChain ReAct agent wrapper with BA Assistant design system.
Provides a chat-style interface for querying a Jira backlog using
a DeepSeek-powered AI agent with 4 custom tools.
"""

import json
import sys
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from services.agent_service import get_all_tickets, get_metrics, run_agent_query
from services.error_logging import log_error

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BA Jira Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
CARD_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

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

* { font-family: var(--font-sans) !important; }

/* Override Streamlit defaults */
header[data-testid="stHeader"] { display: none !important; }
.stRadio div, .stCheckbox div, .stToggle div { background: var(--bg) !important; }
.stButton button:active { transform: scale(0.98) !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--bg-2) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
  font-weight: 700 !important;
  font-size: 1.25rem !important;
  color: var(--text) !important;
}

/* Brand card in sidebar */
.sidebar-brand {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1rem;
  margin-bottom: 1.25rem;
  text-align: center;
  box-shadow: var(--shadow);
}
.sidebar-brand .brand-logo {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}
.sidebar-brand .brand-name {
  font-weight: 700;
  font-size: 1.15rem;
  color: var(--text);
  margin: 0 0 0.25rem 0;
}
.sidebar-brand .brand-desc {
  font-size: 0.8rem;
  color: var(--muted-2);
  line-height: 1.4;
}

/* Hero card */
.hero-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 2.5rem 2rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow-lg);
  text-align: center;
}
.hero-eyebrow {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.5rem;
}
.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.03em;
}
.hero-subtitle {
  font-size: 1rem;
  color: var(--muted);
  max-width: 580px;
  margin: 0 auto 1rem auto;
  line-height: 1.55;
}
.hero-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}
.hero-chip-row span {
  background: var(--panel-soft);
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border);
}

/* Metric cards */
.metric-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1rem;
  text-align: center;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}
.metric-card:hover {
  box-shadow: var(--shadow-lg);
}
.metric-card .metric-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.15;
}
.metric-card .metric-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--muted-2);
  margin-top: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.metric-card .metric-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

/* Accent-colored metric values */
.metric-value.accent { color: var(--accent); }
.metric-value.amber  { color: var(--amber); }
.metric-value.red    { color: var(--red); }
.metric-value.blue   { color: var(--blue); }

/* Ticket table card */
.ticket-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
}
.ticket-card h3 {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text);
  margin: 0 0 0.75rem 0;
}

/* Results area */
.results-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
}
.results-card h3 {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text);
  margin: 0 0 0.75rem 0;
}

/* Query input styling */
.stTextArea textarea {
  border: 1px solid var(--border-strong) !important;
  border-radius: var(--radius-md) !important;
  font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(29,185,84,0.12) !important;
}

/* Submit button */
div.stButton > button {
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  padding: 0.6rem 1.75rem !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
div.stButton > button:hover {
  background: var(--accent-dark) !important;
}
div.stButton > button:active {
  transform: scale(0.98) !important;
}

/* Expander */
.streamlit-expanderHeader {
  font-weight: 600 !important;
  color: var(--text) !important;
}

/* Example query buttons in sidebar */
.example-btn button {
  width: 100% !important;
  text-align: left !important;
  font-size: 0.82rem !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  background: var(--bg) !important;
  color: var(--muted) !important;
  padding: 0.45rem 0.75rem !important;
  margin-bottom: 0.35rem !important;
  transition: all 0.2s ease !important;
}
.example-btn button:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: var(--bg-2) !important;
}

/* Footer */
.app-footer {
  text-align: center;
  color: var(--muted-2);
  font-size: 0.75rem;
  padding: 1.5rem 0 0.5rem 0;
  border-top: 1px solid var(--border);
  margin-top: 2rem;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .hero-card { padding: 1.5rem 1rem; }
  .hero-title { font-size: 1.6rem; }
  .hero-subtitle { font-size: 0.9rem; }
  .metric-card .metric-value { font-size: 1.5rem; }
}

/* DataFrame override */
[data-testid="stDataFrame"] { border: none !important; }
"""

st.markdown(f"<style>{CARD_CSS}</style>", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand card
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-logo">🤖</div>
          <div class="brand-name">BA Jira Agent</div>
          <div class="brand-desc">
            AI-powered backlog analysis.<br>
            LangChain ReAct agent with DeepSeek.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # About section
    with st.expander("ℹ️ About", expanded=False):
        st.markdown(
            """
            **BA Jira Agent** wraps a LangGraph ReAct agent
            in a Streamlit UI. The agent reasons about Jira
            backlogs using 4 custom tools:
            - `load_tickets` — full backlog listing
            - `filter_tickets` — filter by field/value
            - `search_tickets` — keyword search
            - `calculate_metrics` — sprint & backlog stats

            Built with LangChain, LangGraph, and
            DeepSeek Chat API.
            """
        )

    # Example queries
    st.markdown("### 💡 Example Queries")
    example_queries = [
        "Show me all open bugs in Sprint 24",
        "What's the total story points across all tickets?",
        "Search for anything related to performance",
        "Show me unassigned tickets",
        "Calculate sprint velocity for all sprints",
        "How many tickets are assigned to Priya?",
    ]
    for i, q in enumerate(example_queries):
        if st.button(q, key=f"example_{i}", use_container_width=True):
            st.session_state.query = q

# ── Main Area ─────────────────────────────────────────────────────────────────

# Hero card
st.markdown(
    """
    <div class="hero-card">
      <div class="hero-eyebrow">LANGCHAIN REACT AGENT</div>
      <h1 class="hero-title">BA Jira Agent</h1>
      <p class="hero-subtitle">
        AI agent that analyzes Jira backlogs — reasons, calls tools,
        and produces structured summaries.
      </p>
      <div class="hero-chip-row">
        <span>DeepSeek LLM</span>
        <span>4 Custom Tools</span>
        <span>ReAct Pattern</span>
        <span>LangGraph</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Metrics Dashboard ─────────────────────────────────────────────────────────
metrics = get_metrics()
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-icon">📋</div>
          <div class="metric-value">{metrics['total']}</div>
          <div class="metric-label">Total Tickets</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-icon">⚡</div>
          <div class="metric-value accent">{metrics['total_sp']}</div>
          <div class="metric-label">Total Story Points</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-icon">👤</div>
          <div class="metric-value amber">{metrics['unassigned']}</div>
          <div class="metric-label">Unassigned</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-icon">🐛</div>
          <div class="metric-value red">{metrics['open_bugs']}</div>
          <div class="metric-label">Open Bugs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Query Input ───────────────────────────────────────────────────────────────
st.markdown("### 🔍 Ask the Agent")

# Initialize session state for query
if "query" not in st.session_state:
    st.session_state.query = ""

query = st.text_area(
    "Describe what you want to know about the Jira backlog:",
    value=st.session_state.query,
    placeholder="e.g., Show me all critical bugs and their assignees",
    height=80,
    label_visibility="collapsed",
    key="query_input",
)

submit_col, clear_col = st.columns([1, 5])
with submit_col:
    submitted = st.button("🚀 Run Agent", use_container_width=True)
with clear_col:
    if st.button("Clear", use_container_width=True):
        st.session_state.query_response = None
        st.session_state.query_trace = None
        st.rerun()

# ── Execute Agent ─────────────────────────────────────────────────────────────
if submitted and query.strip():
    with st.spinner("🤔 Agent is reasoning... this may take 10–30 seconds"):
        try:
            result = run_agent_query(query.strip())
            st.session_state.query_response = result["answer"]
            st.session_state.query_trace = result["trace"]
        except Exception as exc:
            log_error("ui", f"Agent invocation failed: {exc}", exc_info=True)
            st.session_state.query_response = f"❌ An error occurred: {str(exc)}"
            st.session_state.query_trace = [{"role": "error", "content": str(exc)}]

# ── Results ───────────────────────────────────────────────────────────────────
if "query_response" in st.session_state and st.session_state.query_response:
    st.markdown('<div class="results-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Agent Response")
    st.markdown(st.session_state.query_response)
    st.markdown("</div>", unsafe_allow_html=True)

    # Agent trace expander
    if "query_trace" in st.session_state and st.session_state.query_trace:
        with st.expander("🧠 Agent Thought Process (ReAct Trace)", expanded=False):
            for i, msg in enumerate(st.session_state.query_trace):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                # Color-code by role
                role_colors = {
                    "human": "#2563EB",
                    "ai": "#1DB954",
                    "tool": "#FFA000",
                    "error": "#E53935",
                    "system": "#8A8A8A",
                }
                color = role_colors.get(role, "#8A8A8A")

                st.markdown(
                    f'<span style="color:{color};font-weight:600;">[{role.upper()}]</span>',
                    unsafe_allow_html=True,
                )

                # Truncate very long content in trace
                display_content = content
                if len(content) > 2000:
                    display_content = content[:2000] + "\n\n... (truncated)"

                st.code(display_content, language=None)

                # Show tool calls if present
                if "tool_calls" in msg and msg["tool_calls"]:
                    for tc in msg["tool_calls"]:
                        st.caption(f"🔧 Called tool: `{tc['name']}`")

                if i < len(st.session_state.query_trace) - 1:
                    st.markdown("---")

# ── Ticket Data Table ─────────────────────────────────────────────────────────
st.markdown('<div class="ticket-card">', unsafe_allow_html=True)
st.markdown("### 📊 Jira Backlog Tickets")

tickets = get_all_tickets()
if tickets:
    df = pd.DataFrame(tickets)
    # Reorder and select columns for display
    display_cols = [
        "key",
        "type",
        "priority",
        "status",
        "assignee",
        "story_points",
        "sprint",
        "summary",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    extra_cols = [c for c in df.columns if c not in available_cols and c != "labels" and c != "description"]
    display_df = df[available_cols + extra_cols].copy()

    # Replace None with "—" for display
    display_df = display_df.fillna("—")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "key": st.column_config.TextColumn("Key", width="small"),
            "type": st.column_config.TextColumn("Type", width="small"),
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "assignee": st.column_config.TextColumn("Assignee", width="small"),
            "story_points": st.column_config.NumberColumn("SP", width="small"),
            "sprint": st.column_config.TextColumn("Sprint", width="small"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
        },
    )
else:
    st.warning("No ticket data available. Check data/jira_export.json.")
st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="app-footer">
      BA Jira Agent · LangChain ReAct · DeepSeek ·
      Built {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
    </div>
    """,
    unsafe_allow_html=True,
)
