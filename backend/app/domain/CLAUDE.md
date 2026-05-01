# app/domain — pure logic

Pure functions and dataclasses. Pure means:

- **No FastAPI.** Domain doesn't know about HTTP, routers, or `Depends`.
- **No SQL.** No `sqlite3`, no `sqlalchemy`, no DB connections.
- **No I/O.** No `open()`, no network calls, no `os.environ` reads.
- **No frameworks.** Pydantic is allowed for `types.py` dataclasses.

May import: `app.policy`, stdlib, third-party utility libraries.

May not import: `app.api`, `app.services`, `app.repos`,
`app.integrations`, `app.schemas`. The `domain-pure` contract enforces
this — domain having zero inbound edges is the load-bearing invariant.

Modules are role-named: `calculator.py`, `engine.py`, `lookup.py`,
`predictor.py`, `resolver.py`, `types.py`. The parent folder names the
thing.
