import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, Building } from "@/types";

export const buildingKeys = {
  all: ["buildings"] as const,
  detail: (id: string) => [...buildingKeys.all, id] as const,
};

export function useBuildings() {
  return useQuery({
    queryKey: buildingKeys.all,
    queryFn: () => apiClient.get<ApiResponse<Building[]>>("/api/buildings"),
  });
}

export function useBuilding(id: string | undefined) {
  return useQuery({
    queryKey: id ? buildingKeys.detail(id) : buildingKeys.all,
    queryFn: () => apiClient.get<ApiResponse<Building>>(`/api/buildings/${id}`),
    enabled: Boolean(id),
  });
}
