# Page — Predicting

`/forecasting/predicting?forecastId=…`

Full-viewport loading screen. Animates 0 → 100% and cycles through copy sourced from `FORECAST_STAGES`. On completion, redirects to `/forecasting/report/[forecastId]`.

## Layout

- `ForecastProgress` — centered column with rotating headline, status copy, progress bar + percent.
- Ambient primary-gradient glow behind the bar per DESIGN.md.
