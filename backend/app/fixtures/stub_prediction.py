"""Phase 1 stub `prediction`/`peer`/`ll97` payload.

Hand-pinned to the Contract example in the PRD. The controller hands these
blocks back verbatim until Phases 4-6 replace them with real outputs.
"""

from typing import Any

STUB: dict[str, Any] = {
    "id": "pred_sample_01",
    "generatedAt": "2026-04-16T14:30:00-04:00",
    "input": {
        "propertyType": "multifamily-housing",
        "borough": "brooklyn",
        "grossFloorAreaSqft": 45000,
        "yearBuilt": 1925,
        "numberOfBuildings": 1,
    },
    "prediction": {
        "siteEuiKbtuPerSqft": 87.3,
        "intervalLow": 65.2,
        "intervalHigh": 109.4,
        "modelVersion": "baseline-lr-v1",
    },
    "peer": {
        "cohort": {
            "propertyType": "multifamily-housing",
            "borough": "brooklyn",
            "ageBand": "pre-1950",
        },
        "cohortSize": 1420,
        "medianSiteEui": 74.1,
        "p25SiteEui": 58.0,
        "p75SiteEui": 94.5,
        "percentile": 68,
    },
    "ll97": {
        "capKbtuPerSqft2024To2029": 6.75,
        "capKbtuPerSqft2030To2034": 4.53,
        "projectedAnnualFineUsd2024": 0,
        "projectedAnnualFineUsd2030": 12400,
        "atRisk": True,
    },
}

__all__ = ["STUB"]
