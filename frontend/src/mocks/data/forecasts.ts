import type { Forecast } from "@/types";

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

export const FORECAST_FIXTURES: Forecast[] = [
  {
    id: "forecast-nexus-plaza-a",
    buildingId: "building-nexus-plaza-a",
    predictedAnnualConsumptionMwh: 4280,
    peakLoadMw: 1.85,
    peakTimestamp: "2024-08-14T14:00:00-04:00",
    confidencePct: 96.8,
    breakdown: MONTHS.map((month, i) => ({
      month,
      predicted: 220 + Math.round(Math.sin(i / 2) * 80 + 60),
      savingsPotential: 40 + Math.round(Math.cos(i / 2) * 25 + 18),
    })),
    insights: [
      {
        id: "insight-hvac",
        title: "HVAC System Optimization",
        description:
          "Predictive cycling of cooling units during 14:00–16:00 window could reduce peak demand by ~150kW.",
        badge: "savings",
      },
      {
        id: "insight-solar",
        title: "Solar Energy Potential",
        description:
          "Structural analysis confirms roof can support 400 kW of PV panels, offsetting 18% of day load.",
        badge: "yield-high",
      },
      {
        id: "insight-thermal",
        title: "Thermal Storage ROI",
        description:
          "Predictive cycling of thermal storage assets recommended based on current utility tariff shifts.",
        badge: "verified",
      },
      {
        id: "insight-insulation",
        title: "Insulation Deficiency",
        description:
          "Northeast-wing envelope loses 22% higher heat flux than expected. Envelope audit required.",
        badge: "action",
      },
    ],
  },
];

export function findForecast(id: string): Forecast | undefined {
  return FORECAST_FIXTURES.find((f) => f.id === id);
}
