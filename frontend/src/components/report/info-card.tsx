import * as React from "react";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface InfoRow {
  label: string;
  value: string;
}

interface InfoCardProps {
  title: string;
  rows: InfoRow[];
  /** Optional thumbnail shown at the bottom of the card. */
  thumbnail?: React.ReactNode;
}

export function InfoCard({ title, rows, thumbnail }: InfoCardProps) {
  return (
    <Card data-slot="info-card">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="divide-surface-container-high/60 grid gap-3 text-sm">
          {rows.map((row) => (
            <div key={row.label} className="flex items-baseline justify-between gap-4">
              <dt className="text-on-surface-variant">{row.label}</dt>
              <dd className="text-on-surface text-right font-medium tabular-nums">{row.value}</dd>
            </div>
          ))}
        </dl>
        {thumbnail ? <div className="mt-4">{thumbnail}</div> : null}
      </CardContent>
    </Card>
  );
}
