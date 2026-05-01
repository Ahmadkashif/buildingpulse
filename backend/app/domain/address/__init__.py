"""Address-resolver domain package.

Public surface re-exported here so callers import from
``app.domain.address`` rather than reaching into submodules.
"""

from app.domain.address.resolver import (
    AMBIGUITY_MARGIN,
    FUZZY_CUTOFF,
    lookup,
    normalize_address,
)
from app.domain.address.types import (
    Confidence,
    Ll84Index,
    Ll84Match,
    Ll84Miss,
    Ll84Record,
    MissReason,
)

__all__ = [
    "AMBIGUITY_MARGIN",
    "Confidence",
    "FUZZY_CUTOFF",
    "Ll84Index",
    "Ll84Match",
    "Ll84Miss",
    "Ll84Record",
    "MissReason",
    "lookup",
    "normalize_address",
]
