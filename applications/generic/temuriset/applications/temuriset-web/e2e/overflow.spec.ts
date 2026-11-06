import type { Page } from '@playwright/test';

import { expect, test } from './fixtures';
import { label, ROUTES } from './routes';

/** Port of the prototype's `audit()`: the page and every visible element stay inside the viewport. */
async function overflow(page: Page) {
  return page.evaluate(() => {
    const width = document.documentElement.clientWidth;
    const outside = [...document.querySelectorAll('body *')]
      .filter((element) => {
        if (element.closest('.tr-sr') || element.tagName === 'OPTION') return false;
        const box = element.getBoundingClientRect();
        return box.width > 0 && box.right > width + 1;
      })
      .slice(0, 3)
      .map((element) => `${element.tagName.toLowerCase()}.${String(element.className).slice(0, 40)}`);
    return { scrollWidth: document.documentElement.scrollWidth, width, outside };
  });
}

for (const route of ROUTES) {
  test(`${label(route)} renders once and never scrolls sideways`, async ({ visit }) => {
    const page = await visit(route);

    await expect(page.locator('h1')).toHaveCount(1);
    const result = await overflow(page);
    expect(result.outside, 'elements past the right edge').toEqual([]);
    expect(result.scrollWidth).toBeLessThanOrEqual(result.width + 1);
  });

  test(`${label(route)} reflows with 200% text at 320 px`, async ({ visit }, testInfo) => {
    test.skip(testInfo.project.name !== 'chromium-320', 'Text scaling is checked at the narrowest width.');
    const page = await visit(route);
    await page.evaluate(() => {
      document.documentElement.style.fontSize = '200%';
    });

    const result = await overflow(page);
    expect(result.outside, 'elements past the right edge').toEqual([]);
    expect(result.scrollWidth).toBeLessThanOrEqual(result.width + 1);

    if (route.primary) {
      const action = page.getByRole('button', { name: route.primary });
      await action.scrollIntoViewIfNeeded();
      await expect(action).toBeInViewport();
      // Reachable means the pointer lands on the action itself, not on a bar drawn over it.
      const box = (await action.boundingBox())!;
      const onTop = await page.evaluate(
        ([x, y, name]) => document.elementFromPoint(x, y)?.closest('button')?.textContent?.includes(name) ?? false,
        [box.x + box.width / 2, box.y + box.height / 2, route.primary] as const,
      );
      expect(onTop, `${route.primary} is covered`).toBe(true);
    }
  });
}
