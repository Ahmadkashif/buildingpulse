"use client";

import * as React from "react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { usePdfDownload } from "@/hooks/use-pdf-download";

interface ExportPdfButtonProps {
  predictionId: string;
  unlocked: boolean;
}

const LOCKED_HINT = "Unlock the report by sharing your contact info to download the PDF.";

export function ExportPdfButton({ predictionId, unlocked }: ExportPdfButtonProps) {
  const { status, error, download, reset } = usePdfDownload();
  const isDownloading = status === "downloading";
  const isError = status === "error";
  const disabled = !unlocked || isDownloading;

  const handleClick = () => {
    if (!unlocked) return;
    if (isError) reset();
    void download(predictionId);
  };

  return (
    <div className="flex flex-col gap-2">
      <Button
        variant="tertiary"
        width="full"
        onClick={handleClick}
        disabled={disabled}
        data-testid="cta-export-pdf"
        aria-disabled={disabled || undefined}
        title={!unlocked ? LOCKED_HINT : undefined}
      >
        <Download className="size-4" />
        {isDownloading ? "Preparing PDF…" : "Export Full PDF Report"}
      </Button>
      {isError ? (
        <p
          role="alert"
          data-testid="cta-export-pdf-error"
          className="text-destructive text-xs"
        >
          {error ?? "Download failed"}. Try again.
        </p>
      ) : null}
    </div>
  );
}
