"""Pure-domain test scoping.

Override the project-wide ``_sponsor_env`` autouse fixture so address
domain tests do not import :mod:`app.deps` (and through it the
integrations layer). The address resolver is pure; it has no
dependency on sponsor config or FastAPI lifespan, and isolating these
tests from those imports keeps ``mutmut run`` working when only
``app/domain/address`` is in ``paths_to_mutate``.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _sponsor_env() -> Iterator[None]:
    yield
