import { renderHook, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { vi } from "vitest";

import { server } from "@/mocks/server";
import { useChooseScenario } from "./use-choose-scenario";
import type { ScenarioPublic } from "@/types";

const SCENARIO: ScenarioPublic = {
  id: "heat-pump-conversion",
  name: "Heat Pumps",
  description: "Replace boilers.",
  reductionPct: 0.35,
  costLow: 12,
  costHigh: 30,
  recomputedFineSeries: [],
  recomputedFine2024: 0,
  recomputedFine2030: 0,
  citation: "NYC Mayor's Office",
};

describe("useChooseScenario", () => {
  it("posts to /api/scenarios/:id/select with the prediction id, then redirects to /api/sponsor/cta carrying both ids", async () => {
    const captured: { url: string; body: unknown }[] = [];
    server.use(
      http.post("/api/scenarios/:id/select", async ({ request, params }) => {
        captured.push({
          url: `/api/scenarios/${String(params.id)}/select`,
          body: await request.json(),
        });
        return HttpResponse.json({
          data: {
            predictionId: "pred_xyz",
            scenarioId: String(params.id),
            deduped: false,
          },
        });
      }),
    );
    const redirect = vi.fn();
    const { result } = renderHook(() =>
      useChooseScenario("pred_xyz", { redirect }),
    );

    await act(async () => {
      await result.current(SCENARIO);
    });

    expect(captured).toHaveLength(1);
    expect(captured[0]!.url).toBe("/api/scenarios/heat-pump-conversion/select");
    expect(captured[0]!.body).toEqual({ predictionId: "pred_xyz" });

    expect(redirect).toHaveBeenCalledTimes(1);
    const target = redirect.mock.calls[0]![0] as string;
    expect(target).toContain("/api/sponsor/cta");
    expect(target).toContain("prediction_id=pred_xyz");
    expect(target).toContain("scenario_id=heat-pump-conversion");
  });

  it("ignores rapid re-entrant calls so a double-click only fires one POST", async () => {
    let calls = 0;
    server.use(
      http.post("/api/scenarios/:id/select", async () => {
        calls += 1;
        // Hold the request long enough that the second invocation overlaps.
        await new Promise((r) => setTimeout(r, 25));
        return HttpResponse.json({
          data: { predictionId: "pred_dup", scenarioId: SCENARIO.id, deduped: false },
        });
      }),
    );
    const redirect = vi.fn();
    const { result } = renderHook(() =>
      useChooseScenario("pred_dup", { redirect }),
    );

    await act(async () => {
      const first = result.current(SCENARIO);
      const second = result.current(SCENARIO);
      await Promise.all([first, second]);
    });

    expect(calls).toBe(1);
    expect(redirect).toHaveBeenCalledTimes(1);
  });

  it("still redirects when the audit POST fails so the user is not stranded", async () => {
    server.use(
      http.post("/api/scenarios/:id/select", () =>
        HttpResponse.json(
          { message: "boom", code: "INTERNAL", status: 500 },
          { status: 500 },
        ),
      ),
    );
    const redirect = vi.fn();
    const { result } = renderHook(() =>
      useChooseScenario("pred_err", { redirect }),
    );

    await act(async () => {
      await result.current(SCENARIO);
    });

    expect(redirect).toHaveBeenCalledTimes(1);
    expect(redirect.mock.calls[0]![0]).toContain("prediction_id=pred_err");
  });
});
