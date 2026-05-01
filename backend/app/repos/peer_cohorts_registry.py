"""Process-wide registry for the peer-cohorts parquet artifact.

Loads ``peer_cohorts.parquet`` once at app startup; subsequent reads return
the cached :class:`pandas.DataFrame`. Construction is the load — a missing
file raises immediately so the FastAPI lifespan hook fails fast rather than
letting the first prediction request blow up.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_COHORTS_FILE = "peer_cohorts.parquet"


class PeerCohortsRegistry:
    """Holds the loaded peer-cohorts lookup table."""

    def __init__(self, artifacts_dir: Path | str) -> None:
        directory = Path(artifacts_dir)
        cohorts_path = directory / _COHORTS_FILE
        if not cohorts_path.is_file():
            raise FileNotFoundError(f"missing peer cohorts artifact: {cohorts_path}")
        self._cohorts: pd.DataFrame = pd.read_parquet(cohorts_path, engine="pyarrow")

    @property
    def cohorts(self) -> pd.DataFrame:
        return self._cohorts


__all__ = ["PeerCohortsRegistry"]
