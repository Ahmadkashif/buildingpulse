import { render, screen } from "@testing-library/react";

import { KpiTile } from "./kpi-tile";

describe("KpiTile", () => {
  it("renders label, value and caption", () => {
    render(
      <KpiTile
        label="Forecasting Confidence"
        value="96.8%"
        caption="High confidence based on historical data"
      />,
    );

    expect(screen.getByText("Forecasting Confidence")).toBeInTheDocument();
    expect(screen.getByText("96.8%")).toBeInTheDocument();
    expect(screen.getByText("High confidence based on historical data")).toBeInTheDocument();
  });

  it("applies signature data attribute when signature flag is set", () => {
    render(<KpiTile label="X" value="1" signature />);
    expect(screen.getByText("1").closest('[data-slot="kpi-tile"]')).toHaveAttribute(
      "data-signature",
      "",
    );
  });

  it("renders a delta chip when provided", () => {
    render(<KpiTile label="X" value="1" delta={{ value: "0.4%", direction: "up" }} />);
    expect(screen.getByText(/0.4%/)).toBeInTheDocument();
  });
});
