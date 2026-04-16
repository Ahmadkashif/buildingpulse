import * as React from "react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { InsightBadge } from "@/types";

interface InsightCardProps extends React.ComponentProps<"article"> {
  title: string;
  description: string;
  badge: InsightBadge;
  icon?: React.ReactNode;
}

const BADGE_LABEL: Record<InsightBadge, string> = {
  savings: "Savings",
  verified: "Verified",
  "yield-high": "Yield High",
  action: "Action",
};

const BADGE_ICON_BG: Record<InsightBadge, string> = {
  savings: "bg-secondary-container text-on-secondary-container",
  verified: "bg-primary-container/30 text-primary",
  "yield-high": "bg-tertiary-container text-on-tertiary-container",
  action: "bg-destructive-container text-on-destructive-container",
};

export function InsightCard({
  title,
  description,
  badge,
  icon,
  className,
  ...props
}: InsightCardProps) {
  return (
    <article
      data-slot="insight-card"
      className={cn(
        "bg-card text-card-foreground shadow-ambient flex flex-col gap-3 rounded-xl p-5",
        className,
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-3">
        {icon ? (
          <div className={cn("grid size-9 place-items-center rounded-lg", BADGE_ICON_BG[badge])}>
            {icon}
          </div>
        ) : null}
        <Badge variant={badge}>{BADGE_LABEL[badge]}</Badge>
      </div>
      <div className="flex flex-col gap-1.5">
        <h3 className="font-heading text-on-surface text-sm font-semibold">{title}</h3>
        <p className="text-on-surface-variant text-sm leading-relaxed">{description}</p>
      </div>
    </article>
  );
}
