export type BuildingPropertyType =
  | "commercial-office"
  | "residential-multifamily"
  | "mixed-use"
  | "industrial"
  | "retail";

export type BuildingBorough = "manhattan" | "brooklyn" | "queens" | "bronx" | "staten-island";

export interface Building {
  id: string;
  name: string;
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  grossFloorAreaSqft: number;
  yearBuilt: number;
  numberOfBuildingsOnLot: number;
}

export interface CreateBuildingInput {
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  grossFloorAreaSqft: number;
  yearBuilt: number;
  numberOfBuildingsOnLot: number;
}
