"""Cross-domain type aliases.

Domain modules import :class:`PropertyType` from here so the rest of the
app (and tests) have one canonical enum to pass into pure functions like
:func:`app.domain.ll97.compute`. Values match the string literals used by
``app/policy/ll97_caps.py`` so a ``PropertyType`` member doubles as the
key into ``CAPS``.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["PropertyType"]


class PropertyType(StrEnum):
    """The six frontend property types BuildingPulse models.

    The string value of each member is the canonical wire-format slug —
    the same slug used by ``app.policy.ll97_caps.CAPS`` and the request
    schemas in ``app.schemas``.
    """

    MULTIFAMILY_HOUSING = "multifamily-housing"
    OFFICE = "office"
    HOTEL = "hotel"
    RETAIL = "retail"
    HOSPITAL = "hospital"
    MIXED_USE = "mixed-use"
