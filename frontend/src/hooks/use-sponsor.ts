import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, SponsorPublic } from "@/types";

export const sponsorKeys = {
  all: ["sponsor"] as const,
};

export function useSponsor() {
  return useQuery({
    queryKey: sponsorKeys.all,
    queryFn: () => apiClient.get<ApiResponse<SponsorPublic>>("/api/sponsor"),
  });
}
