import type { PredictionStage } from "@/types";

/**
 * Progress milestone copy for the prediction loading screen.
 * Each stage becomes active when progress crosses its threshold.
 */
export const PREDICTION_STAGES: PredictionStage[] = [
  { threshold: 0, headline: "Calibrating…", status: "Warming up the baseline model…" },
  { threshold: 10, headline: "Gathering…", status: "Pulling LL84 benchmark records…" },
  { threshold: 20, headline: "Locating…", status: "Geolocating borough footprint…" },
  { threshold: 30, headline: "Inspecting…", status: "Inspecting property archetype…" },
  { threshold: 40, headline: "Modeling…", status: "Modeling floor-area envelope…" },
  { threshold: 50, headline: "Cross-checking…", status: "Cross-checking vintage year cohort…" },
  { threshold: 60, headline: "Comparing…", status: "Comparing against peer buildings…" },
  { threshold: 70, headline: "Scoring…", status: "Scoring percentile rank…" },
  { threshold: 80, headline: "Checking…", status: "Checking LL97 compliance caps…" },
  { threshold: 90, headline: "Polishing…", status: "Finalizing your prediction…" },
  { threshold: 100, headline: "Ready.", status: "Your prediction is ready." },
];

/** Milestone copy for the PDF export dialog. */
export const PDF_EXPORT_STAGES: PredictionStage[] = [
  { threshold: 0, headline: "Preparing…", status: "Assembling report sections…" },
  { threshold: 25, headline: "Rendering…", status: "Rendering charts and visualizations…" },
  { threshold: 50, headline: "Composing…", status: "Composing editorial layout…" },
  { threshold: 75, headline: "Packaging…", status: "Embedding fonts and finalizing PDF…" },
  { threshold: 100, headline: "Ready.", status: "Download ready." },
];
