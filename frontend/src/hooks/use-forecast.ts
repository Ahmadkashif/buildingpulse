import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, CreateBuildingInput, Forecast } from "@/types";

export const forecastKeys = {
  all: ["forecasts"] as const,
  detail: (id: string) => [...forecastKeys.all, id] as const,
};

export function usePredictEui() {
  return useMutation({
    mutationFn: (input: CreateBuildingInput) =>
      apiClient.post<ApiResponse<{ id: string }>>("/api/forecasts", { body: input }),
  });
}

export function useForecast(id: string | undefined) {
  return useQuery({
    queryKey: id ? forecastKeys.detail(id) : forecastKeys.all,
    queryFn: () => apiClient.get<ApiResponse<Forecast>>(`/api/forecasts/${id}`),
    enabled: Boolean(id),
  });
}
