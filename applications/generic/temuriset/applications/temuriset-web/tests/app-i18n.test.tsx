import fs from 'node:fs';
import path from 'node:path';

import { render, screen } from '@testing-library/react';
import ts from 'typescript';

import { Screen } from '@/components/tr/Screen';

import { APP_EN } from '@/features/i18n/app-en';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { setAppLocale, t } from '@/features/i18n/t';

const SRC = path.join(__dirname, '..', 'src');

function files(dir: string): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return files(full);
    return /\.tsx?$/.test(entry.name) && !entry.name.endsWith('.generated.ts') ? [full] : [];
  });
}

/** Every `t(...)` call in the app, with its literal key and whether it runs only inside a function. */
function calls(): { file: string; line: number; key: string | null; inFunction: boolean }[] {
  return files(SRC).flatMap((file) => {
    const source = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
    const found: { file: string; line: number; key: string | null; inFunction: boolean }[] = [];
    function visit(node: ts.Node, inFunction: boolean) {
      const inside = inFunction || ts.isFunctionLike(node);
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && (node.expression.text === 't' || node.expression.text === 'tx')) {
        const first = node.arguments[0];
        found.push({
          file: path.relative(SRC, file),
          line: source.getLineAndCharacterOfPosition(node.getStart()).line + 1,
          key: node.expression.text === 't' && first && ts.isStringLiteralLike(first) ? first.text : null,
          inFunction: inside,
        });
      }
      ts.forEachChild(node, (child) => visit(child, inside));
    }
    visit(source, false);
    return found;
  });
}

describe('English for the signed-in app (revamp R7)', () => {
  it('has an English entry for every literal t() key', () => {
    const missing = calls().filter((call) => call.key !== null && !(call.key in APP_EN));
    expect(missing.map((call) => `${call.file}:${call.line} ${call.key}`)).toEqual([]);
  });

  it('never translates while a module loads, which would freeze one language for every visitor', () => {
    const early = calls().filter((call) => !call.inFunction);
    expect(early.map((call) => `${call.file}:${call.line}`)).toEqual([]);
  });

  it('keeps placeholders identical in both languages', () => {
    const names = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
    const broken = Object.entries(APP_EN).filter(([id, en]) => names(id).join() !== names(en).join());
    expect(broken).toEqual([]);
  });

  it('returns the Indonesian source by default and English when the page is English, filling placeholders', () => {
    expect(t('Versi {n}', { n: 2 })).toBe('Versi 2');
    setAppLocale('en');
    expect(t('Versi {n}', { n: 2 })).toBe('Version 2');
    expect(t('Teks tanpa terjemahan')).toBe('Teks tanpa terjemahan');
  });
});

describe('the signed-in shell in English', () => {
  it('shows English navigation, title and the switch back to Indonesian', () => {
    render(
      <LocaleProvider locale="en">
        <Screen persona="inovator" current="beranda" title="Beranda" />
      </LocaleProvider>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Home' })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'My inventions' }).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /View this page in Indonesian/ })).toBeInTheDocument();
  });
});
