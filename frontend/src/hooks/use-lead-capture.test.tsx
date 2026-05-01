import * as React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";

import { server } from "@/mocks/server";
import { useLeadCapture, type LeadCaptureInput } from "./use-lead-capture";

function makeWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

const INPUT: LeadCaptureInput = {
  predictionId: "pred_abc",
  name: "Jane",
  email: "jane@example.com",
  phone: "+1 212 555 0100",
  role: "owner",
  consentGiven: true,
  scenarioId: null,
  propertyType: "office",
  borough: "manhattan",
  grossFloorAreaSqft: 100_000,
  yearBuilt: 1990,
  predictedEui: 95,
  projectedFineUsd: 12345,
  atRisk: true,
  reportUrl: "http://localhost/r",
};

describe("useLeadCapture", () => {
  it("posts to /api/leads and returns the new lead id on success", async () => {
    server.use(
      http.post("/api/leads", () =>
        HttpResponse.json({ data: { id: "lead_ok" } }, { status: 201 }),
      ),
    );
    const { result } = renderHook(() => useLeadCapture(), { wrapper: makeWrapper() });
    result.current.mutate(INPUT);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.data.id).toBe("lead_ok");
  });

  it("surfaces an error when the server rejects the request", async () => {
    server.use(
      http.post("/api/leads", () =>
        HttpResponse.json({ message: "boom", code: "INTERNAL", status: 500 }, { status: 500 }),
      ),
    );
    const { result } = renderHook(() => useLeadCapture(), { wrapper: makeWrapper() });
    result.current.mutate(INPUT);
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
