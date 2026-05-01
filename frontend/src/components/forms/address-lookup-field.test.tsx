import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse, delay } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { server } from "@/mocks/server";
import { AddressLookupField } from "./address-lookup-field";
import type { AddressMatch } from "@/types";

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderField(onMatch: (m: AddressMatch) => void = () => {}) {
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <AddressLookupField onMatch={onMatch} />
    </QueryClientProvider>,
  );
}

describe("AddressLookupField", () => {
  afterEach(() => {
    server.resetHandlers();
  });

  it("renders an address input and a submit button", () => {
    renderField();
    expect(screen.getByTestId("address-lookup-input")).toBeInTheDocument();
    expect(screen.getByTestId("address-lookup-submit")).toBeInTheDocument();
  });

  it("submit button is disabled until the user types a non-blank query", async () => {
    const user = userEvent.setup();
    renderField();
    const submit = screen.getByTestId("address-lookup-submit");
    expect(submit).toBeDisabled();
    await user.type(screen.getByTestId("address-lookup-input"), "100 Synth St");
    expect(submit).toBeEnabled();
  });

  it("shows the loading state while the request is in flight", async () => {
    server.use(
      http.get("/api/address/lookup", async () => {
        await delay(50);
        return HttpResponse.json(
          { message: "Address not found", code: "NOT_FOUND", status: 404 },
          { status: 404 },
        );
      }),
    );
    const user = userEvent.setup();
    renderField();
    await user.type(screen.getByTestId("address-lookup-input"), "100 Synth St");
    await user.click(screen.getByTestId("address-lookup-submit"));
    expect(screen.getByTestId("address-lookup-status")).toHaveTextContent(/Looking up address/i);
    expect(screen.getByTestId("address-lookup-submit")).toBeDisabled();
    await waitFor(() =>
      expect(screen.getByTestId("address-lookup-status")).toHaveTextContent(/couldn't find/i),
    );
  });

  it("on hit: calls onMatch with the resolved record and shows a success message", async () => {
    const onMatch = vi.fn();
    const user = userEvent.setup();
    renderField(onMatch);
    await user.type(screen.getByTestId("address-lookup-input"), "100 Synth St");
    await user.click(screen.getByTestId("address-lookup-submit"));
    await waitFor(() => expect(onMatch).toHaveBeenCalledTimes(1));
    const match = onMatch.mock.calls[0]![0] as AddressMatch;
    expect(match.addressNormalized).toBe("100 SYNTH ST");
    expect(match.borough).toBe("manhattan");
    expect(match.propertyType).toBe("office");
    await waitFor(() =>
      expect(screen.getByTestId("address-lookup-status")).toHaveTextContent(/Match found/i),
    );
  });

  it("on miss: shows a clear message and does not call onMatch", async () => {
    const onMatch = vi.fn();
    const user = userEvent.setup();
    renderField(onMatch);
    await user.type(screen.getByTestId("address-lookup-input"), "9999 Nowhere Blvd");
    await user.click(screen.getByTestId("address-lookup-submit"));
    await waitFor(() =>
      expect(screen.getByTestId("address-lookup-status")).toHaveTextContent(/couldn't find/i),
    );
    expect(onMatch).not.toHaveBeenCalled();
  });
});
