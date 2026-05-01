import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse, delay } from "msw";
import { vi } from "vitest";

import { server } from "@/mocks/server";
import { SCENARIO_FIXTURES } from "@/mocks/data/scenarios";
import { ScenariosCard } from "./scenarios-card";
import type { ScenarioQueryArgs } from "@/hooks/use-scenarios";

const QUERY: ScenarioQueryArgs = {
  predictionId: "pred_test_001",
  propertyType: "office",
  predictedEui: 95.4,
  grossFloorAreaSqft: 100_000,
};

function renderCard(props: Partial<React.ComponentProps<typeof ScenariosCard>> = {}) {
  const onRequestUnlock = props.onRequestUnlock ?? vi.fn();
  const onChooseScenario = props.onChooseScenario ?? vi.fn();
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const utils = render(
    <QueryClientProvider client={client}>
      <ScenariosCard
        unlocked={props.unlocked ?? false}
        query={props.query ?? QUERY}
        onRequestUnlock={onRequestUnlock}
        onChooseScenario={onChooseScenario}
      />
    </QueryClientProvider>,
  );
  return { ...utils, onRequestUnlock, onChooseScenario };
}

describe("ScenariosCard", () => {
  describe("hidden state", () => {
    it("renders the unlock CTA and no scenario items when not unlocked", () => {
      renderCard({ unlocked: false });
      const card = document.querySelector('[data-slot="scenarios-card"]');
      expect(card).toHaveAttribute("data-state", "hidden");
      expect(screen.getByTestId("cta-see-retrofit-options")).toBeInTheDocument();
      expect(screen.queryByTestId("scenarios-list")).toBeNull();
      // No scenario fields are rendered before unlock.
      for (const s of SCENARIO_FIXTURES) {
        expect(screen.queryByText(s.name)).toBeNull();
      }
    });

    it("invokes onRequestUnlock when the CTA is clicked", async () => {
      const user = userEvent.setup();
      const { onRequestUnlock } = renderCard({ unlocked: false });
      await user.click(screen.getByTestId("cta-see-retrofit-options"));
      expect(onRequestUnlock).toHaveBeenCalledTimes(1);
    });
  });

  describe("visible state", () => {
    it("renders each scenario with all API fields after unlock", async () => {
      renderCard({ unlocked: true });

      await screen.findByTestId("scenarios-list");
      const card = document.querySelector('[data-slot="scenarios-card"]');
      expect(card).toHaveAttribute("data-state", "visible");

      for (const s of SCENARIO_FIXTURES) {
        expect(screen.getByText(s.name)).toBeInTheDocument();
        expect(screen.getByText(s.description)).toBeInTheDocument();
        expect(
          screen.getByText(`${Math.round(s.reductionPct * 100)}% EUI reduction`),
        ).toBeInTheDocument();
        expect(
          screen.getByText(`$${s.costLow.toFixed(2)}–$${s.costHigh.toFixed(2)}/sqft`),
        ).toBeInTheDocument();
        expect(
          screen.getByText(
            `$${Math.round(s.recomputedFine2030).toLocaleString()}/yr by 2030`,
          ),
        ).toBeInTheDocument();
        expect(screen.getByText(`Source: ${s.citation}`)).toBeInTheDocument();
      }

      const chooseButtons = screen.getAllByTestId("cta-choose-scenario");
      expect(chooseButtons).toHaveLength(SCENARIO_FIXTURES.length);
    });

    it("renders a loading state while the request is in flight", () => {
      server.use(
        http.get("/api/predictions/:id/scenarios", async () => {
          await delay("infinite");
          return HttpResponse.json({ data: [] });
        }),
      );
      renderCard({ unlocked: true });
      const card = document.querySelector('[data-slot="scenarios-card"]');
      expect(card).toHaveAttribute("data-state", "loading");
      expect(screen.getByRole("status", { name: /loading retrofit scenarios/i })).toBeInTheDocument();
    });

    it("invokes onChooseScenario when 'Choose this scenario' is clicked", async () => {
      const user = userEvent.setup();
      const { onChooseScenario } = renderCard({ unlocked: true });
      await screen.findByTestId("scenarios-list");
      const buttons = screen.getAllByTestId("cta-choose-scenario");
      await user.click(buttons[0]!);
      expect(onChooseScenario).toHaveBeenCalledTimes(1);
      expect(onChooseScenario).toHaveBeenCalledWith(
        expect.objectContaining({ id: SCENARIO_FIXTURES[0]!.id }),
      );
    });
  });

  describe("error state", () => {
    it("renders an alert when the API returns an error", async () => {
      server.use(
        http.get("/api/predictions/:id/scenarios", () =>
          HttpResponse.json(
            { message: "boom", code: "INTERNAL", status: 500 },
            { status: 500 },
          ),
        ),
      );
      renderCard({ unlocked: true });

      await waitFor(() => {
        const card = document.querySelector('[data-slot="scenarios-card"]');
        expect(card).toHaveAttribute("data-state", "error");
      });
      expect(screen.getByRole("alert")).toHaveTextContent(/couldn't load/i);
      expect(screen.queryByTestId("scenarios-list")).toBeNull();
    });
  });
});
