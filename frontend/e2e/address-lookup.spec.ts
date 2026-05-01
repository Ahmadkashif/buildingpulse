import { expect, test } from "@playwright/test";

const FLAG_ON_BASE = "http://localhost:3100";
const FLAG_OFF_BASE = "http://localhost:3101";

test("flag on: typing a known address auto-fills the form fields", async ({ page }) => {
  await page.goto(`${FLAG_ON_BASE}/report`);

  const addressInput = page.getByTestId("address-lookup-input");
  await expect(addressInput).toBeVisible({ timeout: 30_000 });

  await addressInput.fill("100 Synth St");
  await page.getByTestId("address-lookup-submit").click();

  await expect(page.getByTestId("address-lookup-status")).toContainText(/Match found/i);

  // The fixture in src/mocks/data/addresses.ts hits 100 SYNTH ST -> office /
  // manhattan / 75,000 sqft / 1985.
  await expect(page.getByLabel(/Property Type/i)).toHaveValue("office");
  await expect(page.getByLabel(/Borough/i)).toHaveValue("manhattan");
  await expect(page.getByLabel(/Gross Floor Area/i)).toHaveValue("75000");
  await expect(page.getByLabel(/Year Built/i)).toHaveValue("1985");
});

test("flag off: address lookup affordance is not in the DOM", async ({ page }) => {
  await page.goto(`${FLAG_OFF_BASE}/report`);

  // Page must render the predict form (sanity).
  await expect(page.getByLabel(/Property Type/i)).toBeVisible({ timeout: 30_000 });

  await expect(page.getByTestId("address-lookup-field")).toHaveCount(0);
  await expect(page.getByTestId("address-lookup-input")).toHaveCount(0);
  await expect(page.getByTestId("address-lookup-submit")).toHaveCount(0);
});
