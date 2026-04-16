# Building Input

Building specs the user submits to generate a Site EUI prediction. This is the request payload only — no persisted Building entity is modeled for the MVP.

## Shape (`CreateBuildingInput`)

| Field                 | Type                                                                           |
| --------------------- | ------------------------------------------------------------------------------ |
| `propertyType`        | `multifamily-housing \| office \| hotel \| retail \| hospital \| mixed-use`    |
| `borough`             | `manhattan \| brooklyn \| queens \| bronx \| staten-island`                    |
| `grossFloorAreaSqft`  | `number` (500 – 5,000,000)                                                     |
| `yearBuilt`           | `number` (1800 – 2026)                                                         |
| `numberOfBuildings`   | `number` (1 – 10)                                                              |

## Where it's used

- Submitted via `POST /api/predictions` (see `prediction.md`).
- Echoed back inside `PredictionResponse.input` so result pages can render the building profile without a separate fetch.
