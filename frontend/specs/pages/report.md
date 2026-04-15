# Page — AI Forecast Report

`/forecasting/report/[id]`

Report layout (reference: Image A from the source designs).

## Layout

Two-column grid (`lg:grid-cols-[2fr_1fr]`):

- **Left column**
  - KPI row — 3 `KpiTile`s (1 `signature` variant for Confidence)
  - `BarChartCard` — Consumption Breakdown
  - AI Insights grid — 4 `InsightCard`s with rotating icons by badge
- **Right column**
  - `InfoCard` — Building Profile
  - `ActionColumn` — Export PDF, Apply Recommendations, Refine Inputs
  - `RankedListCard` — Top Portfolio Consumers

## Data flow

- `useReport(id)` — `/api/reports/:id`
- `useForecast(id)` — `/api/forecasts/:id` (breakdown + insights)
- `ExportDialog` invoked from the Export CTA; drives the `usePdfExport` stub.
