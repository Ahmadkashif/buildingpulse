# Phase 1 — System Pillars

Every pillar describes one true behavior the Phase 1 system must guarantee. Each pillar becomes at least one test. Implementation does not exist until tests are red.

Phase 1 scope (from `MVP_PLAN.md`): a FastAPI app whose sole endpoint returns a hardcoded fixture matching the Contract. No model, no data loading, no logic.

Pillars are grouped by the module they describe. The ordering is: specs first (schemas, fixture), then the system (handler, app wiring), then phase-scope guards that assert what this phase *does not* do.

---

## Module: `app.schemas` — `CreateBuildingInput`

Request body Pydantic model.

1. Accepts the Contract's canonical example request.
2. Rejects a body missing `propertyType`.
3. Rejects a body missing `borough`.
4. Rejects a body missing `grossFloorAreaSqft`.
5. Rejects a body missing `yearBuilt`.
6. Rejects a body missing `numberOfBuildings`.
7. Rejects an unknown/extra field in the body (strict mode).
8. Rejects `propertyType` values outside the enum.
9. Rejects `borough` values outside the enum.
10. Accepts every defined `propertyType` enum value.
11. Accepts every defined `borough` enum value.
12. Rejects `yearBuilt` below 1800.
13. Rejects `yearBuilt` above 2026.
14. Accepts `yearBuilt` at exactly 1800 (lower boundary).
15. Accepts `yearBuilt` at exactly 2026 (upper boundary).
16. Rejects `grossFloorAreaSqft` below 500.
17. Rejects `grossFloorAreaSqft` above 5,000,000.
18. Accepts `grossFloorAreaSqft` at exactly 500 (lower boundary).
19. Accepts `grossFloorAreaSqft` at exactly 5,000,000 (upper boundary).
20. Rejects `numberOfBuildings` below 1.
21. Rejects `numberOfBuildings` above 10.
22. Accepts `numberOfBuildings` at exactly 1 and 10 (boundaries).
23. Rejects non-integer `grossFloorAreaSqft` (no coercion from floats).
24. Parses camelCase JSON keys on input (`propertyType`, not `property_type`).
25. Rejects snake_case JSON keys on input (one wire format; no ambiguity).
26. Serializes to camelCase JSON keys on output.

## Module: `app.schemas` — `PredictionResponse` (and nested models)

Response Pydantic model composed of `Prediction`, `Peer`, `PeerCohort`, `LL97`.

26. Validates against the Contract's canonical example response.
27. Rejects an unknown/extra top-level field (strict mode).
28. `id` must be a non-empty string.
29. `generatedAt` must be a valid ISO 8601 datetime; non-datetime strings are rejected.
30. `input` must itself satisfy `CreateBuildingInput` validation.
31. `prediction.modelVersion` must be a non-empty string.
32. `peer.percentile` rejects values below 0.
33. `peer.percentile` rejects values above 100.
34. `peer.percentile` accepts 0 and 100 (boundaries).
35. `peer.cohortSize` rejects negative values.
36. `peer.cohort.ageBand` rejects values outside the enum.
37. `peer.cohort.ageBand` accepts every defined enum value.
38. `ll97.atRisk` rejects non-boolean values (no truthy-string coercion).
39. Serializes to camelCase JSON keys on output (all nested levels).
40. Round-trips: `model_validate(model.model_dump(by_alias=True))` equals the original.

## Module: `app.fixtures.stub_prediction`

The hardcoded Phase 1 fixture.

41. `STUB` validates against `PredictionResponse`.
42. `STUB.input` validates against `CreateBuildingInput`.
43. `STUB.prediction.modelVersion` is the string `"baseline-lr-v1"` (matches the Contract example — pins the fixture's intent).

## Module: `app.api.predictions` — `POST /api/predictions` (success path)

44. Returns HTTP 201 for a Contract-valid body.
45. Response body validates against `PredictionResponse` as parsed.
46. Response `input` equals the request body (echoed through unchanged).
47. Response `id` begins with the prefix `pred_`.
48. Two sequential calls return distinct `id` values.
49. Response `generatedAt` is within 5 seconds of the request dispatch time.
50. Two sequential calls return distinct `generatedAt` values.
51. Response `prediction`, `peer`, `ll97` blocks equal the stub fixture's corresponding blocks (Phase 1: no real inference yet).

## Module: `app.api.predictions` — `POST /api/predictions` (validation path)

52. Returns 422 on missing `propertyType`.
53. Returns 422 on missing `borough`.
54. Returns 422 on missing `grossFloorAreaSqft`.
55. Returns 422 on missing `yearBuilt`.
56. Returns 422 on missing `numberOfBuildings`.
57. Returns 422 on `propertyType` outside enum.
58. Returns 422 on `borough` outside enum.
59. Returns 422 on `yearBuilt` = 1799.
60. Returns 422 on `yearBuilt` = 2027.
61. Returns 422 on `grossFloorAreaSqft` = 499.
62. Returns 422 on `grossFloorAreaSqft` = 5,000,001.
63. Returns 422 on `numberOfBuildings` = 0.
64. Returns 422 on `numberOfBuildings` = 11.
65. Returns 422 on an unknown/extra field in the body.
66. 422 response body references the offending field name (so clients can surface per-field errors).

## Module: `app.main` — app wiring

67. `app.main` imports without raising.
68. The FastAPI app instance exposes `POST /api/predictions` as a registered route.
69. CORS is configured: a preflight `OPTIONS` from `http://localhost:3000` receives an `Access-Control-Allow-Origin` header matching that origin.
70. CORS rejects an unrelated origin (e.g. `http://evil.example`) — no matching ACAO header.
71. OpenAPI schema at `/openapi.json` references `CreateBuildingInput` as the request body for `POST /api/predictions`.
72. OpenAPI schema references `PredictionResponse` as the 201 response for `POST /api/predictions`.

## Phase-scope guards

Pillars that assert Phase 1 has *not* done what later phases own. Enforced at source-tree level so drift is caught even without runtime.

73. No source file under `backend/app/` imports `pandas`.
74. No source file under `backend/app/` imports `sklearn`.
75. No source file under `backend/app/` imports `joblib`.
76. No source file under `backend/app/` references the string `"dataset.csv"`.
77. No source file under `backend/app/` references the path `backend/artifacts/` or the string `"model.pkl"`.
78. `backend/artifacts/` does not exist at Phase 1 (later phases create it).

---

## Out of scope (no pillars written this phase)

- Real Site EUI inference (Phase 3/4)
- Peer cohort lookup and percentile math (Phase 5)
- LL97 fine computation (Phase 6)
- Prediction persistence across restarts (post-MVP)
- Authentication / rate limiting (post-MVP)
- `GET /api/predictions/:id` endpoint (the Contract names it; Phase 1 doesn't implement it — frontend uses TanStack Query cache populated by the POST response)
