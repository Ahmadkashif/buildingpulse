import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApiResponse, BuildingBorough, BuildingPropertyType } from "@/types";

export interface LeadCaptureInput {
  predictionId: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  consentGiven: true;
  scenarioId?: string | null;
  propertyType: BuildingPropertyType;
  borough: BuildingBorough;
  grossFloorAreaSqft: number;
  yearBuilt: number;
  predictedEui: number;
  projectedFineUsd: number;
  atRisk: boolean;
  reportUrl: string;
}

export interface LeadCaptureResult {
  id: string;
}

export function useLeadCapture() {
  return useMutation({
    mutationFn: (input: LeadCaptureInput) =>
      apiClient.post<ApiResponse<LeadCaptureResult>>("/api/leads", { body: input }),
  });
}
