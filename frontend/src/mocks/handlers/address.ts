import { http, HttpResponse } from "msw";

import { findAddressMatch } from "@/mocks/data/addresses";

export const addressHandlers = [
  http.get("/api/address/lookup", ({ request }) => {
    const url = new URL(request.url);
    const address = url.searchParams.get("address");
    if (!address || !address.trim()) {
      return HttpResponse.json(
        { message: "address query parameter is required", code: "INVALID", status: 422 },
        { status: 422 },
      );
    }
    const match = findAddressMatch(address);
    if (!match) {
      return HttpResponse.json(
        { message: "Address not found", code: "NOT_FOUND", status: 404 },
        { status: 404 },
      );
    }
    return HttpResponse.json({ data: match });
  }),
];
