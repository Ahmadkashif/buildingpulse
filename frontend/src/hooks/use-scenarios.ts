import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type {
  ApiResponse,
  BuildingPropertyType,
  ScenarioPublic,
} from "@/types";

export interface ScenarioQueryArgs {
  predictionId: string;
  propertyType: BuildingPropertyType;
  predictedEui: number;
  grossFloorAreaSqft: number;
}

export const scenarioKeys = {
  all: ["scenarios"] as const,
  detail: (args: ScenarioQueryArgs) =>
    [
      ...scenarioKeys.all,
      args.predictionId,
      args.propertyType,
      args.predictedEui,
      args.grossFloorAreaSqft,
    ] as const,
};

export function useScenarios(args: ScenarioQueryArgs | null) {
  return useQuery({
    queryKey: args ? scenarioKeys.detail(args) : scenarioKeys.all,
    queryFn: () => {
      if (!args) throw new Error("scenario args required");
      return apiClient.get<ApiResponse<ScenarioPublic[]>>(
        `/api/predictions/${args.predictionId}/scenarios`,
        {
          params: {
            propertyType: args.propertyType,
            predictedEui: String(args.predictedEui),
            grossFloorAreaSqft: String(args.grossFloorAreaSqft),
          },
        },
      );
    },
    enabled: Boolean(args),
  });
}
