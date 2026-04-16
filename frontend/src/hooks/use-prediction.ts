import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, CreateBuildingInput, PredictionResponse } from "@/types";

export const predictionKeys = {
  all: ["predictions"] as const,
  detail: (id: string) => [...predictionKeys.all, id] as const,
};

export function usePredict() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateBuildingInput) =>
      apiClient.post<ApiResponse<PredictionResponse>>("/api/predictions", { body: input }),
    onSuccess: (response) => {
      queryClient.setQueryData(predictionKeys.detail(response.data.id), response);
    },
  });
}

export function usePrediction(id: string | undefined) {
  return useQuery({
    queryKey: id ? predictionKeys.detail(id) : predictionKeys.all,
    queryFn: () => apiClient.get<ApiResponse<PredictionResponse>>(`/api/predictions/${id}`),
    enabled: Boolean(id),
  });
}
