"""Local conftest for the lead resource service tests.

Overrides the project-wide autouse ``_sponsor_env`` fixture with a no-op.
The lead resource service is fully self-contained — it does not boot the
FastAPI app, read sponsor env vars, or touch ``app.deps``. Skipping the
parent fixture lets ``mutmut`` run these tests without requiring the
mutants/ snapshot to include unrelated app modules (audit, deps, main).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _sponsor_env() -> None:
    return None
