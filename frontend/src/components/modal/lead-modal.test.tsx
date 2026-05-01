import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse, delay } from "msw";
import { vi } from "vitest";

import { server } from "@/mocks/server";
import { LeadModal, CONSENT_REQUIRED_MESSAGE, type LeadModalContext } from "./lead-modal";

const CONTEXT: LeadModalContext = {
  predictionId: "pred_abc123",
  propertyType: "office",
  borough: "manhattan",
  grossFloorAreaSqft: 100_000,
  yearBuilt: 1990,
  predictedEui: 95.4,
  projectedFineUsd: 12345,
  atRisk: true,
  reportUrl: "http://localhost:3000/report/pred_abc123",
};

function renderModal(overrides: Partial<React.ComponentProps<typeof LeadModal>> = {}) {
  const onClose = overrides.onClose ?? vi.fn();
  const onSuccess = overrides.onSuccess ?? vi.fn();
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const utils = render(
    <QueryClientProvider client={client}>
      <LeadModal
        open={overrides.open ?? true}
        onClose={onClose}
        onSuccess={onSuccess}
        context={overrides.context ?? CONTEXT}
      />
    </QueryClientProvider>,
  );
  return { ...utils, onClose, onSuccess, client };
}

async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/^name$/i), "Jane Doe");
  await user.type(screen.getByLabelText(/^email$/i), "jane@example.com");
  await user.type(screen.getByLabelText(/^phone$/i), "+1 212 555 0100");
  await user.selectOptions(screen.getByLabelText(/^role$/i), "owner");
}

describe("LeadModal", () => {
  it("does not render when closed", () => {
    renderModal({ open: false });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("renders the dialog with all form fields when open", () => {
    renderModal();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^phone$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^role$/i)).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("shows required-field validation messages on empty submit", async () => {
    const user = userEvent.setup();
    renderModal();
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/phone is required/i)).toBeInTheDocument();
    expect(screen.getByText(/role is required/i)).toBeInTheDocument();
    expect(screen.getByText(CONSENT_REQUIRED_MESSAGE)).toBeInTheDocument();
  });

  it("rejects an invalid email format", async () => {
    const user = userEvent.setup();
    renderModal();
    await user.type(screen.getByLabelText(/^name$/i), "Jane");
    await user.type(screen.getByLabelText(/^email$/i), "not-an-email");
    await user.type(screen.getByLabelText(/^phone$/i), "+1 212 555 0100");
    await user.selectOptions(screen.getByLabelText(/^role$/i), "owner");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    expect(screen.getByText(/valid email/i)).toBeInTheDocument();
  });

  it("rejects an invalid phone format", async () => {
    const user = userEvent.setup();
    renderModal();
    await user.type(screen.getByLabelText(/^name$/i), "Jane");
    await user.type(screen.getByLabelText(/^email$/i), "jane@example.com");
    await user.type(screen.getByLabelText(/^phone$/i), "abc");
    await user.selectOptions(screen.getByLabelText(/^role$/i), "owner");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    expect(screen.getByText(/valid phone/i)).toBeInTheDocument();
  });

  it("blocks submission when consent is missing with the specific message", async () => {
    const user = userEvent.setup();
    const { onSuccess } = renderModal();
    await fillForm(user);
    // Do NOT check consent.
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    expect(screen.getByText(CONSENT_REQUIRED_MESSAGE)).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("disables the submit button and shows loading copy while pending", async () => {
    server.use(
      http.post("/api/leads", async () => {
        await delay(50);
        return HttpResponse.json({ data: { id: "lead_123" } }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderModal();
    await fillForm(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    const submitting = await screen.findByRole("button", { name: /submitting/i });
    expect(submitting).toBeDisabled();
  });

  it("fires onSuccess with the new lead id and closes on 201", async () => {
    server.use(
      http.post("/api/leads", () =>
        HttpResponse.json({ data: { id: "lead_xyz" } }, { status: 201 }),
      ),
    );
    const user = userEvent.setup();
    const { onSuccess, onClose } = renderModal();
    await fillForm(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith("lead_xyz"));
    expect(onClose).toHaveBeenCalled();
  });

  it("renders an error message when the server rejects the request", async () => {
    server.use(
      http.post("/api/leads", () =>
        HttpResponse.json({ message: "boom", code: "INTERNAL", status: 500 }, { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    const { onSuccess } = renderModal();
    await fillForm(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /unlock report/i }));
    await screen.findByText(/couldn't submit/i);
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("closes when Escape is pressed", async () => {
    const user = userEvent.setup();
    const { onClose } = renderModal();
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("closes when the backdrop is clicked", async () => {
    const user = userEvent.setup();
    const { onClose } = renderModal();
    await user.click(screen.getByRole("button", { name: /close dialog/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("closes when the Cancel button is clicked", async () => {
    const user = userEvent.setup();
    const { onClose } = renderModal();
    await user.click(screen.getByRole("button", { name: /^cancel$/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
