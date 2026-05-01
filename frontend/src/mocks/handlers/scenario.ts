import { http, HttpResponse } from "msw";

import { SCENARIO_FIXTURES } from "@/mocks/data/scenarios";

export const scenarioHandlers = [
  http.get("/api/predictions/:id/scenarios", () => {
    return HttpResponse.json({ data: SCENARIO_FIXTURES });
  }),
];
