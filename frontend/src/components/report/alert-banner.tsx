import * as React from "react";

import { cn } from "@/lib/utils";

interface AlertBannerProps extends React.ComponentProps<"aside"> {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
}

export function AlertBanner({
  eyebrow = "Actionable Insight",
  title,
  description,
  actions,
  className,
  ...props
}: AlertBannerProps) {
  return (
    <aside
      data-slot="alert-banner"
      className={cn(
        "bg-signature text-primary-foreground shadow-ambient flex flex-col gap-4 rounded-xl p-6",
        className,
      )}
      {...props}
    >
      <div className="flex flex-col gap-2">
        <span className="text-label-sm text-primary-foreground/80">{eyebrow}</span>
        <h2 className="font-heading text-2xl leading-tight font-bold tracking-tight">{title}</h2>
        <p className="text-primary-foreground/85 text-sm leading-relaxed">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </aside>
  );
}
