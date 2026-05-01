"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Dialog } from "@/components/ui/dialog";
import { FormField } from "@/components/forms/form-field";
import { useLeadCapture, type LeadCaptureInput } from "@/hooks/use-lead-capture";

const ROLES: Array<{ value: string; label: string }> = [
  { value: "owner", label: "Owner" },
  { value: "property-manager", label: "Property Manager" },
  { value: "asset-manager", label: "Asset Manager" },
  { value: "operator", label: "Operator" },
  { value: "other", label: "Other" },
];

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE_PATTERN = /^\+?[0-9][0-9 \-().]{6,}$/;

export const CONSENT_REQUIRED_MESSAGE = "You must agree to be contacted";

export interface LeadModalContext {
  predictionId: string;
  propertyType: LeadCaptureInput["propertyType"];
  borough: LeadCaptureInput["borough"];
  grossFloorAreaSqft: number;
  yearBuilt: number;
  predictedEui: number;
  projectedFineUsd: number;
  atRisk: boolean;
  reportUrl: string;
  scenarioId?: string | null;
}

export interface LeadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (leadId: string) => void;
  context: LeadModalContext;
}

interface Errors {
  name?: string;
  email?: string;
  phone?: string;
  role?: string;
  consent?: string;
  server?: string;
}

export function LeadModal({ open, onClose, onSuccess, context }: LeadModalProps) {
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [role, setRole] = React.useState("");
  const [consent, setConsent] = React.useState(false);
  const [errors, setErrors] = React.useState<Errors>({});

  const capture = useLeadCapture();

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  React.useEffect(() => {
    if (!open) {
      setName("");
      setEmail("");
      setPhone("");
      setRole("");
      setConsent(false);
      setErrors({});
      capture.reset();
    }
    // capture.reset is stable; intentionally omit from deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const validate = (): Errors => {
    const next: Errors = {};
    if (!name.trim()) next.name = "Name is required";
    if (!email.trim()) {
      next.email = "Email is required";
    } else if (!EMAIL_PATTERN.test(email.trim())) {
      next.email = "Enter a valid email address";
    }
    if (!phone.trim()) {
      next.phone = "Phone is required";
    } else if (!PHONE_PATTERN.test(phone.trim())) {
      next.phone = "Enter a valid phone number";
    }
    if (!role) next.role = "Role is required";
    if (!consent) next.consent = CONSENT_REQUIRED_MESSAGE;
    return next;
  };

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const next = validate();
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    const input: LeadCaptureInput = {
      predictionId: context.predictionId,
      name: name.trim(),
      email: email.trim(),
      phone: phone.trim(),
      role,
      consentGiven: true,
      scenarioId: context.scenarioId ?? null,
      propertyType: context.propertyType,
      borough: context.borough,
      grossFloorAreaSqft: context.grossFloorAreaSqft,
      yearBuilt: context.yearBuilt,
      predictedEui: context.predictedEui,
      projectedFineUsd: context.projectedFineUsd,
      atRisk: context.atRisk,
      reportUrl: context.reportUrl,
    };

    capture.mutate(input, {
      onSuccess: (response) => {
        onSuccess(response.data.id);
        onClose();
      },
      onError: () => {
        setErrors({ server: "We couldn't submit your request. Please try again." });
      },
    });
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Unlock your action plan"
      description="Tell us where to send your report and contractor handoff."
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <FormField label="Name" htmlFor="lead-name">
          <Input
            id="lead-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-invalid={errors.name ? true : undefined}
            aria-describedby={errors.name ? "lead-name-error" : undefined}
          />
          {errors.name ? (
            <span id="lead-name-error" role="alert" className="text-destructive text-xs">
              {errors.name}
            </span>
          ) : null}
        </FormField>

        <FormField label="Email" htmlFor="lead-email">
          <Input
            id="lead-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "lead-email-error" : undefined}
          />
          {errors.email ? (
            <span id="lead-email-error" role="alert" className="text-destructive text-xs">
              {errors.email}
            </span>
          ) : null}
        </FormField>

        <FormField label="Phone" htmlFor="lead-phone">
          <Input
            id="lead-phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            aria-invalid={errors.phone ? true : undefined}
            aria-describedby={errors.phone ? "lead-phone-error" : undefined}
          />
          {errors.phone ? (
            <span id="lead-phone-error" role="alert" className="text-destructive text-xs">
              {errors.phone}
            </span>
          ) : null}
        </FormField>

        <FormField label="Role" htmlFor="lead-role">
          <Select
            id="lead-role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            aria-invalid={errors.role ? true : undefined}
            aria-describedby={errors.role ? "lead-role-error" : undefined}
          >
            <option value="" disabled>
              Select your role
            </option>
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </Select>
          {errors.role ? (
            <span id="lead-role-error" role="alert" className="text-destructive text-xs">
              {errors.role}
            </span>
          ) : null}
        </FormField>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            aria-invalid={errors.consent ? true : undefined}
            aria-describedby={errors.consent ? "lead-consent-error" : undefined}
            className="mt-1"
          />
          <span>I agree to be contacted about this report.</span>
        </label>
        {errors.consent ? (
          <span id="lead-consent-error" role="alert" className="text-destructive text-xs">
            {errors.consent}
          </span>
        ) : null}

        {errors.server ? (
          <div role="alert" className="text-destructive text-sm">
            {errors.server}
          </div>
        ) : null}

        <div className="mt-2 flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={capture.isPending}>
            Cancel
          </Button>
          <Button type="submit" variant="gradient" disabled={capture.isPending}>
            {capture.isPending ? "Submitting…" : "Unlock report"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
