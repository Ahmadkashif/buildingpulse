import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { server } from "@/mocks/server";
import { parseFilename, usePdfDownload } from "./use-pdf-download";

const PDF_BYTES = new TextEncoder().encode("%PDF-1.4\nfake\n%%EOF\n");

describe("parseFilename", () => {
  it("extracts the filename from a Content-Disposition header", () => {
    expect(parseFilename('attachment; filename="building-pulse-pred_1.pdf"')).toBe(
      "building-pulse-pred_1.pdf",
    );
    expect(parseFilename("attachment; filename=plain.pdf")).toBe("plain.pdf");
  });

  it("returns null when the header is missing or malformed", () => {
    expect(parseFilename(null)).toBeNull();
    expect(parseFilename("attachment")).toBeNull();
    expect(parseFilename('attachment; filename=""')).toBeNull();
  });
});

describe("usePdfDownload", () => {
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

  it("fetches the PDF and triggers a browser download with the server filename", async () => {
    server.use(
      http.get("/api/predictions/:id/pdf", () =>
        new HttpResponse(PDF_BYTES, {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="building-pulse-pred_1.pdf"',
          },
        }),
      ),
    );

    const { result } = renderHook(() => usePdfDownload());
    expect(result.current.status).toBe("idle");

    await act(async () => {
      await result.current.download("pred_1");
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.error).toBeNull();
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });

  it("transitions to error status when the server rejects the request", async () => {
    server.use(
      http.get("/api/predictions/:id/pdf", () =>
        HttpResponse.json(
          { message: "lead required", code: "FORBIDDEN", status: 403 },
          { status: 403 },
        ),
      ),
    );

    const { result } = renderHook(() => usePdfDownload());

    await act(async () => {
      await result.current.download("pred_locked");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toMatch(/403/);
    expect(clickSpy).not.toHaveBeenCalled();

    act(() => result.current.reset());
    await waitFor(() => expect(result.current.status).toBe("idle"));
    expect(result.current.error).toBeNull();
  });

  it("transitions to error status when the network fails", async () => {
    server.use(http.get("/api/predictions/:id/pdf", () => HttpResponse.error()));

    const { result } = renderHook(() => usePdfDownload());

    await act(async () => {
      await result.current.download("pred_net");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBeTruthy();
  });
});
