import * as fs from "node:fs";
import * as path from "node:path";

import { expect, test } from "@playwright/test";

const PREDICTION_FIXTURE = {
  id: "pred_pdf_e2e",
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

const FAKE_PDF =
  "%PDF-1.4\n%mock-e2e\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<<>>\n%%EOF\n";

test("Export PDF button issues a real download once the report is unlocked", async ({ page }) => {
  await page.route("**/api/predictions/**", async (route) => {
    const url = route.request().url();
    if (url.includes("/pdf")) {
      await route.fulfill({
        status: 200,
        contentType: "application/pdf",
        headers: {
          "Content-Disposition": `attachment; filename="building-pulse-${PREDICTION_FIXTURE.id}.pdf"`,
        },
        body: Buffer.from(FAKE_PDF, "utf-8"),
      });
      return;
    }
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
      body: JSON.stringify({ data: { id: "lead_pdf_e2e" } }),
    });
  });

  await page.goto(`/report/${PREDICTION_FIXTURE.id}`);

  const exportCta = page.getByTestId("cta-export-pdf");
  await expect(exportCta).toBeVisible({ timeout: 30_000 });
  await expect(exportCta).toBeDisabled();
  await expect(exportCta).toHaveAttribute("title", /unlock/i);

  // Unlock via lead capture flow.
  await page.getByTestId("cta-talk-to-contractor").click();
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
  await expect(exportCta).not.toHaveAttribute("title", /.+/);

  // Click Export and wait for the browser-issued download.
  const [download] = await Promise.all([page.waitForEvent("download"), exportCta.click()]);

  const suggested = download.suggestedFilename();
  expect(suggested).toMatch(/\.pdf$/i);

  const downloadDir = test.info().outputDir;
  const savedPath = path.join(downloadDir, suggested);
  await download.saveAs(savedPath);

  const stats = fs.statSync(savedPath);
  expect(stats.size).toBeGreaterThan(0);

  const head = fs.readFileSync(savedPath).slice(0, 5).toString("utf-8");
  expect(head).toBe("%PDF-");
});

