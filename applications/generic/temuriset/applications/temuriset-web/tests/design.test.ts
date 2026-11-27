import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const DESIGN_SYSTEM = join(__dirname, '../../../../../../docs/generic/temuriset/design-system');
const COPIES = [
  ['src/design/tokens.css', 'workbench/tokens.css'],
  ['src/design/bundle.css', 'project/components/bundle.css'],
  ['src/design/fonts/fonts.css', 'project/fonts/fonts.css'],
  ['src/design/fonts/OFL.txt', 'project/fonts/OFL.txt'],
  ['src/design/fonts/IBMPlexSans-Regular-Latin1.woff2', 'project/fonts/IBMPlexSans-Regular-Latin1.woff2'],
  ['src/design/fonts/IBMPlexSans-SemiBold-Latin1.woff2', 'project/fonts/IBMPlexSans-SemiBold-Latin1.woff2'],
  ['src/design/fonts/IBMPlexSans-Bold-Latin1.woff2', 'project/fonts/IBMPlexSans-Bold-Latin1.woff2'],
];

describe('design system copy', () => {
  it.each(COPIES)('%s matches the design system source; run make design after a design system release', (copy, source) => {
    // Compared as bytes, so the font files count too.
    expect(readFileSync(join(__dirname, '..', copy)).equals(readFileSync(join(DESIGN_SYSTEM, source)))).toBe(true);
  });
});
