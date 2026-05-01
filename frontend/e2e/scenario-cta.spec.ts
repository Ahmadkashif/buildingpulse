import { expect, test } from "@playwright/test";

const PREDICTION_FIXTURE = {
  id: "pred_scen_e2e",
  generatedAt: "2026-04-16T14:30:00-04:00",
  input: {
    propertyType: "office",
    borough: "manhattan",
    grossFloorAreaSqft: 100_000,
    yearBuilt: 1990,
    numberOfBuildings: 1,
  },
  prediction: {
    siteEuiKbtuPerSqft: 95.4,
    intervalLow: 78.1,
    intervalHigh: 113.0,
    modelVersion: "baseline-lr-v1",
  },
  peer: {
    cohort: { propertyType: "office", borough: "manhattan", ageBand: "1980-1999" },
    cohortSize: 800,
    medianSiteEui: 80.2,
    p25SiteEui: 65.0,
    p75SiteEui: 100.0,
    percentile: 78,
  },
  ll97: {
    capKbtuPerSqft2024To2029: 8.46,
    capKbtuPerSqft2030To2034: 4.53,
    projectedAnnualFineUsd2024: 0,
    projectedAnnualFineUsd2030: 12345,
    atRisk: true,
    fineSeries: [
      { year: 2026, projectedAnnualFineUsd: 0 },
      { year: 2030, projectedAnnualFineUsd: 12345 },
    ],
  },
};

const SCENARIOS_FIXTURE = [
  {
    id: "heat-pump-conversion",
    name: "Heat pumps",
    description: "Replace boilers with VRF heat pumps.",
    reductionPct: 0.35,
    costLow: 12,
    costHigh: 30,
    recomputedFineSeries: [{ year: 2030, projectedAnnualFineUsd: 5000 }],
    recomputedFine2024: 0,
    recomputedFine2030: 5000,
    citation: "NYC Mayor's Office — Getting to 80x50",
  },
];

test("Choose this scenario fires ScenarioSelected then redirects to sponsor CTA with both ids", async ({
  page,
}) => {
  await page.route("**/api/predictions/pred_scen_e2e", async (route) => {
    const url = route.request().url();
    if (url.includes("/scenarios")) {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: PREDICTION_FIXTURE }),
    });
  });

  await page.route("**/api/predictions/pred_scen_e2e/scenarios*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: SCENARIOS_FIXTURE }),
    });
  });

  await page.route("**/api/leads", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ data: { id: "lead_scen_cta" } }),
    });
  });

  // The select endpoint records ScenarioSelected and returns 200.
  const selectCalls: { url: string; body: string | null }[] = [];
  await page.route("**/api/scenarios/*/select", async (route) => {
    const req = route.request();
    selectCalls.push({ url: req.url(), body: req.postData() });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: { predictionId: "pred_scen_e2e", scenarioId: "heat-pump-conversion", deduped: false },
      }),
    });
  });

  // Stub the sponsor CTA at the same origin: simulate the server-side
  // 302 to the sponsor URL by serving an HTML page so the browser stays
  // on a known location we can assert against.
  const ctaCalls: string[] = [];
  await page.route("**/api/sponsor/cta*", async (route) => {
    ctaCalls.push(route.request().url());
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<html><body><h1>Sponsor CTA landed</h1></body></html>",
    });
  });

  await page.goto("/forecasting/report/pred_scen_e2e");

  // Unlock by capturing a lead so the scenarios card is visible.
  const seeRetrofit = page.getByTestId("cta-see-retrofit-options");
  await expect(seeRetrofit).toBeVisible({ timeout: 30_000 });
  await seeRetrofit.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByLabel(/^name$/i).fill("Jane Doe");
  await dialog.getByLabel(/^email$/i).fill("jane@example.com");
  await dialog.getByLabel(/^phone$/i).fill("+1 212 555 0100");
  await dialog.getByLabel(/^role$/i).selectOption("owner");
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: /unlock report/i }).click();
  await expect(dialog).toBeHidden();

  // Click "Choose this scenario" — this drives the audit POST + redirect.
  const chooseButton = page.getByTestId("cta-choose-scenario").first();
  await expect(chooseButton).toBeVisible();
  await chooseButton.click();

  // The browser should land on the sponsor CTA URL with both ids.
  await page.waitForURL(/\/api\/sponsor\/cta/);
  const landedUrl = new URL(page.url());
  expect(landedUrl.searchParams.get("prediction_id")).toBe("pred_scen_e2e");
  expect(landedUrl.searchParams.get("scenario_id")).toBe("heat-pump-conversion");

  // Both intercepted endpoints were hit exactly once for the single click.
  expect(selectCalls).toHaveLength(1);
  expect(selectCalls[0]!.url).toContain("/api/scenarios/heat-pump-conversion/select");
  expect(JSON.parse(selectCalls[0]!.body ?? "null")).toEqual({
    predictionId: "pred_scen_e2e",
  });

  expect(ctaCalls).toHaveLength(1);
  expect(ctaCalls[0]!).toContain("prediction_id=pred_scen_e2e");
  expect(ctaCalls[0]!).toContain("scenario_id=heat-pump-conversion");
});
