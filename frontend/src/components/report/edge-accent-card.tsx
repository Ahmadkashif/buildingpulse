import * as React from "react";

import { cn } from "@/lib/utils";

interface EdgeAccentCardProps extends React.ComponentProps<"div"> {
  label: string;
  value: string;
  icon?: React.ReactNode;
  accent?: "primary" | "secondary" | "tertiary";
}

const ACCENT_BG: Record<NonNullable<EdgeAccentCardProps["accent"]>, string> = {
  primary: "bg-primary",
  secondary: "bg-secondary",
  tertiary: "bg-tertiary",
};

/** Card with a 4px left-edge accent bar. Reused in metric strips. */
export function EdgeAccentCard({
  label,
  value,
  icon,
  accent = "primary",
  className,
  ...props
}: EdgeAccentCardProps) {
  return (
    <div
      data-slot="edge-accent-card"
      className={cn(
        "bg-card text-card-foreground shadow-ambient relative flex items-center gap-4 overflow-hidden rounded-xl py-4 pr-4 pl-6",
        className,
      )}
      {...props}
    >
      <span aria-hidden className={cn("absolute inset-y-0 left-0 w-1", ACCENT_BG[accent])} />
      {icon ? <div className="text-on-surface-variant shrink-0">{icon}</div> : null}
      <div className="flex flex-col gap-0.5">
        <span className="text-label-md text-on-surface-variant">{label}</span>
        <span className="font-heading text-on-surface text-base font-semibold">{value}</span>
      </div>
    </div>
  );
}
