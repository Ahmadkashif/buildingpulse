import type { Report } from "@/types";

export const REPORT_FIXTURES: Report[] = [
  {
    id: "report-nexus-plaza-a",
    buildingName: "Nexus Plaza Tower A",
    generatedAt: "2024-08-12T10:00:00-04:00",
    kpis: [
      {
        label: "Predicted Annual Consumption",
        value: "4,280 MWh",
        caption: "▲ 0.4% vs Previous Year",
        accent: "primary",
      },
      {
        label: "Peak Load Estimate",
        value: "1.85 MW",
        caption: "Expected peaking on Aug 14, 14:00 – 16:00",
        accent: "secondary",
      },
      {
        label: "Forecasting Confidence",
        value: "96.8%",
        caption:
          "High confidence based on 24 months of historical sensor data and localized weather.",
        signature: true,
      },
    ],
    rankedAssets: [
      { buildingName: "Nexus Plaza Tower A (Tier)", value: "—", unit: "" },
      { buildingName: "Westbridge Industrial", value: "2,640 MWh" },
      { buildingName: "City Hub Retail", value: "2,440 MWh" },
    ],
    profile: [
      { label: "Total Area", value: "124,500 sqft" },
      { label: "Year Built", value: "2014 (Renov. 2023)" },
      { label: "System Type", value: "District Geothermal/Gas Hybrid" },
      { label: "Occupancy", value: "850 FTE / Hybrid" },
      { label: "Primary Usage", value: "Commercial Office (Class A)" },
    ],
  },
];

export function findReport(id: string): Report | undefined {
  return REPORT_FIXTURES.find((r) => r.id === id);
}
