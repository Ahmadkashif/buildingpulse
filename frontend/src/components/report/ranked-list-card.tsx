import * as React from "react";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface RankedListItem {
  label: string;
  value: string;
  unit?: string;
}

interface RankedListCardProps {
  title: string;
  items: RankedListItem[];
}

export function RankedListCard({ title, items }: RankedListCardProps) {
  return (
    <Card data-slot="ranked-list-card" className="p-5">
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3 text-sm">
          {items.map((item) => (
            <li key={item.label} className="flex items-baseline justify-between gap-4">
              <span className="text-on-surface">{item.label}</span>
              <span className="text-on-surface font-semibold tabular-nums">
                {item.value}
                {item.unit ? (
                  <span className="text-on-surface-variant ml-1 text-xs font-normal">
                    {item.unit}
                  </span>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
