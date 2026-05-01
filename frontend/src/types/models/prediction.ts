import type { BuildingBorough, BuildingPropertyType, CreateBuildingInput } from "./building";

export type CohortAgeBand = "pre-1950" | "1950-1979" | "1980-1999" | "2000-plus";

export interface Prediction {
  siteEuiKbtuPerSqft: number;
  intervalLow: number;
  intervalHigh: number;
  modelVersion: string;
}

export interface PeerCohort {
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  ageBand: CohortAgeBand;
}

export interface Peer {
  cohort: PeerCohort;
  cohortSize: number;
  medianSiteEui: number;
  p25SiteEui: number;
  p75SiteEui: number;
  /** 0-100. Higher = uses more energy than peers. */
  percentile: number;
}

export interface FineYear {
  year: number;
  projectedAnnualFineUsd: number;
}

export interface LL97 {
  capKbtuPerSqft2024To2029: number;
  capKbtuPerSqft2030To2034: number;
  projectedAnnualFineUsd2024: number;
  projectedAnnualFineUsd2030: number;
  atRisk: boolean;
  fineSeries: FineYear[];
}

export interface PredictionResponse {
  id: string;
  generatedAt: string;
  input: CreateBuildingInput;
  prediction: Prediction;
  peer: Peer;
  ll97: LL97;
}

/** Client-side derived insight variants rendered on the result page. */
export type InsightBadge = "savings" | "verified" | "yield-high" | "action";

export interface PredictionInsight {
  id: string;
  title: string;
  description: string;
  badge: InsightBadge;
}

/** Loading-screen milestone copy. */
export interface PredictionStage {
  threshold: number;
  headline: string;
  status: string;
}
