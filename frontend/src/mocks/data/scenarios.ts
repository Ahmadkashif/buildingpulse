import type { ScenarioPublic } from "@/types";

export const SCENARIO_FIXTURES: ScenarioPublic[] = [
  {
    id: "lighting-ledr",
    name: "LED + Controls",
    description: "Replace fluorescent lighting with LED fixtures and add occupancy controls.",
    reductionPct: 0.08,
    costLow: 1.5,
    costHigh: 3.0,
    recomputedFineSeries: [
      { year: 2026, projectedAnnualFineUsd: 0 },
      { year: 2030, projectedAnnualFineUsd: 9876 },
    ],
    recomputedFine2024: 0,
    recomputedFine2030: 9876,
    citation: "ACEEE 2022 retrofit cost study",
  },
  {
    id: "envelope-air-seal",
    name: "Envelope Air Sealing",
    description: "Seal air leaks at facade penetrations and roof-wall junctions.",
    reductionPct: 0.12,
    costLow: 3.0,
    costHigh: 6.0,
    recomputedFineSeries: [
      { year: 2026, projectedAnnualFineUsd: 0 },
      { year: 2030, projectedAnnualFineUsd: 6500 },
    ],
    recomputedFine2024: 0,
    recomputedFine2030: 6500,
    citation: "NYSERDA Multifamily Retrofit Guide 2021",
  },
  {
    id: "heat-pump-conversion",
    name: "Heat Pump Conversion",
    description:
      "Replace gas-fired heating with high-efficiency air-source heat pumps and upgrade controls.",
    reductionPct: 0.25,
    costLow: 12.0,
    costHigh: 24.0,
    recomputedFineSeries: [
      { year: 2026, projectedAnnualFineUsd: 0 },
      { year: 2030, projectedAnnualFineUsd: 0 },
    ],
    recomputedFine2024: 0,
    recomputedFine2030: 0,
    citation: "RMI Building Electrification 2023",
  },
];
