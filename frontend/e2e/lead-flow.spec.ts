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

  await page.goto("/forecasting/report/pred_lead_e2e");

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
