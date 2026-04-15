import { http, HttpResponse } from "msw";

import { findReport } from "@/mocks/data/reports";

export const reportHandlers = [
  http.get("/api/reports/:id", ({ params }) => {
    const report = findReport(String(params.id));
    if (!report) {
      return HttpResponse.json(
        { message: "Report not found", code: "NOT_FOUND", status: 404 },
        { status: 404 },
      );
    }
    return HttpResponse.json({ data: report });
  }),

  /** PDF export — scaffold stub, returns immediately with a placeholder url. */
  http.post("/api/reports/:id/export", ({ params }) => {
    return HttpResponse.json({
      data: {
        reportId: String(params.id),
        url: `/api/reports/${params.id}/export.pdf`,
        status: "ready",
      },
    });
  }),
];
