"""Retrofit scenario library by property type.

Source authority
----------------
Reduction ranges and installed-cost bands below are pulled from
public-source decarbonization references. Citations are attached to each
entry as an inline ``citation`` field. Primary sources used:

- NYC Mayor's Office of Climate & Environmental Justice, *Getting to 80x50:
  Pathways for Buildings* (2022), reduction ranges for envelope, lighting,
  controls, and heat-pump conversions in NYC stock.
- Urban Green Council, *Retrofit Market Analysis* (2019, 2021 update),
  installed cost bands ($/gsf) for envelope, MEP, and electrification work
  on NYC commercial and multifamily buildings.
- ACEEE, *Commercial Building Retrofit Strategies* (Report A1801, 2018),
  cross-reference for HVAC, controls/BMS, and lighting reductions.
- ASHRAE, *Advanced Energy Design Guide for K-12 / Hospital / Hotel*
  series, cross-reference for sector-specific HVAC and DHW measures.
- NREL, *End-Use Load Profiles for the U.S. Building Stock* (2022),
  cross-reference for fuel-switching and water-side reductions.

Mapping note
------------
The library is intentionally small (3–5 interventions per property type)
and frozen at import time. The retrofit *engine* in
``app.domain.retrofits`` consumes this data; the data is swappable
without changing engine logic. This is the "code-reviewed configuration"
called out in PRD §"Retrofit scenario engine".
"""

from __future__ import annotations

from typing import Final, get_args

from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from app.policy.ll97_caps import PropertyType

__all__ = [
    "LIBRARY",
    "RetrofitScenario",
]


@dataclass(frozen=True)
class RetrofitScenario:
    """One canned retrofit intervention.

    Fields
    ------
    id
        Stable, kebab-case identifier unique within a property type.
        Wire-format slug used by the scenarios endpoint and lead capture.
    name
        Short human-readable label rendered in the report card.
    description
        One- or two-sentence plain-English summary.
    reduction_pct
        Estimated Site-EUI reduction as a fraction in (0, 1]. Validated
        strictly: 0 means "no effect" (drop the entry) and >1 is
        nonsensical for a single intervention.
    cost_low_usd_per_sqft
        Lower bound of installed cost band, USD per gross square foot.
    cost_high_usd_per_sqft
        Upper bound of installed cost band, USD per gross square foot.
        Must be >= ``cost_low_usd_per_sqft``.
    citation
        Source for the reduction range and cost band; rendered as a
        footnote on the report.
    """

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reduction_pct: float = Field(gt=0.0, le=1.0)
    cost_low_usd_per_sqft: float = Field(ge=0.0)
    cost_high_usd_per_sqft: float = Field(ge=0.0)
    citation: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_cost_band(self) -> "RetrofitScenario":
        if self.cost_high_usd_per_sqft < self.cost_low_usd_per_sqft:
            raise ValueError(
                f"cost_high_usd_per_sqft ({self.cost_high_usd_per_sqft}) "
                f"must be >= cost_low_usd_per_sqft ({self.cost_low_usd_per_sqft}) "
                f"for retrofit {self.id!r}"
            )
        return self


_ENTRIES: Final[dict[PropertyType, tuple[RetrofitScenario, ...]]] = {
    "multifamily-housing": (
        RetrofitScenario(
            id="heat-pump-conversion",
            name="Air-source heat pump conversion",
            description=(
                "Replace gas/oil boilers and through-wall AC with central or "
                "VRF air-source heat pumps for space heating, cooling, and "
                "domestic hot water."
            ),
            reduction_pct=0.40,
            cost_low_usd_per_sqft=20.0,
            cost_high_usd_per_sqft=60.0,
            citation=(
                "Urban Green Council, Retrofit Market Analysis (2021), "
                "multifamily heat-pump conversion case studies; NREL ResStock "
                "2022 fuel-switching impact analysis."
            ),
        ),
        RetrofitScenario(
            id="envelope-upgrade",
            name="Envelope upgrade (windows + air sealing)",
            description=(
                "High-performance window replacement, facade air sealing, and "
                "added wall/roof insulation on a pre-1980 multifamily envelope."
            ),
            reduction_pct=0.18,
            cost_low_usd_per_sqft=15.0,
            cost_high_usd_per_sqft=45.0,
            citation=(
                "NYC Mayor's Office, Getting to 80x50 (2022), envelope "
                "retrofit pathway for pre-1980 multifamily."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="Common-area LED + occupancy controls",
            description=(
                "Convert common-area, corridor, and exterior lighting to LED "
                "with occupancy/daylight controls."
            ),
            reduction_pct=0.05,
            cost_low_usd_per_sqft=0.5,
            cost_high_usd_per_sqft=2.5,
            citation=(
                "ACEEE Report A1801 (2018), lighting retrofit reductions for "
                "multifamily common areas."
            ),
        ),
        RetrofitScenario(
            id="dhw-heat-pump",
            name="Central heat-pump water heater",
            description=(
                "Replace central gas DHW plant with a CO2 or R-134a heat-pump "
                "water heating system serving the building."
            ),
            reduction_pct=0.12,
            cost_low_usd_per_sqft=4.0,
            cost_high_usd_per_sqft=12.0,
            citation=(
                "NREL End-Use Load Profiles (2022), DHW electrification "
                "savings for mid-rise multifamily."
            ),
        ),
    ),
    "office": (
        RetrofitScenario(
            id="vrf-heat-pump",
            name="VRF heat-pump HVAC retrofit",
            description=(
                "Replace gas-fired perimeter heat and packaged DX cooling "
                "with variable refrigerant flow heat pumps and dedicated "
                "outside-air units."
            ),
            reduction_pct=0.35,
            cost_low_usd_per_sqft=25.0,
            cost_high_usd_per_sqft=70.0,
            citation=(
                "Urban Green Council, Retrofit Market Analysis (2021), VRF "
                "office case studies; ACEEE A1801 (2018) HVAC retrofit data."
            ),
        ),
        RetrofitScenario(
            id="bms-controls",
            name="Building management system upgrade",
            description=(
                "Modern BMS with optimized start/stop, demand-controlled "
                "ventilation, and supply-air reset across the central plant."
            ),
            reduction_pct=0.15,
            cost_low_usd_per_sqft=2.0,
            cost_high_usd_per_sqft=8.0,
            citation=(
                "ACEEE Report A1801 (2018), commercial BMS / re-tuning "
                "median savings."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="LED + advanced lighting controls",
            description=(
                "Tenant-floor LED lamp + fixture replacement with networked "
                "occupancy/daylight controls."
            ),
            reduction_pct=0.10,
            cost_low_usd_per_sqft=2.0,
            cost_high_usd_per_sqft=6.0,
            citation=(
                "ACEEE Report A1801 (2018), commercial lighting retrofit "
                "reductions."
            ),
        ),
        RetrofitScenario(
            id="envelope-windows",
            name="High-performance window replacement",
            description=(
                "Replace single-pane or early-double-pane curtain wall with "
                "low-e triple-pane assemblies."
            ),
            reduction_pct=0.08,
            cost_low_usd_per_sqft=18.0,
            cost_high_usd_per_sqft=50.0,
            citation=(
                "NYC Mayor's Office, Getting to 80x50 (2022), commercial "
                "envelope pathway."
            ),
        ),
    ),
    "hotel": (
        RetrofitScenario(
            id="heat-pump-conversion",
            name="Heat-pump HVAC + DHW conversion",
            description=(
                "Replace gas boilers and PTAC units with central air-source "
                "heat pumps for space conditioning and domestic hot water."
            ),
            reduction_pct=0.38,
            cost_low_usd_per_sqft=22.0,
            cost_high_usd_per_sqft=65.0,
            citation=(
                "ASHRAE Advanced Energy Design Guide for Hotels (2018); "
                "Urban Green Council Retrofit Market Analysis (2021)."
            ),
        ),
        RetrofitScenario(
            id="dhw-heat-recovery",
            name="DHW heat recovery + low-flow fixtures",
            description=(
                "Drain-water heat recovery on laundry and shower stacks "
                "paired with low-flow guest-room fixtures."
            ),
            reduction_pct=0.08,
            cost_low_usd_per_sqft=1.0,
            cost_high_usd_per_sqft=4.0,
            citation=(
                "NREL End-Use Load Profiles (2022), hospitality DHW "
                "savings analysis."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="Guest-room + back-of-house LED",
            description=(
                "LED retrofit in guest rooms, corridors, and back-of-house "
                "spaces with key-card occupancy integration."
            ),
            reduction_pct=0.07,
            cost_low_usd_per_sqft=1.5,
            cost_high_usd_per_sqft=4.5,
            citation=(
                "ACEEE Report A1801 (2018), hospitality lighting retrofit."
            ),
        ),
        RetrofitScenario(
            id="bms-controls",
            name="Guest-room thermostat + BMS controls",
            description=(
                "Networked guest-room setbacks tied to occupancy plus "
                "central BMS supply-air reset."
            ),
            reduction_pct=0.12,
            cost_low_usd_per_sqft=2.5,
            cost_high_usd_per_sqft=7.0,
            citation=(
                "ASHRAE Advanced Energy Design Guide for Hotels (2018), "
                "guest-room control savings."
            ),
        ),
    ),
    "retail": (
        RetrofitScenario(
            id="rooftop-heat-pump",
            name="Rooftop heat-pump replacement",
            description=(
                "Swap aged rooftop gas/electric package units with high-"
                "efficiency heat-pump RTUs sized to current load."
            ),
            reduction_pct=0.30,
            cost_low_usd_per_sqft=12.0,
            cost_high_usd_per_sqft=35.0,
            citation=(
                "ACEEE Report A1801 (2018), retail RTU replacement; NYC "
                "Mayor's Office Getting to 80x50 (2022)."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="Sales-floor LED + display controls",
            description=(
                "LED retrofit of sales-floor and display lighting with "
                "scheduled dimming and occupancy controls in stockrooms."
            ),
            reduction_pct=0.15,
            cost_low_usd_per_sqft=2.0,
            cost_high_usd_per_sqft=6.0,
            citation=(
                "ACEEE Report A1801 (2018), retail lighting retrofit "
                "median savings."
            ),
        ),
        RetrofitScenario(
            id="refrigeration-controls",
            name="Refrigeration controls + door retrofits",
            description=(
                "Glass doors on open multi-deck cases, ECM evaporator fans, "
                "and floating head-pressure controls."
            ),
            reduction_pct=0.12,
            cost_low_usd_per_sqft=3.0,
            cost_high_usd_per_sqft=10.0,
            citation=(
                "NREL End-Use Load Profiles (2022), refrigerated retail "
                "case-side savings."
            ),
        ),
        RetrofitScenario(
            id="envelope-air-sealing",
            name="Vestibule + envelope air sealing",
            description=(
                "Add or upgrade entry vestibules, weatherstrip loading "
                "doors, and seal envelope penetrations."
            ),
            reduction_pct=0.06,
            cost_low_usd_per_sqft=1.0,
            cost_high_usd_per_sqft=4.0,
            citation=(
                "NYC Mayor's Office Getting to 80x50 (2022), retail envelope "
                "infiltration pathway."
            ),
        ),
    ),
    "hospital": (
        RetrofitScenario(
            id="chiller-plant-upgrade",
            name="High-efficiency chiller + heat-recovery plant",
            description=(
                "Replace aged centrifugal chillers and steam-driven heat with "
                "magnetic-bearing chillers and heat-recovery chillers serving "
                "reheat loops."
            ),
            reduction_pct=0.22,
            cost_low_usd_per_sqft=20.0,
            cost_high_usd_per_sqft=55.0,
            citation=(
                "ASHRAE Advanced Energy Design Guide for Hospitals (2017); "
                "ACEEE Report A1801 (2018) healthcare HVAC pathway."
            ),
        ),
        RetrofitScenario(
            id="oa-energy-recovery",
            name="Outside-air energy recovery on AHUs",
            description=(
                "Add enthalpy wheels or runaround loops to high-OA hospital "
                "air handlers to cut heating and cooling load."
            ),
            reduction_pct=0.12,
            cost_low_usd_per_sqft=6.0,
            cost_high_usd_per_sqft=18.0,
            citation=(
                "ASHRAE Advanced Energy Design Guide for Hospitals (2017), "
                "energy-recovery section."
            ),
        ),
        RetrofitScenario(
            id="bms-retrocommissioning",
            name="BMS retrocommissioning",
            description=(
                "Retune AHU, chilled-water, and reheat loops; tighten OR/"
                "imaging setbacks; recalibrate critical-space sensors."
            ),
            reduction_pct=0.10,
            cost_low_usd_per_sqft=1.0,
            cost_high_usd_per_sqft=4.0,
            citation=(
                "ACEEE Report A1801 (2018), retrocommissioning median "
                "savings for healthcare."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="LED + circadian lighting controls",
            description=(
                "LED retrofit across patient and clinical areas with "
                "circadian dimming and occupancy controls."
            ),
            reduction_pct=0.07,
            cost_low_usd_per_sqft=2.0,
            cost_high_usd_per_sqft=6.0,
            citation=(
                "ACEEE Report A1801 (2018), healthcare lighting retrofit "
                "savings."
            ),
        ),
    ),
    "mixed-use": (
        RetrofitScenario(
            id="heat-pump-conversion",
            name="Building-wide heat-pump conversion",
            description=(
                "Replace shared boilers and rooftop gas units with VRF / "
                "air-source heat pumps serving both residential and "
                "commercial floors."
            ),
            reduction_pct=0.36,
            cost_low_usd_per_sqft=22.0,
            cost_high_usd_per_sqft=62.0,
            citation=(
                "Urban Green Council Retrofit Market Analysis (2021), "
                "mixed-use case studies; NYC Mayor's Office Getting to 80x50 "
                "(2022)."
            ),
        ),
        RetrofitScenario(
            id="envelope-upgrade",
            name="Envelope upgrade (windows + sealing)",
            description=(
                "Window replacement plus facade air sealing across both "
                "residential and ground-floor commercial portions."
            ),
            reduction_pct=0.15,
            cost_low_usd_per_sqft=15.0,
            cost_high_usd_per_sqft=45.0,
            citation=(
                "NYC Mayor's Office Getting to 80x50 (2022), mixed-use "
                "envelope pathway."
            ),
        ),
        RetrofitScenario(
            id="bms-controls",
            name="Sub-metering + BMS controls",
            description=(
                "Per-tenant sub-metering and a unified BMS with scheduled "
                "setpoints, demand-controlled ventilation, and supply-air "
                "reset."
            ),
            reduction_pct=0.10,
            cost_low_usd_per_sqft=2.0,
            cost_high_usd_per_sqft=7.0,
            citation=(
                "ACEEE Report A1801 (2018), BMS retrofit savings; Urban "
                "Green Council sub-metering analysis (2019)."
            ),
        ),
        RetrofitScenario(
            id="lighting-led",
            name="Common-area + commercial LED retrofit",
            description=(
                "LED retrofit in residential common areas and commercial "
                "tenant spaces with occupancy/daylight controls."
            ),
            reduction_pct=0.07,
            cost_low_usd_per_sqft=1.5,
            cost_high_usd_per_sqft=5.0,
            citation=(
                "ACEEE Report A1801 (2018), lighting retrofit reductions "
                "for mixed-use stock."
            ),
        ),
    ),
}


def _build_library() -> dict[PropertyType, tuple[RetrofitScenario, ...]]:
    expected = set(get_args(PropertyType))
    missing = expected - _ENTRIES.keys()
    if missing:
        raise ValueError(
            f"retrofit library missing required property types: {sorted(missing)}"
        )
    extra = _ENTRIES.keys() - expected
    if extra:
        raise ValueError(
            f"retrofit library has unknown property types: {sorted(extra)}"
        )

    by_type: dict[PropertyType, tuple[RetrofitScenario, ...]] = {}
    for property_type, scenarios in _ENTRIES.items():
        if not 3 <= len(scenarios) <= 5:
            raise ValueError(
                f"retrofit library for {property_type!r} has {len(scenarios)} "
                "interventions; PRD requires 3–5."
            )
        seen_ids: set[str] = set()
        for scenario in scenarios:
            if scenario.id in seen_ids:
                raise ValueError(
                    f"duplicate retrofit id {scenario.id!r} for "
                    f"property type {property_type!r}"
                )
            seen_ids.add(scenario.id)
        by_type[property_type] = scenarios
    return by_type


LIBRARY: Final[dict[PropertyType, tuple[RetrofitScenario, ...]]] = _build_library()
