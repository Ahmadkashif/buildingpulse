import type { ForecastStage } from "@/types";

/**
 * Progress milestone copy for the forecast loading screen.
 * Each stage becomes active when progress crosses its threshold.
 */
export const FORECAST_STAGES: ForecastStage[] = [
  { threshold: 0, headline: "Calibrating…", status: "Warming up DeepGrid V4.2.1…" },
  { threshold: 10, headline: "Gathering…", status: "Pulling LL97 benchmark records…" },
  { threshold: 20, headline: "Locating…", status: "Geolocating borough footprint…" },
  { threshold: 30, headline: "Inspecting…", status: "Inspecting property archetype…" },
  { threshold: 40, headline: "Modeling…", status: "Modeling floor-area envelope…" },
  { threshold: 50, headline: "Cross-checking…", status: "Cross-checking vintage year cohort…" },
  { threshold: 60, headline: "Weighing…", status: "Weighing neighboring lot effects…" },
  { threshold: 70, headline: "Simulating…", status: "Simulating peak-hour draw curves…" },
  { threshold: 80, headline: "Benchmarking…", status: "Benchmarking against market average…" },
  { threshold: 90, headline: "Polishing…", status: "Polishing your forecast…" },
  { threshold: 100, headline: "Ready.", status: "Your forecast is ready." },
];

/** Milestone copy for the PDF export dialog. */
export const PDF_EXPORT_STAGES: ForecastStage[] = [
  { threshold: 0, headline: "Preparing…", status: "Assembling report sections…" },
  { threshold: 25, headline: "Rendering…", status: "Rendering charts and visualizations…" },
  { threshold: 50, headline: "Composing…", status: "Composing editorial layout…" },
  { threshold: 75, headline: "Packaging…", status: "Embedding fonts and finalizing PDF…" },
  { threshold: 100, headline: "Ready.", status: "Download ready." },
];
