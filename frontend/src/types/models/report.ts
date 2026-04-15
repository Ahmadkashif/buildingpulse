export interface ReportKpi {
  label: string;
  value: string;
  caption?: string;
  accent?: "primary" | "secondary" | "tertiary";
  signature?: boolean;
}

export interface ReportAsset {
  buildingName: string;
  value: string;
  unit?: string;
  /** Optional 0..1 relative magnitude used for the inline bar in asset cards. */
  variance?: number;
}

export interface Report {
  id: string;
  buildingName: string;
  generatedAt: string;
  kpis: ReportKpi[];
  rankedAssets: ReportAsset[];
  profile: Array<{ label: string; value: string }>;
}
