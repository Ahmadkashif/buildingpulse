# app/integrations — outbound external calls

Each `<role>_dispatcher.py` wraps one third-party SDK or HTTP target.
Failures are logged, not raised, unless the calling service explicitly
awaits a result.

May import: `app.domain.types`, stdlib, third-party SDKs.

May not import: `app.api`, `app.services`, `app.repos`, `app.schemas`,
`app.policy` (cross-layer business rules belong in services or domain).

A resource service composes this layer; controllers never reach in here
directly.
