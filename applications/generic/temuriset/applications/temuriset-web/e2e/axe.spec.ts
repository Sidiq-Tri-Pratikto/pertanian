import AxeBuilder from '@axe-core/playwright';

import { expect, test } from './fixtures';
import { label, ROUTES } from './routes';

// Every rule runs, contrast included. The design system hides one of the two navigations at each width, so running
// per width checks `landmark-unique` against what is really exposed.
for (const route of ROUTES) {
  test(`${label(route)} has no axe violations`, async ({ visit }) => {
    const page = await visit(route);

    const { violations } = await new AxeBuilder({ page }).analyze();

    const summary = violations.map((violation) => ({
      rule: violation.id,
      impact: violation.impact,
      targets: violation.nodes.slice(0, 3).map((node) => node.target.join(' ')),
    }));
    expect(summary).toEqual([]);
  });
}
