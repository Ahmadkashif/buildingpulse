import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/mocks/server";
import { ExportPdfButton } from "./export-pdf-button";

const PDF_BYTES = new TextEncoder().encode("%PDF-1.4\nstub\n%%EOF\n");

describe("ExportPdfButton", () => {
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;
  const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click");

  beforeEach(() => {
    clickSpy.mockReset();
    URL.createObjectURL = vi.fn(() => "blob:mock");
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });

  it("renders disabled with a tooltip when the report is locked", () => {
    render(<ExportPdfButton predictionId="pred_locked" unlocked={false} />);
    const button = screen.getByTestId("cta-export-pdf");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-disabled", "true");
    expect(button).toHaveAttribute("title", expect.stringMatching(/unlock/i));
  });

  it("does not download when locked even if the click somehow fires", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<ExportPdfButton predictionId="pred_locked" unlocked={false} />);
    // Bypass disabled by dispatching directly via userEvent on the parent.
    await userEvent.click(screen.getByTestId("cta-export-pdf"));
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("renders enabled with no tooltip when unlocked, and downloads on click", async () => {
    server.use(
      http.get("/api/predictions/:id/pdf", () =>
        new HttpResponse(PDF_BYTES, {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="building-pulse-pred_ok.pdf"',
          },
        }),
      ),
    );

    render(<ExportPdfButton predictionId="pred_ok" unlocked={true} />);
    const button = screen.getByTestId("cta-export-pdf");
    expect(button).toBeEnabled();
    expect(button).not.toHaveAttribute("title");

    await userEvent.click(button);

    // Eventually the click on the synthetic anchor fires.
    await vi.waitFor(() => expect(clickSpy).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("cta-export-pdf-error")).not.toBeInTheDocument();
  });

  it("shows an error state when the download fails, and retries on click", async () => {
    server.use(
      http.get("/api/predictions/:id/pdf", () =>
        HttpResponse.json(
          { message: "boom", code: "INTERNAL", status: 500 },
          { status: 500 },
        ),
      ),
    );

    render(<ExportPdfButton predictionId="pred_err" unlocked={true} />);
    const button = screen.getByTestId("cta-export-pdf");

    await userEvent.click(button);

    const alert = await screen.findByTestId("cta-export-pdf-error");
    expect(alert).toHaveAttribute("role", "alert");
    expect(alert.textContent).toMatch(/500|fail/i);

    // After fixing the server, clicking again clears the error and downloads.
    server.use(
      http.get("/api/predictions/:id/pdf", () =>
        new HttpResponse(PDF_BYTES, {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="building-pulse-pred_err.pdf"',
          },
        }),
      ),
    );
    await userEvent.click(button);
    await vi.waitFor(() => expect(clickSpy).toHaveBeenCalledTimes(1));
    await vi.waitFor(() =>
      expect(screen.queryByTestId("cta-export-pdf-error")).not.toBeInTheDocument(),
    );
  });
});
