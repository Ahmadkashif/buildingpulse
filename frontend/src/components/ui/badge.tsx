import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Tonal chip — used as StatusBadge across report, asset cards, and toasts.
 * Per DESIGN.md: never a solid dot, always a tonal background + matching text.
 */
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium tracking-wide uppercase whitespace-nowrap",
  {
    variants: {
      variant: {
        savings: "bg-secondary-container text-on-secondary-container",
        verified: "bg-primary-container/30 text-primary",
        "yield-high": "bg-tertiary-container text-on-tertiary-container",
        action: "bg-destructive-container text-on-destructive-container",
        neutral: "bg-surface-container-high text-on-surface-variant",
        "delta-up": "bg-secondary-container text-on-secondary-container",
        "delta-down": "bg-destructive-container text-on-destructive-container",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

interface BadgeProps extends React.ComponentProps<"span">, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span data-slot="badge" className={cn(badgeVariants({ variant, className }))} {...props} />
  );
}

export { Badge, badgeVariants };
