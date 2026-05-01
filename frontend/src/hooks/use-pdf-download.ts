"use client";

import * as React from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export type PdfDownloadStatus = "idle" | "downloading" | "error";

export interface UsePdfDownloadReturn {
  status: PdfDownloadStatus;
  error: string | null;
  download: (predictionId: string) => Promise<void>;
  reset: () => void;
}

export function usePdfDownload(): UsePdfDownloadReturn {
  const [status, setStatus] = React.useState<PdfDownloadStatus>("idle");
  const [error, setError] = React.useState<string | null>(null);

  const reset = React.useCallback(() => {
    setStatus("idle");
    setError(null);
  }, []);

  const download = React.useCallback(async (predictionId: string) => {
    setStatus("downloading");
    setError(null);
    try {
      const base =
        API_BASE_URL ||
        (typeof window !== "undefined" ? window.location.origin : "http://localhost");
      const url = new URL(`/api/predictions/${predictionId}/pdf`, base).toString();

      const response = await fetch(url, { method: "GET" });
      if (!response.ok) {
        throw new Error(`Download failed (HTTP ${response.status})`);
      }

      const blob = await response.blob();
      const filename =
        parseFilename(response.headers.get("content-disposition")) ??
        `building-pulse-${predictionId}.pdf`;
      triggerBrowserDownload(blob, filename);
      setStatus("idle");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Download failed");
    }
  }, []);

  return { status, error, download, reset };
}

export function parseFilename(header: string | null): string | null {
  if (!header) return null;
  const match = /filename\s*=\s*"?([^";]+)"?/i.exec(header);
  if (!match) return null;
  const name = match[1]?.trim();
  return name && name.length > 0 ? name : null;
}

function triggerBrowserDownload(blob: Blob, filename: string): void {
  if (typeof document === "undefined") return;
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}
