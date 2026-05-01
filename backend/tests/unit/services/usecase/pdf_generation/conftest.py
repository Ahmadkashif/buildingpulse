"""Local conftest — neutralises the project-wide ``_sponsor_env`` fixture.

The template renderer never boots the FastAPI app and never reads
sponsor env vars, so the autouse fixture is a no-op here.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _sponsor_env() -> None:
    return None
