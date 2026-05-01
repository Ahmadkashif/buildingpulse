import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse, delay } from "msw";

import { server } from "@/mocks/server";
import { SPONSOR_FIXTURE } from "@/mocks/data/sponsor";
import { SponsorStrip } from "./sponsor-strip";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("SponsorStrip", () => {
  it("renders a loading skeleton while fetching", () => {
    server.use(
      http.get("/api/sponsor", async () => {
        await delay("infinite");
        return HttpResponse.json({ data: SPONSOR_FIXTURE });
      }),
    );

    renderWithClient(<SponsorStrip />);
    const region = screen.getByRole("status", { name: /loading sponsor/i });
    expect(region).toHaveAttribute("data-state", "loading");
  });

  it("renders sponsor logo and 'Powered by' text on success", async () => {
    renderWithClient(<SponsorStrip />);

    const text = await screen.findByText(/powered by/i);
    expect(text).toBeInTheDocument();
    expect(screen.getByText(SPONSOR_FIXTURE.name)).toBeInTheDocument();

    const logo = screen.getByRole("img", { name: /consolidated edison logo/i });
    expect(logo).toHaveAttribute("src", SPONSOR_FIXTURE.logoUrl);
  });

  it("falls back to a neutral 'Powered by BuildingPulse' on error", async () => {
    server.use(
      http.get("/api/sponsor", () =>
        HttpResponse.json({ message: "boom", code: "INTERNAL", status: 500 }, { status: 500 }),
      ),
    );

    renderWithClient(<SponsorStrip />);

    await waitFor(() => {
      const strip = document.querySelector('[data-slot="sponsor-strip"]');
      expect(strip).toHaveAttribute("data-state", "error");
    });
    expect(screen.getByText(/powered by buildingpulse/i)).toBeInTheDocument();
  });
});
