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

test("Choose this scenario fires ScenarioSelected then redirects to sponsor CTA with both ids", async ({
  page,
}) => {
  // The MSW worker handles /api/scenarios/:id/select and /api/predictions/:id/scenarios
  // (see src/mocks/handlers/scenario.ts) so we leave those alone and just stub the
  // prediction GET + leads POST + a sponsor CTA stand-in (so the page lands on a
  // known URL we can read both query params off of).
  await page.route("**/api/predictions/*", async (route) => {
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

  await page.route("**/api/leads", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ data: { id: "lead_scen_cta" } }),
    });
  });

  await page.route("**/api/sponsor/cta*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<html><body><h1>Sponsor CTA landed</h1></body></html>",
    });
  });

  // Capture network-level events for assertions (page.on('request') sees
  // every outgoing fetch including ones MSW eventually intercepts via SW).
  const selectRequests: { url: string; postData: string | null }[] = [];
  const ctaRequests: string[] = [];
  page.on("request", (req) => {
    const u = req.url();
    if (req.method() === "POST" && u.includes("/api/scenarios/") && u.endsWith("/select")) {
      selectRequests.push({ url: u, postData: req.postData() });
    }
    if (u.includes("/api/sponsor/cta")) {
      ctaRequests.push(u);
    }
  });

  await page.goto("/report/pred_scen_e2e");

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

  // Click "Choose this scenario" on the first scenario item — this drives
  // the audit POST + sponsor CTA redirect. Read the id off the rendered
  // card so the assertions stay stable under fixture churn.
  const firstItem = page.locator('[data-slot="scenario-item"]').first();
  await expect(firstItem).toBeVisible();
  const expectedScenarioId = await firstItem.getAttribute("data-scenario-id");
  expect(expectedScenarioId).toBeTruthy();
  await firstItem.getByTestId("cta-choose-scenario").click();

  // The browser should land on the sponsor CTA URL with both ids — this
  // is the user-visible contract per AC #2 ("sponsor URL receives both
  // ids in the redirect target").
  await page.waitForURL(/\/api\/sponsor\/cta/);
  const landedUrl = new URL(page.url());
  expect(landedUrl.searchParams.get("prediction_id")).toBe("pred_scen_e2e");
  expect(landedUrl.searchParams.get("scenario_id")).toBe(expectedScenarioId);

  // Single click -> single ScenarioSelected POST (debounce guard) and a
  // single sponsor CTA navigation.
  expect(selectRequests).toHaveLength(1);
  expect(selectRequests[0]!.url).toContain(
    `/api/scenarios/${encodeURIComponent(expectedScenarioId!)}/select`,
  );
  expect(JSON.parse(selectRequests[0]!.postData ?? "null")).toEqual({
    predictionId: "pred_scen_e2e",
  });
  expect(ctaRequests.length).toBeGreaterThanOrEqual(1);
  expect(ctaRequests[0]!).toContain("prediction_id=pred_scen_e2e");
  expect(ctaRequests[0]!).toContain(`scenario_id=${expectedScenarioId}`);
});
