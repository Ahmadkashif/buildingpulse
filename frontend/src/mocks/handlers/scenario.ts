import { http, HttpResponse } from "msw";

import { SCENARIO_FIXTURES } from "@/mocks/data/scenarios";

export const scenarioHandlers = [
  http.get("/api/predictions/:id/scenarios", () => {
    return HttpResponse.json({ data: SCENARIO_FIXTURES });
  }),
  http.post("/api/scenarios/:scenarioId/select", async ({ params, request }) => {
    const body = (await request.json()) as { predictionId?: string };
    return HttpResponse.json({
      data: {
        predictionId: body.predictionId ?? "",
        scenarioId: String(params.scenarioId),
        deduped: false,
      },
    });
  }),
];
