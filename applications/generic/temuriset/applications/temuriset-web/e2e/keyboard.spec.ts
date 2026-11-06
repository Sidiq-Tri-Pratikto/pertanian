import { expect, test } from './fixtures';
import { label, ROUTES } from './routes';

const MAX_TABS = 60;

type Focus = { name: string; outline: boolean; inViewport: boolean; underBar: boolean } | null;

for (const route of ROUTES.filter((entry) => entry.status === undefined)) {
  test(`${label(route)} keeps every focused control visible at 360 px`, async ({ visit }, testInfo) => {
    test.skip(testInfo.project.name !== 'chromium-360', 'Keyboard reach is checked at phone width with the tab bar.');
    const page = await visit(route);

    const seen: string[] = [];
    const problems: string[] = [];
    for (let step = 0; step < MAX_TABS; step += 1) {
      await page.keyboard.press('Tab');
      const focus: Focus = await page.evaluate(() => {
        const element = document.activeElement as HTMLElement | null;
        if (!element || element === document.body) return null;
        const style = getComputedStyle(element);
        const box = element.getBoundingClientRect();
        const bar = document.querySelector('.tr-tabbar:not(.is-static)');
        const barTop = bar && getComputedStyle(bar).display !== 'none' ? bar.getBoundingClientRect().top : Infinity;
        return {
          name: `${element.tagName.toLowerCase()} ${(element.textContent ?? '').trim().slice(0, 30)}`,
          outline: (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== 'none',
          inViewport: box.bottom > 0 && box.top < window.innerHeight && box.width > 0 && box.height > 0,
          underBar: !(bar?.contains(element) ?? false) && box.bottom > barTop + 1,
        };
      });
      if (focus === null || seen.includes(focus.name)) break;
      seen.push(focus.name);
      if (!focus.outline) problems.push(`${focus.name}: no visible focus indicator`);
      if (!focus.inViewport) problems.push(`${focus.name}: outside the viewport`);
      if (focus.underBar) problems.push(`${focus.name}: covered by the tab bar`);
    }

    expect(seen.length, 'reachable controls').toBeGreaterThan(0);
    expect(problems).toEqual([]);
  });

  test(`${label(route)} skip link moves focus to the main region`, async ({ visit }, testInfo) => {
    test.skip(testInfo.project.name !== 'chromium-360', 'Checked once, at phone width.');
    test.skip(route.persona === null, 'The start screen has no navigation to skip.');
    const page = await visit(route);

    await page.keyboard.press('Tab');
    const skip = page.getByRole('link', { name: 'Langsung ke isi utama' });
    await expect(skip).toBeFocused();
    await expect(skip).toBeInViewport();
    await page.keyboard.press('Enter');

    await expect(page.locator('main#isi')).toBeFocused();
  });
}
