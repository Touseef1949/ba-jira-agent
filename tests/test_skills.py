"""
Tests for the Claude-Code-style skill layer.

Covers the SkillRegistry (discovery, frontmatter parsing, catalog, command
resolution), the load_skill tool (progressive disclosure), project memory
(AGENT.md), and system-prompt composition in agent.build_system_prompt.
"""

import textwrap

import pytest

from core.skills import Skill, SkillRegistry, _parse_skill_md
from core import project_memory


# ── helpers ────────────────────────────────────────────────────────────────────

def _write_skill(root, slug, name, description, when_to_use="", command="", body="Do the thing."):
    """Write a skills/<slug>/SKILL.md under root and return its directory."""
    skill_dir = root / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    front = f"---\nname: {name}\ndescription: {description}\n"
    if when_to_use:
        front += f"when_to_use: {when_to_use}\n"
    if command:
        front += f"command: {command}\n"
    front += "---\n\n" + body + "\n"
    (skill_dir / "SKILL.md").write_text(front, encoding="utf-8")
    return skill_dir


# ── frontmatter parsing ─────────────────────────────────────────────────────────

class TestParseSkillMd:
    @pytest.mark.unit
    def test_parses_frontmatter_and_body(self):
        text = textwrap.dedent(
            """\
            ---
            name: demo
            description: A demo skill.
            command: /demo
            ---

            # Demo

            Body text here.
            """
        )
        front, body = _parse_skill_md(text)
        assert front["name"] == "demo"
        assert front["description"] == "A demo skill."
        assert front["command"] == "/demo"
        assert body.startswith("# Demo")
        assert "Body text here." in body

    @pytest.mark.unit
    def test_no_frontmatter_returns_empty_dict(self):
        front, body = _parse_skill_md("# Just markdown\n\nno fence")
        assert front == {}
        assert "Just markdown" in body

    @pytest.mark.unit
    def test_malformed_yaml_degrades_gracefully(self):
        # Unterminated fence — should not raise.
        front, body = _parse_skill_md("---\nname: x: y: z\n")
        assert isinstance(front, dict)


# ── registry discovery ──────────────────────────────────────────────────────────

class TestSkillRegistryDiscovery:
    @pytest.mark.unit
    def test_discovers_skills_in_custom_dir(self, tmp_path):
        _write_skill(tmp_path, "alpha", "alpha", "First skill.", command="/a")
        _write_skill(tmp_path, "beta", "beta", "Second skill.", command="/b")
        reg = SkillRegistry(str(tmp_path))
        names = [s.name for s in reg.list_skills()]
        assert names == ["alpha", "beta"]

    @pytest.mark.unit
    def test_skips_dirs_without_skill_md(self, tmp_path):
        (tmp_path / "empty").mkdir()
        _write_skill(tmp_path, "real", "real", "Real skill.")
        reg = SkillRegistry(str(tmp_path))
        assert [s.name for s in reg.list_skills()] == ["real"]

    @pytest.mark.unit
    def test_skips_skill_missing_name_or_description(self, tmp_path):
        d = tmp_path / "broken"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: broken\n---\nbody", encoding="utf-8")
        reg = SkillRegistry(str(tmp_path))
        assert reg.list_skills() == []

    @pytest.mark.unit
    def test_missing_skills_dir_is_safe(self, tmp_path):
        reg = SkillRegistry(str(tmp_path / "does-not-exist"))
        assert reg.list_skills() == []
        assert reg.catalog() == ""


# ── access: get / get_body / resolve_command / catalog ──────────────────────────

class TestSkillRegistryAccess:
    @pytest.fixture
    def reg(self, tmp_path):
        _write_skill(
            tmp_path, "velocity-forecast", "velocity-forecast",
            "Compute per-sprint velocity.", command="/velocity",
            body="# Velocity\n\nStep 1.",
        )
        return SkillRegistry(str(tmp_path))

    @pytest.mark.unit
    def test_get_by_name_and_slug(self, reg):
        assert reg.get("velocity-forecast") is not None
        assert reg.get("VELOCITY-FORECAST") is not None  # case-insensitive

    @pytest.mark.unit
    def test_get_body(self, reg):
        body = reg.get_body("velocity-forecast")
        assert body is not None and "Step 1." in body
        assert reg.get_body("nope") is None

    @pytest.mark.unit
    def test_resolve_command_variants(self, reg):
        assert reg.resolve_command("/velocity").name == "velocity-forecast"
        assert reg.resolve_command("velocity").name == "velocity-forecast"
        assert reg.resolve_command("/velocity-forecast").name == "velocity-forecast"
        assert reg.resolve_command("/nope") is None
        assert reg.resolve_command("") is None

    @pytest.mark.unit
    def test_catalog_contains_name_and_description(self, reg):
        cat = reg.catalog()
        assert "velocity-forecast" in cat
        assert "Compute per-sprint velocity." in cat

    @pytest.mark.unit
    def test_expand_slash_command(self, reg):
        assert reg.expand_slash_command("/velocity") == (
            "Run the 'velocity-forecast' skill for the current backlog."
        )

    @pytest.mark.unit
    def test_expand_slash_command_with_remainder(self, reg):
        out = reg.expand_slash_command("/velocity focus on Sprint 24")
        assert out.startswith("Run the 'velocity-forecast' skill")
        assert "Additional context: focus on Sprint 24" in out

    @pytest.mark.unit
    def test_expand_unknown_or_plain_passes_through(self, reg):
        assert reg.expand_slash_command("/nope") == "/nope"
        assert reg.expand_slash_command("show me bugs") == "show me bugs"
        assert reg.expand_slash_command("") == ""


# ── the real shipped skills ─────────────────────────────────────────────────────

class TestShippedSkills:
    @pytest.mark.unit
    def test_four_seed_skills_present(self):
        reg = SkillRegistry()
        names = {s.name for s in reg.list_skills()}
        assert {
            "sprint-health-report",
            "unassigned-risk-triage",
            "velocity-forecast",
            "standup-summary",
        }.issubset(names)

    @pytest.mark.unit
    def test_every_shipped_skill_has_command_and_body(self):
        reg = SkillRegistry()
        for skill in reg.list_skills():
            assert skill.command, f"{skill.name} missing command"
            assert skill.body.strip(), f"{skill.name} missing body"


# ── load_skill tool ─────────────────────────────────────────────────────────────

class TestLoadSkillTool:
    @pytest.mark.unit
    def test_known_skill_returns_procedure(self):
        from tools import load_skill
        out = load_skill.invoke({"skill_name": "sprint-health-report"})
        assert "# Skill: sprint-health-report" in out
        assert "Procedure" in out

    @pytest.mark.unit
    def test_unknown_skill_lists_available(self):
        from tools import load_skill
        out = load_skill.invoke({"skill_name": "does-not-exist"})
        assert "No skill named" in out
        assert "velocity-forecast" in out  # available skills listed

    @pytest.mark.unit
    def test_load_skill_surfaces_bundled_tools(self):
        from tools import load_skill
        out = load_skill.invoke({"skill_name": "velocity-forecast"})
        assert "Bundled tools" in out
        assert "forecast_next_sprint" in out


# ── bundled tools (Phase 4) ─────────────────────────────────────────────────────

class TestBundledTools:
    @pytest.mark.unit
    def test_registry_discovers_bundled_tools(self):
        reg = SkillRegistry()
        assert reg.has_tools("velocity-forecast") is True
        assert "forecast_next_sprint" in reg.get_skill_tools("velocity-forecast")

    @pytest.mark.unit
    def test_skill_without_bundle_has_no_tools(self):
        reg = SkillRegistry()
        assert reg.has_tools("sprint-health-report") is False
        assert reg.get_skill_tools("sprint-health-report") == {}

    @pytest.mark.unit
    def test_get_skill_tools_unknown_skill(self):
        reg = SkillRegistry()
        assert reg.get_skill_tools("does-not-exist") == {}

    @pytest.mark.unit
    def test_use_skill_tool_runs_bundled(self):
        from tools import use_skill_tool
        out = use_skill_tool.invoke(
            {"skill_name": "velocity-forecast", "tool_name": "forecast_next_sprint"}
        )
        assert "Forecast" in out and "SP" in out

    @pytest.mark.unit
    def test_use_skill_tool_unknown_tool(self):
        from tools import use_skill_tool
        out = use_skill_tool.invoke(
            {"skill_name": "velocity-forecast", "tool_name": "nope"}
        )
        assert "No bundled tool" in out
        assert "forecast_next_sprint" in out  # lists what IS available


# ── subagents (Phase 4) ─────────────────────────────────────────────────────────

class TestSpawnSubagent:
    @pytest.mark.unit
    def test_unknown_skill_returns_error_without_llm(self):
        from tools import spawn_subagent
        out = spawn_subagent.invoke({"skill_name": "does-not-exist", "task": "x"})
        assert "No skill named" in out
        assert "velocity-forecast" in out  # available skills listed

    @pytest.mark.unit
    def test_spawn_subagent_registered_on_agent(self):
        import agent
        names = [t.name for t in agent.tools]
        assert "spawn_subagent" in names
        assert "use_skill_tool" in names


# ── project memory (AGENT.md) ───────────────────────────────────────────────────

class TestProjectMemory:
    @pytest.mark.unit
    def test_loads_present_file(self, tmp_path):
        f = tmp_path / "AGENT.md"
        f.write_text("Team rules here.\n", encoding="utf-8")
        assert project_memory.load_project_memory(str(f)) == "Team rules here."

    @pytest.mark.unit
    def test_absent_file_returns_empty(self, tmp_path):
        assert project_memory.load_project_memory(str(tmp_path / "nope.md")) == ""

    @pytest.mark.unit
    def test_shipped_agent_md_has_conventions(self):
        mem = project_memory.load_project_memory()
        assert "Definition of done" in mem
        assert "Priya Sharma" in mem


# ── system prompt composition ───────────────────────────────────────────────────

class TestBuildSystemPrompt:
    @pytest.mark.unit
    def test_injects_catalog_and_memory_in_order(self, tmp_path):
        from agent import build_system_prompt
        _write_skill(tmp_path, "alpha", "alpha", "First skill.", command="/a")
        reg = SkillRegistry(str(tmp_path))
        prompt = build_system_prompt(registry=reg, memory_loader=lambda: "MEMORY_BLOCK")
        assert "MEMORY_BLOCK" in prompt
        assert "## Available skills" in prompt
        assert "alpha: First skill." in prompt
        assert prompt.index("MEMORY_BLOCK") < prompt.index("## Available skills")

    @pytest.mark.unit
    def test_omits_sections_when_empty(self, tmp_path):
        from agent import build_system_prompt
        reg = SkillRegistry(str(tmp_path / "empty"))  # no skills
        prompt = build_system_prompt(registry=reg, memory_loader=lambda: "")
        assert "## Available skills" not in prompt
        assert "## Project context" not in prompt
        assert "BA Assistant AI agent" in prompt  # base persona still present

    @pytest.mark.unit
    def test_default_build_includes_shipped_skills(self):
        from agent import build_system_prompt
        prompt = build_system_prompt()
        assert "sprint-health-report" in prompt
        assert "load_skill" in prompt
