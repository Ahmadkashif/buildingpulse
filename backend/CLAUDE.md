# Backend rules

This is the BuildingPulse backend. The architecture is layered; the layering
is enforced by `import-linter` (config in `.importlinter`, runs in CI).

## Layering (top imports down only)

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
training     → may import domain, policy. NEVER imports from app.api/services/repos/integrations.
```

Domain has zero edges into the rest of `app/`. That invariant keeps the
LL97 calculator, retrofit engine, peer lookup, predictor and address
resolver pure and unit-testable forever.

## Conventions

- Path encodes the resource. Filename encodes the role.
- `api/v1/<resource>/controller.py`     class `<Resource>Controller`
- `services/resource/<resource>/service.py` class `<Resource>ResourceService`
- `services/usecase/<usecase>/service.py`   class `<UseCase>UseCaseService`
- `repos/<resource>_repo.py`            class `<Resource>Repo`
- `integrations/<role>_dispatcher.py`   class `<Role>Dispatcher`
- Domain modules use role names: `calculator.py`, `engine.py`, `lookup.py`,
  `predictor.py`, `resolver.py`, `types.py`.

Every package's `__init__.py` declares an explicit `__all__`. Symbols
not listed are package-private and may not be imported across packages.

See each layer's `CLAUDE.md` for what belongs and what may be imported.
