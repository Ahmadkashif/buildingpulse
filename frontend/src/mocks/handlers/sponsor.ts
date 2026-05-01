import { http, HttpResponse } from "msw";

import { SPONSOR_FIXTURE } from "@/mocks/data/sponsor";

export const sponsorHandlers = [
  http.get("/api/sponsor", () => {
    return HttpResponse.json({ data: SPONSOR_FIXTURE });
  }),
];
