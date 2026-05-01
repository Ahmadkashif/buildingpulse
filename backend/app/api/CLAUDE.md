# app/api — HTTP boundary

Controllers are thin: parse the request, validate via Pydantic, call **one**
service method, shape the response. No business `if` branching here.

May import: `app.services`, `app.schemas`, `app.deps`, `app.errors`,
`app.domain.types`.

May not import: `app.repos`, `app.integrations`, anything from another
controller package. Each `controller.py` owns exactly one router.

Each resource lives at `api/v1/<resource>/controller.py` and exports a
`router` object plus its `<Resource>Controller` class.
