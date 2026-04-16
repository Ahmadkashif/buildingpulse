import { render, screen } from "@testing-library/react";

import { ForecastProgress } from "./forecast-progress";

describe("ForecastProgress", () => {
  it("renders initial stage copy", () => {
    render(<ForecastProgress tickMs={10_000} />);
    expect(screen.getByText("buildingPulse Prediction Engine")).toBeInTheDocument();
    expect(screen.getByText("Calibrating…")).toBeInTheDocument();
    expect(screen.getByText(/Warming up/)).toBeInTheDocument();
  });
});
