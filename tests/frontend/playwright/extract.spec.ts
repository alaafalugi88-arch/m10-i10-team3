import { test, expect } from "@playwright/test";

test("extract page loads", async ({ page }) => {
  await page.goto("http://localhost:3000/extract");

  await expect(
    page.getByRole("heading", {
      name: /Extract/i,
    })
  ).toBeVisible();

  await expect(page.locator("textarea")).toBeVisible();

  await expect(page.getByRole("button")).toBeVisible();
});