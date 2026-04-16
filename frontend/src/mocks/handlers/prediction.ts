import { http, HttpResponse } from "msw";

import { PREDICTION_FIXTURES, findPrediction } from "@/mocks/data/predictions";
import type { CreateBuildingInput } from "@/types";

export const predictionHandlers = [
  /** Submit building specs, receive a full prediction payload. */
  http.post("/api/predictions", async ({ request }) => {
    // Shape is validated on the client; echo input into the fixture.
    const input = (await request.json()) as CreateBuildingInput;
    const fixture = PREDICTION_FIXTURES[0]!;
    return HttpResponse.json(
      {
        data: {
          ...fixture,
          id: `pred_${Math.random().toString(36).slice(2, 10)}`,
          generatedAt: new Date().toISOString(),
          input,
        },
      },
      { status: 201 },
    );
  }),

  http.get("/api/predictions/:id", ({ params }) => {
    const prediction = findPrediction(String(params.id)) ?? PREDICTION_FIXTURES[0];
    if (!prediction) {
      return HttpResponse.json(
        { message: "Prediction not found", code: "NOT_FOUND", status: 404 },
        { status: 404 },
      );
    }
    return HttpResponse.json({ data: { ...prediction, id: String(params.id) } });
  }),
];
