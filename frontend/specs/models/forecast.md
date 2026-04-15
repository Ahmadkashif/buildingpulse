# Forecast

The output of the DeepGrid prediction model for a submitted building.

## Shape

- `id`, `buildingId`, `predictedAnnualConsumptionMwh`, `peakLoadMw`, `peakTimestamp`, `confidencePct`
- `breakdown: { month, predicted, savingsPotential }[]` — monthly stacked-bar data
- `insights: { id, title, description, badge }[]` — `badge` ∈ `savings | verified | yield-high | action`

## Endpoints

- `POST /api/forecasts` (body: `CreateBuildingInput`) → `{ id }`
- `GET /api/forecasts/:id`

## Stages

`FORECAST_STAGES` in `src/mocks/data/forecast-stages.ts` drives the loading-screen copy at 10% milestones.
