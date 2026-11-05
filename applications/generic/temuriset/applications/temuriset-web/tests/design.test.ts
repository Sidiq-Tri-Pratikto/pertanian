import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const DESIGN_SYSTEM = join(__dirname, '../../../../../../docs/generic/temuriset/design-system');
const COPIES = [
  ['src/design/tokens.css', 'workbench/tokens.css'],
  ['src/design/bundle.css', 'project/components/bundle.css'],
];

describe('design system copy', () => {
  it.each(COPIES)('%s matches the design system source; run make design after a design system release', (copy, source) => {
    expect(readFileSync(join(__dirname, '..', copy), 'utf8')).toBe(readFileSync(join(DESIGN_SYSTEM, source), 'utf8'));
  });
});
