import * as React from "react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { badgeVariants } from "@/components/ui/badge";
import type { VariantProps } from "class-variance-authority";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

interface AssetCardProps extends React.ComponentProps<"article"> {
  title: string;
  cover?: React.ReactNode;
  badge?: { label: string; variant: BadgeVariant };
  metricLabel: string;
  metricValue: string;
  comparisonLabel: string;
  comparisonValue: string;
  /** Variance 0–1, used to fill the inline bar. */
  variance: number;
}

export function AssetCard({
  title,
  cover,
  badge,
  metricLabel,
  metricValue,
  comparisonLabel,
  comparisonValue,
  variance,
  className,
  ...props
}: AssetCardProps) {
  const pct = Math.max(0, Math.min(100, variance * 100));
  return (
    <article
      data-slot="asset-card"
      className={cn(
        "bg-card text-card-foreground shadow-ambient flex flex-col overflow-hidden rounded-xl",
        className,
      )}
      {...props}
    >
      <div className="bg-surface-container-high relative aspect-[16/9] w-full">
        {cover}
        {badge ? (
          <div className="absolute top-3 left-3">
            <Badge variant={badge.variant}>{badge.label}</Badge>
          </div>
        ) : null}
      </div>
      <div className="flex flex-col gap-4 p-5">
        <h3 className="font-heading text-on-surface text-sm font-semibold">{title}</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-label-sm text-on-surface-variant">{metricLabel}</span>
            <span className="font-heading text-lg font-semibold tabular-nums">{metricValue}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-label-sm text-on-surface-variant">{comparisonLabel}</span>
            <span className="font-heading text-lg font-semibold tabular-nums">
              {comparisonValue}
            </span>
          </div>
        </div>
        <div className="bg-surface-container-high h-1 w-full rounded-full">
          <div className="bg-primary h-full rounded-full" style={{ width: `${pct}%` }} />
        </div>
      </div>
    </article>
  );
}
