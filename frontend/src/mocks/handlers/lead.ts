import { http, HttpResponse } from "msw";

export const leadHandlers = [
  http.post("/api/leads", async () => {
    return HttpResponse.json(
      { data: { id: `lead_${Math.random().toString(36).slice(2, 10)}` } },
      { status: 201 },
    );
  }),
];
