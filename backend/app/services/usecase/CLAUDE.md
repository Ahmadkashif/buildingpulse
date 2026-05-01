# app/services/usecase — workflow services

A use-case service composes resource services to run a workflow that
touches more than one resource (e.g. `LeadCaptureUseCaseService`).

May import: `app.services.resource`, `app.domain`, `app.policy`.

May not import: `app.repos`, `app.integrations` (the
`usecases-compose-resources-only` contract enforces this), `app.api`.
Reach the database / outside world only through resource services.
