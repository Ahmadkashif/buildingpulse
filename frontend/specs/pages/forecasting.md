# Page — Predict Building Site EUI

`/forecasting`

Form workflow for submitting building specifications.

## Layout

- `PageHeader` — title + description
- `Card` — form container
  - `PredictEuiForm` (client)
    - `FormField` wrappers around `Select`, `Input`, `Slider`
    - Primary CTA — gradient `Button`
- `EdgeAccentCard` strip — Efficiency Target, Market Average, Model Version

## Data flow

On submit, `usePredictEui` posts to `/api/forecasts`; the response `id` drives the redirect to `/forecasting/predicting?forecastId=…`.
