# Prediction

The output of the Site EUI prediction pipeline for a submitted building. This is the single domain entity the MVP exposes.

## Shape (`PredictionResponse`)

Top-level:

| Field         | Type                 | Notes                                           |
| ------------- | -------------------- | ----------------------------------------------- |
| `id`          | `string`             | e.g. `pred_01HXYZ…`                             |
| `generatedAt` | `string` (ISO 8601)  |                                                 |
| `input`       | `CreateBuildingInput`| Echoed from the request                         |
| `prediction`  | `Prediction`         | Raw Site EUI model output                       |
| `peer`        | `Peer`               | Peer cohort percentile ranking                  |
| `ll97`        | `LL97`               | Local Law 97 compliance outlook + fine estimate |

### `Prediction`

| Field                | Type     |
| -------------------- | -------- |
| `siteEuiKbtuPerSqft` | `number` |
| `intervalLow`        | `number` |
| `intervalHigh`       | `number` |
| `modelVersion`       | `string` |

### `Peer`

| Field            | Type        |
| ---------------- | ----------- |
| `cohort`         | `PeerCohort`|
| `cohortSize`     | `number`    |
| `medianSiteEui`  | `number`    |
| `p25SiteEui`     | `number`    |
| `p75SiteEui`     | `number`    |
| `percentile`     | `number` (0–100, higher = uses more energy than peers) |

### `PeerCohort`

| Field          | Type                                                          |
| -------------- | ------------------------------------------------------------- |
| `propertyType` | `BuildingPropertyType`                                        |
| `borough`      | `BuildingBorough`                                             |
| `ageBand`      | `pre-1950 \| 1950-1979 \| 1980-1999 \| 2000-plus`             |

### `LL97`

| Field                            | Type      |
| -------------------------------- | --------- |
| `capKbtuPerSqft2024to2029`       | `number`  |
| `capKbtuPerSqft2030to2034`       | `number`  |
| `projectedAnnualFineUsd2024`     | `number`  |
| `projectedAnnualFineUsd2030`     | `number`  |
| `atRisk`                         | `boolean` |

## Endpoints

- `POST /api/predictions` (body: `CreateBuildingInput`) → `{ data: PredictionResponse }` (201)
- `GET /api/predictions/:id` → `{ data: PredictionResponse }` (200)

## Client-side derived

`PredictionInsight` and `InsightBadge` are **not** part of the backend response — the result page builds insights client-side from `prediction`, `peer`, and `ll97` fields. Keep this derivation out of the contract.

## Stages

`PREDICTION_STAGES` in `src/mocks/data/prediction-stages.ts` drives the loading-screen copy at 10% milestones.
