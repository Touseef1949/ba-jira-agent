---
name: velocity-forecast
description: Compute per-sprint velocity (story points per sprint), read the trend, and give a grounded forecast for the next sprint's capacity. Use for "sprint velocity", "how fast are we going", "capacity for next sprint", or velocity-trend questions.
when_to_use: The user wants a velocity trend read and a forecast of next-sprint capacity. Do NOT use for a single sprint's raw numbers ("velocity for Sprint 24?") — answer that directly with calculate_metrics.
command: /velocity
---

# Velocity Forecast

Turn the per-sprint story-point data into a velocity read and a defensible next-sprint forecast.

## Procedure

1. Call `calculate_metrics("sprint")` to get ticket count and story points for each sprint (Sprint 23–27).
2. Order the sprints chronologically and read the story-point series.
3. Compute the **average velocity** across completed sprints and note the **trend** (rising, flat, or falling).
4. Forecast next-sprint capacity as the trailing average, adjusted for the trend — and state the assumption explicitly.

## Output format

- **Velocity table** — sprint, tickets, story points, one row each, in order.
- **Trend** — one sentence: is velocity rising, flat, or falling, and by roughly how much.
- **Forecast** — "Next sprint can likely absorb ~N story points" with the reasoning (e.g. "trailing 3-sprint average of X, trending up/down").
- **Caveats** — call out anything that weakens the forecast (a sprint still in progress, an outlier, small sample size).

Never present the forecast as a commitment — it is a planning estimate grounded in the observed data.
