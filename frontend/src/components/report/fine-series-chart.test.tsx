import { render, screen } from "@testing-library/react";

import { FineSeriesChart, formatCurrency } from "./fine-series-chart";
import type { FineYear } from "@/types";

const STRADDLING: FineYear[] = [
  { year: 2026, projectedAnnualFineUsd: 0 },
  { year: 2027, projectedAnnualFineUsd: 0 },
  { year: 2028, projectedAnnualFineUsd: 0 },
  { year: 2029, projectedAnnualFineUsd: 0 },
  { year: 2030, projectedAnnualFineUsd: 12400 },
  { year: 2031, projectedAnnualFineUsd: 12400 },
  { year: 2032, projectedAnnualFineUsd: 12400 },
  { year: 2033, projectedAnnualFineUsd: 12400 },
  { year: 2034, projectedAnnualFineUsd: 12400 },
];

const UNDER: FineYear[] = STRADDLING.map((row) => ({ ...row, projectedAnnualFineUsd: 0 }));
const OVER: FineYear[] = STRADDLING.map((row) => ({ ...row, projectedAnnualFineUsd: 8000 }));

describe("FineSeriesChart", () => {
  it("renders both flat segments and the 2030 step for a straddling case", () => {
    render(<FineSeriesChart title="LL97 Fine Outlook" data={STRADDLING} />);

    expect(screen.getByText("LL97 Fine Outlook")).toBeInTheDocument();
    expect(screen.getByTestId("ll97-segment-2024-2029")).toBeInTheDocument();
    expect(screen.getByTestId("ll97-segment-2030-2034")).toBeInTheDocument();
    expect(screen.getByTestId("ll97-step-2030")).toBeInTheDocument();
    expect(screen.getByText("2030 cliff")).toBeInTheDocument();
  });

  it("renders both segments without a step when fines are flat across the cliff (under case)", () => {
    render(<FineSeriesChart title="LL97 Fine Outlook" data={UNDER} />);

    expect(screen.getByTestId("ll97-segment-2024-2029")).toBeInTheDocument();
    expect(screen.getByTestId("ll97-segment-2030-2034")).toBeInTheDocument();
    expect(screen.queryByTestId("ll97-step-2030")).toBeNull();
  });

  it("renders both segments without a step when fines are flat across the cliff (over case)", () => {
    render(<FineSeriesChart title="LL97 Fine Outlook" data={OVER} />);

    expect(screen.getByTestId("ll97-segment-2024-2029")).toBeInTheDocument();
    expect(screen.getByTestId("ll97-segment-2030-2034")).toBeInTheDocument();
    expect(screen.queryByTestId("ll97-step-2030")).toBeNull();
  });

  it("handles an empty fine series without crashing", () => {
    render(<FineSeriesChart title="LL97 Fine Outlook" data={[]} />);

    expect(screen.getByTestId("ll97-fine-series-empty")).toBeInTheDocument();
    expect(screen.queryByTestId("ll97-step-2030")).toBeNull();
  });

  it("formats projected fines as USD with no fractional digits in the summary", () => {
    render(<FineSeriesChart title="LL97 Fine Outlook" data={STRADDLING} />);

    const summary = screen.getByTestId("ll97-fine-series-summary");
    expect(summary.textContent).toContain("$0/yr");
    expect(summary.textContent).toContain("$12,400/yr");
  });

  it("formats currency with no fractional digits", () => {
    expect(formatCurrency(0)).toBe("$0");
    expect(formatCurrency(12400)).toBe("$12,400");
    expect(formatCurrency(1234567)).toBe("$1,234,567");
  });
});
