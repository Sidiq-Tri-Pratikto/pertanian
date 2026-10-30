import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { tokens } from '@/design/tokens.generated';

const source = JSON.parse(readFileSync(join(__dirname, '../design/tokens.json'), 'utf8'));

describe('design tokens', () => {
  it('resolves semantic colours to the design system values', () => {
    expect(tokens.color.backgroundCanvas).toBe('#f6f7f3');
    expect(tokens.color.actionPrimaryBackground).toBe('#1f6947');
    expect(tokens.color.focusRing).toBe('#145cc5');
    expect(tokens.component.tabSelectedIndicator).toBe('#1f6947');
  });

  it('exposes every semantic colour and no palette value', () => {
    const semantic = source.color.tokens.filter((token: { name: string }) => token.name.startsWith('color-'));

    expect(Object.keys(tokens.color)).toHaveLength(semantic.length);
    expect(Object.keys(tokens.color).some((name) => name.startsWith('palette'))).toBe(false);
  });

  it('converts type from rem to logical units and keeps the 48 target', () => {
    expect(tokens.type.metric).toEqual({ fontSize: 34, lineHeight: 40, fontWeight: '600' });
    expect(tokens.type.body).toEqual({ fontSize: 16, lineHeight: 24, fontWeight: '400' });
    expect(tokens.size.targetMinimum).toBe(48);
  });
});
