"""Process-wide application config.

Parsed once at startup from environment variables. Missing or invalid
values raise immediately so a misconfigured deployment fails loud rather
than 500-ing on the first request that touches the bad value.

Sponsor identity is supplied via env vars at deploy time (one sponsor per
deployment): id, display name, logo URL, CTA label, CTA URL, lead-routing
email, optional lead-routing webhook URL. The display fields are exposed
publicly via ``GET /api/sponsor``; the routing fields stay server-side.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = ["AppConfig", "ConfigError", "SponsorConfig", "load_app_config"]


class ConfigError(RuntimeError):
    """Raised when required env vars are missing or invalid."""


@dataclass(frozen=True, slots=True)
class SponsorConfig:
    id: str
    name: str
    logo_url: str
    cta_label: str
    cta_url: str
    lead_email: str
    lead_webhook_url: str | None


@dataclass(frozen=True, slots=True)
class AppConfig:
    sponsor: SponsorConfig


_REQUIRED_SPONSOR_ENV: tuple[tuple[str, str], ...] = (
    ("SPONSOR_ID", "id"),
    ("SPONSOR_NAME", "name"),
    ("SPONSOR_LOGO_URL", "logo_url"),
    ("SPONSOR_CTA_LABEL", "cta_label"),
    ("SPONSOR_CTA_URL", "cta_url"),
    ("SPONSOR_LEAD_EMAIL", "lead_email"),
)


def _load_sponsor(env: dict[str, str] | None = None) -> SponsorConfig:
    src = os.environ if env is None else env
    values: dict[str, str] = {}
    missing: list[str] = []
    for var, field in _REQUIRED_SPONSOR_ENV:
        raw = src.get(var, "")
        if not raw or not raw.strip():
            missing.append(var)
        else:
            values[field] = raw.strip()
    if missing:
        raise ConfigError(
            "Missing required sponsor env vars: " + ", ".join(sorted(missing))
        )
    webhook_raw = src.get("SPONSOR_LEAD_WEBHOOK_URL", "").strip()
    return SponsorConfig(
        id=values["id"],
        name=values["name"],
        logo_url=values["logo_url"],
        cta_label=values["cta_label"],
        cta_url=values["cta_url"],
        lead_email=values["lead_email"],
        lead_webhook_url=webhook_raw or None,
    )


def load_app_config(env: dict[str, str] | None = None) -> AppConfig:
    """Build an :class:`AppConfig` from the process environment.

    Raises :class:`ConfigError` if any required env var is missing.
    Called from :mod:`app.main`'s lifespan hook so misconfiguration fails
    at startup, not on the first request.
    """
    return AppConfig(sponsor=_load_sponsor(env))
