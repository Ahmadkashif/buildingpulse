"""SponsorResourceService — the resource service for sponsor identity.

Reads the active sponsor's display fields and lead-routing fields from
:class:`~app.config.SponsorConfig`. There is exactly one active sponsor
per deployment (config is loaded once at startup).
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config import SponsorConfig

__all__ = ["SponsorDisplay", "SponsorResourceService"]

_UTM_SOURCE = "buildingpulse"
_UTM_CAMPAIGN = "ll97_report"


@dataclass(frozen=True, slots=True)
class SponsorDisplay:
    """The five public co-brand fields. Lead-routing fields are excluded."""

    id: str
    name: str
    logo_url: str
    cta_label: str
    cta_url: str


class SponsorResourceService:
    """Owns read access to the active sponsor's configured fields."""

    def __init__(self, sponsor: SponsorConfig) -> None:
        self._sponsor = sponsor

    def get_display(self) -> SponsorDisplay:
        """Return only the fields that may be exposed publicly."""
        s = self._sponsor
        return SponsorDisplay(
            id=s.id,
            name=s.name,
            logo_url=s.logo_url,
            cta_label=s.cta_label,
            cta_url=s.cta_url,
        )

    def cta_redirect_url(
        self, prediction_id: str, scenario_id: str | None
    ) -> str:
        """Build the sponsor CTA URL with prediction/scenario ids and UTM tags appended."""
        parts = urlsplit(self._sponsor.cta_url)
        params = parse_qsl(parts.query, keep_blank_values=True)
        params.append(("prediction_id", prediction_id))
        if scenario_id is not None:
            params.append(("scenario_id", scenario_id))
        params.append(("utm_source", _UTM_SOURCE))
        params.append(("utm_campaign", _UTM_CAMPAIGN))
        return urlunsplit(parts._replace(query=urlencode(params)))

    @property
    def lead_email(self) -> str:
        return self._sponsor.lead_email

    @property
    def lead_webhook_url(self) -> str | None:
        return self._sponsor.lead_webhook_url
