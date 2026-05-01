import type { AddressMatch } from "@/types";

/** Fixtures returned by the /api/address/lookup MSW handler.
 *
 * The match logic is intentionally simple: any address string that, after
 * upper-casing and trimming, contains the fixture's `addressNormalized`
 * value (or vice-versa) is treated as a hit. Anything else is a miss.
 */
export const ADDRESS_FIXTURES: AddressMatch[] = [
  {
    bbl: "1-00123-0001",
    addressRaw: "100 Synth St, Manhattan, NY",
    addressNormalized: "100 SYNTH ST",
    propertyType: "office",
    borough: "manhattan",
    grossFloorAreaSqft: 75_000,
    yearBuilt: 1985,
    numberOfBuildings: 1,
    siteEui: 88.4,
    confidence: "high",
  },
];

export function findAddressMatch(query: string): AddressMatch | null {
  const needle = query.trim().toUpperCase();
  if (!needle) return null;
  for (const record of ADDRESS_FIXTURES) {
    if (needle.includes(record.addressNormalized) || record.addressNormalized.includes(needle)) {
      return record;
    }
  }
  return null;
}
