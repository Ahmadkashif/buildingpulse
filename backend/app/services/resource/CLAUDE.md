# app/services/resource — leaf services

One service per resource. Owns that resource's verbs, holds its repo and
integration deps, returns domain types.

May import: `app.repos`, `app.integrations`, `app.domain`, `app.policy`.

May not import: another resource service (the `resource-leaves`
import-linter contract enforces this), `app.services.usecase`,
`app.api`, `app.schemas`.

If a flow needs methods from two resource services, lift it into a
use-case service.
