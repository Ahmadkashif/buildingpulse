import type { BuildingBorough, BuildingPropertyType } from "./building";

export interface AddressMatch {
  bbl: string;
  addressRaw: string;
  addressNormalized: string;
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  grossFloorAreaSqft: number;
  yearBuilt: number;
  numberOfBuildings: number;
  siteEui: number | null;
  confidence: "high" | "low";
}
