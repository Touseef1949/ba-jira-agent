"""
Project memory for the BA Jira Agent — the ``AGENT.md`` analogue of ``CLAUDE.md``.

If an ``AGENT.md`` file exists at the project root, its contents are always
injected into the agent's system prompt: persistent team context such as sprint
cadence, definition-of-done, priority conventions, and the team roster. Absent
the file, the agent simply runs without it.
"""

from __future__ import annotations

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_MD_PATH = os.path.join(PROJECT_ROOT, "AGENT.md")


def load_project_memory(path: str | None = None) -> str:
    """Return the AGENT.md contents (stripped), or "" if the file is absent/empty."""
    target = path or AGENT_MD_PATH
    if not os.path.isfile(target):
        return ""
    try:
        with open(target, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def render_memory_section(memory_loader=load_project_memory) -> str:
    """Render the injectable "Project context (AGENT.md)" block, or "" when empty.

    Single source of truth for how project memory is presented to a model, shared
    by the main agent's system prompt and by spawned sub-agents so both honor the
    same persistent team conventions (definition-of-done, priority ladder, roster).
    """
    memory = memory_loader() if memory_loader else ""
    if not memory:
        return ""
    return (
        "## Project context (AGENT.md)\n"
        "Persistent team context — honor it in every answer:\n\n" + memory
    )
