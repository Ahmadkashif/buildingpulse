"use client";

import * as React from "react";
import { FileText, Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useScenarios, type ScenarioQueryArgs } from "@/hooks/use-scenarios";
import type { ScenarioPublic } from "@/types";

export interface ScenariosCardProps {
  unlocked: boolean;
  /** Building inputs needed by the API. Required when unlocked. */
  query: ScenarioQueryArgs | null;
  /** Called when the user clicks the hidden-state CTA. */
  onRequestUnlock: () => void;
  /** Called when the user picks a scenario from the unlocked card. */
  onChooseScenario?: (scenario: ScenarioPublic) => void;
}

export function ScenariosCard({
  unlocked,
  query,
  onRequestUnlock,
  onChooseScenario,
}: ScenariosCardProps) {
  if (!unlocked) {
    return (
      <Card data-slot="scenarios-card" data-state="hidden">
        <CardHeader>
          <CardTitle>Retrofit Scenarios</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-start gap-3">
          <p className="text-on-surface-variant text-sm">
            Unlock cited retrofit scenarios with EUI reduction estimates, cost bands, and
            recomputed LL97 fines.
          </p>
          <Button
            variant="gradient"
            onClick={onRequestUnlock}
            data-testid="cta-see-retrofit-options"
          >
            <Lock className="size-4" /> See retrofit options
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <UnlockedScenarios query={query} onChooseScenario={onChooseScenario} />;
}

function UnlockedScenarios({
  query,
  onChooseScenario,
}: {
  query: ScenarioQueryArgs | null;
  onChooseScenario?: (scenario: ScenarioPublic) => void;
}) {
  const result = useScenarios(query);

  if (result.isLoading || result.isPending) {
    return (
      <Card data-slot="scenarios-card" data-state="loading">
        <CardHeader>
          <CardTitle>Retrofit Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <p
            role="status"
            aria-label="Loading retrofit scenarios"
            className="text-on-surface-variant text-sm"
          >
            Loading retrofit scenarios…
          </p>
        </CardContent>
      </Card>
    );
  }

  if (result.isError || !result.data) {
    return (
      <Card data-slot="scenarios-card" data-state="error">
        <CardHeader>
          <CardTitle>Retrofit Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <p role="alert" className="text-destructive text-sm">
            We couldn&apos;t load retrofit scenarios. Please try again.
          </p>
        </CardContent>
      </Card>
    );
  }

  const scenarios = result.data.data;

  if (scenarios.length === 0) {
    return (
      <Card data-slot="scenarios-card" data-state="empty">
        <CardHeader>
          <CardTitle>Retrofit Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-on-surface-variant text-sm">
            No retrofit scenarios are available for this building profile.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-slot="scenarios-card" data-state="visible">
      <CardHeader>
        <CardTitle>Retrofit Scenarios</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-4 md:grid-cols-2" data-testid="scenarios-list">
          {scenarios.map((s) => (
            <ScenarioItem key={s.id} scenario={s} onChoose={onChooseScenario} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function ScenarioItem({
  scenario,
  onChoose,
}: {
  scenario: ScenarioPublic;
  onChoose?: (scenario: ScenarioPublic) => void;
}) {
  const reductionLabel = `${Math.round(scenario.reductionPct * 100)}% EUI reduction`;
  const costLabel = `$${scenario.costLow.toFixed(2)}–$${scenario.costHigh.toFixed(2)}/sqft`;
  const fineLabel = `$${Math.round(scenario.recomputedFine2030).toLocaleString()}/yr by 2030`;

  return (
    <li
      data-slot="scenario-item"
      data-scenario-id={scenario.id}
      className="bg-card text-card-foreground shadow-ambient flex flex-col gap-3 rounded-xl p-5"
    >
      <div className="flex flex-col gap-1">
        <h3 className="font-heading text-on-surface text-sm font-semibold">{scenario.name}</h3>
        <p className="text-on-surface-variant text-sm leading-relaxed">{scenario.description}</p>
      </div>
      <dl className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex flex-col">
          <dt className="text-on-surface-variant">EUI Reduction</dt>
          <dd className="text-on-surface font-medium tabular-nums">{reductionLabel}</dd>
        </div>
        <div className="flex flex-col">
          <dt className="text-on-surface-variant">Cost Band</dt>
          <dd className="text-on-surface font-medium tabular-nums">{costLabel}</dd>
        </div>
        <div className="flex flex-col col-span-2">
          <dt className="text-on-surface-variant">Recomputed LL97 Fine</dt>
          <dd className="text-on-surface font-medium tabular-nums">{fineLabel}</dd>
        </div>
      </dl>
      <p className="text-on-surface-variant text-xs italic" data-testid="scenario-citation">
        Source: {scenario.citation}
      </p>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => onChoose?.(scenario)}
        data-testid="cta-choose-scenario"
      >
        <FileText className="size-4" /> Choose this scenario
      </Button>
    </li>
  );
}
