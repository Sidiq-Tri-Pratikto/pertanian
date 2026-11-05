// TemuRiset Design System — token validation and generated outputs.
// Authorities: project/tokens.json (values) and tools/catalog.mjs (component contracts and demos).
// Usage: node tools/build.mjs   (exit code 1 on any integrity failure)
import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { components, pages } from './catalog.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const P = (...p) => join(ROOT, ...p);
const SYSTEM = 'TemuRiset Design System';
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
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const lum = (hex) => { const [r, g, b] = rgb(hex).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const sys = (n) => `tr-sys-color-${n}`;
const GROUNDS = ['canvas', 'surface', 'surface-subtle', 'selected-surface'].map(sys);
const STATUS = ['danger', 'success', 'warning'];
const PAIRS = [
  ...GROUNDS.flatMap((g) => [[sys('text-primary'), g, 4.5, 'Main text'], [sys('text-secondary'), g, 4.5, 'Supporting text'], [sys('link'), g, 4.5, 'Link']]),
  ...STATUS.map((s) => [sys('text-primary'), sys(`${s}-surface`), 4.5, 'Main text on status surface']),
  ...STATUS.flatMap((s) => [sys('surface'), sys('canvas'), sys(`${s}-surface`)].map((g) => [sys(`${s}-text`), g, 4.5, `${s} text and icon`])),
  [sys('action-primary-foreground'), sys('action-primary-background'), 4.5, 'Primary label'],
  [sys('action-primary-foreground'), sys('action-primary-hover'), 4.5, 'Primary label, hover'],
  [sys('action-primary-foreground'), sys('action-primary-pressed'), 4.5, 'Primary label, pressed'],
  [sys('action-danger-foreground'), sys('action-danger-background'), 4.5, 'Destructive label'],
  [sys('action-danger-foreground'), sys('action-danger-hover'), 4.5, 'Destructive label, hover'],
  [sys('action-secondary-foreground'), sys('surface'), 4.5, 'Secondary label'],
  [sys('action-secondary-foreground'), sys('action-secondary-hover'), 4.5, 'Secondary label, hover'],
  [sys('selected-foreground'), sys('selected-surface'), 4.5, 'Selected text'],
  [sys('disabled-foreground'), sys('disabled-surface'), 4.5, 'Disabled label stays readable'],
  ...[...GROUNDS, ...STATUS.map((s) => sys(`${s}-surface`))].map((g) => [sys('focus'), g, 3, 'Focus ring']),
  [sys('focus'), sys('focus-gap'), 3, 'Focus ring against its gap'],
  [sys('action-primary-background'), sys('focus-gap'), 3, 'Primary fill against focus gap'],
  ...[sys('surface'), sys('canvas'), sys('surface-subtle')].map((g) => [sys('border-control'), g, 3, 'Control boundary']),
  [sys('selected-border'), sys('selected-surface'), 3, 'Selected boundary'],
  ['tr-comp-field-borderError', sys('surface'), 3, 'Invalid field boundary'],
  [sys('border-decorative'), sys('surface'), 3, 'Decorative border (expected to fail: decorative only)', true],
];
const contrast = PAIRS.map(([fg, bg, min, role, expectFail]) => {
  const r = ratio(resolved.get(fg), resolved.get(bg));
  const pass = r >= min;
  if (!pass && !expectFail) fail(`contrast ${fg} on ${bg} = ${r.toFixed(2)} < ${min}`);
  return { fg, bg, fgValue: resolved.get(fg), bgValue: resolved.get(bg), ratio: Math.round(r * 10000) / 10000, minimum: min, role, result: pass ? 'pass' : expectFail ? 'fail (restricted to decorative use)' : 'FAIL' };
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

// ---- component READMEs and previews, from one record each
const previewHtml = (e) => `<!-- @dsCard group="${e.group}" height=${e.height}${e.width ? ` width=${e.width}` : ''}${e.page ? ' page' : ''} -->
<!doctype html>
<html lang="id">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${e.name} — preview</title></head>
<body>
<div id="root"${e.root === '' ? '' : ' class="tr-root tr-pad tr-stack"'}></div>
<script>
var TR = window.TR, h = React.createElement, F = TR.format, X = TR.demo.fixtures, useState = React.useState;
function S(label, child) { return h('div', { className: 'tr-stack' }, h('p', { className: 'tr-sys-type-support tr-muted' }, label), child); }
function Demo() {${e.demo}
}
ReactDOM.createRoot(document.getElementById('root')).render(h(Demo));
</script>
</body>
</html>
`;
const readme = (c) => `# ${c.name}

${c.summary}

**Anatomy.** ${c.anatomy}

**Consumer provides.** ${c.provides}

**States.** ${c.states}

**Keyboard and screen reader.** ${c.a11y}

**Tokens.** ${c.tokens}

**Responsive.** ${c.responsive}

**Do.** ${c.do}

**Don't.** ${c.dont}
`;
for (const c of [...components, ...pages.map((x) => ({ ...x, page: true }))]) {
  mkdirSync(P('project/components', c.name), { recursive: true });
  writeFileSync(P('project/components', c.name, 'preview.html'), previewHtml(c));
  if (!c.page) writeFileSync(P('project/components', c.name, 'README.md'), readme(c));
}

// ---- every var(--x) in the stylesheet and bundle must exist; no raw colours in components
const known = new Set([...all.keys(), ...Object.keys(tokens.type.families).map((k) => `font-${k}`)]);
const styleNames = new Set(tokens.type.groups.flatMap((g) => g.styles.map((s) => s.name)));
const usage = new Set();
for (const f of ['components/bundle.css', 'components/bundle.js']) {
  const src = readFileSync(P('project', f), 'utf8');
  for (const m of src.matchAll(/var\(--([A-Za-z0-9_.-]+)\)/g)) {
    usage.add(m[1]);
    if (!known.has(m[1]) && !['tr-ring', 'tr-section-gap', 'tr-gutter'].includes(m[1])) fail(`${f} uses undefined --${m[1]}`);
  }
  for (const m of src.matchAll(/\b(tr-sys-type-[a-z-]+)\b/g)) if (!styleNames.has(m[1])) fail(`${f} uses unknown type class ${m[1]}`);
  const raw = src.replace(/\/\*[\s\S]*?\*\//g, '').match(/#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(/g);
  if (raw) fail(`${f} contains raw colour values: ${[...new Set(raw)].join(', ')}`);
}
const header = JSON.parse(/@ds-bundle: (\{.*\}) \*\//.exec(readFileSync(P('project/components/bundle.js'), 'utf8'))[1]);
const headerNames = header.components.map((c) => c.name).sort().join();
if (headerNames !== components.map((c) => c.name).sort().join()) fail('bundle header and catalog list different components');
const unusedSemantic = [...all.keys()].filter((n) => /^tr-(sys|comp)-/.test(n) && !usage.has(n));

// ---- export, with a reversible id mapping: dotted TR path <-> css name
const idOf = (n) => n.replace(/^tr-/, 'TR.').replace(/-/g, '.');
const layerOf = (n) => (n.startsWith('tr-ref-') ? 'primitive' : n.startsWith('tr-comp-') ? 'component' : 'semantic');
const typeOf = { color: 'color', spacing: 'dimension', radius: 'dimension', size: 'dimension', fontWeight: 'fontWeight', duration: 'duration', easing: 'cubicBezier', shadow: 'shadow' };
const unitOf = (v) => (/^-?[\d.]+(px|rem|ms|ch|%)$/.exec(String(v)) || [])[1] || null;
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
  value: { fontFamily: `{TR.font.${s.family || g.family}}`, fontSize: s.fontSize, lineHeight: s.lineHeight, fontWeight: s.fontWeight },
  alias: null, resolved: { fontFamily: tokens.type.families[s.family || g.family], fontSize: s.fontSize, lineHeight: s.lineHeight, fontWeight: s.fontWeight },
  unit: 'rem (1rem = 16 CSS px at default text size)', usage: s.usage,
});
for (const [k, v] of Object.entries(tokens.type.families)) exportTokens.push({ id: `TR.font.${k}`, cssVar: `--font-${k}`, layer: 'primitive', type: 'fontFamily', value: v, alias: null, resolved: v, unit: null, usage: 'System sans-serif stack; no font files are fetched.' });

const sha = (f) => createHash('sha256').update(readFileSync(P('project', f))).digest('hex');
const componentIds = header.components.map((x) => `TR.${x.name}`);
const ADDITIONS = ['NextStep', 'Steps', 'SummaryList', 'Screen', 'Icon'];

const tokenExport = JSON.stringify({
  $schema: 'temuriset-tokens/1 (custom; not a W3C DTCG file; documented in guide/01-token-registry.md)',
  system: SYSTEM, version: VERSION, authority: 'project/tokens.json', authoritySha256: sha('tokens.json'),
  themes: tokens.color.themes,
  idRule: 'id = "TR." + css name without its "tr-" prefix, with "-" replaced by "."; cssVar = "--" + css name. Segments never contain "-", so the mapping is reversible.',
  dtcgConversion: 'Not claimed. To produce DTCG 2025.10: nest id segments as groups, use $root where an id is also a group (TR.sys.color.surface), and convert colour and dimension values to their object forms.',
  tokens: exportTokens,
}, null, 2) + '\n';

const manifest = JSON.stringify({
  system: SYSTEM, version: VERSION, reviewStatus: 'draft — not owner-approved; validation recorded in guide/05-validation-report.md',
  productContract: 'TemuRiset PRD generic v1.1', handoff: '04_Claude_Design_System_TemuRiset_EN.md v1.0',
  runtime: 'Claude Design System artifact type (contract 0.2.47), private artifact; React 18.3.1 previews; local workbench served over http from the same files',
  supply: { kind: 'portable local reference, mirrored to a private artifact made from the Design System type', artifact: 'https://claude.ai/artifact/KU4iHKHaVL7QgL8bhSgfWV', registeredInClaudePicker: 'not verified', published: false, organizationDefault: false },
  sourceFormat: { tokens: 'tokens.json (Design System type list grammar)', export: 'exports/temuriset-design-system.tokens.json (temuriset-tokens/1, custom)', components: 'components/bundle.js — one classic script assigning window.TR, hand-written ES2017 using React.createElement; no build step', styles: 'components/bundle.css', types: 'components/index.d.ts (documentation)', contracts: 'tools/catalog.mjs generates each README and preview' },
  namespace: 'TR', components: componentIds, intentionalAdditions: ADDITIONS.map((n) => `TR.${n}`), themes: tokens.color.themes.map((t) => t.id),
  patterns: pages.filter((x) => x.group === 'Patterns').map((x) => x.name),
  fingerprints: Object.fromEntries(['tokens.json', 'components/bundle.js', 'components/bundle.css', 'components/index.d.ts'].map((f) => [f, `sha256:${sha(f)}`])),
  limitations: ['Light theme only.', 'React web only; no server, database, file scanning, booking or authorization exists here.', 'No participant study; comprehension is unverified.', 'No screen-reader run.', 'Previews use fictional fixtures (Demo · Data fiktif).'],
  secrets: 'none',
}, null, 2) + '\n';
for (const dir of ['project/exports', 'exports']) {
  writeFileSync(P(dir, 'temuriset-design-system.tokens.json'), tokenExport);
  writeFileSync(P(dir, 'temuriset-design-system.manifest.json'), manifest);
}

// ---- generated token registry section
const groups = { primitive: [], semantic: [], component: [] };
for (const t of exportTokens) groups[t.layer].push(t);
const fmtVal = (t) => (typeof t.value === 'object' ? `${t.value.fontSize} / ${t.value.lineHeight} · ${t.value.fontWeight}` : String(t.value));
const row = (t) => `| \`${t.id}\` | \`${t.cssVar || t.cssClass}\` | ${t.type} | \`${fmtVal(t)}\` | ${typeof t.resolved === 'object' ? '' : `\`${t.resolved}\``} | ${t.usage.replace(/\|/g, '\\|')} |`;
let md = `# Token registry\n\nGenerated by \`tools/build.mjs\` from \`tokens.json\` (sha256 \`${sha('tokens.json').slice(0, 16)}…\`). Do not edit by hand: change \`tokens.json\`, then rebuild.\n\n`;
md += `**Rules.** Components read semantic or component aliases, never primitives. Logical id \`TR.sys.color.action.primary.background\` is CSS \`--tr-sys-color-action-primary-background\`; camelCase segments are kept, so the mapping reverses. Colour aliases are live (\`{tr-ref-color-teal-700}\`); spacing and radius aliases are recorded as \`Alias: <token>.\` in the usage note and checked for equality on every build. Type styles are classes sized in rem.\n\n`;
md += `**Export format.** \`exports/temuriset-design-system.tokens.json\` is custom JSON, \`temuriset-tokens/1\`. It is not a DTCG file and no DTCG 2025.10 compatibility is claimed; its \`dtcgConversion\` field states the conversion.\n\n`;
md += `Build result: ${errors.length ? `**${errors.length} integrity errors**` : `**0 integrity errors** — ${exportTokens.length} tokens, every alias resolves, no cycles, no duplicate names, no raw colours in bundle.css/bundle.js, every \`var(--…)\` used exists`}.\n\n`;
for (const layer of ['semantic', 'component', 'primitive']) {
  md += `## ${layer[0].toUpperCase() + layer.slice(1)} tokens\n\n| ID | CSS | Type | Value | Resolved | Usage |\n|---|---|---|---|---|---|\n${groups[layer].map(row).join('\n')}\n\n`;
}
md += `## Computed contrast of resolved pairs\n\nWCAG 2 relative-luminance ratios of opaque resolved token values, rounded for display. These are token calculations; rendered checks are in the validation report.\n\n| Foreground | Background | Ratio | Min | Role | Result |\n|---|---|---:|---:|---|---|\n`;
md += contrast.map((x) => `| \`${idOf(x.fg)}\` ${x.fgValue} | \`${idOf(x.bg)}\` ${x.bgValue} | ${x.ratio.toFixed(4)}:1 | ${x.minimum}:1 | ${x.role} | ${x.result} |`).join('\n') + '\n';
if (unusedSemantic.length) md += `\nSemantic tokens not referenced by bundle.css/bundle.js (kept as declared roles): ${unusedSemantic.map((n) => `\`${idOf(n)}\``).join(', ')}.\n`;
writeFileSync(P('project/guide/01-token-registry.md'), md);

// ---- the single-file system guide
const guideFiles = ['README.md', ...readdirSync(P('project/guide')).filter((f) => f.endsWith('.md')).sort().map((f) => `guide/${f}`)].filter((f) => existsSync(P('project', f)));
const guide = [`# ${SYSTEM} ${VERSION}\n\nSingle-file guide concatenated from the system's README, guide sections and component READMEs. Authority remains project/tokens.json and the component files.\n`,
  ...guideFiles.map((f) => readFileSync(P('project', f), 'utf8').replace(/^# /gm, '## ').replace(/^(#{3,}) /gm, '#$1 ')),
  '## Component contracts\n', ...components.map((c) => readFileSync(P('project/components', c.name, 'README.md'), 'utf8').replace(/^# (.*)$/m, '### TR.$1'))].join('\n\n');
writeFileSync(P('exports/temuriset-design-system.md'), guide);

// ---- workbench preview list
writeFileSync(P('workbench/previews.json'), JSON.stringify([...pages.map((x) => ({ name: x.name, group: x.group, page: true })), ...components.map((c) => ({ name: c.name, group: c.group, page: false }))], null, 2) + '\n');

console.log(`${exportTokens.length} tokens · ${componentIds.length} components (${ADDITIONS.length} additions) · ${pages.length} pages · ${contrast.filter((x) => x.result === 'pass').length}/${contrast.length} contrast pairs pass`);
if (unusedSemantic.length) console.log('unreferenced semantic:', unusedSemantic.join(', '));
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
