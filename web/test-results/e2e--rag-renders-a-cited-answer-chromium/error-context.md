# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e.spec.ts >> /rag renders a cited answer
- Location: tests\e2e.spec.ts:28:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="citation-marker"]').first()
Expected: visible
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 30000ms
  - waiting for locator('[data-testid="citation-marker"]').first()

```

```yaml
- main:
  - heading "RAG — Cited Answer" [level=1]
  - textbox "Ask a recipe question...": How do I prep ginger for stir-fry?
  - button "Ask"
  - alert: Network error reaching the backend.
- alert
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | // Playwright smoke tests — exercise each page against the running
  4  | // backend. The autograder runs `npm ci && npm run build` first, then
  5  | // brings the dev server up via playwright.config.ts `webServer`.
  6  | 
  7  | test("/ landing page lists three demo links", async ({ page }) => {
  8  |   await page.goto("/");
  9  |   await expect(page.getByRole("link", { name: /Extract entities/i })).toBeVisible();
  10 |   await expect(page.getByRole("link", { name: /knowledge graph/i })).toBeVisible();
  11 |   await expect(page.getByRole("link", { name: /RAG/i })).toBeVisible();
  12 | });
  13 | 
  14 | test("/extract renders entity spans for a known input", async ({ page }) => {
  15 |   await page.goto("/extract");
  16 |   await page.locator("textarea").fill("Akira Kurosawa directed Seven Samurai in 1954.");
  17 |   await page.getByRole("button", { name: /Extract/i }).click();
  18 |   await expect(page.locator('[data-testid="entity-span"]').first()).toBeVisible({ timeout: 10_000 });
  19 | });
  20 | 
  21 | test("/kg renders rows for a seeded question", async ({ page }) => {
  22 |   await page.goto("/kg");
  23 |   await page.locator("input").fill("Find Sichuan recipes");
  24 |   await page.getByRole("button", { name: /Ask/i }).click();
  25 |   await expect(page.locator('[data-testid="kg-row"]').first()).toBeVisible({ timeout: 10_000 });
  26 | });
  27 | 
  28 | test("/rag renders a cited answer", async ({ page }) => {
  29 |   await page.goto("/rag");
  30 |   await page.locator("input").fill("How do I prep ginger for stir-fry?");
  31 |   await page.getByRole("button", { name: /Ask/i }).click();
> 32 |   await expect(page.locator('[data-testid="citation-marker"]').first()).toBeVisible({ timeout: 30_000 });
     |                                                                         ^ Error: expect(locator).toBeVisible() failed
  33 | });
  34 | 
```