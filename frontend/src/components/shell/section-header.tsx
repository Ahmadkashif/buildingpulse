import * as React from "react";

import { cn } from "@/lib/utils";

interface SectionHeaderProps extends React.ComponentProps<"div"> {
  title: string;
  description?: string;
  /** Optional step number displayed as an eyebrow, e.g. "01". */
  step?: string;
  actions?: React.ReactNode;
}

export function SectionHeader({
  title,
  description,
  step,
  actions,
  className,
  ...props
}: SectionHeaderProps) {
  return (
    <div
      data-slot="section-header"
      className={cn("flex items-start justify-between gap-4", className)}
      {...props}
    >
      <div className="flex items-start gap-3">
        {step ? <span className="text-label-md text-primary mt-1 tabular-nums">{step}</span> : null}
        <div className="flex flex-col gap-0.5">
          <h2 className="font-heading text-on-surface text-lg font-semibold tracking-tight">
            {title}
          </h2>
          {description ? <p className="text-on-surface-variant text-sm">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
