import { render, screen } from "@testing-library/react";

import { Badge } from "./badge";

describe("Badge", () => {
  it("renders its children", () => {
    render(<Badge variant="savings">Savings</Badge>);
    expect(screen.getByText("Savings")).toBeInTheDocument();
  });

  it("defaults to neutral variant", () => {
    render(<Badge>Plain</Badge>);
    const el = screen.getByText("Plain");
    expect(el).toHaveAttribute("data-slot", "badge");
  });
});
