import { http, HttpResponse } from "msw";

const FAKE_PDF_BYTES = new TextEncoder().encode(
  "%PDF-1.4\n%mock\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n",
);

export const pdfHandlers = [
  http.get("/api/predictions/:id/pdf", ({ params }) => {
    const filename = `building-pulse-${String(params.id)}.pdf`;
    return new HttpResponse(FAKE_PDF_BYTES, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  }),
];
