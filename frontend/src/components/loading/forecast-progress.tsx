"use client";

import * as React from "react";

import { Progress } from "@/components/ui/progress";
import { PREDICTION_STAGES } from "@/mocks/data/prediction-stages";

interface ForecastProgressProps {
  /** Called once the animation reaches 100%. */
  onComplete?: () => void;
  /** Milliseconds between each 4% tick. Defaults to 160ms (~4s total). */
  tickMs?: number;
}

export function ForecastProgress({ onComplete, tickMs = 160 }: ForecastProgressProps) {
  const [progress, setProgress] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    const id = setInterval(() => {
      if (cancelled) return;
      setProgress((p) => {
        const next = Math.min(100, p + 4);
        if (next >= 100) clearInterval(id);
        return next;
      });
    }, tickMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tickMs]);

  React.useEffect(() => {
    if (progress >= 100) onComplete?.();
  }, [progress, onComplete]);

  const stage =
    [...PREDICTION_STAGES].reverse().find((s) => progress >= s.threshold) ?? PREDICTION_STAGES[0]!;

  return (
    <div
      data-slot="forecast-progress"
      className="relative mx-auto flex w-full max-w-xl flex-col items-center gap-8 py-24 text-center"
    >
      <div
        aria-hidden
        className="bg-signature/20 pointer-events-none absolute -inset-x-20 top-1/3 h-48 rounded-full blur-3xl"
      />
      <div className="relative flex flex-col gap-3">
        <span className="text-label-md text-on-surface-variant">buildingPulse Prediction Engine</span>
        <h1 className="font-heading text-on-surface text-5xl font-bold tracking-tight">
          {stage.headline}
        </h1>
        <p className="text-on-surface-variant text-base">{stage.status}</p>
      </div>
      <div className="relative flex w-full items-center gap-4">
        <Progress value={progress} />
        <span className="font-heading text-on-surface w-14 shrink-0 text-right text-xl font-bold tabular-nums">
          {progress}%
        </span>
      </div>
    </div>
  );
}
