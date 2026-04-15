# Report

The editorial-style view of a forecast — KPIs, insights, asset profile.

## Shape

- `id`, `buildingName`, `generatedAt`
- `kpis: { label, value, caption?, accent?, signature? }[]` — `signature` tiles use the primary gradient
- `rankedAssets: { buildingName, value, unit?, variance }[]`
- `profile: { label, value }[]` — rendered in the Building Profile card

## Endpoints

- `GET /api/reports/:id`
- `POST /api/reports/:id/export` — PDF export stub (returns `{ reportId, url, status }`)
