import * as React from "react";

import { cn } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

interface BarChartDatum {
  label: string;
  primary: number;
  secondary: number;
}

interface BarChartCardProps {
  title: string;
  description?: string;
  data: BarChartDatum[];
  legend: { primary: string; secondary: string };
}

/**
 * Minimal stacked-bar chart rendered with SVG. For scaffold only — swap for
 * a dedicated chart library (e.g. recharts) when real analytics land.
 */
export function BarChartCard({ title, description, data, legend }: BarChartCardProps) {
  const max = Math.max(1, ...data.map((d) => d.primary + d.secondary));
  const barWidth = 22;
  const gap = 16;
  const innerWidth = data.length * (barWidth + gap);
  const height = 160;

  return (
    <Card data-slot="bar-chart-card">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </div>
        <div className="flex items-center gap-3 text-xs">
          <LegendChip dotClass="bg-primary" label={legend.primary} />
          <LegendChip dotClass="bg-secondary" label={legend.secondary} />
        </div>
      </CardHeader>
      <CardContent>
        <svg
          role="img"
          aria-label={title}
          viewBox={`0 0 ${innerWidth} ${height + 20}`}
          className="w-full"
          preserveAspectRatio="none"
        >
          {data.map((d, i) => {
            const primaryH = (d.primary / max) * height;
            const secondaryH = (d.secondary / max) * height;
            const x = i * (barWidth + gap);
            const yPrimary = height - primaryH;
            const ySecondary = yPrimary - secondaryH;
            return (
              <g key={d.label}>
                <rect
                  x={x}
                  y={ySecondary}
                  width={barWidth}
                  height={secondaryH}
                  rx={3}
                  className="fill-secondary"
                />
                <rect
                  x={x}
                  y={yPrimary}
                  width={barWidth}
                  height={primaryH}
                  rx={3}
                  className="fill-primary"
                />
                <text
                  x={x + barWidth / 2}
                  y={height + 14}
                  textAnchor="middle"
                  className="fill-on-surface-variant text-[10px]"
                >
                  {d.label}
                </text>
              </g>
            );
          })}
        </svg>
      </CardContent>
    </Card>
  );
}

function LegendChip({ dotClass, label }: { dotClass: string; label: string }) {
  return (
    <span className="text-on-surface-variant inline-flex items-center gap-1.5">
      <span className={cn("inline-block size-2 rounded-full", dotClass)} />
      {label}
    </span>
  );
}
