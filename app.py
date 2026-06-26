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
import streamlit.components.v1 as components

from services.agent_service import get_all_tickets, get_metrics, run_agent_query
from services.error_logging import log_error

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BA Jira Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
CARD_CSS = """
<style>
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
  --shadow: 0 1px 3px rgba(29, 185, 84, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
  --shadow-lg: 0 4px 12px rgba(29, 185, 84, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04);
  --radius-xl: 20px;
  --radius-lg: 14px;
  --radius-md: 10px;
  --radius-sm: 8px;
  --amber: #FFA000;
  --red: #E53935;
  --blue: #2563EB;
  --violet: #7C3AED;
  --font-sans: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

* { font-family: var(--font-sans) !important; }
html { scroll-behavior: smooth; }

.stApp { background: var(--bg); color: var(--text); }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1080px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--bg-2); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: var(--muted); }
[data-testid="stSidebar"] div.stButton > button {
  background: var(--bg) !important; border-color: var(--border) !important; color: var(--text) !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
  background: var(--panel-soft) !important; border-color: var(--accent) !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }
[data-testid="stSidebar"] .stButton { margin-bottom: 0.35rem; }
[data-testid="stSidebarContent"]::-webkit-scrollbar-track { background: var(--panel-soft); }
[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb { background: rgba(29,185,84,0.3); }

/* ── Sidebar brand card ── */
.sidebar-brand {
  border: 1px solid var(--border); border-radius: var(--radius-lg);
  background: var(--bg); padding: 1rem; margin: 0.35rem 0 1rem; box-shadow: var(--shadow);
}
.sidebar-brand p { color: var(--muted) !important; font-size: 0.86rem; line-height: 1.45; margin: 0; }

/* ── Input fields ── */
.stTextInput input, .stTextArea textarea {
  background: var(--bg) !important; border-color: var(--border) !important; color: var(--text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(29,185,84,0.12) !important;
}

/* ── Primary button ── */
button[kind="primary"] {
  border-radius: var(--radius-sm) !important;
  background: var(--accent) !important; border-color: var(--accent) !important; color: #FFFFFF !important;
}
button[kind="primary"]:hover { background: var(--accent-light) !important; }
button[kind="primary"]:active { transform: scale(0.98) !important; }

/* ── Universal text overrides ── */
h1, h2, h3, h4, h5, h6 { color: var(--text) !important; text-wrap: balance; }
p, li, label, span, div { color: var(--text) !important; text-wrap: pretty; }
[data-testid="stMarkdownContainer"] p { color: var(--muted) !important; }

/* ── Button hover states ── */
.stButton button {
  border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important;
  transition: all 0.2s !important; background: var(--bg) !important; color: var(--text) !important;
}
.stButton button:hover { border-color: var(--accent) !important; background: rgba(29,185,84,0.08) !important; }
.stButton button:active { transform: scale(0.98) !important; }

/* ── Radio / Checkbox / Toggle ── */
.stRadio div, .stCheckbox div, .stToggle div { background: var(--bg) !important; }
.stRadio [role="radio"][aria-checked="true"] div { background: var(--accent) !important; }

/* ── Hero card with gradient bottom border ── */
.hero-card {
  border: 1px solid var(--border); border-radius: var(--radius-xl);
  background: var(--bg); box-shadow: var(--shadow);
  overflow: hidden; position: relative; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
}
.hero-card::after {
  content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent-light), var(--violet));
}
.hero-eyebrow {
  color: #0d7a2e !important; font-size: 0.78rem; font-weight: 800;
  letter-spacing: 0.12em; margin-bottom: 0.5rem; text-transform: uppercase;
}
.hero-title {
  font-size: clamp(1.8rem, 4vw, 2.6rem); font-weight: 900;
  letter-spacing: -0.02em; line-height: 1.1; color: var(--text); margin-bottom: 0.4rem;
}
.hero-subtitle { color: var(--muted); font-size: 1.02rem; margin: 0; max-width: 760px; line-height: 1.55; }
.hero-chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
.hero-chip-row span {
  background: var(--panel-softer); border: 1px solid var(--border);
  border-radius: 999px; color: var(--muted) !important; font-size: 0.78rem; padding: 0.35rem 0.7rem;
}

/* ── Metric cards ── */
.metric-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 1rem;
  box-shadow: var(--shadow); text-align: center;
}
.metric-card .metric-value { font-size: 2rem; font-weight: 800; color: var(--text); line-height: 1.2; }
.metric-card .metric-label { font-size: 0.75rem; font-weight: 600; color: var(--muted-2); margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value.accent { color: var(--accent) !important; }
.metric-value.amber  { color: var(--amber) !important; }
.metric-value.red    { color: var(--red) !important; }

/* ── Results card ── */
.results-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
}

/* ── Ticket table card ── */
.ticket-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
}

/* ── Submit button ── */
div.stButton > button[kind="primary"] {
  background: var(--accent) !important; color: #fff !important;
  border: none !important; border-radius: var(--radius-md) !important;
  font-weight: 600 !important; font-size: 0.95rem !important;
  padding: 0.6rem 1.75rem !important; width: 100% !important;
}
div.stButton > button[kind="primary"]:hover { background: var(--accent-dark) !important; }

/* ── Footer ── */
.app-footer { text-align: center; color: var(--muted-2); font-size: 0.75rem; padding: 1.5rem 0 0.5rem 0; border-top: 1px solid var(--border); margin-top: 2rem; }

/* ═══════════════════════════════════════════════════════════════════
   MOBILE OVERLAY SIDEBAR (768px breakpoint)
   ═══════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  /* ── Overlay sidebar drawer ── */
  [data-testid="stSidebar"] {
    position: fixed !important; top: 0; left: 0; bottom: 0;
    width: 85vw !important; max-width: 320px !important; min-width: 280px !important;
    z-index: 9999 !important;
    transform: translateX(-100%) !important;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  [data-testid="stSidebar"][aria-expanded="true"] {
    transform: translateX(0) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.3);
  }

  /* ── Scrim backdrop ── */
  .stApp::after {
    content: ""; display: block; position: fixed; inset: 0;
    background: rgba(0,0,0,0.5); z-index: 9998;
    opacity: 0; visibility: hidden; pointer-events: none;
    transition: opacity 0.3s ease;
  }
  .stApp:has([data-testid="stSidebar"][aria-expanded="true"])::after {
    opacity: 1; visibility: visible; pointer-events: auto;
  }

  /* ── FAB — sidebar toggle button ── */
  button[data-testid="stExpandSidebarButton"] {
    position: fixed !important; top: 0.75rem !important; left: 0.75rem !important;
    z-index: 10000 !important;
    width: 44px !important; height: 44px !important;
    min-height: 44px !important; min-width: 44px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12) !important;
  }
  button[data-testid="stExpandSidebarButton"] svg { width: 22px !important; height: 22px !important; }

  /* ── Main content ── */
  [data-testid="stAppViewContainer"] .block-container {
  padding: 1.25rem 1.25rem 4rem 1.25rem !important; margin-left: 0 !important; max-width: 100% !important;
  }
  [data-testid="stAppViewContainer"] > section { padding-top: 0.5rem !important; }

  /* ── Stack columns ── */
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex: 0 0 100% !important; width: 100% !important;
  }

  /* ── 14px font floor ── */
  [data-testid="stAppViewContainer"] .block-container p,
  [data-testid="stAppViewContainer"] .block-container span:not(.hero-chip-row span),
  [data-testid="stAppViewContainer"] .block-container label,
  [data-testid="stAppViewContainer"] .block-container small {
    font-size: 0.875rem !important; line-height: 1.4 !important;
  }

  /* ── 44px tap targets ── */
  [data-testid="stAppViewContainer"] .block-container a,
  [data-testid="stAppViewContainer"] .block-container button,
  [data-testid="stAppViewContainer"] .block-container [role="button"],
  [data-testid="stAppViewContainer"] .block-container select,
  [data-testid="stAppViewContainer"] .block-container input {
    min-height: 44px !important; min-width: 44px !important;
  }

  .hero-card { padding: 1.2rem 1rem; }
  .hero-title { font-size: 1.5rem !important; }
  .hero-subtitle { font-size: 0.88rem !important; }
  .hero-chip-row span { font-size: 0.7rem !important; padding: 0.25rem 0.5rem; white-space: nowrap; }
}
</style>
"""

st.markdown(CARD_CSS, unsafe_allow_html=True)

# ── Mobile sidebar tap-to-close JS ────────────────────────────────────────────

components.html("""
<script>
(function() {
  // Auto-collapse sidebar on mobile load (poll until button exists)
  if (window.innerWidth < 768) {
    var attempts = 0;
    var autoCollapse = setInterval(function() {
      var collapseBtn = parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button');
      if (collapseBtn) {
        collapseBtn.click();
        clearInterval(autoCollapse);
      }
      if (++attempts > 30) clearInterval(autoCollapse);
    }, 200);
  }

  function setupScrimClose() {
    const app = parent.document.querySelector('.stApp') || parent.document.querySelector('[data-testid="stAppViewContainer"]');
    const sidebar = parent.document.querySelector('[data-testid="stSidebar"]');
    if (!app || !sidebar) { setTimeout(setupScrimClose, 500); return; }
    app.addEventListener('click', function(e) {
      if (sidebar.getAttribute('aria-expanded') !== 'true') return;
      const r = sidebar.getBoundingClientRect();
      if (e.clientX > r.right || e.clientX < r.left) {
        const btn = sidebar.querySelector('[data-testid="stSidebarCollapseButton"] button');
        if (btn) btn.click();
      }
    }, { capture: true });
  }

  // Fix FAB button size — Streamlit emotion CSS sets 0x0 with !important
  function fixFab() {
    const fab = parent.document.querySelector('[data-testid="stExpandSidebarButton"]');
    if (fab) {
      fab.style.setProperty('width', '44px', 'important');
      fab.style.setProperty('height', '44px', 'important');
      fab.style.setProperty('min-width', '44px', 'important');
      fab.style.setProperty('min-height', '44px', 'important');
    }
  }

  setTimeout(setupScrimClose, 1000);
  setTimeout(fixFab, 800);
  if (parent.document.body) {
    const observer = new MutationObserver(function() {
      clearTimeout(window._scrimTimer);
      window._scrimTimer = setTimeout(setupScrimClose, 500);
      fixFab();
    });
    observer.observe(parent.document.body, { childList: true, subtree: true });
  }
})();
</script>
""", height=0)

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
        if st.button(q, key=f"example_{i}", width="stretch"):
            st.session_state.query = q
            st.session_state[f"query_input"] = q

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
        <span>ReAct Agent</span>
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
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

query = st.text_area(
    "Describe what you want to know about the Jira backlog:",
    placeholder="e.g., Show me all critical bugs and their assignees",
    height=80,
    label_visibility="collapsed",
    key="query_input",
)

submit_col, clear_col = st.columns([1, 1])
with submit_col:
    submitted = st.button("🚀 Run Agent", width="stretch", type="primary")
with clear_col:
    if st.button("🗑️ Clear", width="stretch"):
        st.session_state.query_response = None
        st.session_state.query_trace = None
        st.rerun()

# ── Execute Agent ─────────────────────────────────────────────────────────────
if submitted and st.session_state.get("query_input", "").strip():

    with st.spinner("🤔 Agent is reasoning... this may take 10–30 seconds"):
        try:
            result = run_agent_query(st.session_state.query_input.strip())
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
        width="stretch",
        hide_index=True,
        height=550,
        column_config={
            "key": st.column_config.TextColumn("Key", width="small"),
            "type": st.column_config.TextColumn("Type", width="small"),
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "assignee": st.column_config.TextColumn("Assignee", width="medium"),
            "story_points": st.column_config.NumberColumn("SP", width="small"),
            "sprint": st.column_config.TextColumn("Sprint", width="medium"),
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
