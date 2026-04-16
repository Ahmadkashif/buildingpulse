# BuildingPulse MVP — Execution Plan

> This document is picked up by agents. Each phase is self-contained. Do **not** skip ahead, do **not** scaffold files that a future phase will need — write things when the phase that needs them arrives.
>
> `PLAN.md` is the learning curriculum. This file is the build order.

---

## Product (one line)

A small building owner enters their building's basics and gets back: a **Site EUI prediction**, where they sit in the **percentile distribution of similar buildings**, and a **projected LL97 fine** if they're over the cap. That's the MVP. Nothing else.

Everything we build serves this loop. Features that don't contribute to this loop are out of scope until after the MVP ships.

---

## Load-bearing decision (Phase 0 depends on this)

The frontend specs (`frontend/specs/`) and existing code (`src/types`, `src/mocks`, components like `BarChartCard`, `ActionColumn`) were written for a different product: a "DeepGrid" energy forecast with MWh annual consumption, peak load MW, and a monthly breakdown. **That product is not the one we're building.**

**Resolution (default, pending confirmation):** The domain model gets rewritten in Phase 0 to match the Site EUI peer-report product defined in the Contract below. Reusable UI is kept; domain-shaped mocks/types/specs are rewritten.

- **Keep:** app shell (`SideNav`, `TopBar`, `AppShell`), form primitives (`FormField`, `Input`, `Select`, `Slider`, `YesNoToggle`), `KpiTile`, `InsightCard`, `InfoCard`, `Card`, `Badge`, loading screen, page shells.
- **Rewrite:** `src/types/models/*`, `src/mocks/data/*`, `src/mocks/handlers/*`, all files under `frontend/specs/models/` and `frontend/specs/pages/`, the `PredictEuiForm` field list, and any chart currently rendering monthly MWh.
- **Kill:** anything tied to peak load, monthly consumption breakdown, or a multi-asset "ranked list" (`RankedListCard` — not in MVP).

No agent proceeds past Phase 0 until the human has confirmed this resolution.

---

## The Contract

Defined here once. Backend returns this shape; frontend consumes this shape. If a phase needs to change it, the change happens here first, then propagates.

### `POST /api/predictions`

**Request:**
```json
{
  "propertyType": "Multifamily Housing",
  "borough": "Brooklyn",
  "grossFloorAreaSqft": 45000,
  "yearBuilt": 1925,
  "numberOfBuildings": 1
}
```

**Response:**
```json
{
  "id": "pred_01HXYZ...",
  "generatedAt": "2026-04-16T18:22:01Z",
  "input": { "...echo of request..." },
  "prediction": {
    "siteEuiKbtuPerSqft": 87.3,
    "intervalLow": 65.2,
    "intervalHigh": 109.4,
    "modelVersion": "baseline-lr-v1"
  },
  "peer": {
    "cohort": {
      "propertyType": "Multifamily Housing",
      "borough": "Brooklyn",
      "ageBand": "pre-1950"
    },
    "cohortSize": 1420,
    "medianSiteEui": 74.1,
    "p25SiteEui": 58.0,
    "p75SiteEui": 94.5,
    "percentile": 68
  },
  "ll97": {
    "capKbtuPerSqft2024To2029": 6.75,
    "capKbtuPerSqft2030To2034": 4.53,
    "projectedAnnualFineUsd2024": 0,
    "projectedAnnualFineUsd2030": 12400,
    "atRisk": true
  }
}
```

Field rules:
- All energy values are numbers (not strings). No units in values; units live in field names or UI.
- `percentile` is 0–100, integer. Higher = uses more energy than peers (worse).
- `atRisk` = `true` iff projected EUI exceeds either cap.
- `modelVersion` is a free-string tag written by the training pipeline; the API just passes it through.

Unknown/missing fields in the request → 422 with a JSON body `{ "error": "...", "field": "..." }`. No silent defaults.

---

## Repo layout (target)

```
backend/
  app/
    main.py               # FastAPI entry
    api/predictions.py    # the one endpoint
    schemas.py            # Pydantic models mirroring the Contract
    model/
      predictor.py        # load model.pkl, predict
      peer.py             # percentile lookup
      ll97.py             # fine calculation
    fixtures/
      stub_prediction.py  # Phase 1 only
  training/
    train_baseline.py     # dataset.csv → artifacts/
    clean.py              # shared data cleaning
  artifacts/
    model.pkl             # written by training, read by app
    metrics.json
    peer_cohorts.parquet  # precomputed percentiles by cohort
  data/
    dataset.csv           # already present
  requirements.txt
  pyproject.toml          # or just requirements.txt — pick one in Phase 1

frontend/
  (unchanged structure; Phase 0 rewrites types/mocks/specs only)
```

Anything not listed above is out of scope until a later phase asks for it.

---

## Phases

Each phase has: **Goal**, **Files**, **Acceptance**, **Out of scope**. Agents execute one phase per session. A phase is done only when Acceptance passes.

---

### Phase 0 — Lock the domain contract (docs + types only, no runtime code)

**Goal:** kill the semantic mismatch between frontend and the actual product. After Phase 0, every later phase has one canonical contract to build against.

**Files touched:**
- `frontend/specs/models/building.md` — rewrite input fields to: `propertyType`, `borough`, `grossFloorAreaSqft`, `yearBuilt`, `numberOfBuildings`.
- `frontend/specs/models/prediction.md` — **new file** replacing `forecast.md` and `report.md`. Mirrors the Contract above.
- Delete: `frontend/specs/models/forecast.md`, `frontend/specs/models/report.md`, `frontend/specs/pages/forecasting.md`, `frontend/specs/pages/predicting.md`, `frontend/specs/pages/report.md` — replace with a single `frontend/specs/pages/predict.md` describing the one user flow: form → loading → result.
- `frontend/src/types/models/` — delete `forecast.ts`, `report.ts`. Add `prediction.ts` matching the Contract. Keep `building.ts` but reshape fields.
- `frontend/src/mocks/data/` — rewrite fixtures to match `prediction.ts`. One happy-path fixture is enough.
- `frontend/src/mocks/handlers/` — one handler: `POST /api/predictions` returning the fixture.
- `frontend/src/hooks/` — replace `use-forecast.ts` / `use-report.ts` with a single `use-prediction.ts` exposing `usePredict()` (mutation) and `usePrediction(id)` (query).
- `frontend/src/app/forecasting/**` — rename route to `predict/`. Pages stay structurally similar (form → loading → result) but consume the new types.

**Acceptance:**
- `npm run build` passes in `frontend/`.
- `npm run dev` + clicking through the form lands on a result page populated entirely from the new fixture. No MWh, peak load, or monthly chart anywhere in the rendered output.
- `rg -i "deepgrid|peakLoadMw|monthlyConsumption|MWh"` in `frontend/src` returns zero matches.

**Out of scope:** any backend work. Any real math. Chart visual design beyond "it renders without errors."

---

### Phase 1 — Backend skeleton serving the Contract from a fixture

**Goal:** stand up a FastAPI app whose sole endpoint returns a hardcoded response matching the Contract byte-for-byte. No model, no data loading, no logic.

**Files:**
- `backend/requirements.txt` — pin at minimum: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pandas`, `numpy`, `scikit-learn`, `joblib`. (Training-only deps can go in a separate file later; for MVP one file is fine.)
- `backend/app/__init__.py`
- `backend/app/main.py` — FastAPI instance, CORS allowing `http://localhost:3000`, one router mounted.
- `backend/app/schemas.py` — Pydantic v2 models `PredictionRequest`, `PredictionResponse`, `Peer`, `Prediction`, `LL97` mirroring the Contract exactly.
- `backend/app/api/predictions.py` — `POST /api/predictions` handler. Returns `backend/app/fixtures/stub_prediction.py:STUB` with `input` echoed from the request and a fresh `id` + `generatedAt`.
- `backend/app/fixtures/stub_prediction.py` — a single Python dict matching `PredictionResponse`.
- `backend/README.md` — 10 lines: how to install and run (`uvicorn app.main:app --reload --port 8000`).

**Acceptance:**
- `cd backend && pip install -r requirements.txt` succeeds in a fresh venv.
- `uvicorn app.main:app --port 8000` starts without errors.
- `curl -X POST http://localhost:8000/api/predictions -H 'content-type: application/json' -d '{"propertyType":"Multifamily Housing","borough":"Brooklyn","grossFloorAreaSqft":45000,"yearBuilt":1925,"numberOfBuildings":1}'` returns a JSON body that validates against `PredictionResponse`.
- Validation errors return 422 with the Pydantic default body (fine for MVP).

**Out of scope:** loading `dataset.csv`, training anything, any ML library calls at runtime, persistence, auth, rate-limiting, logging beyond uvicorn defaults.

---

### Phase 2 — Wire the frontend to the real backend (still fixture data)

**Goal:** prove the contract end-to-end before any ML complexity enters. MSW becomes dev-only fallback; the dev default is the live backend.

**Files:**
- `frontend/.env.local.example` — document `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.
- `frontend/src/mocks/` — gate MSW behind an env flag (`NEXT_PUBLIC_USE_MOCKS=true`). Default off.
- `frontend/src/lib/api-client.ts` — confirm it reads `NEXT_PUBLIC_API_BASE_URL`. Adjust if path prefix drifted.
- No other changes expected. If the contract was honored in Phase 0 and Phase 1, no type edits are needed.

**Acceptance:**
- Backend running on :8000, frontend running on :3000 with `NEXT_PUBLIC_API_BASE_URL` set.
- Submitting the form triggers a real network call to `http://localhost:8000/api/predictions` (verify in browser devtools).
- The result page renders the backend's stub response. MSW is not involved.
- Setting `NEXT_PUBLIC_USE_MOCKS=true` and pointing `NEXT_PUBLIC_API_BASE_URL` at a dead URL still works via MSW.

**Out of scope:** error UI polish, retry logic, loading state changes, real predictions.

---

### Phase 3 — Training pipeline: dataset → `model.pkl` + `metrics.json`

**Goal:** one script, run from CLI, reads `backend/data/dataset.csv`, produces artifacts. Completely decoupled from the running API.

**Files:**
- `backend/training/clean.py` — `load_and_clean(csv_path) -> pd.DataFrame` with: drop rows missing Site EUI, filter `1 <= eui <= 1000`, coerce numeric columns, standardize property type and borough strings. Returns a tidy frame with columns: `property_type`, `borough`, `gross_floor_area_sqft`, `year_built`, `number_of_buildings`, `site_eui`.
- `backend/training/train_baseline.py` — CLI entry: `python -m training.train_baseline`. Does:
  1. `load_and_clean`
  2. train/test split (80/20, `random_state=42`)
  3. one-hot encode `property_type`, `borough`; pass numerics through
  4. fit `LinearRegression` on `log1p(site_eui)`
  5. evaluate on test: R², RMSE on original scale (expm1 back first)
  6. `joblib.dump` the full pipeline to `backend/artifacts/model.pkl`
  7. write `backend/artifacts/metrics.json` with `{r2, rmse, modelVersion, trainRows, testRows, trainedAt}`
- `backend/artifacts/.gitkeep`

**Acceptance:**
- `cd backend && python -m training.train_baseline` exits 0.
- `backend/artifacts/model.pkl` and `metrics.json` exist.
- `metrics.json.r2 > 0.20` on the test set. (Realistic floor. Higher is great; lower means clean.py has a bug.)
- Re-running produces identical metrics (seed is fixed).

**Out of scope:** Ridge/Lasso, feature engineering beyond one-hot, cross-validation, cohort tables (Phase 5), the API using this model (Phase 4).

---

### Phase 4 — Serve real predictions from the model

**Goal:** replace the fixture response with live inference. Percentile + LL97 fields stay hardcoded in this phase; only `prediction.*` becomes real.

**Files:**
- `backend/app/model/predictor.py` — loads `artifacts/model.pkl` at module import (fail loud if missing), exposes `predict(request: PredictionRequest) -> PredictionOutput` returning `siteEuiKbtuPerSqft`, `intervalLow`, `intervalHigh`, `modelVersion`. Interval for now: `pred ± 1.5 * rmse` pulled from `metrics.json`. Read `modelVersion` from `metrics.json` too.
- `backend/app/api/predictions.py` — call `predictor.predict(...)` instead of reading the stub's `prediction` block. Keep fixture values for `peer` and `ll97`.
- `backend/app/fixtures/stub_prediction.py` — shrink to just `PEER_STUB` and `LL97_STUB`; delete the `prediction` block.

**Acceptance:**
- Same curl as Phase 1 returns a response where `prediction.siteEuiKbtuPerSqft` changes when the input changes (e.g., doubling sqft shifts the answer).
- `prediction.modelVersion` matches `metrics.json`.
- Frontend still renders without errors.

**Out of scope:** real percentile, real fine, confidence interval from anything fancier than RMSE.

---

### Phase 5 — Real peer percentile

**Goal:** `peer.*` stops being a fixture.

**Files:**
- `backend/training/train_baseline.py` — extend to also emit `backend/artifacts/peer_cohorts.parquet`: one row per `(property_type, borough, age_band)` cohort with columns `cohort_size, median, p25, p75, eui_sorted` (the last is an array or the raw sorted numpy array, used for exact percentile lookup). Age bands: `pre-1950`, `1950-1979`, `1980-1999`, `2000-plus`.
- `backend/app/model/peer.py` — `lookup(property_type, borough, year_built, predicted_eui) -> Peer`. Falls back to broader cohort (drop borough, then drop age_band) if the narrow cohort has fewer than 30 rows. Return the cohort actually used.
- `backend/app/api/predictions.py` — call `peer.lookup(...)`.

**Acceptance:**
- For a request where the narrow cohort is populated, response's `peer.cohortSize >= 30` and `peer.percentile` is an integer in `[0, 100]`.
- Inputting an extreme EUI (force via an unusual building) shifts percentile monotonically.
- Fallback path is exercised: pick an input known to have a sparse narrow cohort (e.g., rare property type in Staten Island) and verify the returned cohort is a broader fallback.

**Out of scope:** LL97 fine, retraining cadence, cohort visualization in frontend (already has fields to render).

---

### Phase 6 — Real LL97 fine

**Goal:** `ll97.*` stops being a fixture.

**Files:**
- `backend/app/model/ll97.py` — constants for 2024–2029 and 2030–2034 caps per property type (lookup table; values pulled from NYC LL97 rule text — agent: cite the source in a comment). Function: `compute(property_type, predicted_eui, gross_floor_area_sqft) -> LL97`. Formula: `fine = max(0, (predicted_eui - cap) * sqft * 0.00268) annually` (LL97 penalty is $268 per metric ton CO2e; 0.00268 is the simplification for kBTU→tons for the MVP — leave a comment flagging this as coarse).
- `backend/app/api/predictions.py` — call `ll97.compute(...)`.
- `backend/app/fixtures/stub_prediction.py` — delete; nothing fixture-backed remains.

**Acceptance:**
- Building clearly over cap → `atRisk: true` and `projectedAnnualFineUsd2030 > 0`.
- Building clearly under cap → both fines are 0, `atRisk: false`.
- Unknown property type → 422 at request validation (enum in Pydantic). Don't silently fall through to a default cap.

**Out of scope:** true CO2e conversion from fuel mix, multi-year amortization, any UI around fine breakdown beyond the single number.

---

## After the MVP (not in this plan)

Listed only so agents don't preemptively build them:
- Ridge / Lasso / log-transform feature engineering (rerun Phase 3, bump `modelVersion`)
- PDF export (`ExportDialog` is a stub today — leave it)
- Auth, user accounts, saved predictions
- Multi-city (Chicago, Seattle) — domain shift story
- Residual analysis UI
- A `/api/metrics` endpoint exposing model health

---

## Agent rules

1. **One phase per session.** Don't blend. If you finish Phase N early, stop — don't start N+1.
2. **Don't scaffold files a future phase owns.** If the file isn't listed in your phase, don't create it.
3. **The Contract is canonical.** If reality forces a change, edit the Contract section first, then propagate. Don't let backend and frontend drift.
4. **No new dependencies without justification in the phase's PR description.** If you add a library, say why the phase needs it.
5. **Acceptance is a checklist, not a vibe.** Run each bullet. If one fails, the phase isn't done.
6. **If a phase is blocked by ambiguity, stop and ask the human. Don't guess.**
