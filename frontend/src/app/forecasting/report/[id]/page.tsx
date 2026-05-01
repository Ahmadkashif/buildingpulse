"use client";

import * as React from "react";
import { use } from "react";
import { Download, FileText, Pencil, Leaf, Phone, Sun, Thermometer, Wind } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shell/page-header";
import { KpiTile } from "@/components/report/kpi-tile";
import { BarChartCard } from "@/components/report/bar-chart-card";
import { FineSeriesChart } from "@/components/report/fine-series-chart";
import { InfoCard } from "@/components/report/info-card";
import { InsightCard } from "@/components/report/insight-card";
import { ActionColumn } from "@/components/report/action-column";
import { ExportDialog } from "@/components/report/export-dialog";
import { SponsorStrip } from "@/components/report/sponsor-strip";
import { ScenariosCard } from "@/components/report/scenarios-card";
import { LeadModal, type LeadModalContext } from "@/components/modal/lead-modal";
import { usePrediction } from "@/hooks/use-prediction";
import { useUnlock } from "@/providers/unlock-provider";
import type {
  BuildingBorough,
  BuildingPropertyType,
  InsightBadge,
  PredictionInsight,
  PredictionResponse,
} from "@/types";

const INSIGHT_ICONS: Record<InsightBadge, React.ComponentType<{ className?: string }>> = {
  savings: Thermometer,
  verified: Wind,
  "yield-high": Sun,
  action: Leaf,
};

const PROPERTY_TYPE_LABELS: Record<BuildingPropertyType, string> = {
  "multifamily-housing": "Multifamily Housing",
  office: "Office",
  hotel: "Hotel",
  retail: "Retail",
  hospital: "Hospital",
  "mixed-use": "Mixed Use",
};

const BOROUGH_LABELS: Record<BuildingBorough, string> = {
  manhattan: "Manhattan",
  brooklyn: "Brooklyn",
  queens: "Queens",
  bronx: "Bronx",
  "staten-island": "Staten Island",
};

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [exportOpen, setExportOpen] = React.useState(false);
  const [leadOpen, setLeadOpen] = React.useState(false);

  const { isUnlocked, unlock } = useUnlock();
  const unlocked = isUnlocked(id);

  const query = usePrediction(id);

  if (query.isLoading) {
    return <ReportSkeleton />;
  }

  const prediction = query.data?.data;

  if (!prediction) {
    return (
      <div className="mx-auto flex max-w-3xl flex-col gap-4 py-24 text-center">
        <h1 className="font-heading text-2xl font-bold">Prediction not found</h1>
        <p className="text-on-surface-variant text-sm">
          We couldn&apos;t load the prediction for {id}.
        </p>
      </div>
    );
  }

  const kpis = buildKpis(prediction);
  const peerChart = buildPeerChart(prediction);
  const insights = buildInsights(prediction);
  const profile = buildProfile(prediction);
  const pageTitle = `Site EUI Prediction · ${PROPERTY_TYPE_LABELS[prediction.input.propertyType]}`;

  return (
    <div className="flex flex-col gap-8">
      <SponsorStrip />
      <PageHeader
        title={pageTitle}
        description="Predicted Site Energy Use Intensity, peer cohort ranking, and LL97 compliance outlook."
      />

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="flex flex-col gap-6">
          <section aria-label="Headline metrics" className="grid gap-4 md:grid-cols-3">
            {kpis.map((kpi) => (
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
            title="Peer Cohort Comparison"
            description={`Your building vs. ${prediction.peer.cohortSize.toLocaleString()} similar buildings in ${BOROUGH_LABELS[prediction.peer.cohort.borough]}.`}
            data={peerChart}
            legend={{ primary: "Peer Cohort", secondary: "Your Building" }}
          />

          <FineSeriesChart
            title="LL97 Fine Outlook"
            description="Projected annual fines across the 2024–2029 and 2030–2034 compliance periods."
            data={prediction.ll97.fineSeries}
          />

          <ScenariosCard
            unlocked={unlocked}
            query={{
              predictionId: id,
              propertyType: prediction.input.propertyType,
              predictedEui: prediction.prediction.siteEuiKbtuPerSqft,
              grossFloorAreaSqft: prediction.input.grossFloorAreaSqft,
            }}
            onRequestUnlock={() => setLeadOpen(true)}
          />

          <section aria-label="Insights" className="flex flex-col gap-4">
            <h2 className="font-heading text-lg font-semibold tracking-tight">
              Insights &amp; Observations
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {insights.map((insight) => {
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
          <InfoCard title="Building Profile" rows={profile} />

          <ActionColumn>
            <Button
              variant="tertiary"
              width="full"
              onClick={() => setExportOpen(true)}
              disabled={!unlocked}
              data-testid="cta-export-pdf"
              aria-disabled={!unlocked || undefined}
            >
              <Download className="size-4" /> Export Full PDF Report
            </Button>
            <Button
              variant="secondary"
              width="full"
              disabled={!unlocked}
              data-testid="cta-retrofit-scenarios"
              aria-disabled={!unlocked || undefined}
            >
              <FileText className="size-4" /> View Retrofit Options
            </Button>
            <Button variant="tertiary" width="full">
              <Pencil className="size-4" /> Refine Building Inputs
            </Button>
          </ActionColumn>
        </div>
      </div>

      <section
        data-testid="report-bottom-cta"
        className="border-outline-variant/40 mt-4 flex flex-col items-center gap-3 rounded-2xl border-t border-dashed py-8 text-center"
      >
        {unlocked ? (
          <>
            <h2 className="font-heading text-xl font-semibold">You&apos;re unlocked</h2>
            <p className="text-on-surface-variant max-w-prose text-sm">
              Retrofit scenarios and the PDF export are now available. A contractor will reach out
              shortly.
            </p>
          </>
        ) : (
          <>
            <h2 className="font-heading text-xl font-semibold">Ready to fix this?</h2>
            <p className="text-on-surface-variant max-w-prose text-sm">
              Talk to a vetted contractor about retrofits that bring this building back into
              compliance — and unlock your PDF report and retrofit scenarios.
            </p>
            <Button
              variant="gradient"
              size="lg"
              onClick={() => setLeadOpen(true)}
              data-testid="cta-talk-to-contractor"
            >
              <Phone className="size-4" /> Talk to a contractor
            </Button>
          </>
        )}
      </section>

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} reportId={id} />
      <LeadModal
        open={leadOpen}
        onClose={() => setLeadOpen(false)}
        onSuccess={() => unlock(id)}
        context={buildLeadContext(id, prediction)}
      />
    </div>
  );
}

interface KpiViewModel {
  label: string;
  value: string;
  caption?: string;
  signature?: boolean;
}

function buildKpis(p: PredictionResponse): KpiViewModel[] {
  const eui = p.prediction.siteEuiKbtuPerSqft;
  return [
    {
      label: "Predicted Site EUI",
      value: `${eui.toFixed(1)} kBtu/sf`,
      caption: `Interval: ${p.prediction.intervalLow.toFixed(1)} – ${p.prediction.intervalHigh.toFixed(1)} kBtu/sf`,
      signature: true,
    },
    {
      label: "Peer Percentile",
      value: `${p.peer.percentile}${ordinal(p.peer.percentile)}`,
      caption: `Higher = uses more energy than peers`,
    },
    {
      label: "LL97 Status",
      value: p.ll97.atRisk ? "At Risk" : "Compliant",
      caption: p.ll97.atRisk
        ? `Projected fine: $${p.ll97.projectedAnnualFineUsd2030.toLocaleString()}/yr by 2030`
        : "Below current cap",
    },
  ];
}

function buildPeerChart(p: PredictionResponse) {
  return [
    { label: "p25", primary: p.peer.p25SiteEui, secondary: 0 },
    { label: "Median", primary: p.peer.medianSiteEui, secondary: 0 },
    { label: "You", primary: 0, secondary: p.prediction.siteEuiKbtuPerSqft },
    { label: "p75", primary: p.peer.p75SiteEui, secondary: 0 },
  ];
}

function buildInsights(p: PredictionResponse): PredictionInsight[] {
  const insights: PredictionInsight[] = [];
  const eui = p.prediction.siteEuiKbtuPerSqft;
  const gap = eui - p.peer.medianSiteEui;
  const typeLabel = PROPERTY_TYPE_LABELS[p.input.propertyType].toLowerCase();

  if (p.peer.percentile >= 75) {
    insights.push({
      id: "high-usage",
      badge: "action",
      title: "High Energy Use",
      description: `Your building sits at the ${p.peer.percentile}${ordinal(p.peer.percentile)} percentile — using more energy than most comparable ${typeLabel} buildings in this cohort.`,
    });
  } else if (p.peer.percentile <= 25) {
    insights.push({
      id: "top-performer",
      badge: "verified",
      title: "Leading Your Cohort",
      description: `Predicted Site EUI falls below the 25th percentile for this cohort — a strong efficiency baseline.`,
    });
  } else {
    insights.push({
      id: "median-range",
      badge: "verified",
      title: "Near Cohort Median",
      description: `Predicted Site EUI sits within the middle 50% of the ${typeLabel} cohort for this vintage.`,
    });
  }

  if (p.ll97.atRisk) {
    insights.push({
      id: "ll97-risk",
      badge: "action",
      title: "Projected LL97 Fine",
      description: `At current efficiency, annual LL97 penalties are projected at ~$${p.ll97.projectedAnnualFineUsd2030.toLocaleString()} starting 2030.`,
    });
  }

  if (gap > 0) {
    const savings = Math.round(gap * p.input.grossFloorAreaSqft);
    insights.push({
      id: "retrofit-opportunity",
      badge: "savings",
      title: "Retrofit Opportunity",
      description: `Reaching cohort median (${p.peer.medianSiteEui.toFixed(1)} kBtu/sf) would cut site energy by ~${savings.toLocaleString()} kBtu/yr.`,
    });
  } else {
    insights.push({
      id: "vintage-cohort",
      badge: "yield-high",
      title: "Vintage Cohort Context",
      description: `Benchmarked against ${p.peer.cohortSize.toLocaleString()} ${p.peer.cohort.ageBand} ${typeLabel} buildings in ${BOROUGH_LABELS[p.peer.cohort.borough]}.`,
    });
  }

  return insights.slice(0, 4);
}

function buildLeadContext(id: string, p: PredictionResponse): LeadModalContext {
  const reportUrl =
    typeof window !== "undefined" && window.location
      ? `${window.location.origin}/forecasting/report/${id}`
      : `/forecasting/report/${id}`;
  return {
    predictionId: id,
    propertyType: p.input.propertyType,
    borough: p.input.borough,
    grossFloorAreaSqft: p.input.grossFloorAreaSqft,
    yearBuilt: p.input.yearBuilt,
    predictedEui: p.prediction.siteEuiKbtuPerSqft,
    projectedFineUsd: p.ll97.projectedAnnualFineUsd2030,
    atRisk: p.ll97.atRisk,
    reportUrl,
  };
}

function buildProfile(p: PredictionResponse) {
  return [
    { label: "Property Type", value: PROPERTY_TYPE_LABELS[p.input.propertyType] },
    { label: "Borough", value: BOROUGH_LABELS[p.input.borough] },
    { label: "Gross Floor Area", value: `${p.input.grossFloorAreaSqft.toLocaleString()} sqft` },
    { label: "Year Built", value: String(p.input.yearBuilt) },
    { label: "Buildings on Lot", value: String(p.input.numberOfBuildings) },
    { label: "Model Version", value: p.prediction.modelVersion },
  ];
}

function ordinal(n: number): string {
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 13) return "th";
  switch (n % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
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
