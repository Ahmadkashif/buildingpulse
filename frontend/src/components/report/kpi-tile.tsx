import * as React from "react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface KpiTileProps extends React.ComponentProps<"div"> {
  label: string;
  value: string;
  caption?: string;
  delta?: { value: string; direction: "up" | "down" };
  /** Signature variant = gradient-filled card. Reserved for the headline metric. */
  signature?: boolean;
}

export function KpiTile({
  label,
  value,
  caption,
  delta,
  signature = false,
  className,
  ...props
}: KpiTileProps) {
  return (
    <div
      data-slot="kpi-tile"
      data-signature={signature ? "" : undefined}
      className={cn(
        "shadow-ambient relative flex flex-col gap-3 overflow-hidden rounded-xl p-6",
        signature ? "bg-signature text-primary-foreground" : "bg-card text-card-foreground",
        className,
      )}
      {...props}
    >
      <span
        className={cn(
          "text-label-md",
          signature ? "text-primary-foreground/80" : "text-on-surface-variant",
        )}
      >
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className="font-heading text-4xl leading-none font-bold tabular-nums">{value}</span>
        {delta ? (
          <Badge variant={delta.direction === "up" ? "delta-up" : "delta-down"}>
            {delta.direction === "up" ? "▲" : "▼"} {delta.value}
          </Badge>
        ) : null}
      </div>
      {caption ? (
        <span
          className={cn(
            "text-xs",
            signature ? "text-primary-foreground/80" : "text-on-surface-variant",
          )}
        >
          {caption}
        </span>
      ) : null}
    </div>
  );
}
