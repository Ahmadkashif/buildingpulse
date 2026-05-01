import { Leaf, LineChart, Wrench } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { Card } from "@/components/ui/card";
import { PredictEuiForm } from "@/components/forms/predict-eui-form";
import { EdgeAccentCard } from "@/components/report/edge-accent-card";

export default function ForecastingPage() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8">
      <PageHeader
        title="Predict Building Site EUI"
        description="Enter your NYC building specifications to calculate the predicted Site Energy Use Intensity (EUI)."
      />

      <Card className="p-10">
        <PredictEuiForm />
      </Card>

      <section aria-label="Forecast context" className="grid gap-4 md:grid-cols-3">
        <EdgeAccentCard
          accent="secondary"
          label="Efficiency Target"
          value="LL97 Compliance"
          icon={<Leaf className="size-5" />}
        />
        <EdgeAccentCard
          accent="primary"
          label="Benchmark Source"
          value="NYC LL84 Disclosure"
          icon={<LineChart className="size-5" />}
        />
        <EdgeAccentCard
          accent="tertiary"
          label="Model Version"
          value="Baseline LR v1"
          icon={<Wrench className="size-5" />}
        />
      </section>
    </div>
  );
}
