import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AddressMatch, ApiError, ApiResponse } from "@/types";

export type AddressLookupError = ApiError & { kind: "miss" | "error" };

async function lookupAddress(address: string): Promise<AddressMatch> {
  try {
    const response = await apiClient.get<ApiResponse<AddressMatch>>("/api/address/lookup", {
      params: { address },
    });
    return response.data;
  } catch (raw) {
    const err = raw as ApiError;
    const tagged: AddressLookupError = {
      ...err,
      kind: err.status === 404 ? "miss" : "error",
    };
    throw tagged;
  }
}

export function useAddressLookup() {
  return useMutation<AddressMatch, AddressLookupError, string>({
    mutationFn: lookupAddress,
  });
}
