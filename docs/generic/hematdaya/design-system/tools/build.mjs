// HematDaya Design System — token validation and generated outputs.
// Authority: project/tokens.json. Everything this script writes is derived from it.
// Usage: node tools/build.mjs   (exit code 1 on any integrity failure)
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const P = (...p) => join(ROOT, ...p);
const SYSTEM = 'HematDaya Design System';
const VERSION = '1.0.0-draft';
const errors = [];
const fail = (m) => errors.push(m);

const tokens = JSON.parse(readFileSync(P('project/tokens.json'), 'utf8'));
const NAME = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/;
const FAMILIES = Object.keys(tokens).filter((k) => tokens[k] && Array.isArray(tokens[k].tokens));

// ---- names: valid and unique across every family but type
const all = new Map();
for (const fam of FAMILIES) for (const t of tokens[fam].tokens) {
  if (!NAME.test(t.name)) fail(`invalid name ${t.name}`);
  if (all.has(t.name)) fail(`duplicate name ${t.name}`);
  if (!t.usage) fail(`missing usage ${t.name}`);
  all.set(t.name, { ...t, family: fam });
}

// ---- colour aliases: exist, no cycles, depth <= 16
const colors = new Map(tokens.color.tokens.map((t) => [t.name, t]));
const ALIAS = /^\{([^}]+)\}$/;
const HEX = /^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
const RGBA = /^rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\s*\)$/;
function resolveColor(name, seen = []) {
  const t = colors.get(name);
  if (!t) { fail(`alias to missing colour ${name} via ${seen.join(' > ')}`); return null; }
  if (seen.includes(name)) { fail(`alias cycle ${[...seen, name].join(' > ')}`); return null; }
  if (seen.length > 16) { fail(`alias chain too deep at ${name}`); return null; }
  const m = ALIAS.exec(t.value);
  if (m) return resolveColor(m[1], [...seen, name]);
  if (!HEX.test(t.value) && !RGBA.test(t.value)) fail(`unsupported colour value ${name}: ${t.value}`);
  return t.value;
}
const resolved = new Map([...colors.keys()].map((n) => [n, resolveColor(n)]));

// ---- non-colour aliases are recorded as "Alias: <token>." and must equal the target
const aliasOf = (t) => (/^Alias: ([A-Za-z0-9_.-]+)\./.exec(t.usage) || [])[1] || null;
for (const fam of FAMILIES.filter((f) => f !== 'color')) for (const t of tokens[fam].tokens) {
  const a = aliasOf(t);
  if (!a) continue;
  const target = all.get(a);
  if (!target) fail(`${t.name} aliases missing ${a}`);
  else if (String(target.value) !== String(t.value)) fail(`${t.name}=${t.value} differs from its alias ${a}=${target.value}`);
}

// ---- contrast (WCAG 2 relative luminance) on opaque resolved values
const rgb = (hex) => { let h = hex.slice(1); if (h.length === 3) h = [...h].map((c) => c + c).join(''); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255); };
const lin = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const lum = (hex) => { const [r, g, b] = rgb(hex).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const c = (n) => resolved.get(n);
// [foreground, background, minimum, role]
const PAIRS = [
  ['color-text-primary', 'color-background-canvas', 4.5, 'Body text on canvas'],
  ['color-text-primary', 'color-background-surface', 4.5, 'Body text on surface'],
  ['color-text-primary', 'color-background-subtle', 4.5, 'Body text on subtle / neutral notice'],
  ['color-text-primary', 'color-status-info-background', 4.5, 'Notice body on info'],
  ['color-text-primary', 'color-status-attention-background', 4.5, 'Notice body on attention'],
  ['color-text-primary', 'color-status-error-background', 4.5, 'Notice body on error'],
  ['color-text-primary', 'color-status-success-background', 4.5, 'Notice body on success'],
  ['color-text-secondary', 'color-background-surface', 4.5, 'Labels/help on surface'],
  ['color-text-secondary', 'color-background-canvas', 4.5, 'Labels/help on canvas'],
  ['color-text-secondary', 'color-background-subtle', 4.5, 'Disabled reason / metadata on subtle'],
  ['color-text-link', 'color-background-surface', 4.5, 'Link on surface'],
  ['color-text-link', 'color-background-canvas', 4.5, 'Link on canvas'],
  ['color-action-primary-foreground', 'color-action-primary-background', 4.5, 'Primary label'],
  ['color-action-primary-foreground', 'color-action-primary-hover', 4.5, 'Primary label, hover'],
  ['color-action-primary-foreground', 'color-action-primary-pressed', 4.5, 'Primary label, pressed'],
  ['color-action-secondary-foreground', 'color-action-secondary-background', 4.5, 'Secondary label'],
  ['color-action-secondary-foreground', 'color-action-secondary-hover', 4.5, 'Secondary label, hover'],
  ['color-action-secondary-foreground', 'color-background-canvas', 4.5, 'Text button on canvas'],
  ['color-action-destructive-foreground', 'color-action-destructive-background', 4.5, 'Destructive label'],
  ['color-action-destructive-foreground', 'color-action-destructive-hover', 4.5, 'Destructive label, hover'],
  ['color-selection-foreground', 'color-selection-background', 4.5, 'Selected tab/option text'],
  ['color-disabled-foreground', 'color-disabled-background', 4.5, 'Disabled label (kept readable)'],
  ['color-status-info-foreground', 'color-status-info-background', 4.5, 'Info label'],
  ['color-status-info-foreground', 'color-background-surface', 4.5, 'Info label on surface'],
  ['color-status-attention-foreground', 'color-status-attention-background', 4.5, 'Attention label'],
  ['color-status-attention-foreground', 'color-background-surface', 4.5, 'Attention qualifier on surface'],
  ['color-status-attention-foreground', 'color-background-canvas', 4.5, 'Attention qualifier on canvas'],
  ['color-status-error-foreground', 'color-status-error-background', 4.5, 'Error label'],
  ['color-status-error-foreground', 'color-background-surface', 4.5, 'Inline field error on surface'],
  ['color-status-error-foreground', 'color-background-canvas', 4.5, 'Inline field error on canvas'],
  ['color-status-success-foreground', 'color-status-success-background', 4.5, 'Confirmed save label'],
  ['color-border-control', 'color-background-surface', 3, 'Control boundary on surface'],
  ['color-border-control', 'color-background-canvas', 3, 'Control boundary on canvas'],
  ['color-border-control', 'color-background-subtle', 3, 'Disabled control boundary on subtle'],
  ['field-border-error', 'color-background-surface', 3, 'Error field boundary'],
  ['color-focus-ring', 'color-focus-gap', 3, 'Focus ring against its gap'],
  ['color-focus-ring', 'color-background-canvas', 3, 'Focus ring on canvas'],
  ['color-focus-ring', 'color-background-surface', 3, 'Focus ring on surface'],
  ['color-focus-ring', 'color-background-subtle', 3, 'Focus ring on subtle'],
  ['color-focus-ring', 'color-selection-background', 3, 'Focus ring on selected row'],
  ['color-focus-ring', 'color-status-info-background', 3, 'Focus ring inside info notice'],
  ['color-focus-ring', 'color-status-attention-background', 3, 'Focus ring inside attention notice'],
  ['color-focus-ring', 'color-status-error-background', 3, 'Focus ring inside error notice'],
  ['color-action-primary-background', 'color-focus-gap', 3, 'Primary fill edge against focus gap'],
  ['color-selection-indicator', 'color-background-surface', 3, 'Selected indicator bar'],
  ['color-chart-current', 'color-background-surface', 3, 'Current series bar'],
  ['color-chart-reference', 'color-background-surface', 3, 'Reference series outline'],
  ['color-chart-reference', 'color-chart-referenceFill', 3, 'Reference outline on its fill'],
  ['color-chart-missingMarker', 'color-background-surface', 3, 'Missing-data hatch'],
  ['color-chart-baseline', 'color-background-surface', 3, 'Zero baseline / measured-zero tick'],
  ['color-status-attention-foreground', 'color-status-attention-background', 3, 'Attention icon'],
  ['color-border-decorative', 'color-background-surface', 3, 'Decorative border (expected to fail: decorative only)', true],
];
const contrast = PAIRS.map(([fg, bg, min, role, expectFail]) => {
  const r = ratio(c(fg), c(bg));
  const pass = r >= min;
  if (!pass && !expectFail) fail(`contrast ${fg} on ${bg} = ${r.toFixed(2)} < ${min}`);
  return { fg, bg, fgValue: c(fg), bgValue: c(bg), ratio: Math.round(r * 100) / 100, minimum: min, role, result: pass ? 'pass' : expectFail ? 'fail (restricted to decorative use)' : 'FAIL' };
});

// ---- tokens.css, laid out as the page compiles it (local workbench and consuming sample only)
const theme = tokens.color.themes[0].id;
const cssVal = (v) => (ALIAS.test(v) ? `var(--${ALIAS.exec(v)[1]})` : v);
let css = `/* ${SYSTEM} — generated from tokens.json */\n:root, [data-theme="${theme}"] {\n`;
for (const t of tokens.color.tokens) css += `  --${t.name}: ${cssVal(t.value)};\n`;
for (const t of tokens.shadow.tokens) css += `  --${t.name}: ${t.value};\n`;
css += '}\n:root {\n';
for (const fam of FAMILIES.filter((f) => !['color', 'shadow'].includes(f))) for (const t of tokens[fam].tokens) css += `  --${t.name}: ${t.value};\n`;
for (const [k, v] of Object.entries(tokens.type.families)) css += `  --font-${k}: ${v};\n`;
css += '}\n';
for (const g of tokens.type.groups) for (const s of g.styles) {
  css += `.${s.name} { font-family: var(--font-${s.family || g.family}); font-size: ${s.fontSize}; line-height: ${s.lineHeight}; font-weight: ${s.fontWeight}; }\n`;
}
writeFileSync(P('workbench/tokens.css'), css);

// ---- every var(--x) in the stylesheet and bundle must exist; no raw colours in components
const known = new Set([...all.keys(), ...Object.keys(tokens.type.families).map((k) => `font-${k}`)]);
const styleNames = new Set(tokens.type.groups.flatMap((g) => g.styles.map((s) => s.name)));
const usage = { vars: new Set(), typeClasses: new Set() };
for (const f of ['components/bundle.css', 'components/bundle.js']) {
  const src = readFileSync(P('project', f), 'utf8');
  for (const m of src.matchAll(/var\(--([A-Za-z0-9_.-]+)\)/g)) { usage.vars.add(m[1]); if (!known.has(m[1]) && !m[1].startsWith('hd-')) fail(`${f} uses undefined --${m[1]}`); }
  for (const m of src.matchAll(/['" ](type-[a-z-]+)['" ]/g)) { if (styleNames.has(m[1])) usage.typeClasses.add(m[1]); }
  const raw = src.replace(/\/\*[\s\S]*?\*\//g, '').match(/#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(/g);
  if (raw) fail(`${f} contains raw colour values: ${[...new Set(raw)].join(', ')}`);
}
const unusedSemantic = [...all.keys()].filter((n) => !/^palette-|^space-\d|^radius-(\d|full)|^duration-\d/.test(n) && !usage.vars.has(n));

// ---- dotted IDs, layers, export
const idOf = (n) => n.replace(/-/g, '.');
const layerOf = (n) => (/^palette-/.test(n) || /^(space|radius|duration)-(\d+|full)$/.test(n) ? 'primitive' : /^(button|field|tab)-/.test(n) ? 'component' : 'semantic');
const typeOf = { color: 'color', spacing: 'dimension', radius: 'dimension', size: 'dimension', fontWeight: 'fontWeight', duration: 'duration', easing: 'cubicBezier', shadow: 'shadow' };
const unitOf = (v) => (/^-?[\d.]+(px|rem|ms|%)$/.exec(String(v)) || [])[1] || null;
const exportTokens = [];
for (const fam of FAMILIES) for (const t of tokens[fam].tokens) {
  const colourAlias = fam === 'color' && ALIAS.test(t.value) ? ALIAS.exec(t.value)[1] : null;
  const alias = colourAlias || aliasOf(t);
  exportTokens.push({
    id: idOf(t.name), cssVar: `--${t.name}`, layer: layerOf(t.name), type: typeOf[fam] || fam,
    value: fam === 'color' ? (colourAlias ? `{${idOf(colourAlias)}}` : t.value) : t.value,
    alias: alias ? idOf(alias) : null,
    resolved: fam === 'color' ? resolved.get(t.name) : t.value,
    unit: fam === 'color' ? null : fam === 'fontWeight' ? 'weight (CSS 1–1000)' : unitOf(t.value),
    usage: t.usage,
  });
}
for (const g of tokens.type.groups) for (const s of g.styles) exportTokens.push({
  id: idOf(s.name), cssVar: null, cssClass: `.${s.name}`, layer: 'semantic', type: 'typography',
  value: { fontFamily: `{font.${s.family || g.family}}`, fontSize: s.fontSize, lineHeight: s.lineHeight, fontWeight: s.fontWeight },
  alias: null, resolved: { fontFamily: tokens.type.families[s.family || g.family], fontSize: s.fontSize, lineHeight: s.lineHeight, fontWeight: s.fontWeight },
  unit: 'rem (1rem = 16 logical units at default text size)', usage: s.usage,
});
for (const [k, v] of Object.entries(tokens.type.families)) exportTokens.push({ id: `font.${k}`, cssVar: `--font-${k}`, layer: 'primitive', type: 'fontFamily', value: v, alias: null, resolved: v, unit: null, usage: 'System sans-serif stack; no font files are fetched.' });

const sha = (f) => createHash('sha256').update(readFileSync(P('project', f))).digest('hex');
const bundleSrc = readFileSync(P('project/components/bundle.js'), 'utf8');
const header = JSON.parse(/@ds-bundle: (\{.*\}) \*\//.exec(bundleSrc)[1]);
const componentIds = header.components.map((x) => `HD.${x.name}`);

writeFileSync(P('project/exports/hematdaya-design-system.tokens.json'), JSON.stringify({
  $schema: 'hematdaya-tokens/1 (custom; documented in guide/01-token-registry.md; not a W3C DTCG file)',
  system: SYSTEM, version: VERSION, authority: 'project/tokens.json', authoritySha256: sha('tokens.json'),
  themes: tokens.color.themes, idRule: 'id = CSS name with "-" replaced by "."; cssVar = "--" + CSS name. Segments never contain "-", so the mapping is reversible.',
  tokens: exportTokens,
}, null, 2) + '\n');

writeFileSync(P('project/exports/hematdaya-design-system.manifest.json'), JSON.stringify({
  system: SYSTEM, version: VERSION, reviewStatus: 'draft — not owner-approved; validation recorded in guide/05-validation-report.md',
  productContract: 'HematDaya PRD Generic 1.2', handoff: '04_Claude_Design_System_HematDaya_EN.md v1.0',
  runtime: 'Claude Design System artifact type (contract 0.2.47), private artifact; React 18.3.1 previews; local workbench served over http from the same files',
  supply: { kind: 'private Claude design-system artifact (created from the Design System type)', registeredInClaudeDesignPicker: 'not verified', published: false, organizationDefault: false },
  sourceFormat: { tokens: 'tokens.json (Design System type list grammar)', export: 'exports/hematdaya-design-system.tokens.json (hematdaya-tokens/1)', components: 'components/bundle.js — one classic script assigning window.HD, hand-written ES2017 using React.createElement; no build step', styles: 'components/bundle.css', types: 'components/index.d.ts (documentation)' },
  namespace: 'HD', components: componentIds, themes: tokens.color.themes.map((t) => t.id),
  capabilityScope: ['monitoring and advice only', 'three destinations: Beranda, Perangkat, Saran', 'optional tariff, schedule and output metric', 'household, business and industrial presets share one token authority'],
  fingerprints: Object.fromEntries(['tokens.json', 'components/bundle.js', 'components/bundle.css', 'components/index.d.ts'].map((f) => [f, `sha256:${sha(f)}`])),
  limitations: ['Light theme only; dark and client themes deferred.', 'No native (React Native/Expo, Android, iOS) source or build; native mappings are documentation.', 'No participant study; comprehension is unverified.', 'Previews use synthetic fixtures (Demo · Data simulasi).'],
  secrets: 'none',
}, null, 2) + '\n');

// ---- generated token registry section
const groups = { primitive: [], semantic: [], component: [] };
for (const t of exportTokens) groups[t.layer].push(t);
const fmtVal = (t) => (typeof t.value === 'object' ? `${t.value.fontSize} / ${t.value.lineHeight} · ${t.value.fontWeight}` : String(t.value));
const row = (t) => `| \`${t.id}\` | \`${t.cssVar || t.cssClass}\` | ${t.type} | \`${fmtVal(t)}\` | ${typeof t.resolved === 'object' ? '' : `\`${t.resolved}\``} | ${t.usage.replace(/\|/g, '\\|')} |`;
let md = `# Token registry\n\nGenerated by \`tools/build.mjs\` from \`tokens.json\` (sha256 \`${sha('tokens.json').slice(0, 16)}…\`). Do not edit by hand: change \`tokens.json\`, then rebuild.\n\n`;
md += `**Rules.** Components read semantic or component aliases, never primitives. ID \`color.action.primary.background\` is CSS \`--color-action-primary-background\` (dots become hyphens; camelCase segments are kept). Colour aliases are live (\`{palette-forest-700}\`); spacing, radius and duration aliases are recorded as \`Alias: <token>.\` in the usage note and checked for equality on every build. Type styles are classes (\`.type-body\`) sized in rem so the user's text-size setting scales them.\n\n`;
md += `Build result: ${errors.length ? `**${errors.length} integrity errors**` : `**0 integrity errors** — ${exportTokens.length} tokens, every alias resolves, no cycles, no duplicate names, no raw colours in bundle.css/bundle.js, every \`var(--…)\` used exists`}.\n\n`;
for (const layer of ['semantic', 'component', 'primitive']) {
  md += `## ${layer[0].toUpperCase() + layer.slice(1)} tokens\n\n| ID | CSS | Type | Value | Resolved | Usage |\n|---|---|---|---|---|---|\n${groups[layer].map(row).join('\n')}\n\n`;
}
md += `## Computed contrast of resolved pairs\n\nWCAG 2 relative-luminance ratios of the opaque resolved token values. These are token-level calculations: rendered checks (actual elements, states, focus geometry) are in the validation report.\n\n| Foreground | Background | Ratio | Min | Role | Result |\n|---|---|---:|---:|---|---|\n`;
md += contrast.map((x) => `| \`${idOf(x.fg)}\` ${x.fgValue} | \`${idOf(x.bg)}\` ${x.bgValue} | ${x.ratio.toFixed(2)}:1 | ${x.minimum}:1 | ${x.role} | ${x.result} |`).join('\n') + '\n';
if (unusedSemantic.length) md += `\nSemantic tokens not referenced by bundle.css/bundle.js (kept for consumers): ${unusedSemantic.map((n) => `\`${idOf(n)}\``).join(', ')}.\n`;
writeFileSync(P('project/guide/01-token-registry.md'), md);

// ---- the single-file system guide (local export; inside project/ these files are the brand book sections)
const guideFiles = ['README.md', ...readdirSync(P('project/guide')).filter((f) => f.endsWith('.md')).sort().map((f) => `guide/${f}`)];
const compDir = P('project/components');
const compReadmes = header.components.map((x) => `components/${x.name}/README.md`).filter((f) => existsSync(P('project', f)));
const guide = [`# ${SYSTEM} ${VERSION}\n\nSingle-file guide concatenated from the system's README, guide sections and component READMEs. Authority remains project/tokens.json and the component files.\n`,
  ...guideFiles.map((f) => readFileSync(P('project', f), 'utf8').replace(/^# /gm, '## ').replace(/^(#{3,}) /gm, '#$1 ')),
  '## Component contracts\n', ...compReadmes.map((f) => readFileSync(P('project', f), 'utf8').replace(/^# (.*)$/m, '### HD.$1').replace(/^## /gm, '#### '))].join('\n\n');
writeFileSync(P('exports/hematdaya-design-system.md'), guide);
writeFileSync(P('exports/hematdaya-design-system.tokens.json'), readFileSync(P('project/exports/hematdaya-design-system.tokens.json')));
writeFileSync(P('exports/hematdaya-design-system.manifest.json'), readFileSync(P('project/exports/hematdaya-design-system.manifest.json')));

// ---- workbench preview list
const previews = readdirSync(compDir, { withFileTypes: true }).filter((d) => d.isDirectory() && existsSync(join(compDir, d.name, 'preview.html')))
  .map((d) => { const first = readFileSync(join(compDir, d.name, 'preview.html'), 'utf8').split('\n')[0]; return { name: d.name, group: (/group="([^"]+)"/.exec(first) || [])[1] || '', page: /\bpage\b/.test(first) }; });
writeFileSync(P('workbench/previews.json'), JSON.stringify(previews, null, 2) + '\n');

console.log(`${exportTokens.length} tokens · ${componentIds.length} components · ${previews.length} previews · ${contrast.filter((x) => x.result === 'pass').length}/${contrast.length} contrast pairs pass`);
for (const x of contrast) console.log(`${x.ratio.toFixed(2).padStart(6)}  ${x.result.padEnd(5)}  ${x.fg} on ${x.bg}`);
if (unusedSemantic.length) console.log('unreferenced semantic:', unusedSemantic.join(', '));
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
