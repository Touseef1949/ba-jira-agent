"""
BA Jira Agent — LangChain ReAct agent backed by DeepSeek API.
Uses LangChain 1.3.x / LangGraph API (create_react_agent from langgraph.prebuilt).

Exports `agent` (compiled graph), `executor` (alias), and `run_agent(query)`.
"""

import os

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from tools import (
    configure_tools,
    load_tickets,
    filter_tickets,
    search_tickets,
    calculate_metrics,
    load_skill,
    use_skill_tool,
    spawn_subagent,
    _skill_registry,
)
from core.project_memory import load_project_memory, render_memory_section

# ── Load environment ──────────────────────────────────────────────────────────
_project_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_project_dir, ".env")
load_dotenv(_env_path, override=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "DEEPSEEK_API_KEY not found. "
        "Create a .env file in the project directory with:\n"
        "  DEEPSEEK_API_KEY=your-deepseek-api-key-here"
    )

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="deepseek-v4-flash",
    base_url="https://api.deepseek.com/v1",
    api_key=DEEPSEEK_API_KEY,
    temperature=0,
)

# ── Tools ─────────────────────────────────────────────────────────────────────
# Data tools + skill-layer tools: load_skill (progressive disclosure of procedures),
# use_skill_tool (run a skill's bundled tools), spawn_subagent (delegate to a
# single-skill specialist sub-agent).
tools = [
    load_tickets,
    filter_tickets,
    search_tickets,
    calculate_metrics,
    load_skill,
    use_skill_tool,
    spawn_subagent,
]

# ── System Prompt ─────────────────────────────────────────────────────────────
_BASE_PROMPT = (
    "You are a BA Assistant AI agent. You help Product Owners analyze Jira backlogs. "
    "You have tools to load tickets, filter them, search them, and calculate metrics. "
    "Always use tools to get data before answering. "
    "Provide structured, actionable summaries."
)


def build_system_prompt(registry=_skill_registry, memory_loader=load_project_memory) -> str:
    """Compose the system prompt from base persona + project memory + skill catalog.

    Progressive disclosure: only the skill *catalog* (name + description) is
    injected here. The agent calls the ``load_skill`` tool to pull a skill's full
    procedure on demand, keeping the base prompt small.
    """
    sections = [_BASE_PROMPT]

    memory_section = render_memory_section(memory_loader)
    if memory_section:
        sections.append(memory_section)

    catalog = registry.catalog() if registry else ""
    if catalog:
        sections.append(
            "## Available skills\n"
            "These are reusable playbooks for multi-step BA tasks:\n\n"
            f"{catalog}\n\n"
            "Use a skill ONLY when the user asks for a full report, analysis, forecast, "
            "or multi-step triage. In that case call the `load_skill` tool with the "
            "skill's name FIRST, then follow its procedure using your data tools.\n"
            "Do NOT use a skill for a direct factual question — a count, a single lookup, "
            "'how many', 'which tickets', 'find X', 'who is assigned'. Answer those "
            "concisely with the data tools alone, and keep the answer scoped to exactly "
            "what was asked (no extra risk analysis or recommendations unless requested).\n"
            "Advanced (report/analysis work only): after load_skill, a skill may list "
            "bundled tools — run one with `use_skill_tool(skill, tool)`. For a heavy, "
            "self-contained part of a larger analysis, delegate it to a specialist with "
            "`spawn_subagent(skill, task)`."
        )

    return "\n\n".join(sections)


# Composed once at import for the module-level default agent.
SYSTEM_PROMPT = build_system_prompt()

# ── Agent (compiled LangGraph ReAct agent) ────────────────────────────────────
# LangChain 1.3.x: create_react_agent returns a compiled StateGraph, not AgentExecutor.
# Invoke with: agent.invoke({"messages": [{"role": "user", "content": query}]})
# Result: {"messages": [...]} — last message is the final answer.
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)

# Alias for compatibility
executor = agent


def get_agent(data_source: str = "mock", jira_config: dict | None = None):
    """
    Create a fresh LangGraph ReAct agent configured for mock or live Jira data.

    Args:
        data_source: Either "mock" or "jira".
        jira_config: Jira connection configuration for live Jira mode.

    Returns:
        A compiled LangGraph StateGraph.
    """
    configure_tools(data_source, jira_config)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )


# ── Public API ────────────────────────────────────────────────────────────────
def run_agent(query: str) -> str:
    """
    Run the BA Jira agent with a natural-language query.
    Returns the agent's final answer as a string.
    """
    result = agent.invoke({
        "messages": [{"role": "user", "content": query}],
    })
    messages = result.get("messages", [])
    if messages:
        final = messages[-1]
        if hasattr(final, "content"):
            return final.content
        elif isinstance(final, dict):
            return final.get("content", "No output returned by the agent.")
    return "No output returned by the agent."