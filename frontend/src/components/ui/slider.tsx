"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface SliderProps extends Omit<React.ComponentProps<"input">, "type"> {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number) => void;
}

function Slider({
  className,
  value,
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  ...props
}: SliderProps) {
  const pct = Math.max(0, Math.min(100, ((value - min) / Math.max(1, max - min)) * 100));

  return (
    <div className={cn("relative flex h-6 w-full items-center", className)}>
      <div className="bg-surface-container-highest absolute inset-x-0 h-1.5 rounded-full" />
      <div className="bg-primary absolute left-0 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
      <input
        data-slot="slider"
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onValueChange?.(Number(e.target.value))}
        className="[&::-webkit-slider-thumb]:bg-primary [&::-moz-range-thumb]:bg-primary relative z-10 h-6 w-full cursor-pointer appearance-none bg-transparent [&::-moz-range-thumb]:size-5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-webkit-slider-thumb]:size-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-md"
        {...props}
      />
    </div>
  );
}

export { Slider };
