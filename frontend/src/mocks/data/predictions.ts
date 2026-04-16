import type { PredictionResponse } from "@/types";

export const PREDICTION_FIXTURES: PredictionResponse[] = [
  {
    id: "pred_sample_01",
    generatedAt: "2026-04-16T14:30:00-04:00",
    input: {
      propertyType: "multifamily-housing",
      borough: "brooklyn",
      grossFloorAreaSqft: 45000,
      yearBuilt: 1925,
      numberOfBuildings: 1,
    },
    prediction: {
      siteEuiKbtuPerSqft: 87.3,
      intervalLow: 65.2,
      intervalHigh: 109.4,
      modelVersion: "baseline-lr-v1",
    },
    peer: {
      cohort: {
        propertyType: "multifamily-housing",
        borough: "brooklyn",
        ageBand: "pre-1950",
      },
      cohortSize: 1420,
      medianSiteEui: 74.1,
      p25SiteEui: 58.0,
      p75SiteEui: 94.5,
      percentile: 68,
    },
    ll97: {
      capKbtuPerSqft2024to2029: 6.75,
      capKbtuPerSqft2030to2034: 4.53,
      projectedAnnualFineUsd2024: 0,
      projectedAnnualFineUsd2030: 12400,
      atRisk: true,
    },
  },
];

export function findPrediction(id: string): PredictionResponse | undefined {
  return PREDICTION_FIXTURES.find((p) => p.id === id);
}
