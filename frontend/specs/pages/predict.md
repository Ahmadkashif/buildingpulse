# Page Flow — Predict Site EUI

Single user flow, three route segments under `/report/*`. The legacy `/forecasting/*` paths 308-redirect to the new ones for one release.

## 1. Form · `/report`

### Layout

- `PageHeader` — title + description
- `Card` — form container
  - `PredictEuiForm` (client)
    - `FormField` wrappers around `Select`, `Input`, `Slider`
    - Primary CTA — gradient `Button`
- `EdgeAccentCard` strip — Efficiency Target · Benchmark Source · Model Version

### Data flow

On submit, `usePredict()` posts `CreateBuildingInput` to `POST /api/predictions`. The full `PredictionResponse` is cached by id in TanStack Query, then the form redirects to `/report/predicting?predictionId={id}`.

## 2. Loading · `/report/predicting?predictionId=…`

Full-viewport progress screen. Animates 0 → 100% and cycles through copy from `PREDICTION_STAGES`. On completion, redirects to `/report/{predictionId}`.

### Layout

- `ForecastProgress` — centered column with rotating headline, status copy, progress bar + percent.
- Ambient primary-gradient glow behind the bar.

## 3. Result · `/report/[id]`

### Layout

Two-column grid (`lg:grid-cols-[2fr_1fr]`):

- **Left column**
  - KPI row — 3 `KpiTile`s: Predicted Site EUI (signature), Peer Percentile, LL97 Status
  - `BarChartCard` — Peer Cohort Comparison (bars: p25, Median, You, p75)
  - Insights grid — up to 4 `InsightCard`s, badges derived from percentile + LL97 atRisk
- **Right column**
  - `InfoCard` — Building Profile (echo of `input` + model version)
  - `ActionColumn` — Export PDF, View Retrofit Options, Refine Inputs

### Data flow

- `usePrediction(id)` — `GET /api/predictions/:id` (served from cache if the mutation populated it)
- `ExportDialog` invoked from the Export CTA; drives the `usePdfExport` stub (no real PDF yet)
