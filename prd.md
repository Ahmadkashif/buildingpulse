# BuildingPulse — LL97 Compliance Report & Lead Funnel

## Problem Statement

NYC's Local Law 97 caps building emissions starting 2024 and tightens those caps roughly 3× in 2030. Industry consensus puts 60–80% of covered buildings (>25k sqft) over the 2030 caps without retrofits. Building owners and property managers are aware the deadline is coming but don't have a credible, friction-free way to put a dollar number on their personal exposure — most existing free LL97 calculators stop at "you may be at risk."

On the other side, the firms that *fix* this problem — ESCOs, MEP engineers, heat-pump installers, envelope contractors, decarbonization consultants — have no efficient way to source warm leads of buildings that are knowingly at risk. Retrofit projects run $100K–$5M; their cost-per-acquisition tolerance is high, but the lead supply is fragmented.

The current BuildingPulse MVP predicts Site EUI, peer percentile, and a projected LL97 fine for a single building, but the experience ends at the diagnostic. There is no lead capture, no retrofit guidance, no co-branding for a sponsor, and no way for a contractor to plug this into their outbound funnel. The report is informative but commercially inert.

## Solution

A free, public, single-page experience where a NYC building owner enters a small set of building specs (or an address) and receives a credible LL97 risk report: predicted EUI, peer cohort placement, fine projections for 2024–2029 and 2030–2034, and a compliance timeline.

The diagnostic half of the report is anonymous and ungated — it earns trust. The action half — downloadable PDF, retrofit scenarios that recompute the fine under different interventions, and a "Talk to a contractor" CTA — sits behind a one-step lead capture (name, email, phone, role). Captured leads are routed to a single configured sponsor partner.

The page carries a co-branded sponsor slot (logo, name, CTA URL) configured at deploy time. Each report has a stable shareable URL so it propagates inside a building owner's organization. The MVP serves a single sponsor; multi-tenant white-label is deliberately out of scope.

The unit economics are asymmetric: a report costs cents of compute, a qualified retrofit lead with a quantified fine number is worth $50–$500 to the right contractor.

## User Stories

1. As a NYC building owner, I want to type my building's basics into a single form, so that I can see whether I am exposed to LL97 fines without paying a consultant.
2. As a NYC building owner, I want the form to optionally accept my building's street address, so that I do not have to look up sqft and year built myself.
3. As a NYC building owner, I want to see a predicted Site EUI with a confidence range, so that I understand the prediction is an estimate and not a promise.
4. As a NYC building owner, I want to see how my predicted EUI compares to peer buildings of the same type, borough, and age, so that I have intuitive context for whether my number is bad.
5. As a NYC building owner, I want to see a clear at-risk / not-at-risk verdict, so that I know in five seconds whether I need to act.
6. As a NYC building owner, I want to see fine projections for both the 2024–2029 period and the 2030–2034 period, so that I can plan around the cliff.
7. As a NYC building owner, I want to see a timeline chart of how my fine grows over time, so that I emotionally feel the urgency rather than just reading two numbers.
8. As a NYC building owner, I want the diagnostic part of the report to render without filling in any contact information, so that I can evaluate the tool's credibility before trusting it with my email.
9. As a NYC building owner, I want a clear "Download PDF report" action, so that I can forward the report to my owner, board, or asset manager.
10. As a NYC building owner, I want a clear "See retrofit options that fix this" action, so that the tool tells me what to do, not just what's wrong.
11. As a NYC building owner, when I click into retrofit scenarios, I want to see a small set of named interventions (e.g., heat pump conversion, envelope upgrade, controls/BMS upgrade) each with an estimated EUI reduction and rough cost band, so that I can compare my options at a glance.
12. As a NYC building owner, I want each retrofit scenario to recompute my projected fine, so that I can see the dollar payoff of each intervention.
13. As a NYC building owner, I want one form to capture my name, email, phone, and role before I unlock retrofit scenarios and the PDF, so that the price of the actionable content is just my contact info.
14. As a NYC building owner, I want a single primary "Talk to a contractor" CTA at the end of the report, so that if I want help I have one obvious next step.
15. As a NYC building owner, I want each report to have a stable shareable URL, so that I can send the link to colleagues without losing the result.
16. As a NYC building owner, I want the report to cite its data source (NYC LL84 Energy and Water Disclosure) and show which model version produced the prediction, so that I trust the numbers.
17. As a NYC building owner, I want the report to display the sponsor's logo and name as a co-brand, so that I understand who is offering this service for free.
18. As a NYC building owner, I want validation errors on bad input (e.g., sqft of zero) to be returned with a clear message, so that I can correct the form without guessing.
19. As a sponsor partner / contractor, I want the report to display my logo, name, and CTA URL prominently, so that the funnel is unambiguously branded as mine.
20. As a sponsor partner / contractor, I want every captured lead to include the lead's contact information, the prediction id, the building specs, the predicted EUI, the projected fine, the at-risk verdict, and the report URL, so that my sales team can prioritize and personalize outreach immediately.
21. As a sponsor partner / contractor, I want leads delivered to a single configured destination (an email address and/or webhook), so that they flow into my existing CRM without bespoke integration.
22. As a sponsor partner / contractor, I want the lead capture step to require name, email, and phone, so that my sales team can reach the prospect by either channel.
23. As a sponsor partner / contractor, I want the system to record which retrofit scenario (if any) the lead expressed interest in, so that my sales team can lead with the relevant pitch.
24. As an operator of the system, I want sponsor branding (logo URL, name, CTA URL, lead destination) configured via environment variables at deploy time, so that I can swap sponsors without a code change.
25. As an operator of the system, I want each lead capture event to be persisted server-side with a timestamp, so that I have an authoritative record independent of the partner's CRM.
26. As an operator of the system, I want the prediction model and the LL97 cap table to be loaded once at process start, so that report generation stays fast.
27. As an operator of the system, I want the LL97 cap values and the retrofit scenario library to live in code-reviewed configuration files with cited sources, so that reviewers can audit the numbers behind the report.
28. As a developer, I want the LL97 fine calculator, the retrofit scenario engine, the peer cohort lookup, and the address resolver to be pure modules with explicit inputs and outputs, so that I can test each in isolation without standing up the full app.

## Implementation Decisions

### Architecture

The MVP plan in `MVP_PLAN.md` already establishes the request/response contract for a single building prediction. This PRD extends that contract — it does not replace it. Phases 0–6 of the MVP plan remain the foundation; the work below adds onto Phase 6 and beyond.

The system stays a stateless FastAPI backend + Next.js frontend, with two new server-side concerns: lead persistence and partner notification. No auth, no user accounts.

### Backend modules

- **LL97 calculator** — pure function. Inputs: property type, predicted EUI, sqft. Outputs: cap for each compliance period, projected annual fine for each period, at-risk boolean, full year-by-year fine series for the timeline chart. Caps and emissions coefficients live in a configuration file with cited LL97 rule references. This is an extension of the `ll97.py` module already specified in MVP Phase 6.
- **Retrofit scenario engine** — pure function. Inputs: property type, baseline predicted EUI, sqft. Outputs: a list of canned interventions, each with a name, a description, an estimated EUI reduction percentage, a rough installed-cost-per-sqft band, a recomputed projected fine using the LL97 calculator, and a citation for the reduction range. The library is small (3–5 interventions per property type) and lives as static data in a code-reviewed file. The engine itself takes that data as a dependency, so the data can be swapped without changing the logic.
- **Address resolver** — pure function with one I/O dependency (an LL84 lookup table built at training time, shipped as a parquet/csv artifact). Inputs: a free-form address string or BBL. Outputs: building basics (property type, borough, sqft, year built, number of buildings) and, when present in LL84, a measured Site EUI that the UI can show alongside the prediction. Returns a clear "not found" result rather than guessing. This module is optional in v1 and can ship behind a feature flag if the LL84 join proves messy.
- **Lead capture service** — single module exposed to the API layer. Inputs: contact info, prediction id, optional retrofit scenario id. Side effects: persist a lead row, dispatch a notification to the configured sponsor destination (email and/or webhook). The notification payload is the full lead context defined in the user stories. The dispatch step is fire-and-forget from the user's perspective; failures are logged but do not block the API response.
- **Lead store** — minimum viable persistence. SQLite file in the backend container is acceptable for v1. The schema captures: lead id, prediction id, name, email, phone, role, scenario id, sponsor id, timestamp, and the predicted fine snapshot at capture time.
- **Predictor and peer cohort lookup** — already specified in MVP Phases 4–5. No changes.

### API contract additions

- The existing `POST /api/predictions` and `GET /api/predictions/:id` remain the source of the diagnostic half of the report. Their response shape stays as defined in `MVP_PLAN.md` plus a new `ll97.fineSeries` field — an array of `{ year, projectedAnnualFineUsd }` rows from the current year through 2034 — so the timeline chart has data without a second call.
- New endpoint: `GET /api/predictions/:id/scenarios`. Returns the retrofit scenario list for that prediction's property type and sqft, with each scenario's recomputed fine. Read-only, ungated server-side; the gating is a UX concern, not a security concern.
- New endpoint: `POST /api/leads`. Body: prediction id, contact fields (name, email, phone, role), optional scenario id, sponsor id (echoed from the page's deploy config). Returns 201 with a lead id. Idempotency by (prediction id + email) is good enough; duplicate submissions overwrite the prior row's contact info and re-fire the partner notification.
- New endpoint: `GET /api/sponsor`. Returns the active sponsor's display fields (id, name, logo URL, CTA label, CTA URL) sourced from environment variables. The frontend reads this once on page load.
- The PDF "download" action calls `GET /api/predictions/:id/pdf`. Server renders the same report as HTML and converts to PDF. The PDF endpoint returns 403 unless a lead exists for that prediction id; that is the gating mechanism.

### Sponsor configuration

Sponsor identity is supplied via environment variables read at process start: sponsor id, display name, logo URL, primary CTA label and URL, lead notification email, optional lead webhook URL. Changing sponsors is a redeploy, not a code change. There is exactly one active sponsor per deployment.

### Frontend modules

- **Form page** — extend the existing `/forecasting` form with an optional "Look up by address" affordance. When the address resolver returns a hit, the rest of the form fields auto-fill but stay editable. When it returns a miss, the form falls back to the current manual flow. No new pages.
- **Result page** — extend the existing `/forecasting/report/[id]`:
  - Add a compliance timeline chart driven by `ll97.fineSeries`.
  - Replace the existing "View Retrofit Options" stub with a real action that opens a lead-capture modal on first click, then on success expands an inline retrofit scenarios section fetched from `GET /api/predictions/:id/scenarios`.
  - Replace the export PDF stub with the gated PDF endpoint above; gating UX runs through the same lead-capture modal.
  - Add a co-brand strip (sponsor logo + name) at the top of the page, and a primary "Talk to a contractor" CTA at the bottom that deep-links to the sponsor CTA URL with the prediction id appended as a query param.
- **Lead capture modal** — single shared component. Posts to `POST /api/leads`. On success, unlocks PDF download and retrofit scenarios for the current session via local state; the gate is purely UX since a determined visitor could still call the API directly (acceptable for v1 — abuse risk is low and the retrofit data is not commercially sensitive).
- **Sponsor slot component** — reads from `GET /api/sponsor` once and renders the co-brand strip and the final CTA.
- **Retrofit scenarios card** — renders the list from the scenarios endpoint. Each scenario shows its name, EUI reduction, cost band, recomputed fine, and a "Choose this scenario" button that re-opens the lead capture modal pre-filled with the scenario id.

### Out-of-band concerns

- **Email delivery** for partner notifications uses a single transactional provider (e.g., SES or Postmark) configured via env vars. No template management; the email body is a server-rendered text block.
- **Rate limiting** is intentionally out of scope for v1. The form is public and free, and abuse risk for a free LL97 estimator is low.
- **Analytics** — page view, form submit, lead capture, scenario click, CTA click are tracked via a single client-side event sink (env-configured). No server-side analytics in v1.

## Testing Decisions

The bar for "good test" on this project: tests that exercise the **external behavior** of a module — given inputs, assert outputs and side effects — and avoid asserting implementation details (no mocking internal helpers, no asserting that a private method was called, no snapshotting opaque structures). When a test fails, a reviewer should be able to read it and understand which user-visible behavior broke.

Modules that get tests in this PRD:

- **LL97 calculator.** Unit tests over a fixture of building shapes covering: clearly under cap (verdict false, both fines zero, full series zero), straddling 2030 cap (verdict true, 2024 fine zero, 2030 fine positive, series shows the cliff at 2030), clearly over both caps (verdict true, both fines positive, monotonic series), unknown property type (raises). Caps and coefficients are loaded from the production config file in tests, not redefined in fixtures, so a config drift breaks the tests.
- **Retrofit scenario engine.** Unit tests asserting: every scenario for a given property type has a valid reduction percentage, every scenario's recomputed fine is less than or equal to the baseline fine for an at-risk building, scenarios are returned in a stable order, the engine is pure (calling it twice with the same inputs returns equal outputs). One end-to-end fixture per property type pinned in the test data.
- **Address resolver.** Unit tests against a small frozen LL84 fixture covering: known address returns full record, ambiguous address returns the closest match with a confidence flag, unknown address returns a clean miss, malformed input returns a validation error. The fixture is a tiny parquet file in `backend/tests/fixtures/`.
- **Lead capture service.** Tests assert: a successful capture writes a row to the lead store and fires a notification with the documented payload, a notification dispatch failure logs but does not raise, idempotent re-submission for the same (prediction id, email) updates the row and re-fires the notification. The notification dispatcher is the module's seam — tests substitute a recording fake at that boundary, not at any point further inside.
- **API endpoints** for `POST /api/leads`, `GET /api/predictions/:id/scenarios`, `GET /api/sponsor`, and `GET /api/predictions/:id/pdf`. Integration tests using FastAPI's test client. Assertions cover the contract defined above: status codes, response shapes, the gating rule (PDF is 403 without a lead, 200 with one), and validation errors on bad request bodies.

Modules that **do not** get isolated tests: the React form components, the modal component, the chart components, the sponsor slot. Their behavior is covered indirectly by an end-to-end smoke test that drives the full happy path with a real backend and asserts that the result page renders the predicted EUI, the timeline chart, the gated retrofit section, and the sponsor strip. No component-level snapshot tests.

Prior art in the repo: the Phase 1 tests added in commit `12dc663` and described in `TESTING.md` already establish the FastAPI + pytest pattern. The new tests follow that same shape — pytest, real FastAPI test client for endpoint tests, plain function calls for module tests — so reviewers do not have to learn a second style.

## Out of Scope

- Multi-building / portfolio uploads. A property manager pasting 30 BBLs and getting an aggregated portfolio risk report is the obvious v2; it is not in v1.
- White-label multi-tenant deployment. v1 serves exactly one sponsor per deployment, configured via env vars. Per-request sponsor resolution, sponsor onboarding flows, and per-sponsor lead routing rules are out.
- True CO2e conversion from the building's actual fuel mix. The MVP uses a coarse kBTU-to-tons coefficient, with the simplification flagged in code and on the report itself.
- LL84 benchmarking submission help. The system reads from LL84; it does not help owners file LL84.
- Authenticated user accounts, saved reports, history, billing. Reports are anonymous and addressed only by URL.
- Real-time integrations into named CRMs (Salesforce, HubSpot). v1 ships with email + webhook only; named CRM connectors are a v2 ask.
- Payment infrastructure for paid leads (Stripe, lead marketplace, attribution). v1 assumes a single bilateral commercial agreement with one sponsor; the platform records the leads but does not invoice for them.
- Ridge / Lasso / advanced feature engineering on the prediction model. Model improvements continue on the cadence defined in the MVP plan and bump `modelVersion`; they do not block this PRD.
- Full retrofit project costing. The cost bands shown alongside scenarios are public-source ranges, not bespoke estimates. Bespoke estimating is the sponsor partner's job, not the report's.

## Further Notes

- **Why the diagnostic half stays ungated.** Trust is the conversion variable. Three free LL97 calculators already exist; gating the verdict behind a contact form makes us the worst of them. Gating the *action* (PDF, retrofit scenarios, contractor CTA) at the moment of highest urgency is the right trade.
- **Why retrofit scenarios are canned, not modeled.** The MVP's predictor is a linear regression on a handful of features — it has no causal claim about retrofit impact. A canned library with cited reduction ranges is more honest than a model pretending to optimize a portfolio. The library is configuration data; future versions can replace it without changing the engine.
- **Why one sponsor per deployment.** Multi-tenant white-label is an order of magnitude more product surface (sponsor onboarding, per-sponsor branding, per-sponsor lead routing, per-sponsor analytics). The single-sponsor v1 ships in weeks and proves the funnel works before that surface gets built.
- **Risk to flag for the operator.** The retrofit scenario data and the LL97 cap table are commercial inputs to a public-facing report. Any change to either should go through code review with a citation in the diff, the same as any other production config.
- **Path to revenue.** v1 establishes the funnel mechanics under one bilateral sponsor deal. v2 (out of scope here) opens up: portfolio uploads → higher-LTV leads, multi-tenant white-label → recurring SaaS, per-sponsor lead routing → marketplace dynamics. None of those make sense to build before the single-sponsor funnel is proven.

---

## Technical Specifications — Backend Architecture

This section is reference material. The goal is a codebase that protects itself: layered, machine-enforced, and structured so AI agents have one obvious correct place to put any given line of code.

### Directory layout

```
backend/
  app/
    main.py                          # FastAPI factory + lifespan
    config.py                        # AppConfig dataclass — env loaded once
    deps.py                          # FastAPI Depends() providers (DI wiring)
    errors.py                        # domain exceptions → HTTP mapping

    api/v1/
      predictions/controller.py
      leads/controller.py
      scenarios/controller.py
      sponsor/controller.py
      pdf/controller.py

    schemas/
      requests.py                    # Pydantic — API boundary only
      responses.py

    services/
      resource/                      # Leaf services. One resource each.
        prediction/service.py        # PredictionResourceService
        lead/service.py              # LeadResourceService
        sponsor/service.py           # SponsorResourceService
        scenario/service.py          # ScenarioResourceService
        notification/service.py      # NotificationResourceService (wraps email + webhook)
      usecase/                       # Orchestrators. Compose resource services.
        lead_capture/service.py      # LeadCaptureUseCaseService
        pdf_generation/service.py    # PdfGenerationUseCaseService

    domain/                          # Pure logic. No I/O. No frameworks.
      ll97/         calculator.py, types.py
      retrofits/    engine.py, types.py
      peer/         lookup.py, types.py
      prediction/   predictor.py, types.py
      address/      resolver.py, types.py

    repos/
      lead_repo.py                   # SQLite owner — only file that runs SQL
      artifact_registry.py           # loads model.pkl, parquet, policy at startup

    integrations/
      email_dispatcher.py
      webhook_dispatcher.py

    policy/                          # Python constants. Reviewed config data.
      ll97_caps.py                   # Pydantic-validated frozen dataclasses + citations
      retrofits.py                   # Retrofit library, same shape

    artifacts/                       # Built by training/. Read at runtime. .gitkeep only.

  training/                          # Offline. NOT importable by app/.
    clean.py
    train_baseline.py
    build_peer_cohorts.py
    build_ll84_index.py

  data/                              # Source datasets (CSV/parquet inputs).
  tests/
    unit/domain/                     # Pure. No fakes. Milliseconds.
    unit/services/                   # Fake repos + integrations (resource); fake resources (usecase).
    integration/api/                 # FastAPI test client end-to-end.
    fixtures/

  pyproject.toml
  .importlinter                      # Layering enforcement — see contracts below.
  CLAUDE.md                          # Backend root rules.
  app/<each-layer>/CLAUDE.md         # Per-layer "what belongs here" docs.
```

### Naming conventions

The path encodes the resource. The filename encodes the role. Both are signal for agents.

- Controllers live at `api/v1/<resource>/controller.py`. Class: `<Resource>Controller`. Each file owns exactly one router.
- Resource services live at `services/resource/<resource>/service.py`. Class: `<Resource>ResourceService`.
- Use-case services live at `services/usecase/<usecase>/service.py`. Class: `<UseCase>UseCaseService`.
- Repos live at `repos/<resource>_repo.py`. Class: `<Resource>Repo`.
- Integrations live at `integrations/<role>_dispatcher.py`. Class: `<Role>Dispatcher`.
- Domain modules use role-named files: `calculator.py`, `engine.py`, `lookup.py`, `resolver.py`, `predictor.py`, `types.py`. No `<thing>_calculator.py` — the parent folder names the thing.

Every package has an explicit `__all__` in its `__init__.py`. Symbols not listed are package-private and may not be imported across packages.

### Layering rules

```
api          → services, schemas, deps, errors, domain.types
services     → domain, repos, integrations, policy, schemas
  resource   → repos, integrations, domain, policy
  usecase    → services.resource, domain, policy
repos        → domain.types, policy        (+ stdlib, third-party)
integrations → domain.types                (+ stdlib, third-party)
domain       → policy                      (+ stdlib, third-party)
policy       → (stdlib, third-party only)
schemas      → domain.types                (+ stdlib, third-party)
training     → may import domain, policy. NEVER imports from app.api / app.services / app.repos / app.integrations.
```

Domain having zero edges into the rest of `app/` is the load-bearing invariant. It is what keeps the LL97 calculator, the retrofit engine, the peer lookup, the predictor, and the address resolver pure and unit-testable forever.

### import-linter contracts (`.importlinter`)

```ini
[importlinter]
root_package = app

[importlinter:contract:layers]
name = Layered architecture
type = layers
layers =
    app.api
    app.services
    app.repos | app.integrations
    app.domain
    app.schemas | app.policy

[importlinter:contract:resource-leaves]
name = Resource services do not import each other
type = independence
modules =
    app.services.resource.prediction
    app.services.resource.lead
    app.services.resource.sponsor
    app.services.resource.scenario
    app.services.resource.notification

[importlinter:contract:usecases-compose-resources-only]
name = Use-case services may not import repos or integrations directly
type = forbidden
source_modules =
    app.services.usecase
forbidden_modules =
    app.repos
    app.integrations

[importlinter:contract:resources-below-usecases]
name = Resource services may not import use-case services
type = forbidden
source_modules =
    app.services.resource
forbidden_modules =
    app.services.usecase

[importlinter:contract:domain-pure]
name = Domain has no app-internal dependencies
type = forbidden
source_modules =
    app.domain
forbidden_modules =
    app.api
    app.services
    app.repos
    app.integrations
    app.schemas

[importlinter:contract:sql-confined]
name = SQL drivers may only be imported by the repos layer
type = forbidden
source_modules =
    app.api
    app.services
    app.domain
    app.integrations
    app.schemas
    app.policy
forbidden_modules =
    sqlite3
    sqlalchemy

[importlinter:contract:training-isolated]
name = Training pipeline does not import the running app
type = forbidden
source_modules =
    training
forbidden_modules =
    app.api
    app.services
    app.repos
    app.integrations
```

`lint-imports` runs in CI on every PR. A violation fails the build.

### Per-layer CLAUDE.md files

Each layer ships a 10–20 line `CLAUDE.md` describing what belongs in that directory and what may be imported. Minimum set:

- `backend/CLAUDE.md` — the layering diagram + a pointer to `.importlinter`.
- `app/api/CLAUDE.md` — controllers are thin: parse, validate, call one service, shape response. No `if` branching on business rules.
- `app/services/resource/CLAUDE.md` — resource services do not import each other. They own one resource's verbs, hold their repo + integration deps, return domain types.
- `app/services/usecase/CLAUDE.md` — use-case services compose resource services. Never import repos or integrations directly.
- `app/domain/CLAUDE.md` — pure functions and dataclasses. No FastAPI, no SQL, no `open()`, no `os.environ`.
- `app/repos/CLAUDE.md` — only place SQL runs. Connection lifecycle owned here.
- `app/integrations/CLAUDE.md` — outbound external calls only. Failures are logged, not raised, unless the calling service explicitly awaits a result.
- `app/policy/CLAUDE.md` — frozen, code-reviewed config data. Every constant has a citation comment.

### Service split — resource vs. use-case

| Service kind | Owns | May import | Tested by |
| --- | --- | --- | --- |
| Resource (`<R>ResourceService`) | one resource's verbs (CRUD-ish) | repos, integrations, domain, policy | unit test with fake repo + fake integration |
| Use-case (`<U>UseCaseService`) | a workflow that touches >1 resource | resource services, domain, policy | unit test with fake resource services |

**Hard rule:** if a controller or use-case ever needs methods from two resource services in the same flow, the flow must live in a use-case service. Controllers never compose two resource services. The `resource-leaves` and `usecases-compose-resources-only` contracts are what enforce this.

**`NotificationResourceService`** wraps both `EmailDispatcher` and `WebhookDispatcher`. This keeps the rule "use-cases compose resources, resources own I/O" intact — `LeadCaptureUseCaseService` does not reach into `integrations/`.

### Policy modules (Python over YAML)

LL97 caps and the retrofit scenario library live as Pydantic-validated frozen dataclasses in `app/policy/`. Citations live in docstrings above the constants. Reasons:

- Type checker catches typos before PR open.
- Adding a new property type lights up every exhaustiveness site.
- No silent missing-key bugs — Pydantic raises on construction at import time.
- Diffs read identically to YAML diffs for reviewers.

### Domain types (the contracts that hold deep modules together)

These are the dataclasses that flow between domain modules. Defined once in each module's `types.py`, immutable (`frozen=True`), no methods that touch I/O.

- `domain/prediction/types.py` — `BuildingInput`, `EuiPrediction { value, low, high, modelVersion }`.
- `domain/peer/types.py` — `PeerCohort { propertyType, borough, ageBand }`, `PeerOutlook { cohort, cohortSize, median, p25, p75, percentile }`.
- `domain/ll97/types.py` — `Ll97Outlook { capCurrent, capFuture, fineCurrent, fineFuture, fineSeries, atRisk }`, `FineYear { year, projectedAnnualFineUsd }`.
- `domain/retrofits/types.py` — `RetrofitScenario { id, name, description, euiReductionPct, costPerSqftLow, costPerSqftHigh, recomputedFine, citation }`.
- `domain/address/types.py` — `Ll84Match { confidence, building: BuildingInput, measuredEui: float | None }`, `Ll84Miss`.

Schemas in `app/schemas/responses.py` are thin adapters over these — they exist to add JSON-friendly field names and the `id`/`generatedAt` envelope. Domain types never know they're being serialized.

### Database boundary (v1 → v2)

- v1 uses SQLite at a path configured via `AppConfig`. Single-instance deploy. `lead_repo.py` is the only file that imports `sqlite3`.
- The moment the deployment goes multi-instance, lead capture races. Migration to Postgres is a known boundary, not a surprise. The `sql-confined` contract ensures the migration touches exactly one file.
- No ORM in v1. Hand-written SQL with parameterized queries. Schema lives in `repos/migrations/` as numbered `.sql` files; a `lifespan` hook runs pending migrations on startup.

### Dependency injection

- `AppConfig` and `ArtifactRegistry` are the only process-wide singletons. Both built in `main.py`'s lifespan.
- All other services are instantiated per-request via FastAPI `Depends` providers in `app/deps.py`.
- This kills the "passes alone, fails in suite" failure mode and means every service can be tested by passing fakes to its constructor.

### Frontend ↔ backend interface

- The wire contract is what the OpenAPI schema produced by FastAPI says it is. The frontend generates its types from that schema (codegen step in CI), so the two cannot drift silently.
- `frontend/src/types/models/` is generated; hand-edits to those files are reverted by CI. The frontend's domain shapes live elsewhere if any reshaping is needed.
- All API responses are wrapped: `{ data: <Resource> }` or `{ error: { code, message, field? } }`. Validation errors are 422 with the `error` envelope and a `field` pointer.

### What this architecture defends against

| Failure mode | Caught by |
| --- | --- |
| Controller running SQL | `layers` contract + `sql-confined` contract |
| Domain importing FastAPI | `domain-pure` contract |
| Resource service depending on another resource | `resource-leaves` contract |
| Use-case service reaching into a repo | `usecases-compose-resources-only` contract |
| Training script reading prod app state | `training-isolated` contract |
| Frontend type drifting from backend | OpenAPI codegen + CI revert check |
| Silent missing key in config | Pydantic policy load fails at startup |
| "Passes alone, fails in suite" tests | No singletons except `AppConfig` + `ArtifactRegistry` |
| Unspecified public surfaces | Explicit `__all__` per package |

---

## Technical Specifications — Operational + Resolved Decisions

This section is the output of the grilling pass. Each line is a locked decision that the architecture and the implementation phases must honor.

### Project posture
- v1 is a **learning vehicle that demos well**. Every external seam (email, webhook, sponsor) ships as a clean stub with the same interface a production version would expose. No real partner integrations.
- Observability, request tracing, audit logging, CI checks, and unit testing are **non-negotiable** even at this posture.

### Telemetry stack
- **OpenTelemetry** for traces and metrics; **structlog** for application logs that reference the active `trace_id`.
- Setup is folded into `app/deps.py` — no separate `app/observability/` package.
- Dev exporter: console. Future deploy exporter: OTLP to **Grafana Tempo** (traces), **Loki** (logs), **Prometheus/Mimir** (metrics).
- New `import-linter` rule (an eighth contract): only `app/deps.py` and `app/main.py` may import `opentelemetry`.

### Audit logging
- Dedicated `AuditService` (resource service) at `services/resource/audit/service.py`, backed by `AuditRepo` at `repos/audit_repo.py`, persisting to a single `audit_log` table in the same SQLite database.
- Events typed as a Pydantic discriminated union: `PredictionGenerated | LeadCaptured | PartnerNotificationDispatched | PartnerNotificationFailed | ScenarioSelected | PdfGenerated | SponsorCtaFollowed`.
- Recording is **explicit** — use-case services call `await self.audit.record(LeadCaptured(...))` at the audit point. No decorators, no auto-instrumentation.
- Schema columns: `id`, `event_type`, `occurred_at`, `request_id`, `trace_id`, `prediction_id` (nullable), `lead_id` (nullable), `actor_session_id`, `payload_json`. PII appears only in `LeadCaptured.payload_json`.

### CI gates (all required to merge)
1. **Static**: `ruff` (lint + format), `mypy --strict` on `app/`, `lint-imports` (eight contracts).
2. **Unit**: `pytest tests/unit/` — domain pure, services with fakes. Coverage rubric below.
3. **Integration**: `pytest tests/integration/api/` — FastAPI test client against in-memory SQLite with migrations applied per session.
4. **E2E smoke**: Playwright, single happy-path spec, runs against a docker-compose'd backend.
5. **Schema drift**: CI dumps OpenAPI from FastAPI, diffs against committed `backend/openapi.json`; CI runs `openapi-typescript` and diffs against committed `frontend/src/types/api.ts`. Either drift fails the build.
6. **Mutation**: `mutmut run --paths-to-mutate app/domain` — mutation score ≥ 90% on `app/domain/**`. Mutation testing is constrained to the domain layer because it is too slow to run repo-wide; the domain layer is also the layer where assertion strength matters most.
- Single `.github/workflows/ci.yml`, jobs run in parallel.
- Mirror commands available locally via `Makefile`: `make check`, `make test`, `make e2e`, `make schema`, `make mutate`.

### Coverage rubric (per layer)

The gate replaces a single "≥85% global" threshold with per-layer targets. Coverage chasing is a known anti-pattern; the rubric below is structured so that any number below the target reflects an untested *behavior*, not untested glue.

| Layer | Target | Measurement | Notes |
| --- | --- | --- | --- |
| `app/domain/**` | **100% branch coverage** + mutation score **≥ 90%** | `pytest --cov-branch` + `mutmut` | Pure modules. The most expensive bar; this is where confidence lives. |
| `app/policy/**` | **100% statement coverage** | `pytest --cov` | A single load test per policy module forces every constant + Pydantic validator. |
| `app/services/usecase/**` | **100% branch coverage** | `pytest --cov-branch` with fakes for resource deps | Orchestration logic — every branch matters. |
| `app/services/resource/**` | **100% branch coverage** | `pytest --cov-branch` with fakes for repo + integration deps | One leaf service per resource. |
| `app/repos/**` | **100% line coverage** | `pytest --cov` via integration tests against in-memory SQLite | Each query path covered. |
| `app/integrations/**` | **100% line coverage** | `pytest --cov` with fakes at the third-party SDK boundary | The dispatcher seam. |
| `app/api/v1/**/controller.py` | **100% branch coverage via integration tests only** | `pytest --cov-branch` on `tests/integration/api/` | Do **not** unit-test controllers. The FastAPI test client is the right tool. |
| `app/schemas/**` | **100% statement coverage** | round-trip request/response tests force every field | |
| `app/main.py`, `app/deps.py` | **Excluded** from coverage report | `[tool.coverage.run] omit=` + `# pragma: no cover` | DI wiring is covered transitively by integration tests; unit-testing it produces coupled tests. |
| `frontend/src/hooks/**` | **100% branch coverage** | `vitest --coverage` | |
| `frontend/src/lib/**` | **100% branch coverage** | `vitest --coverage` | |
| `frontend/src/components/forms/**`, `**/modal/**` | **100% interaction coverage** | Vitest + Testing Library — every button, every validation path | |
| `frontend/src/components/ui/**` (presentational primitives) | **excluded** | n/a | No behavior to test; covered by Playwright via the pages that use them. |
| `frontend/src/app/**/page.tsx` | covered by Playwright happy path | E2E only | |
| `frontend/src/types/api.ts` | **excluded** (generated) | omit | |
| `frontend/src/mocks/**` | **excluded** (test infra) | omit | |

Every issue's acceptance criteria includes a "coverage targets met per the rubric" checkbox. CI's coverage report fails the build if any non-excluded module falls below its target.

### Persistence
- **SQLite v1.** Single file at `${DB_PATH:-./var/buildingpulse.db}`. `var/` is gitignored.
- **Migrations**: hand-rolled. Numbered `.sql` files under `app/repos/migrations/` (e.g., `0001_create_leads.sql`, `0002_create_audit_log.sql`). Runner is `app/repos/migrations.py`, ~30 lines, invoked from `main.py` lifespan, tracks applied versions in a `schema_migrations` table.
- **Connection**: `app/repos/connection.py` is the sole sqlite3 importer. PRAGMAs applied on open: `foreign_keys = ON`, `journal_mode = WAL`.
- **Test DB**: pytest fixture builds an in-memory `:memory:` connection, runs migrations once per session.
- **Retention**: v1 keeps everything forever. Right-to-delete is acknowledged in `backend/CLAUDE.md` as v2.

### PDF rendering
- **WeasyPrint.** Server-rendered HTML → PDF. Lives in `services/usecase/pdf_generation/`. No system binaries beyond what wheels provide.

### Frontend type generation
- **`openapi-typescript`.** Generates `frontend/src/types/api.ts` from `backend/openapi.json`. Types-only — `lib/api-client.ts` keeps its current `fetch` shape.
- Generated file is committed; CI re-runs the generator and fails on drift.

### E2E framework
- **Playwright.** One spec covering: form submit → loading → result page renders KPIs + chart + sponsor strip → lead modal → PDF download → scenario click → sponsor CTA redirect (mocked sponsor URL).

### Address resolver
- Module ships in v1 (`domain/address/resolver.py`) with full unit tests and a `training/build_ll84_index.py` pipeline producing `artifacts/ll84_index.parquet`.
- UI is hidden behind feature flag `ADDRESS_LOOKUP_ENABLED` (default `false`). Flipping the flag enables the form's "Look up by address" affordance.

### Compliance timeline
- `Ll97Outlook.fineSeries` is one row per year from current year through 2034: `[{year: int, projectedAnnualFineUsd: number}]`.
- Values are flat within each compliance period (2024–2029, 2030–2034). The chart renders a step function with the cliff at 2030.
- Post-2034 rows are not emitted; future caps are TBD by NYC.

### LL97 cap mapping
- `policy/ll97_caps.py` defines a `dict[PropertyType, OccupancyMapping]`. Each mapping picks one LL97 occupancy group as the canonical match (median tier where multiple sub-tiers exist), with a docstring citation per entry.
- The report carries a footnote: "Estimate based on the dominant occupancy class. Multi-occupancy buildings may have different exposure."

### Retrofit scenarios
- Shown for **all reports**, not just at-risk. Headline copy adapts based on `atRisk`.
- Math: `recomputedEui = baselineEui × (1 - reductionPct)` → `Ll97Calculator.compute(...)` → recomputed `fineSeries`. The retrofit engine has a one-way dependency on the LL97 calculator inside `domain/`.
- "Choose this scenario" behavior: if a lead exists in the session, record `ScenarioSelected` and redirect to sponsor CTA. Otherwise, open the lead modal pre-filled with the `scenario_id`.

### Lead capture
- **Idempotency**: 1-hour window per `(prediction_id, email)`. Within window, update the row but do not re-fire the partner notification. Outside window, treat as a new lead. Window length is a constant in `policy/`.
- **Consent**: a single required checkbox — "I agree to be contacted by [Sponsor Name] about this report." Stored as `consent_given_at` timestamp on the lead row. Granular GDPR text is v2.
- **Gating**: PDF endpoint returns `403` unless a lead exists for the prediction id (server-enforced). Scenarios endpoint is server-ungated; gating is UX-only.
- **Failures**: notification dispatch failures are recorded as `PartnerNotificationFailed` audit events and logged; the API still returns `201`.

### Sponsor handoff
- All sponsor display fields (id, name, logo URL, CTA label, CTA URL, lead-notification email, optional lead-webhook URL) are env-configured at deploy time. One sponsor per deployment.
- CTA redirect goes through a server-side endpoint: `GET /api/sponsor/cta?prediction_id=…&scenario_id=…` records a `SponsorCtaFollowed` audit event, then `302`s to the configured URL with `prediction_id`, `scenario_id`, `utm_source=buildingpulse`, `utm_campaign=ll97_report` appended.

### URL structure
- `/report` (form), `/report/predicting?predictionId=…` (loading), `/report/[id]` (result).
- `/forecasting/*` 308-redirects to `/report/*` for one release, then is removed.

### Browser + device support
- Mobile-responsive (single-column layout on narrow viewports).
- Modern evergreen browsers only (last two stable versions of Chrome, Safari, Firefox, Edge). No IE, no native app.

### Scope of "outreach service"
- v1 is **outbound only** — leads flow out to the sponsor partner.
- Inbound traffic acquisition (SEO program, ads, cold email) is out of scope.

### Phase ordering vs `MVP_PLAN.md`
The MVP plan's Phases 0–6 stand as written, with one insertion and one extension:

- **Phases 0–1** (existing): domain contract, FastAPI skeleton with stub. Unchanged.
- **Phase 2A** (new, inserted): architecture + harness + CI. Lay the layered directory structure, write `.importlinter` (eight contracts), wire OTel + structlog into `deps.py`, set up `migrations.py` with `schema_migrations`, add the `Makefile`, set up the GitHub Actions workflow with all five gates, commit `openapi.json` and `frontend/src/types/api.ts`. No functional change to the API surface.
- **Phases 2–6** (existing): wire the frontend, train the model, serve real predictions, real peer cohort, real LL97 fine. Each phase now executes *inside* the layered structure.
- **Phase 7** (new): policy modules + audit logging. `policy/ll97_caps.py`, `policy/retrofits.py`, `AuditService`, `audit_log` migration, audit calls wired into existing endpoints.
- **Phase 8** (new): lead capture + sponsor co-brand. `LeadResourceService`, `NotificationResourceService`, `LeadCaptureUseCaseService`, `SponsorResourceService`, `POST /api/leads`, `GET /api/sponsor`, `GET /api/sponsor/cta`, sponsor strip + lead modal in the frontend.
- **Phase 9** (new): retrofit scenarios. `domain/retrofits/engine.py`, `ScenarioResourceService`, `GET /api/predictions/:id/scenarios`, scenarios card in the frontend.
- **Phase 10** (new): compliance timeline (server emits `fineSeries`; frontend renders step chart) + PDF generation (WeasyPrint via `PdfGenerationUseCaseService` and gated `GET /api/predictions/:id/pdf`).
- **Phase 11** (new): address resolver. `domain/address/resolver.py`, `training/build_ll84_index.py`, frontend "Look up by address" affordance behind `ADDRESS_LOOKUP_ENABLED`.

---

## Resolved Understanding (closing summary)

**Locked product decisions.** Free, ungated diagnostic report (predicted EUI + peer percentile + LL97 fine projection + step-function fine timeline through 2034) for any NYC building >25k sqft. Action half — PDF, retrofit scenarios, "Talk to a contractor" CTA — gated behind a single name/email/phone/role form with a required consent checkbox. Single sponsor configured per deployment. Retrofit scenarios shown to all visitors, not just at-risk. Address lookup module shipped but UI flagged off in v1.

**Locked architecture decisions.** Layered FastAPI app with eight `import-linter` contracts. Folder-per-resource controllers (`api/v1/<resource>/controller.py`). Two service layers — resource (leaves) and use-case (composers). Pure `domain/`, isolated `repos/` and `integrations/`, Python-typed `policy/`. SQLite v1 with hand-rolled migrations and a known Postgres boundary. OpenTelemetry + structlog wired in `app/deps.py`, Grafana stack as the dashboard target. Explicit Pydantic-typed audit events written through a dedicated `AuditService`.

**Locked CI/quality decisions.** All five merge gates required: ruff + mypy strict + import-linter + pytest unit (coverage ≥85% on domain/services) + pytest integration + Playwright happy-path E2E + OpenAPI schema drift + frontend type codegen drift. Same commands runnable locally via `Makefile`.

**Locked scope decisions.** Mobile-responsive web only; no native app. Modern evergreen browsers. v1 is outbound-only — no inbound acquisition program. No retention/deletion job in v1. No real email or webhook delivery — stubs that match the production interface.

**Open risks acknowledged.**
- LL97 cap mapping is coarse (6 frontend types → 60 occupancy groups, median tier picked). Reports carry a footnote.
- The `(prediction_id, email)` 1-hour idempotency window is a heuristic; sufficiently determined abuse defeats it. v1 accepts this.
- Single SQLite file = single-instance deploy. Multi-instance requires Postgres migration; the `sql-confined` contract guarantees this is a one-file change.
- v1 keeps all leads forever. Right-to-delete is named as v2 work in `backend/CLAUDE.md` so an agent doesn't quietly "fix" it without scoping.
- The audit-call invariant ("every use-case service writes at least one audit event") is enforced by code review and a `CLAUDE.md` rule, not by `import-linter`. This is the one harness gap and the one I'd fix first if v1 ships and we want v2 to be safer.

**Deferred to v2 (explicit non-goals for this PRD).** Portfolio uploads, multi-tenant white-label, true CO2e from fuel mix, LL84 submission help, authenticated user accounts, payment infrastructure, named-CRM connectors, Ridge/Lasso modeling, retention/deletion, granular GDPR consent, real outbound traffic acquisition.
