# Building

A NYC property the user submits for an EUI forecast.

## Shape

| Field                    | Type                                                                                |
| ------------------------ | ----------------------------------------------------------------------------------- |
| `id`                     | `string`                                                                            |
| `name`                   | `string`                                                                            |
| `propertyType`           | `commercial-office \| residential-multifamily \| mixed-use \| industrial \| retail` |
| `borough`                | `manhattan \| brooklyn \| queens \| bronx \| staten-island`                         |
| `grossFloorAreaSqft`     | `number` (500 – 5,000,000)                                                          |
| `yearBuilt`              | `number` (1800 – 2024)                                                              |
| `numberOfBuildingsOnLot` | `number` (1 – 10)                                                                   |

## Endpoints

- `GET /api/buildings` — list
- `GET /api/buildings/:id` — detail
