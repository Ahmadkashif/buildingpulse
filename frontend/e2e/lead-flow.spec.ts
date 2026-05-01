import { expect, test } from "@playwright/test";

const PREDICTION_FIXTURE = {
  id: "pred_lead_e2e",
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

test("lead capture flow unlocks PDF export and retrofit scenarios", async ({ page }) => {
  await page.route("**/api/predictions/*", async (route) => {
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
      body: JSON.stringify({ data: { id: "lead_e2e_xyz" } }),
    });
  });

  await page.goto("/report/pred_lead_e2e");

  const exportCta = page.getByTestId("cta-export-pdf");
  const retrofitCta = page.getByTestId("cta-retrofit-scenarios");
  const talkCta = page.getByTestId("cta-talk-to-contractor");

  await expect(talkCta).toBeVisible({ timeout: 30_000 });
  await expect(exportCta).toBeDisabled();
  await expect(retrofitCta).toBeDisabled();

  await talkCta.click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();

  await dialog.getByLabel(/^name$/i).fill("Jane Doe");
  await dialog.getByLabel(/^email$/i).fill("jane@example.com");
  await dialog.getByLabel(/^phone$/i).fill("+1 212 555 0100");
  await dialog.getByLabel(/^role$/i).selectOption("owner");
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: /unlock report/i }).click();

  await expect(dialog).toBeHidden();
  await expect(exportCta).toBeEnabled();
  await expect(retrofitCta).toBeEnabled();
  await expect(page.getByText(/you're unlocked/i)).toBeVisible();

  // Unlocked state survives a full page reload (sessionStorage in same tab).
  await page.reload();
  await expect(page.getByTestId("cta-export-pdf")).toBeEnabled({ timeout: 30_000 });
  await expect(page.getByTestId("cta-retrofit-scenarios")).toBeEnabled();
});

test("scenarios card hides scenarios until lead capture and surfaces all fields", async ({
  page,
}) => {
  // Don't intercept the scenarios endpoint — let the MSW dev worker handle it
  // so the test exercises the real fetch path. We only stub the prediction
  // and leads endpoints to keep the rest of the report deterministic.
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
      body: JSON.stringify({ data: { id: "lead_e2e_scen" } }),
    });
  });

  await page.goto("/report/pred_lead_e2e");

  const seeRetrofitCta = page.getByTestId("cta-see-retrofit-options");
  await expect(seeRetrofitCta).toBeVisible({ timeout: 30_000 });

  // Hidden state: no scenario item is rendered before unlock.
  await expect(page.getByTestId("scenarios-list")).toHaveCount(0);
  await expect(page.locator('[data-slot="scenario-item"]')).toHaveCount(0);
  // The MSW fixture's first scenario name must not be in the DOM source either.
  const html = await page.content();
  expect(html).not.toContain("LED + Controls");

  // Click the hidden CTA -> opens lead modal.
  await seeRetrofitCta.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();

  await dialog.getByLabel(/^name$/i).fill("Jane Doe");
  await dialog.getByLabel(/^email$/i).fill("jane@example.com");
  await dialog.getByLabel(/^phone$/i).fill("+1 212 555 0100");
  await dialog.getByLabel(/^role$/i).selectOption("owner");
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: /unlock report/i }).click();

  await expect(dialog).toBeHidden();
  await expect(page.getByTestId("scenarios-list")).toBeVisible();

  // Scenario items render with name, EUI %, cost band, recomputed fine, citation.
  const items = page.locator('[data-slot="scenario-item"]');
  await expect(items.first()).toBeVisible();
  await expect(items).not.toHaveCount(0);

  const firstItem = items.first();
  await expect(firstItem.getByText(/% EUI reduction/)).toBeVisible();
  await expect(firstItem.getByText(/\/sqft$/)).toBeVisible();
  await expect(firstItem.getByText(/\/yr by 2030$/)).toBeVisible();
  await expect(firstItem.getByText(/^Source: /)).toBeVisible();
  await expect(firstItem.getByTestId("cta-choose-scenario")).toBeVisible();
});
