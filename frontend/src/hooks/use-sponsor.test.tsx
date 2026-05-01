import * as React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";

import { server } from "@/mocks/server";
import { SPONSOR_FIXTURE } from "@/mocks/data/sponsor";
import { useSponsor, sponsorKeys } from "./use-sponsor";

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useSponsor", () => {
  it("exposes a stable query key", () => {
    expect(sponsorKeys.all).toEqual(["sponsor"]);
  });

  it("starts in a loading state before resolving", () => {
    const { result } = renderHook(() => useSponsor(), { wrapper: makeWrapper() });
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it("returns sponsor data on success", async () => {
    const { result } = renderHook(() => useSponsor(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.data).toEqual(SPONSOR_FIXTURE);
    expect(result.current.isError).toBe(false);
  });

  it("surfaces an error when the endpoint fails", async () => {
    server.use(
      http.get("/api/sponsor", () =>
        HttpResponse.json({ message: "boom", code: "INTERNAL", status: 500 }, { status: 500 }),
      ),
    );

    const { result } = renderHook(() => useSponsor(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});
