@AGENTS.md

# buildingPulse

Energy-forecasting UI scaffold. A NYC building operator inputs specifications, a forecasting model produces a Site EUI estimate, and the operator reviews the resulting report.

## Design system

- Fonts: **Manrope** (headlines) + **Inter** (body, labels).
- Core brand: primary `#005FB8`, secondary `#2E7D32`, tertiary `#00796B`, neutral `#45474A`.
- Design philosophy — "Kinetic Precision Framework": borderless surface hierarchy, gradient primary CTAs, ambient depth (no hard shadows), tonal status chips, ghost inputs. See `specs/` for details.

## Workflow

1. `/forecasting` — form page for building specifications.
2. `/forecasting/predicting` — loading animation with 10% milestone copy.
3. `/forecasting/report/[id]` — report layout (KPIs, chart, insights, action column).
4. Export dialog — PDF export stub reuses the progress primitive.
