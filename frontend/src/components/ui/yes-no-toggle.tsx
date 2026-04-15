"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface YesNoToggleProps {
  value: boolean | null;
  onValueChange: (value: boolean) => void;
  className?: string;
  "aria-label"?: string;
}

function YesNoToggle({ value, onValueChange, className, ...aria }: YesNoToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label={aria["aria-label"]}
      className={cn(
        "bg-surface-container-high inline-flex w-fit items-center gap-1 rounded-full p-1",
        className,
      )}
    >
      <button
        type="button"
        role="radio"
        aria-checked={value === true}
        onClick={() => onValueChange(true)}
        className={cn(
          "rounded-full px-4 py-1.5 text-xs font-semibold tracking-wider uppercase transition-colors",
          value === true
            ? "bg-secondary text-secondary-foreground shadow-ambient"
            : "text-on-surface-variant",
        )}
      >
        Yes
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={value === false}
        onClick={() => onValueChange(false)}
        className={cn(
          "rounded-full px-4 py-1.5 text-xs font-semibold tracking-wider uppercase transition-colors",
          value === false
            ? "bg-surface-container-lowest text-on-surface shadow-ambient"
            : "text-on-surface-variant",
        )}
      >
        No
      </button>
    </div>
  );
}

export { YesNoToggle };
