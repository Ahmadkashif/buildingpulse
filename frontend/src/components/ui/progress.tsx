import * as React from "react";

import { cn } from "@/lib/utils";

interface ProgressProps extends React.ComponentProps<"div"> {
  /** Progress value 0–100. */
  value: number;
}

function Progress({ className, value, ...props }: ProgressProps) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      data-slot="progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      className={cn(
        "bg-surface-container-high relative h-2 w-full overflow-hidden rounded-full",
        className,
      )}
      {...props}
    >
      <div
        data-slot="progress-fill"
        className="bg-signature absolute inset-y-0 left-0 rounded-full transition-[width] duration-500 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export { Progress };
