import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { usePredictEui, useForecast } from "./use-forecast";
import type { CreateBuildingInput } from "@/types";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

const SAMPLE_INPUT: CreateBuildingInput = {
  propertyType: "commercial-office",
  borough: "manhattan",
  grossFloorAreaSqft: 50000,
  yearBuilt: 2014,
  numberOfBuildingsOnLot: 1,
};

describe("usePredictEui", () => {
  it("posts building input and returns a forecast id", async () => {
    const { result } = renderHook(() => usePredictEui(), { wrapper: createWrapper() });

    result.current.mutate(SAMPLE_INPUT);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(typeof result.current.data?.data.id).toBe("string");
  });
});

describe("useForecast", () => {
  it("fetches the fixture forecast by id", async () => {
    const { result } = renderHook(() => useForecast("forecast-nexus-plaza-a"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.data.id).toBe("forecast-nexus-plaza-a");
    expect(result.current.data?.data.insights.length).toBeGreaterThan(0);
  });
});
