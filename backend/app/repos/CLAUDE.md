# app/repos — persistence boundary

The only place SQL runs. Connection lifecycle owned here. Each
`<resource>_repo.py` exports a `<Resource>Repo` class with parameterized
queries.

May import: `app.domain.types`, `app.policy`, stdlib, third-party DB
drivers.

May not import: `app.api`, `app.services`, `app.integrations`,
`app.schemas`. The `sql-confined` contract makes this layer the only
permitted importer of `sqlite3` / `sqlalchemy`.

Schema migrations live as numbered `.sql` files under `migrations/`,
applied at startup by the `lifespan` hook in `app/main.py`.
