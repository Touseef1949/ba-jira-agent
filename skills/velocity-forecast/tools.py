"""
Bundled tools for the velocity-forecast skill.

Demonstrates Claude-Code-style skills-ship-scripts: this module is discovered by
the SkillRegistry and its public functions become tools the agent can call via
``use_skill_tool('velocity-forecast', 'forecast_next_sprint')`` — but only after
the skill is loaded (progressive disclosure).
"""


def _load_tickets() -> list[dict]:
    """Return tickets from the agent's configured data source (mock or live Jira).

    Routes through the main ``tools`` module so the forecast honors the same
    ``configure_tools`` mock/Jira selection as the data tools, instead of always
    reading the local mock export and silently serving mock forecasts in Live mode.
    """
    from tools import _load_all_tickets

    return _load_all_tickets()


def forecast_next_sprint(arg: str = "") -> str:
    """Linear-trend forecast of next sprint's story points from sprint history.

    Reads the backlog, sums story points per sprint, fits a simple linear trend,
    and projects the next sprint's capacity. Returns a text summary. ``arg`` is
    unused (accepted so the dispatcher can pass a string uniformly).
    """
    tickets = _load_tickets()

    sp_by_sprint: dict[str, int] = {}
    for t in tickets:
        sprint = t.get("sprint", "Unknown")
        sp_by_sprint[sprint] = sp_by_sprint.get(sprint, 0) + (t.get("story_points") or 0)

    sprints = sorted(sp_by_sprint)
    series = [sp_by_sprint[s] for s in sprints]
    if len(series) < 2:
        return "Not enough sprint history to forecast (need at least 2 sprints)."

    n = len(series)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(series) / n
    denom = sum((x - mean_x) ** 2 for x in xs) or 1
    slope = sum((xs[i] - mean_x) * (series[i] - mean_y) for i in range(n)) / denom
    forecast = round(mean_y + slope * (n - mean_x))  # project the next sprint (x = n)

    trend = "rising" if slope > 0.5 else "falling" if slope < -0.5 else "flat"
    return (
        f"Story points per sprint: {dict(zip(sprints, series))}. "
        f"Trailing average {round(mean_y, 1)} SP; trend {trend} "
        f"({slope:+.1f} SP/sprint). "
        f"Forecast for the next sprint ≈ {forecast} SP "
        f"(planning estimate from a linear trend — not a commitment)."
    )
