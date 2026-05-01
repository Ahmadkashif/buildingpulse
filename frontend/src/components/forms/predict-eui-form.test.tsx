import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import { PredictEuiForm } from "./predict-eui-form";

function renderForm() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <PredictEuiForm />
    </QueryClientProvider>,
  );
}

describe("PredictEuiForm — address lookup feature flag", () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("does not render the address lookup affordance by default (flag off)", () => {
    vi.stubEnv("NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED", "");
    renderForm();
    expect(screen.queryByTestId("address-lookup-field")).not.toBeInTheDocument();
    expect(screen.queryByTestId("address-lookup-input")).not.toBeInTheDocument();
  });

  it("renders the address lookup affordance when the flag is enabled", () => {
    vi.stubEnv("NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED", "true");
    renderForm();
    expect(screen.getByTestId("address-lookup-field")).toBeInTheDocument();
    expect(screen.getByTestId("address-lookup-input")).toBeInTheDocument();
  });

  it("on a successful address hit, auto-fills form fields but keeps them editable", async () => {
    vi.stubEnv("NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED", "true");
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByTestId("address-lookup-input"), "100 Synth St");
    await user.click(screen.getByTestId("address-lookup-submit"));

    const propertyType = screen.getByLabelText(/Property Type/i) as HTMLSelectElement;
    const borough = screen.getByLabelText(/Borough/i) as HTMLSelectElement;
    const gfa = screen.getByLabelText(/Gross Floor Area/i) as HTMLInputElement;
    const yearBuilt = screen.getByLabelText(/Year Built/i) as HTMLInputElement;

    await waitFor(() => expect(propertyType.value).toBe("office"));
    expect(borough.value).toBe("manhattan");
    expect(gfa.value).toBe("75000");
    expect(yearBuilt.value).toBe("1985");

    // Editable: user can override the auto-filled value.
    await user.clear(yearBuilt);
    await user.type(yearBuilt, "2001");
    expect(yearBuilt.value).toBe("2001");
  });

  it("on miss, shows a clear message and the manual entry remains usable", async () => {
    vi.stubEnv("NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED", "true");
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByTestId("address-lookup-input"), "9999 Nowhere Blvd");
    await user.click(screen.getByTestId("address-lookup-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("address-lookup-status")).toHaveTextContent(/couldn't find/i),
    );

    const gfa = screen.getByLabelText(/Gross Floor Area/i) as HTMLInputElement;
    expect(gfa.value).toBe("");
    expect(gfa).toBeEnabled();
    await user.type(gfa, "50000");
    expect(gfa.value).toBe("50000");
  });
});
