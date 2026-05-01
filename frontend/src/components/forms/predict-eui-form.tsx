"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Calendar } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { FormField } from "@/components/forms/form-field";
import { AddressLookupField } from "@/components/forms/address-lookup-field";
import { usePredict } from "@/hooks/use-prediction";
import { isAddressLookupEnabled } from "@/lib/address-lookup-flag";
import type {
  AddressMatch,
  BuildingBorough,
  BuildingPropertyType,
  CreateBuildingInput,
} from "@/types";

const PROPERTY_TYPES: Array<{ value: BuildingPropertyType; label: string }> = [
  { value: "multifamily-housing", label: "Multifamily Housing" },
  { value: "office", label: "Office" },
  { value: "hotel", label: "Hotel" },
  { value: "retail", label: "Retail" },
  { value: "hospital", label: "Hospital" },
  { value: "mixed-use", label: "Mixed Use" },
];

const BOROUGHS: Array<{ value: BuildingBorough; label: string }> = [
  { value: "manhattan", label: "Manhattan" },
  { value: "brooklyn", label: "Brooklyn" },
  { value: "queens", label: "Queens" },
  { value: "bronx", label: "Bronx" },
  { value: "staten-island", label: "Staten Island" },
];

export function PredictEuiForm() {
  const router = useRouter();
  const predict = usePredict();

  const [propertyType, setPropertyType] = React.useState<BuildingPropertyType | "">("");
  const [borough, setBorough] = React.useState<BuildingBorough | "">("");
  const [grossFloorArea, setGrossFloorArea] = React.useState("");
  const [yearBuilt, setYearBuilt] = React.useState("");
  const [numberOfBuildings, setNumberOfBuildings] = React.useState(1);

  const addressLookupEnabled = isAddressLookupEnabled();

  const onAddressMatch = (match: AddressMatch) => {
    setPropertyType(match.propertyType);
    setBorough(match.borough);
    setGrossFloorArea(String(match.grossFloorAreaSqft));
    setYearBuilt(String(match.yearBuilt));
    setNumberOfBuildings(Math.max(1, match.numberOfBuildings || 1));
  };

  const isValid =
    propertyType !== "" &&
    borough !== "" &&
    Number(grossFloorArea) > 0 &&
    Number(yearBuilt) >= 1800 &&
    Number(yearBuilt) <= 2026;

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!isValid) return;

    const input: CreateBuildingInput = {
      propertyType: propertyType as BuildingPropertyType,
      borough: borough as BuildingBorough,
      grossFloorAreaSqft: Number(grossFloorArea),
      yearBuilt: Number(yearBuilt),
      numberOfBuildings,
    };

    predict.mutate(input, {
      onSuccess: (response) => {
        router.push(`/report/predicting?predictionId=${response.data.id}`);
      },
    });
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-8">
      {addressLookupEnabled ? <AddressLookupField onMatch={onAddressMatch} /> : null}
      <div className="grid gap-6 md:grid-cols-2">
        <FormField label="Property Type" htmlFor="property-type">
          <Select
            id="property-type"
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value as BuildingPropertyType)}
          >
            <option value="" disabled>
              Select property type
            </option>
            {PROPERTY_TYPES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Borough" htmlFor="borough">
          <Select
            id="borough"
            value={borough}
            onChange={(e) => setBorough(e.target.value as BuildingBorough)}
          >
            <option value="" disabled>
              Select borough
            </option>
            {BOROUGHS.map((b) => (
              <option key={b.value} value={b.value}>
                {b.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          label="Gross Floor Area (sq ft)"
          htmlFor="gross-floor-area"
          hint="Accepted range: 500 – 5,000,000 sq ft"
        >
          <div className="relative">
            <Input
              id="gross-floor-area"
              type="number"
              inputMode="numeric"
              min={500}
              max={5000000}
              placeholder="e.g. 50,000"
              value={grossFloorArea}
              onChange={(e) => setGrossFloorArea(e.target.value)}
              className="pr-16"
            />
            <span className="text-on-surface-variant text-label-sm pointer-events-none absolute top-1/2 right-3 -translate-y-1/2">
              sq ft
            </span>
          </div>
        </FormField>

        <FormField label="Year Built" htmlFor="year-built" hint="Accepted range: 1800 – 2026">
          <div className="relative">
            <Input
              id="year-built"
              type="number"
              inputMode="numeric"
              min={1800}
              max={2026}
              placeholder="YYYY"
              value={yearBuilt}
              onChange={(e) => setYearBuilt(e.target.value)}
              className="pr-10"
            />
            <Calendar className="text-on-surface-variant pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2" />
          </div>
        </FormField>
      </div>

      <FormField label="Number of Buildings on Lot">
        <div className="flex items-center gap-4">
          <Slider
            value={numberOfBuildings}
            onValueChange={setNumberOfBuildings}
            min={1}
            max={10}
            aria-label="Number of buildings on lot"
          />
          <div className="bg-surface-container-high text-on-surface grid h-10 w-14 shrink-0 place-items-center rounded-md text-sm font-semibold tabular-nums">
            {numberOfBuildings}
          </div>
        </div>
      </FormField>

      <div className="flex flex-col items-center gap-3">
        <Button type="submit" variant="gradient" size="lg" disabled={!isValid || predict.isPending}>
          {predict.isPending ? "Predicting…" : "Predict EUI"}
          <ArrowRight className="size-4" />
        </Button>
        <p className="text-on-surface-variant text-xs">
          Calculations are based on NYC Local Law 84 benchmark data.
        </p>
      </div>
    </form>
  );
}
