"""Production Streamlit interface for the BA Jira Agent."""

from datetime import datetime, timezone
from html import escape

import pandas as pd
import streamlit as st

from core.examples import GUIDED_EXAMPLES, QUICK_TOOL_EXAMPLES
from core.skills import SkillRegistry
from core.trace_summary import summarize_tool_calls
from services import auth_service
from services.agent_service import get_all_tickets, get_metrics, run_agent_query
from services.error_logging import log_error


skill_registry = SkillRegistry()


def set_query_prompt(prompt: str) -> None:
    """Populate the analysis composer from a recommended prompt."""
    st.session_state.query_input = prompt


def clear_query() -> None:
    """Reset the composer and the latest analysis."""
    st.session_state.query_input = ""
    st.session_state.query_response = None
    st.session_state.query_trace = None
    st.session_state.last_query = ""


def render_metric(label: str, value: int | float, detail: str, tone: str = "") -> None:
    """Render a compact product metric card."""
    st.markdown(
        f"""
        <div class="metric-card {tone}">
          <div class="metric-label">{escape(label)}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-detail">{escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_execution_details(trace: list[dict]) -> None:
    """Show an auditable, secondary view of agent activity."""
    tool_calls = summarize_tool_calls(trace)
    if tool_calls:
        labels = []
        for call in tool_calls:
            label = call["name"]
            if call["skill_name"]:
                label += f" · {call['skill_name']}"
            labels.append(f"`{label}`")
        st.caption("Execution path")
        st.markdown(" → ".join(labels))

    with st.expander("View execution details", expanded=False):
        st.caption("Tool activity and intermediate messages used to produce this analysis.")
        for index, message in enumerate(trace):
            role = str(message.get("role", "unknown")).replace("_", " ").title()
            content = str(message.get("content", ""))
            if len(content) > 2000:
                content = content[:2000] + "\n\n… output truncated"
            st.markdown(f"**{role}**")
            st.code(content, language=None)
            for tool_call in message.get("tool_calls", []) or []:
                st.caption(f"Tool called: `{tool_call.get('name', 'unknown')}`")
            if index < len(trace) - 1:
                st.divider()


st.set_page_config(
    page_title="BA Jira Agent",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20,400,0,0&display=swap');

:root {
  --accent: #0C66E4;
  --accent-hover: #0055CC;
  --success: #1F845A;
  --warning: #B65C02;
  --danger: #C9372C;
  --ink: #172B4D;
  --muted: #626F86;
  --subtle: #8590A2;
  --border: #DFE1E6;
  --surface: #FFFFFF;
  --canvas: #F7F8FA;
  --surface-subtle: #F1F2F4;
  --shadow: 0 1px 2px rgba(9,30,66,.08), 0 1px 3px rgba(9,30,66,.06);
  --shadow-raised: 0 8px 24px rgba(9,30,66,.10);
  --radius: 12px;
  --font: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

* { font-family: var(--font) !important; }
[data-testid="stIconMaterial"],
[data-testid="stIconMaterial"] *,
.material-symbols-rounded {
  font-family: "Material Symbols Rounded" !important;
  font-weight: normal !important;
  font-style: normal !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  white-space: nowrap !important;
  word-wrap: normal !important;
  direction: ltr !important;
  -webkit-font-feature-settings: "liga" !important;
  -webkit-font-smoothing: antialiased !important;
  font-feature-settings: "liga" !important;
}
html { scroll-behavior: smooth; }
.stApp { background: var(--canvas); color: var(--ink); }
header[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
.block-container { max-width: 1280px !important; padding: 1.35rem 2rem 2.5rem !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--border); }
[data-testid="stSidebarContent"] { padding-top: .75rem; }
[data-testid="stSidebar"] hr { border-color: var(--border); }
.brand-lockup { display: flex; align-items: center; gap: .75rem; margin: .25rem 0 1.2rem; }
.brand-mark {
  display: grid; place-items: center; width: 38px; height: 38px; border-radius: 10px;
  background: var(--accent); color: white !important; font-size: .78rem; font-weight: 700;
  letter-spacing: .04em;
}
.brand-name { color: var(--ink) !important; font-size: 1rem; font-weight: 700; line-height: 1.1; }
.brand-meta { color: var(--muted) !important; font-size: .75rem; margin-top: .2rem; }
.sidebar-label { color: var(--subtle) !important; font-size: .68rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.source-card {
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface-subtle);
  padding: .75rem .85rem; margin: .4rem 0 .8rem;
}
.source-card strong { color: var(--ink) !important; font-size: .86rem; }
.source-card span { color: var(--muted) !important; font-size: .76rem; }
.status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--success); margin-right: .4rem; }

/* Header */
.workspace-header {
  display: flex; justify-content: space-between; align-items: center; gap: 2rem;
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  padding: 1.35rem 1.55rem; box-shadow: var(--shadow); margin-bottom: 1.15rem;
}
.workspace-kicker { color: var(--accent) !important; font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.workspace-title { color: var(--ink) !important; font-size: 1.65rem; font-weight: 700; line-height: 1.2; margin: .3rem 0; }
.workspace-subtitle { color: var(--muted) !important; font-size: .92rem; margin: 0; }
.header-status {
  display: inline-flex; align-items: center; white-space: nowrap; color: var(--ink) !important;
  background: #E9F2FF; border: 1px solid #CCE0FF; border-radius: 999px;
  padding: .45rem .75rem; font-size: .78rem; font-weight: 600;
}

/* Metrics */
.metric-card {
  min-height: 118px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1rem 1.05rem; box-shadow: var(--shadow);
  border-top: 3px solid #B3B9C4;
}
.metric-card.accent { border-top-color: var(--accent); }
.metric-card.warning { border-top-color: #E2B203; }
.metric-card.danger { border-top-color: var(--danger); }
.metric-label { color: var(--muted) !important; font-size: .72rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
.metric-value { color: var(--ink) !important; font-size: 1.85rem; font-weight: 700; line-height: 1.15; margin: .35rem 0 .2rem; }
.metric-detail { color: var(--subtle) !important; font-size: .75rem; }

/* Streamlit surfaces */
[data-testid="stTabs"] [role="tablist"] { gap: .35rem; border-bottom: 1px solid var(--border); }
[data-testid="stTabs"] [role="tab"] { color: var(--muted) !important; font-weight: 600 !important; padding: .7rem 1rem !important; }
[data-testid="stTabs"] [role="tab"] p { color: inherit !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--accent) !important; }
[data-testid="stTabs"] [role="tab"] .react-aria-SelectionIndicator { background: var(--accent) !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface); border-color: var(--border) !important; border-radius: var(--radius) !important;
  box-shadow: var(--shadow);
}
.stTextArea textarea, .stTextInput input, [data-baseweb="select"] > div {
  background: var(--surface) !important; border-color: var(--border) !important; color: var(--ink) !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(12,102,228,.13) !important;
}
.stButton button {
  min-height: 40px; border: 1px solid var(--border) !important; border-radius: 8px !important;
  background: var(--surface) !important; color: var(--ink) !important; font-weight: 600 !important;
  transition: background .15s, border-color .15s, transform .15s;
}
.stButton button:hover { background: #F0F6FF !important; border-color: var(--accent) !important; color: var(--accent) !important; }
.stButton button:active { transform: scale(.985); }
.stButton button[kind="primary"] { background: var(--accent) !important; border-color: var(--accent) !important; color: white !important; }
.stButton button[kind="primary"]:hover { background: var(--accent-hover) !important; color: white !important; }
a, a:visited { color: var(--accent); }
[data-testid="stToggle"] [data-checked="true"],
[data-testid="stCheckbox"] [data-checked="true"] { background-color: var(--accent) !important; }

/* Assistant */
.section-kicker { color: var(--accent) !important; font-size: .68rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.section-title { color: var(--ink) !important; font-size: 1.35rem; font-weight: 700; margin: .25rem 0 .3rem; }
.section-copy { color: var(--muted) !important; font-size: .88rem; margin: 0 0 1rem; }
.empty-state {
  text-align: center; background: linear-gradient(180deg,#FFFFFF 0%,#F8FAFC 100%);
  border: 1px dashed #B3B9C4; border-radius: var(--radius); padding: 2.5rem 1.5rem; margin-top: 1rem;
}
.empty-state strong { display: block; color: var(--ink) !important; font-size: 1rem; margin-bottom: .35rem; }
.empty-state span { color: var(--muted) !important; font-size: .84rem; }
.request-card {
  background: #E9F2FF; border: 1px solid #CCE0FF; border-radius: 10px;
  padding: .85rem 1rem; color: var(--ink) !important; font-size: .88rem; margin: .9rem 0;
}
.response-header { display: flex; align-items: center; justify-content: space-between; margin: .2rem 0 .75rem; }
.response-header strong { color: var(--ink) !important; font-size: 1rem; }
.response-state { color: var(--success) !important; font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
.workflow-card {
  background: var(--surface-subtle); border: 1px solid var(--border); border-radius: 10px;
  padding: .85rem .9rem; margin: .55rem 0 .75rem;
}
.workflow-card strong { color: var(--ink) !important; font-size: .87rem; }
.workflow-card p { color: var(--muted) !important; font-size: .78rem; line-height: 1.45; margin: .3rem 0 0; }
.system-row { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: .48rem 0; font-size: .78rem; }
.system-row:last-child { border-bottom: 0; }
.system-row span { color: var(--muted) !important; }
.system-row strong { color: var(--ink) !important; }

/* Backlog */
.table-summary { color: var(--muted) !important; font-size: .8rem; margin: .25rem 0 .75rem; }
.app-footer { color: var(--subtle) !important; text-align: center; font-size: .72rem; padding: 1.75rem 0 .2rem; }

@media (max-width: 768px) {
  .block-container { padding: 1rem 1rem 3rem !important; }
  .workspace-header { align-items: flex-start; flex-direction: column; gap: .8rem; }
  .workspace-title { font-size: 1.4rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
  .metric-card { min-height: 100px; }
  .stButton button, input, textarea, select { min-height: 44px !important; }
}
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)


# Session state
for key, default in (
    ("jira_config", None),
    ("jira_connection_user", ""),
    ("query_input", ""),
    ("query_response", None),
    ("query_trace", None),
    ("last_query", ""),
):
    if key not in st.session_state:
        st.session_state[key] = default


# Sidebar application shell
st.sidebar.markdown(
    """
    <div class="brand-lockup">
      <div class="brand-mark">BA</div>
      <div><div class="brand-name">BA Jira Agent</div><div class="brand-meta">Delivery intelligence</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
st.sidebar.markdown("**Product delivery**  \nSprint planning & backlog operations")

with st.sidebar.expander("Data source", expanded=True):
    use_live_jira = st.toggle(
        "Use live Jira",
        value=False,
        key="use_live_jira",
        help="Turn this off to work with the bundled demonstration backlog.",
    )

    if use_live_jira:
        jira_url = st.text_input(
            "Jira URL",
            placeholder="https://your-domain.atlassian.net",
            key="jira_url",
        )
        jira_email = st.text_input("Email", placeholder="you@company.com", key="jira_email")
        jira_pat = st.text_input(
            "API token",
            type="password",
            placeholder="Your Jira API token",
            key="jira_pat",
        )
        if st.button("Test connection", key="test_jira_connection", width="stretch"):
            result = auth_service.validate_jira_connection(jira_url, jira_pat, jira_email)
            if result.get("connected"):
                normalized_url = jira_url.strip()
                if normalized_url and not normalized_url.startswith(("http://", "https://")):
                    normalized_url = f"https://{normalized_url}"
                st.session_state.jira_config = {
                    "jira_url": normalized_url.rstrip("/"),
                    "email": jira_email.strip(),
                    "pat": jira_pat,
                }
                st.session_state.jira_connection_user = result.get("user", "Jira user")
                st.success(f"Connected as {st.session_state.jira_connection_user}")
            else:
                st.session_state.jira_config = None
                st.session_state.jira_connection_user = ""
                st.error(result.get("error", "Connection failed."))

        current_user = st.session_state.get("jira_connection_user", "")
        if st.session_state.get("jira_config") and current_user:
            st.caption(
                f"Signed in as {current_user} · "
                f"{auth_service.mask_pat(st.session_state.jira_config.get('pat', ''))}"
            )
        else:
            st.caption("Enter Jira Cloud credentials to enable live analysis.")
    else:
        st.caption("Safe demo mode with the bundled Jira export.")

active_jira_config = st.session_state.get("jira_config") if use_live_jira else None
data_source = "jira" if use_live_jira and active_jira_config else "mock"
source_label = "Live Jira" if data_source == "jira" else "Demo workspace"

st.sidebar.markdown(
    f"""
    <div class="source-card">
      <strong><span class="status-dot"></span>{source_label}</strong><br>
      <span>{'Connected and ready' if data_source == 'jira' else 'Local sample data · read only'}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

_skills = skill_registry.list_skills()
with st.sidebar.expander(f"Agent capabilities · {len(_skills)}", expanded=False):
    for skill in _skills:
        display_name = skill.name.replace("-", " ").title()
        st.markdown(f"**{display_name}**  ")
        st.caption(f"{skill.command} · {skill.description}")

st.sidebar.divider()
st.sidebar.caption("DeepSeek · LangChain · Auditable tool execution")


# Workspace header and KPIs
st.markdown(
    f"""
    <div class="workspace-header">
      <div>
        <div class="workspace-kicker">Delivery intelligence</div>
        <div class="workspace-title">Plan with evidence, not assumptions</div>
        <p class="workspace-subtitle">Ask questions across backlog health, ownership, sprint risk, and delivery capacity.</p>
      </div>
      <div class="header-status"><span class="status-dot"></span>{source_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

metrics = get_metrics(data_source=data_source, jira_config=active_jira_config)
total = int(metrics.get("total", 0) or 0)
total_sp = int(metrics.get("total_sp", 0) or 0)
unassigned = int(metrics.get("unassigned", 0) or 0)
open_bugs = int(metrics.get("open_bugs", 0) or 0)
ownership_rate = round(((total - unassigned) / total) * 100) if total else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric("Backlog items", total, "Tickets in the active data source")
with m2:
    render_metric("Story points", total_sp, "Estimated delivery scope", "accent")
with m3:
    render_metric("Unassigned", unassigned, f"{ownership_rate}% currently has an owner", "warning")
with m4:
    render_metric("Open bugs", open_bugs, "Defects requiring attention", "danger")

st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)
assistant_tab, backlog_tab = st.tabs(["Assistant", "Backlog explorer"])


with assistant_tab:
    analysis_col, rail_col = st.columns([2.15, 1], gap="large")

    with analysis_col:
        with st.container(border=True):
            st.markdown('<div class="section-kicker">AI analysis</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">What do you need to know?</div>', unsafe_allow_html=True)
            st.markdown(
                '<p class="section-copy">Describe the decision you are making. The agent will select the appropriate workflow and inspect Jira data before answering.</p>',
                unsafe_allow_html=True,
            )
            st.text_area(
                "Ask about your backlog",
                placeholder="Example: Where is Sprint 24 most likely to slip, and what should we do today?",
                height=125,
                label_visibility="collapsed",
                key="query_input",
            )
            run_col, clear_col = st.columns([2, 1])
            with run_col:
                submitted = st.button(
                    "Run analysis",
                    width="stretch",
                    type="primary",
                    key="run_agent",
                )
            with clear_col:
                st.button(
                    "Clear",
                    width="stretch",
                    key="clear_query",
                    on_click=clear_query,
                )
            st.caption("Responses are grounded in the selected Jira source. Review important decisions against the underlying tickets.")

        if submitted and st.session_state.query_input.strip():
            original_query = st.session_state.query_input.strip()
            with st.spinner("Reviewing backlog data and preparing the analysis…"):
                try:
                    query_to_run = skill_registry.expand_slash_command(original_query)
                    result = run_agent_query(
                        query_to_run,
                        data_source=data_source,
                        jira_config=active_jira_config,
                    )
                    st.session_state.last_query = original_query
                    st.session_state.query_response = result["answer"]
                    st.session_state.query_trace = result["trace"]
                except Exception as exc:
                    log_error("ui", f"Agent invocation failed: {exc}", exc_info=True)
                    st.session_state.last_query = original_query
                    st.session_state.query_response = f"Analysis could not be completed: {exc}"
                    st.session_state.query_trace = [{"role": "error", "content": str(exc)}]

        if st.session_state.query_response:
            if st.session_state.last_query:
                st.markdown(
                    f'<div class="request-card"><strong>Request</strong><br>{escape(st.session_state.last_query)}</div>',
                    unsafe_allow_html=True,
                )
            with st.container(border=True):
                st.markdown(
                    '<div class="response-header"><strong>Analysis</strong><span class="response-state">Complete</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(st.session_state.query_response)
                if st.session_state.query_trace:
                    st.divider()
                    render_execution_details(st.session_state.query_trace)
        else:
            st.markdown(
                """
                <div class="empty-state">
                  <strong>Your analysis will appear here</strong>
                  <span>Start with a question or choose a recommended workflow from the panel.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with rail_col:
        with st.container(border=True):
            st.markdown('<div class="section-kicker">Recommended</div>', unsafe_allow_html=True)
            st.markdown("#### Start with a workflow")
            selected_index = st.selectbox(
                "Workflow",
                options=range(len(GUIDED_EXAMPLES)),
                format_func=lambda index: GUIDED_EXAMPLES[index].title,
                key="guided_workflow_select",
                label_visibility="collapsed",
            )
            selected_example = GUIDED_EXAMPLES[selected_index]
            st.markdown(
                f"""
                <div class="workflow-card">
                  <strong>{escape(selected_example.title)}</strong>
                  <p>{escape(selected_example.outcome)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                "Use this workflow",
                key="guided_example_load",
                width="stretch",
                on_click=set_query_prompt,
                args=(selected_example.prompt,),
            )

            st.markdown("##### Quick questions")
            for index, prompt in enumerate(QUICK_TOOL_EXAMPLES[:3]):
                st.button(
                    prompt,
                    key=f"quick_example_{index}",
                    width="stretch",
                    on_click=set_query_prompt,
                    args=(prompt,),
                )

        with st.container(border=True):
            st.markdown('<div class="section-kicker">Workspace status</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="system-row"><span>Data source</span><strong>{source_label}</strong></div>
                <div class="system-row"><span>Backlog items</span><strong>{total}</strong></div>
                <div class="system-row"><span>Available workflows</span><strong>{len(_skills)}</strong></div>
                <div class="system-row"><span>Execution</span><strong>Auditable</strong></div>
                """,
                unsafe_allow_html=True,
            )


with backlog_tab:
    tickets = get_all_tickets(data_source=data_source, jira_config=active_jira_config)
    with st.container(border=True):
        st.markdown('<div class="section-kicker">Source of truth</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Backlog explorer</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-copy">Search, filter, inspect, and export the Jira records used by the assistant.</p>',
            unsafe_allow_html=True,
        )

        if tickets:
            df = pd.DataFrame(tickets)
            search_col, status_col, priority_col = st.columns([2, 1, 1])
            with search_col:
                search_term = st.text_input(
                    "Search",
                    placeholder="Search key, summary, assignee, or description",
                    key="backlog_search",
                )
            with status_col:
                status_options = ["All"] + sorted(
                    value for value in df.get("status", pd.Series(dtype=str)).dropna().astype(str).unique()
                )
                selected_status = st.selectbox("Status", status_options, key="backlog_status")
            with priority_col:
                priority_options = ["All"] + sorted(
                    value for value in df.get("priority", pd.Series(dtype=str)).dropna().astype(str).unique()
                )
                selected_priority = st.selectbox("Priority", priority_options, key="backlog_priority")

            filtered_df = df.copy()
            if search_term.strip():
                searchable_columns = [
                    column
                    for column in ("key", "summary", "assignee", "description")
                    if column in filtered_df.columns
                ]
                mask = pd.Series(False, index=filtered_df.index)
                for column in searchable_columns:
                    mask |= filtered_df[column].fillna("").astype(str).str.contains(
                        search_term.strip(), case=False, regex=False
                    )
                filtered_df = filtered_df[mask]
            if selected_status != "All" and "status" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["status"].astype(str) == selected_status]
            if selected_priority != "All" and "priority" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["priority"].astype(str) == selected_priority]

            display_columns = [
                "key",
                "type",
                "priority",
                "status",
                "assignee",
                "story_points",
                "sprint",
                "summary",
            ]
            available_columns = [column for column in display_columns if column in filtered_df.columns]
            display_df = filtered_df[available_columns].copy().fillna("—")
            st.markdown(
                f'<div class="table-summary">Showing {len(display_df)} of {len(df)} tickets</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
                height=500,
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
            st.download_button(
                "Export filtered CSV",
                data=display_df.to_csv(index=False).encode("utf-8"),
                file_name="jira-backlog.csv",
                mime="text/csv",
                key="export_backlog",
            )
        else:
            st.info("No Jira records are available for the selected data source.")


st.markdown(
    f'<div class="app-footer">BA Jira Agent · Delivery intelligence workspace · {datetime.now(timezone.utc).strftime("%Y-%m-%d")}</div>',
    unsafe_allow_html=True,
)
