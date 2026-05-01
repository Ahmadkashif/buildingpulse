"use client";

import * as React from "react";

import { useSponsor } from "@/hooks/use-sponsor";
import { cn } from "@/lib/utils";

/**
 * Co-brand strip rendered at the top of the report page. Reads the active
 * sponsor via `useSponsor`. Has explicit loading and error states; the
 * error state degrades silently into a neutral fallback so the report
 * itself is never blocked.
 */
export function SponsorStrip({ className }: { className?: string }) {
  const query = useSponsor();

  if (query.isLoading) {
    return (
      <div
        data-slot="sponsor-strip"
        data-state="loading"
        role="status"
        aria-label="Loading sponsor"
        className={cn(
          "bg-surface-container-high/60 flex animate-pulse items-center gap-3 rounded-xl px-4 py-3",
          "flex-col sm:flex-row sm:items-center",
          className,
        )}
      >
        <div className="bg-surface-container-high h-8 w-8 rounded" />
        <div className="bg-surface-container-high h-4 w-40 rounded" />
      </div>
    );
  }

  const sponsor = query.data?.data;

  if (query.isError || !sponsor) {
    return (
      <div
        data-slot="sponsor-strip"
        data-state="error"
        className={cn(
          "text-on-surface-variant bg-surface-container-high/40 rounded-xl px-4 py-3 text-sm",
          className,
        )}
      >
        Powered by BuildingPulse
      </div>
    );
  }

  return (
    <div
      data-slot="sponsor-strip"
      data-state="ready"
      className={cn(
        "bg-surface-container-high/60 flex items-center gap-3 rounded-xl px-4 py-3",
        "flex-col text-center sm:flex-row sm:text-left",
        className,
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={sponsor.logoUrl}
        alt={`${sponsor.name} logo`}
        className="h-8 w-auto shrink-0 object-contain"
      />
      <span className="text-on-surface-variant text-sm">
        Powered by <span className="text-on-surface font-medium">{sponsor.name}</span>
      </span>
    </div>
  );
}
