"""
Skill layer for the BA Jira Agent — Claude-Code-style progressive disclosure.

A *skill* is a folder under ``skills/`` containing a ``SKILL.md`` file with YAML
frontmatter (``name``, ``description``, optional ``when_to_use`` and ``command``)
followed by a markdown *procedure* body.

Only each skill's name + description ("the catalog") is injected into the agent's
system prompt. The full procedure body is loaded on demand via the ``load_skill``
tool — this is the progressive-disclosure pattern that keeps the base prompt cheap.
"""

from __future__ import annotations

import importlib.util
import inspect
import os
from dataclasses import dataclass

import yaml

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


@dataclass(frozen=True)
class Skill:
    """A single discovered skill parsed from a SKILL.md file."""

    name: str
    description: str
    body: str
    when_to_use: str = ""
    command: str = ""
    slug: str = ""


def _parse_skill_md(text: str) -> tuple[dict, str]:
    """Split a SKILL.md file into (frontmatter dict, body markdown).

    Expects a leading ``---`` fenced YAML block. Returns an empty dict and the
    raw text unchanged if no valid frontmatter fence is present.
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text.strip()

    # Drop the opening fence, then split on the closing fence.
    after_open = stripped[3:]
    parts = after_open.split("\n---", 1)
    if len(parts) != 2:
        return {}, text.strip()

    front_raw, body = parts
    try:
        front = yaml.safe_load(front_raw) or {}
    except yaml.YAMLError:
        front = {}
    if not isinstance(front, dict):
        front = {}
    return front, body.lstrip("\n").strip()


class SkillRegistry:
    """Discovers and serves skills from the ``skills/`` directory."""

    def __init__(self, skills_dir: str | None = None):
        self.skills_dir = skills_dir or SKILLS_DIR
        self._skills: dict[str, Skill] = {}
        self._tool_cache: dict[str, dict] = {}
        self.reload()

    # ── discovery ──────────────────────────────────────────────────────────────
    def reload(self) -> None:
        """(Re)scan the skills directory and rebuild the in-memory registry."""
        self._skills = {}
        self._tool_cache = {}
        if not os.path.isdir(self.skills_dir):
            return

        for entry in sorted(os.listdir(self.skills_dir)):
            skill_path = os.path.join(self.skills_dir, entry, "SKILL.md")
            if not os.path.isfile(skill_path):
                continue
            try:
                with open(skill_path, "r", encoding="utf-8") as fh:
                    front, body = _parse_skill_md(fh.read())
            except OSError:
                continue

            name = str(front.get("name") or entry).strip()
            description = str(front.get("description") or "").strip()
            # A skill without a name or description can't be catalogued usefully.
            if not name or not description:
                continue

            skill = Skill(
                name=name,
                description=description,
                body=body,
                when_to_use=str(front.get("when_to_use") or "").strip(),
                command=str(front.get("command") or "").strip(),
                slug=entry,
            )
            self._skills[name] = skill

    # ── access ─────────────────────────────────────────────────────────────────
    def list_skills(self) -> list[Skill]:
        """Return all discovered skills, sorted by name (for the UI)."""
        return sorted(self._skills.values(), key=lambda s: s.name)

    def get(self, name: str) -> Skill | None:
        """Look up a skill by exact name, then by slug, then case-insensitively."""
        if name in self._skills:
            return self._skills[name]
        target = (name or "").strip().lower()
        for skill in self._skills.values():
            if skill.slug.lower() == target or skill.name.lower() == target:
                return skill
        return None

    def get_body(self, name: str) -> str | None:
        """Return the full procedure body for a skill, or None if unknown."""
        skill = self.get(name)
        return skill.body if skill else None

    # ── bundled tools (Claude-Code-style skills-ship-scripts) ────────────────────
    def get_skill_tools(self, name: str) -> dict:
        """Return ``{func_name: callable}`` for a skill's optional ``tools.py``.

        A skill may ship executable tools alongside its procedure at
        ``skills/<slug>/tools.py``. Public top-level functions (not starting with
        ``_``) become bundled tools, loaded lazily and cached. Import errors yield
        an empty dict — a broken bundle never takes down the agent.
        """
        skill = self.get(name)
        if skill is None:
            return {}
        if skill.slug in self._tool_cache:
            return self._tool_cache[skill.slug]

        tools_path = os.path.join(self.skills_dir, skill.slug, "tools.py")
        found: dict = {}
        if os.path.isfile(tools_path):
            try:
                spec = importlib.util.spec_from_file_location(
                    f"skill_tools_{skill.slug}", tools_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for fname, fn in inspect.getmembers(module, inspect.isfunction):
                    if not fname.startswith("_") and fn.__module__ == module.__name__:
                        found[fname] = fn
            except Exception:
                found = {}
        self._tool_cache[skill.slug] = found
        return found

    def has_tools(self, name: str) -> bool:
        """True if the skill ships bundled tools."""
        return bool(self.get_skill_tools(name))

    def resolve_command(self, command: str) -> Skill | None:
        """Resolve a slash command (e.g. ``/velocity`` or ``velocity``) to a skill."""
        target = (command or "").strip().lower().lstrip("/")
        if not target:
            return None
        for skill in self._skills.values():
            cmd = skill.command.lower().lstrip("/")
            if cmd and cmd == target:
                return skill
        # Fall back to slug / name match so `/velocity-forecast` also works.
        return self.get(target)

    def expand_slash_command(self, raw: str) -> str:
        """Expand a leading ``/slash`` command into a natural-language skill invocation.

        ``/velocity`` → "Run the 'velocity-forecast' skill for the current backlog."
        Non-slash input, or an unrecognized command, is returned unchanged so the
        agent still handles it directly.
        """
        text = (raw or "").strip()
        if not text.startswith("/"):
            return text
        token = text.split()[0]
        skill = self.resolve_command(token)
        if skill is None:
            return text
        remainder = text[len(token):].strip()
        invocation = f"Run the '{skill.name}' skill for the current backlog."
        if remainder:
            invocation += f" Additional context: {remainder}"
        return invocation

    def catalog(self) -> str:
        """Render the name + description catalog injected into the system prompt.

        Kept deliberately compact — this is the always-present, cheap half of the
        progressive-disclosure contract. The full body is fetched via load_skill.
        """
        skills = self.list_skills()
        if not skills:
            return ""
        lines = []
        for skill in skills:
            lines.append(f"- {skill.name}: {skill.description}")
            if skill.when_to_use:
                lines.append(f"    when_to_use: {skill.when_to_use}")
        return "\n".join(lines)
