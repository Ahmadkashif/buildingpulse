import * as React from "react";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import type { FineYear } from "@/types";

const STEP_YEAR = 2030;

interface FineSeriesChartProps {
  title: string;
  description?: string;
  data: FineYear[];
}

/**
 * Step-function chart of LL97 projected annual fines from the current
 * compliance period (2024–2029) into the 2030–2034 cliff. Two flat
 * segments joined by a vertical step at 2030.
 */
export function FineSeriesChart({ title, description, data }: FineSeriesChartProps) {
  if (data.length === 0) {
    return (
      <Card data-slot="fine-series-chart" data-testid="ll97-fine-series-chart">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
        <CardContent>
          <p
            className="text-on-surface-variant text-sm"
            data-testid="ll97-fine-series-empty"
          >
            No projected fine data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const before = data.filter((d) => d.year < STEP_YEAR);
  const after = data.filter((d) => d.year >= STEP_YEAR);

  const fineBefore = before[0]?.projectedAnnualFineUsd ?? 0;
  const fineAfter = after[0]?.projectedAnnualFineUsd ?? fineBefore;

  const years = data.map((d) => d.year);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);
  const yearSpan = Math.max(1, maxYear - minYear);

  const maxFine = Math.max(1, fineBefore, fineAfter);

  const width = 480;
  const height = 220;
  const paddingX = 48;
  const paddingTop = 16;
  const paddingBottom = 36;
  const innerWidth = width - paddingX * 2;
  const innerHeight = height - paddingTop - paddingBottom;

  const xFor = (year: number) => paddingX + ((year - minYear) / yearSpan) * innerWidth;
  const yFor = (fine: number) => paddingTop + innerHeight - (fine / maxFine) * innerHeight;

  const stepX = xFor(STEP_YEAR);
  const yBefore = yFor(fineBefore);
  const yAfter = yFor(fineAfter);
  const yBase = paddingTop + innerHeight;

  const hasBefore = before.length > 0;
  const hasAfter = after.length > 0;
  const showStep = hasBefore && hasAfter && fineBefore !== fineAfter;

  return (
    <Card data-slot="fine-series-chart" data-testid="ll97-fine-series-chart">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <svg
          role="img"
          aria-label={title}
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          preserveAspectRatio="xMidYMid meet"
        >
          <line
            x1={paddingX}
            y1={yBase}
            x2={width - paddingX}
            y2={yBase}
            className="stroke-outline-variant"
            strokeWidth={1}
          />

          {hasBefore ? (
            <line
              x1={xFor(before[0]!.year)}
              y1={yBefore}
              x2={stepX}
              y2={yBefore}
              className="stroke-primary"
              strokeWidth={3}
              data-testid="ll97-segment-2024-2029"
            />
          ) : null}

          {hasAfter ? (
            <line
              x1={stepX}
              y1={yAfter}
              x2={xFor(maxYear)}
              y2={yAfter}
              className="stroke-secondary"
              strokeWidth={3}
              data-testid="ll97-segment-2030-2034"
            />
          ) : null}

          {showStep ? (
            <g data-testid="ll97-step-2030">
              <line
                x1={stepX}
                y1={yBefore}
                x2={stepX}
                y2={yAfter}
                className="stroke-secondary"
                strokeWidth={3}
                strokeDasharray="4 4"
              />
              <circle cx={stepX} cy={yAfter} r={5} className="fill-secondary" />
              <text
                x={stepX}
                y={Math.max(paddingTop + 12, yAfter - 10)}
                textAnchor="middle"
                className="fill-secondary text-[11px] font-semibold"
              >
                2030 cliff
              </text>
            </g>
          ) : null}

          <text
            x={paddingX}
            y={height - 12}
            textAnchor="start"
            className="fill-on-surface-variant text-[10px]"
          >
            {minYear}
          </text>
          <text
            x={stepX}
            y={height - 12}
            textAnchor="middle"
            className="fill-on-surface-variant text-[10px]"
          >
            {STEP_YEAR}
          </text>
          <text
            x={width - paddingX}
            y={height - 12}
            textAnchor="end"
            className="fill-on-surface-variant text-[10px]"
          >
            {maxYear}
          </text>

          <text
            x={paddingX - 8}
            y={yBefore + 4}
            textAnchor="end"
            className="fill-on-surface-variant text-[10px]"
          >
            {formatCurrency(fineBefore)}
          </text>
          {showStep ? (
            <text
              x={paddingX - 8}
              y={yAfter + 4}
              textAnchor="end"
              className="fill-secondary text-[10px] font-semibold"
            >
              {formatCurrency(fineAfter)}
            </text>
          ) : null}
        </svg>

        <dl
          className="text-on-surface-variant mt-4 grid grid-cols-2 gap-4 text-xs sm:text-sm"
          data-testid="ll97-fine-series-summary"
        >
          <div>
            <dt className="font-medium">2024–2029 period</dt>
            <dd className="text-on-surface font-semibold">
              {formatCurrency(fineBefore)}/yr
            </dd>
          </div>
          <div>
            <dt className="text-secondary font-medium">2030–2034 period</dt>
            <dd className="text-on-surface font-semibold">{formatCurrency(fineAfter)}/yr</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}
