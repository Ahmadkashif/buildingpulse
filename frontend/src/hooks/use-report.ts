import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, Report } from "@/types";

export const reportKeys = {
  all: ["reports"] as const,
  detail: (id: string) => [...reportKeys.all, id] as const,
};

export function useReport(id: string | undefined) {
  return useQuery({
    queryKey: id ? reportKeys.detail(id) : reportKeys.all,
    queryFn: () => apiClient.get<ApiResponse<Report>>(`/api/reports/${id}`),
    enabled: Boolean(id),
  });
}
