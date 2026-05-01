import * as React from "react";

import { apiClient } from "@/lib/api-client";
import type { ScenarioPublic } from "@/types";

export interface ChooseScenarioResult {
  predictionId: string;
  scenarioId: string;
  deduped: boolean;
}

export interface UseChooseScenarioOptions {
  /** Override the default ``window.location.assign`` redirect — used in tests. */
  redirect?: (url: string) => void;
}

/**
 * Returns a click handler for "Choose this scenario": POSTs the
 * ``ScenarioSelected`` audit event to ``/api/scenarios/:id/select`` and
 * then navigates to ``/api/sponsor/cta`` (which records
 * ``SponsorCtaFollowed`` and 302s to the sponsor URL with both ids).
 *
 * Idempotency: the hook ignores re-entrant calls while a request is in
 * flight, so a rapid double-click on the same button only fires one
 * audit pair. Server-side dedupe on the audit endpoint covers the case
 * of two clicks on different scenarios that race the same window.
 */
export function useChooseScenario(
  predictionId: string,
  options: UseChooseScenarioOptions = {},
) {
  const inFlight = React.useRef(false);
  const { redirect } = options;

  return React.useCallback(
    async (scenario: ScenarioPublic) => {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        await apiClient.post<{ data: ChooseScenarioResult }>(
          `/api/scenarios/${encodeURIComponent(scenario.id)}/select`,
          { body: { predictionId } },
        );
      } catch {
        // Swallow audit failures — the user-visible action is the
        // sponsor CTA redirect, and the server-side audit is best-effort.
      }
      const ctaUrl =
        `/api/sponsor/cta?prediction_id=${encodeURIComponent(predictionId)}` +
        `&scenario_id=${encodeURIComponent(scenario.id)}`;
      if (redirect) {
        redirect(ctaUrl);
      } else if (typeof window !== "undefined") {
        window.location.assign(ctaUrl);
      }
    },
    [predictionId, redirect],
  );
}
