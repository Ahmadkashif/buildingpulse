"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ForecastProgress } from "@/components/loading/forecast-progress";

function PredictingInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const forecastId = searchParams.get("forecastId");

  const onComplete = React.useCallback(() => {
    if (!forecastId) return;
    const id = setTimeout(() => {
      router.push(`/forecasting/report/${forecastId}`);
    }, 600);
    return () => clearTimeout(id);
  }, [forecastId, router]);

  return <ForecastProgress onComplete={onComplete} />;
}

export default function PredictingPage() {
  return (
    <React.Suspense fallback={<ForecastProgress />}>
      <PredictingInner />
    </React.Suspense>
  );
}
