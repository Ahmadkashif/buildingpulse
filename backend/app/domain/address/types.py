"""Domain types for the address-resolver role.

The resolver translates a free-form NYC street address into a building
record from the LL84 disclosure. The dataclasses here are the contract
the rest of the app sees — pure, frozen, no I/O.

A successful lookup returns :class:`Ll84Match` with a confidence flag:
``"high"`` when the resolver is sure (clear single best candidate) and
``"low"`` when the input could plausibly resolve to more than one
record. A failed lookup returns :class:`Ll84Miss` with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["Confidence", "Ll84Index", "Ll84Match", "Ll84Miss", "Ll84Record", "MissReason"]


Confidence = Literal["high", "low"]
MissReason = Literal["malformed", "not_found"]


@dataclass(frozen=True, slots=True)
class Ll84Record:
    """A single building row from the LL84 lookup index.

    All fields mirror the parquet artifact built by
    :mod:`training.build_ll84_index`. ``site_eui`` is ``None`` when the
    source row has no measured EUI.
    """

    bbl: str
    address_raw: str
    address_normalized: str
    property_type: str
    borough: str
    gross_floor_area_sqft: int
    year_built: int
    number_of_buildings: int
    site_eui: float | None


@dataclass(frozen=True, slots=True)
class Ll84Index:
    """Pre-loaded address lookup index.

    Constructed once at process start from the parquet artifact and
    handed to :func:`app.domain.address.resolver.lookup` on every
    request. Holding records as a tuple keeps the index hashable-shaped
    and immutable — the resolver cannot accidentally mutate it.
    """

    records: tuple[Ll84Record, ...]


@dataclass(frozen=True, slots=True)
class Ll84Match:
    """A resolved address with the building record and a confidence flag."""

    record: Ll84Record
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class Ll84Miss:
    """A failed lookup with a reason the caller can surface to the user."""

    reason: MissReason
