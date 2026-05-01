"""LL97 building emissions caps by property type.

Source authority
----------------
- NYC Local Law 97 of 2019, codified at New York City Administrative Code
  §28-320.3.1 ("Building emissions limits"). Caps are in tCO2e per gross
  square foot per year, indexed by occupancy group.
- NYC Department of Buildings, *Local Law 97 Rules*, 1 RCNY §103-14,
  mapping building uses to LL97 occupancy groups.
- Public reference page: https://www.nyc.gov/site/buildings/codes/local-laws.page

Mapping note
------------
Each frontend property type is bound to one canonical LL97 occupancy group.
Multi-occupancy buildings are simplified to the dominant class; this is the
"median tier" mapping called out in `prd.md` §"LL97 cap mapping". The
report carries a footnote acknowledging the simplification.
"""

from __future__ import annotations

from typing import Final, Literal, get_args

from pydantic import Field
from pydantic.dataclasses import dataclass

__all__ = [
    "CAPS",
    "EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU",
    "EmissionsCap",
    "FINE_USD_PER_TCO2E_OVER_CAP",
    "PropertyType",
]


# Statutory penalty for exceeding an LL97 emissions cap: $268 per metric ton
# of CO2e over the cap, per year.
# Source: NYC Admin Code §28-320.6 (LL97 of 2019).
FINE_USD_PER_TCO2E_OVER_CAP: Final[float] = 268.0


# Site-EUI → emissions conversion. The MVP collapses NYC's per-fuel
# emissions coefficients (NYC Admin Code §28-320.3.2 / 1 RCNY §103-14
# Table 1: electricity 0.000288962 tCO2e/kWh ≈ 0.0000847 tCO2e/kBTU,
# natural gas 0.0000531 tCO2e/kBTU, #2 fuel oil 0.0000742 tCO2e/kBTU) into
# a single weighted average appropriate for a NYC commercial building
# whose fuel mix is unknown at form-submission time. The PRD calls this
# out as a v1 simplification; per-fuel breakdown is v2 work.
EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU: Final[float] = 0.0000681


PropertyType = Literal[
    "multifamily-housing",
    "office",
    "hotel",
    "retail",
    "hospital",
    "mixed-use",
]


@dataclass(frozen=True)
class EmissionsCap:
    """Emissions cap pair for one property type, in tCO2e/gsf/year.

    Both caps must be positive and the 2030-2034 cap must be strictly
    tighter than (or equal to) the 2024-2029 cap; LL97 only ratchets down.
    The ``citation`` field names the LL97 occupancy group the property
    type maps onto.
    """

    property_type: PropertyType
    cap_2024_2029: float = Field(gt=0.0)
    cap_2030_2034: float = Field(gt=0.0)
    citation: str = Field(min_length=1)


# Cap values: NYC Admin Code §28-320.3.1, Tables 1 (2024-2029) and 2 (2030-2034).
# Units: tCO2e per gross square foot per year.
_ENTRIES: Final[tuple[EmissionsCap, ...]] = (
    EmissionsCap(
        property_type="multifamily-housing",
        cap_2024_2029=0.00675,
        cap_2030_2034=0.00407,
        citation=(
            "LL97 Occupancy Group R-2 (residential multifamily). "
            "NYC Admin Code §28-320.3.1, Tables 1 & 2."
        ),
    ),
    EmissionsCap(
        property_type="office",
        cap_2024_2029=0.00846,
        cap_2030_2034=0.00453,
        citation=(
            "LL97 Occupancy Group B (business). "
            "NYC Admin Code §28-320.3.1, Tables 1 & 2."
        ),
    ),
    EmissionsCap(
        property_type="hotel",
        cap_2024_2029=0.00987,
        cap_2030_2034=0.00526,
        citation=(
            "LL97 Occupancy Group R-1 (transient residential / hotel). "
            "NYC Admin Code §28-320.3.1, Tables 1 & 2."
        ),
    ),
    EmissionsCap(
        property_type="retail",
        cap_2024_2029=0.01181,
        cap_2030_2034=0.00403,
        citation=(
            "LL97 Occupancy Group M (mercantile). "
            "NYC Admin Code §28-320.3.1, Tables 1 & 2."
        ),
    ),
    EmissionsCap(
        property_type="hospital",
        cap_2024_2029=0.02381,
        cap_2030_2034=0.01193,
        citation=(
            "LL97 Occupancy Group I-2 (institutional, hospitals). "
            "NYC Admin Code §28-320.3.1, Tables 1 & 2."
        ),
    ),
    EmissionsCap(
        property_type="mixed-use",
        cap_2024_2029=0.00846,
        cap_2030_2034=0.00453,
        citation=(
            "Mixed-use buildings default to LL97 Occupancy Group B (business) "
            "as the canonical median tier per 1 RCNY §103-14. "
            "Buildings with a dominant non-business occupancy may carry a "
            "different exposure; see report footnote."
        ),
    ),
)


def _build_caps() -> dict[PropertyType, EmissionsCap]:
    by_type: dict[PropertyType, EmissionsCap] = {}
    for entry in _ENTRIES:
        if entry.property_type in by_type:
            raise ValueError(
                f"duplicate LL97 cap entry for property type {entry.property_type!r}"
            )
        if entry.cap_2030_2034 > entry.cap_2024_2029:
            raise ValueError(
                f"LL97 cap for {entry.property_type!r} loosens after 2030 "
                f"({entry.cap_2030_2034} > {entry.cap_2024_2029}); "
                "caps must ratchet down."
            )
        by_type[entry.property_type] = entry

    expected = set(get_args(PropertyType))
    missing = expected - by_type.keys()
    if missing:
        raise ValueError(
            f"LL97 caps missing required property types: {sorted(missing)}"
        )
    return by_type


CAPS: Final[dict[PropertyType, EmissionsCap]] = _build_caps()
