export type BuildingPropertyType =
  | "multifamily-housing"
  | "office"
  | "hotel"
  | "retail"
  | "hospital"
  | "mixed-use";

export type BuildingBorough = "manhattan" | "brooklyn" | "queens" | "bronx" | "staten-island";

export interface CreateBuildingInput {
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  grossFloorAreaSqft: number;
  yearBuilt: number;
  numberOfBuildings: number;
}
