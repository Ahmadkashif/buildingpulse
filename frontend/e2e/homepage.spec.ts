import { expect, test } from "@playwright/test";

// Skeleton smoke test: confirms the Playwright harness can boot a browser,
// navigate, and assert against the DOM. The full Next.js dev-server boot
// arrives with the first real user-flow test (issue #52+).
test("homepage loads", async ({ page }) => {
  await page.setContent(
    "<!doctype html><html><head><title>BuildingPulse</title></head><body><h1>BuildingPulse</h1></body></html>",
  );
  await expect(page).toHaveTitle("BuildingPulse");
  await expect(page.locator("h1")).toHaveText("BuildingPulse");
});
