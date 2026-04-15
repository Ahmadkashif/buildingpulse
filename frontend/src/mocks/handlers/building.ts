import { http, HttpResponse } from "msw";

import { BUILDING_FIXTURES } from "@/mocks/data/buildings";

export const buildingHandlers = [
  http.get("/api/buildings", () => HttpResponse.json({ data: BUILDING_FIXTURES })),
  http.get("/api/buildings/:id", ({ params }) => {
    const building = BUILDING_FIXTURES.find((b) => b.id === params.id);
    if (!building) {
      return HttpResponse.json(
        { message: "Building not found", code: "NOT_FOUND", status: 404 },
        { status: 404 },
      );
    }
    return HttpResponse.json({ data: building });
  }),
];
