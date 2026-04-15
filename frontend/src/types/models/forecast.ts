export interface ForecastStage {
  /** Progress milestone 0–100 where the stage copy becomes active. */
  threshold: number;
  headline: string;
  status: string;
}

export type ForecastInsightBadge = "savings" | "verified" | "yield-high" | "action";

export interface ForecastInsight {
  id: string;
  title: string;
  description: string;
  badge: ForecastInsightBadge;
}

export interface Forecast {
  id: string;
  buildingId: string;
  predictedAnnualConsumptionMwh: number;
  peakLoadMw: number;
  peakTimestamp: string;
  confidencePct: number;
  /** Monthly consumption breakdown: predicted vs savings potential. */
  breakdown: Array<{
    month: string;
    predicted: number;
    savingsPotential: number;
  }>;
  insights: ForecastInsight[];
}
