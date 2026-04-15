"use client";

import * as React from "react";
import { use } from "react";
import { Download, FileText, Pencil, Leaf, Sun, Thermometer, Wind } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shell/page-header";
import { KpiTile } from "@/components/report/kpi-tile";
import { BarChartCard } from "@/components/report/bar-chart-card";
import { InfoCard } from "@/components/report/info-card";
import { InsightCard } from "@/components/report/insight-card";
import { RankedListCard } from "@/components/report/ranked-list-card";
import { ActionColumn } from "@/components/report/action-column";
import { ExportDialog } from "@/components/report/export-dialog";
import { useForecast } from "@/hooks/use-forecast";
import { useReport } from "@/hooks/use-report";
import type { ForecastInsightBadge } from "@/types";

const INSIGHT_ICONS: Record<ForecastInsightBadge, React.ComponentType<{ className?: string }>> = {
  savings: Thermometer,
  verified: Wind,
  "yield-high": Sun,
  action: Leaf,
};

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [exportOpen, setExportOpen] = React.useState(false);

  const reportQuery = useReport(id);
  const forecastQuery = useForecast(id);

  if (reportQuery.isLoading || forecastQuery.isLoading) {
    return <ReportSkeleton />;
  }

  const report = reportQuery.data?.data;
  const forecast = forecastQuery.data?.data;

  if (!report || !forecast) {
    return (
      <div className="mx-auto flex max-w-3xl flex-col gap-4 py-24 text-center">
        <h1 className="font-heading text-2xl font-bold">Report not found</h1>
        <p className="text-on-surface-variant text-sm">
          We couldn&apos;t load the forecast report for {id}.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title={`AI Forecast Report: ${report.buildingName}`}
        description="Predicted energy profile, insights, and recommended interventions."
      />

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="flex flex-col gap-6">
          <section aria-label="Headline metrics" className="grid gap-4 md:grid-cols-3">
            {report.kpis.map((kpi) => (
              <KpiTile
                key={kpi.label}
                label={kpi.label}
                value={kpi.value}
                caption={kpi.caption}
                signature={kpi.signature}
              />
            ))}
          </section>

          <BarChartCard
            title="Consumption Breakdown"
            description="Monthly predictive analysis for the 2024 calendar year."
            data={forecast.breakdown.map((d) => ({
              label: d.month,
              primary: d.predicted,
              secondary: d.savingsPotential,
            }))}
            legend={{ primary: "Predicted", secondary: "Savings Potential" }}
          />

          <section aria-label="AI insights" className="flex flex-col gap-4">
            <h2 className="font-heading text-lg font-semibold tracking-tight">
              AI Insights &amp; Observations
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {forecast.insights.map((insight) => {
                const Icon = INSIGHT_ICONS[insight.badge];
                return (
                  <InsightCard
                    key={insight.id}
                    title={insight.title}
                    description={insight.description}
                    badge={insight.badge}
                    icon={<Icon className="size-4" />}
                  />
                );
              })}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-6">
          <InfoCard title="Building Profile" rows={report.profile} />

          <ActionColumn>
            <Button variant="tertiary" width="full" onClick={() => setExportOpen(true)}>
              <Download className="size-4" /> Export Full PDF Report
            </Button>
            <Button variant="secondary" width="full">
              <FileText className="size-4" /> Apply Recommendations
            </Button>
            <Button variant="tertiary" width="full">
              <Pencil className="size-4" /> Refine Building Inputs
            </Button>
          </ActionColumn>

          <RankedListCard
            title="Top Portfolio Consumers"
            items={report.rankedAssets.map((a) => ({
              label: a.buildingName,
              value: a.value,
              unit: a.unit,
            }))}
          />
        </div>
      </div>

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} reportId={id} />
    </div>
  );
}

function ReportSkeleton() {
  return (
    <div className="flex animate-pulse flex-col gap-6 py-8">
      <div className="bg-surface-container-high h-10 w-96 rounded-md" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-container-high h-32 rounded-xl" />
        <div className="bg-surface-container-high h-32 rounded-xl" />
        <div className="bg-surface-container-high h-32 rounded-xl" />
      </div>
      <div className="bg-surface-container-high h-64 rounded-xl" />
    </div>
  );
}
