@AGENTS.md

# buildingPulse

Site EUI prediction UI for NYC building owners. A user submits building specifications (type, borough, sqft, year built, number of buildings) and receives back a predicted Site Energy Use Intensity, their percentile ranking within a peer cohort, and a Local Law 97 compliance outlook with projected fine.

## Design system

- Fonts: **Manrope** (headlines) + **Inter** (body, labels).
- Core brand: primary `#005FB8`, secondary `#2E7D32`, tertiary `#00796B`, neutral `#45474A`.
- Design philosophy — "Kinetic Precision Framework": borderless surface hierarchy, gradient primary CTAs, ambient depth (no hard shadows), tonal status chips, ghost inputs. See `specs/` for details.

## Workflow

1. `/report` — form page for building specifications.
2. `/report/predicting?predictionId=…` — loading animation with 10% milestone copy.
3. `/report/[id]` — result layout (KPIs: EUI / percentile / LL97; peer cohort chart; insights; action column).
4. Export dialog — PDF export stub reuses the progress primitive.

See `specs/models/prediction.md` for the `PredictionResponse` contract shared with the backend.
