"""Unit tests for app.config.

The contract: missing required env vars raise a clear ``ConfigError`` —
they never silently default. The webhook URL is optional and resolves to
``None`` when blank or unset.
"""

from __future__ import annotations

import pytest
from app.config import AppConfig, ConfigError, SponsorConfig, load_app_config

_FULL_ENV: dict[str, str] = {
    "SPONSOR_ID": "acme-energy",
    "SPONSOR_NAME": "Acme Energy",
    "SPONSOR_LOGO_URL": "https://cdn.example.com/logo.svg",
    "SPONSOR_CTA_LABEL": "Talk to a contractor",
    "SPONSOR_CTA_URL": "https://acme.example.com/contact",
    "SPONSOR_LEAD_EMAIL": "leads@acme.example.com",
    "SPONSOR_LEAD_WEBHOOK_URL": "https://hooks.example.com/acme",
}


def test_full_env_produces_populated_app_config() -> None:
    cfg = load_app_config(env=dict(_FULL_ENV))

    assert isinstance(cfg, AppConfig)
    assert cfg.sponsor == SponsorConfig(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme.example.com/contact",
        lead_email="leads@acme.example.com",
        lead_webhook_url="https://hooks.example.com/acme",
    )


def test_missing_webhook_resolves_to_none() -> None:
    env = {k: v for k, v in _FULL_ENV.items() if k != "SPONSOR_LEAD_WEBHOOK_URL"}
    cfg = load_app_config(env=env)
    assert cfg.sponsor.lead_webhook_url is None


def test_blank_webhook_resolves_to_none() -> None:
    env = dict(_FULL_ENV) | {"SPONSOR_LEAD_WEBHOOK_URL": "   "}
    cfg = load_app_config(env=env)
    assert cfg.sponsor.lead_webhook_url is None


@pytest.mark.parametrize(
    "missing_var",
    [
        "SPONSOR_ID",
        "SPONSOR_NAME",
        "SPONSOR_LOGO_URL",
        "SPONSOR_CTA_LABEL",
        "SPONSOR_CTA_URL",
        "SPONSOR_LEAD_EMAIL",
    ],
)
def test_each_required_var_is_required(missing_var: str) -> None:
    env = {k: v for k, v in _FULL_ENV.items() if k != missing_var}

    with pytest.raises(ConfigError) as excinfo:
        load_app_config(env=env)

    assert missing_var in str(excinfo.value)


def test_blank_required_var_is_treated_as_missing() -> None:
    env = dict(_FULL_ENV) | {"SPONSOR_NAME": "   "}

    with pytest.raises(ConfigError) as excinfo:
        load_app_config(env=env)

    assert "SPONSOR_NAME" in str(excinfo.value)


def test_multiple_missing_vars_listed_alphabetically() -> None:
    env = {
        k: v
        for k, v in _FULL_ENV.items()
        if k not in {"SPONSOR_NAME", "SPONSOR_ID"}
    }

    with pytest.raises(ConfigError) as excinfo:
        load_app_config(env=env)

    msg = str(excinfo.value)
    assert "SPONSOR_ID" in msg
    assert "SPONSOR_NAME" in msg
    assert msg.index("SPONSOR_ID") < msg.index("SPONSOR_NAME")


def test_load_app_config_reads_os_environ_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for k, v in _FULL_ENV.items():
        monkeypatch.setenv(k, v)
    cfg = load_app_config()
    assert cfg.sponsor.id == "acme-energy"
