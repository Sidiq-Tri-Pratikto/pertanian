import { describe, expect, it } from 'vitest';

import { amount, money, range, UNKNOWN_AMOUNT } from '@/features/money';

const NBSP = ' ';

describe('money formatting from strings (mirrors TR.format)', () => {
  it('groups digits the Indonesian way and drops trailing zero decimals', () => {
    expect(amount('20000.0000')).toBe('20.000');
    expect(amount('1234567.5000')).toBe('1.234.567,5');
    expect(amount('0.3000')).toBe('0,3');
    expect(amount('-1500')).toBe('-1.500');
    expect(amount('99999999999999999.1234')).toBe('99.999.999.999.999.999,1234');
  });

  it('says unknown instead of zero', () => {
    expect(money('USD', null)).toBe(UNKNOWN_AMOUNT);
    expect(range('USD', null, null)).toBe('Belum ditentukan');
    expect(money('IDR', '0.0000')).toBe(`IDR${NBSP}0`);
  });

  it('formats ranges, open ends and equal ends', () => {
    expect(range('USD', '20000.0000', '30000.0000')).toBe(`USD${NBSP}20.000–30.000`);
    expect(range('USD', null, '30000')).toBe(`Hingga USD${NBSP}30.000`);
    expect(range('USD', '50000', null)).toBe(`Mulai USD${NBSP}50.000`);
    expect(range('USD', '500000.0000', '500000.0000')).toBe(`USD${NBSP}500.000`);
  });
});
