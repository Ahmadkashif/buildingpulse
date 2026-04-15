"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { YesNoToggle } from "@/components/ui/yes-no-toggle";
import { usePdfExport } from "@/hooks/use-pdf-export";

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  reportId: string;
}

export function ExportDialog({ open, onClose, reportId }: ExportDialogProps) {
  const pdf = usePdfExport();
  const [includeCharts, setIncludeCharts] = React.useState<boolean>(true);
  const [includeAppendix, setIncludeAppendix] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (!open) pdf.reset();
  }, [open, pdf]);

  const handleDownload = () => {
    // Scaffold stub: we don't actually write a file, just animate.
    pdf.start();
  };

  const isReady = pdf.status === "ready";
  const isExporting = pdf.status === "exporting";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Export Report as PDF"
      description={`Report ${reportId} · DeepGrid editorial layout`}
    >
      {pdf.status === "idle" ? (
        <div className="flex flex-col gap-5">
          <OptionRow
            label="Include Charts"
            hint="Embed SVG visualizations in the export."
            value={includeCharts}
            onValueChange={setIncludeCharts}
          />
          <OptionRow
            label="Include Raw Data Appendix"
            hint="Attach the underlying monthly tables."
            value={includeAppendix}
            onValueChange={setIncludeAppendix}
          />
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="tertiary" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="gradient" onClick={handleDownload}>
              Export PDF
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <span className="font-heading text-base font-semibold">{pdf.stage.headline}</span>
            <span className="text-on-surface-variant text-sm">{pdf.stage.status}</span>
          </div>
          <div className="flex items-center gap-4">
            <Progress value={pdf.progress} />
            <span className="font-heading w-12 text-right text-sm font-semibold tabular-nums">
              {pdf.progress}%
            </span>
          </div>
          <div className="flex items-center justify-end gap-2 pt-2">
            {isExporting ? (
              <Button variant="tertiary" onClick={pdf.reset}>
                Cancel
              </Button>
            ) : null}
            {isReady ? (
              <>
                <Button variant="tertiary" onClick={onClose}>
                  Done
                </Button>
                <Button variant="gradient" disabled>
                  Download (stub)
                </Button>
              </>
            ) : null}
          </div>
        </div>
      )}
    </Dialog>
  );
}

interface OptionRowProps {
  label: string;
  hint: string;
  value: boolean;
  onValueChange: (v: boolean) => void;
}

function OptionRow({ label, hint, value, onValueChange }: OptionRowProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-semibold">{label}</span>
        <span className="text-on-surface-variant text-xs">{hint}</span>
      </div>
      <YesNoToggle value={value} onValueChange={onValueChange} aria-label={label} />
    </div>
  );
}
