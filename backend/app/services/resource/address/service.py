"""AddressResourceService — thin façade over the address resolver.

Fixes the verb (``lookup``) on the address resource and binds the
process-wide :class:`~app.domain.address.types.Ll84Index` so the
controller stays import-linter compliant (controllers may not reach
into ``app.domain.address.resolver`` directly through a function call,
they go through the resource service).
"""

from __future__ import annotations

from app.domain.address import Ll84Index, Ll84Match, Ll84Miss, lookup

__all__ = ["AddressResourceService"]


class AddressResourceService:
    """Owns the ``lookup`` verb on the address resource."""

    def __init__(self, index: Ll84Index) -> None:
        self._index = index

    def lookup(self, address: str) -> Ll84Match | Ll84Miss:
        return lookup(address, self._index)
