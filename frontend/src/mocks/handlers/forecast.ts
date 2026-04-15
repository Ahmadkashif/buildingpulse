import { http, HttpResponse } from "msw";

import { FORECAST_FIXTURES, findForecast } from "@/mocks/data/forecasts";
import type { CreateBuildingInput } from "@/types";

export const forecastHandlers = [
  /** Submit building specs, receive a forecast id. */
  http.post("/api/forecasts", async ({ request }) => {
    // Input shape is validated on the client; we just acknowledge and return the fixture.
    await (request.json() as Promise<CreateBuildingInput>);
    const fixture = FORECAST_FIXTURES[0];
    return HttpResponse.json({ data: { id: fixture!.id } }, { status: 201 });
  }),

  http.get("/api/forecasts/:id", ({ params }) => {
    const forecast = findForecast(String(params.id));
    if (!forecast) {
      return HttpResponse.json(
        { message: "Forecast not found", code: "NOT_FOUND", status: 404 },
        { status: 404 },
      );
    }
    return HttpResponse.json({ data: forecast });
  }),
];
