"""Local conftest — neutralises the project-wide ``_sponsor_env`` fixture.

The use-case service is fully self-contained: it composes three resource
services through fakes, never boots the FastAPI app, and never reads
sponsor env vars. Skipping the parent autouse fixture keeps these tests
hermetic and lets ``mutmut`` run them in isolation.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _sponsor_env() -> None:
    return None
