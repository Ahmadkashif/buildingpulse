import type { FineYear } from "./prediction";

export interface ScenarioPublic {
  id: string;
  name: string;
  description: string;
  /** Fractional EUI reduction. 0.18 == 18%. */
  reductionPct: number;
  /** USD per sqft, low end of the cost band. */
  costLow: number;
  /** USD per sqft, high end of the cost band. */
  costHigh: number;
  recomputedFineSeries: FineYear[];
  recomputedFine2024: number;
  recomputedFine2030: number;
  citation: string;
}
