import { expect, test } from "@playwright/test";

const PREDICTION_FIXTURE = {
  id: "pred_e2e_01",
  generatedAt: "2026-04-16T14:30:00-04:00",
  input: {
    propertyType: "multifamily-housing",
    borough: "brooklyn",
    grossFloorAreaSqft: 45000,
    yearBuilt: 1925,
    numberOfBuildings: 1,
  },
  prediction: {
    siteEuiKbtuPerSqft: 87.3,
    intervalLow: 65.2,
    intervalHigh: 109.4,
    modelVersion: "baseline-lr-v1",
  },
  peer: {
    cohort: { propertyType: "multifamily-housing", borough: "brooklyn", ageBand: "pre-1950" },
    cohortSize: 1420,
    medianSiteEui: 74.1,
    p25SiteEui: 58.0,
    p75SiteEui: 94.5,
    percentile: 68,
  },
  ll97: {
    capKbtuPerSqft2024To2029: 6.75,
    capKbtuPerSqft2030To2034: 4.53,
    projectedAnnualFineUsd2024: 0,
    projectedAnnualFineUsd2030: 12400,
    atRisk: true,
    fineSeries: [
      { year: 2026, projectedAnnualFineUsd: 0 },
      { year: 2027, projectedAnnualFineUsd: 0 },
      { year: 2028, projectedAnnualFineUsd: 0 },
      { year: 2029, projectedAnnualFineUsd: 0 },
      { year: 2030, projectedAnnualFineUsd: 12400 },
      { year: 2031, projectedAnnualFineUsd: 12400 },
      { year: 2032, projectedAnnualFineUsd: 12400 },
      { year: 2033, projectedAnnualFineUsd: 12400 },
      { year: 2034, projectedAnnualFineUsd: 12400 },
    ],
  },
};

/**
 * Stubs the prediction API at the network layer (independent of MSW),
 * loads the report page directly, and asserts the LL97 step marker is
 * present once the prediction has been "successfully" returned.
 */
test("prediction report renders the LL97 step at 2030", async ({ page }) => {
  await page.route("**/api/predictions/*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: PREDICTION_FIXTURE }),
    });
  });

  await page.goto("/forecasting/report/pred_e2e_01");

  await expect(page.getByTestId("ll97-fine-series-chart")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByTestId("ll97-step-2030")).toBeVisible();
});
