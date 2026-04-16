"use client";

import * as React from "react";

import { PDF_EXPORT_STAGES } from "@/mocks/data/prediction-stages";
import type { PredictionStage } from "@/types";

type ExportStatus = "idle" | "exporting" | "ready" | "error";

interface UsePdfExportReturn {
  status: ExportStatus;
  progress: number;
  stage: PredictionStage;
  start: () => void;
  reset: () => void;
}

/**
 * Scaffold stub — drives the UI animation for PDF export but does not
 * actually produce a PDF. Swap the `start` body for a real network call once
 * the rendering backend is wired up.
 */
export function usePdfExport(): UsePdfExportReturn {
  const [status, setStatus] = React.useState<ExportStatus>("idle");
  const [progress, setProgress] = React.useState(0);
  const timerRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const stage = React.useMemo(() => {
    const active = [...PDF_EXPORT_STAGES].reverse().find((s) => progress >= s.threshold);
    return active ?? PDF_EXPORT_STAGES[0]!;
  }, [progress]);

  const stop = React.useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = React.useCallback(() => {
    stop();
    setStatus("exporting");
    setProgress(0);
    timerRef.current = setInterval(() => {
      setProgress((p) => {
        const next = Math.min(100, p + 4);
        if (next >= 100) {
          stop();
          setStatus("ready");
        }
        return next;
      });
    }, 120);
  }, [stop]);

  const reset = React.useCallback(() => {
    stop();
    setStatus("idle");
    setProgress(0);
  }, [stop]);

  React.useEffect(() => stop, [stop]);

  return { status, progress, stage, start, reset };
}
