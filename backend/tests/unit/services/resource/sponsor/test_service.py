"""Unit tests for SponsorResourceService.

Pins the public/private split: ``get_display`` returns only the five
co-brand fields, never the lead-routing fields. Lead-routing access is
exposed only to server-side callers via the dedicated properties.
"""

from __future__ import annotations

import dataclasses

import pytest
from app.config import SponsorConfig
from app.services.resource.sponsor.service import (
    SponsorDisplay,
    SponsorResourceService,
)


@pytest.fixture
def sponsor() -> SponsorConfig:
    return SponsorConfig(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/acme-logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme-energy.example.com/contact",
        lead_email="leads@acme-energy.example.com",
        lead_webhook_url="https://hooks.example.com/acme",
    )


def test_get_display_returns_only_five_public_fields(sponsor: SponsorConfig) -> None:
    service = SponsorResourceService(sponsor)
    display = service.get_display()

    assert display == SponsorDisplay(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/acme-logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme-energy.example.com/contact",
    )

    public_fields = {f.name for f in dataclasses.fields(SponsorDisplay)}
    assert public_fields == {"id", "name", "logo_url", "cta_label", "cta_url"}
    assert "lead_email" not in public_fields
    assert "lead_webhook_url" not in public_fields


def test_lead_routing_fields_exposed_only_via_dedicated_properties(
    sponsor: SponsorConfig,
) -> None:
    service = SponsorResourceService(sponsor)
    assert service.lead_email == "leads@acme-energy.example.com"
    assert service.lead_webhook_url == "https://hooks.example.com/acme"


def test_lead_webhook_url_passes_through_none_when_unset() -> None:
    sponsor = SponsorConfig(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/acme-logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme-energy.example.com/contact",
        lead_email="leads@acme-energy.example.com",
        lead_webhook_url=None,
    )
    service = SponsorResourceService(sponsor)
    assert service.lead_webhook_url is None
