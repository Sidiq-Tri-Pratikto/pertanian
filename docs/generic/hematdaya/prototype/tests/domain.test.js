// Fixture and boundary oracles for the HematDaya prototype domain (PRD Generic 1.2 §19, handoff §8-9).
// Run: node docs/generic/hematdaya/prototype/tests/domain.test.js
'use strict';
const assert = require('assert');
const D = require('../project/app/hematdaya-domain.js');
D.DELAY.value = 0;

const results = [];
async function t(id, name, fn) {
  try { await fn(); results.push({ id, name, status: 'pass' }); }
  catch (e) { results.push({ id, name, status: 'fail', error: e.message }); }
}
const TZ = 'Asia/Jakarta';
const P = (ws, s, e, ids) => { const b = D.periodBounds({ start: s, end: e || s }, ws.site.tz); return D.summarize(ws, { startMs: b.start, endMs: b.end, assetIds: ids }); };
const Q = (ws, s, e) => { const b = D.periodBounds({ start: s, end: e || s }, ws.site.tz); return { startMs: b.start, endMs: b.end }; };
const kwh = (m) => D.fmtKwh(m);
const rp = (s) => D.fmtRp(s.cost.nano);

(async () => {
  await t('FX-01', 'Both fixtures have 2,688 simulated hourly rows, four disjoint assets', () => {
    for (const id of ['h-base', 'i-base']) {
      const ws = D.buildScenario(id);
      assert.strictEqual(ws.readings.length, 2688);
      assert.strictEqual(ws.assets.length, 4);
      assert.ok(ws.sources.every((s) => s.origin === 'simulated'));
      assert.strictEqual(D.scopeIssues(ws, ws.selection).length, 0);
      assert.ok(ws.readings.every((r) => r.t1 - r.t0 === D.HOUR && Number.isInteger(r.mWh)));
    }
  });
  await t('AT-05', 'Household H daily/week/four-week energy and cost', () => {
    const ws = D.buildScenario('h-base');
    const d = P(ws, '2026-10-19'); assert.strictEqual(kwh(d.totalMWh), '2,100 kWh'); assert.strictEqual(rp(d), 'Rp3.150');
    const w = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(kwh(w.totalMWh), '14,700 kWh'); assert.strictEqual(rp(w), 'Rp22.050');
    const f = P(ws, '2026-09-28', '2026-10-25'); assert.strictEqual(kwh(f.totalMWh), '58,800 kWh'); assert.strictEqual(rp(f), 'Rp88.200');
    const r = D.ranking(w); assert.deepStrictEqual(r.map((x) => [x.name, kwh(x.mWh)]), [['Kulkas', '8,400 kWh'], ['TV', '2,520 kWh'], ['Pompa Air', '2,100 kWh'], ['Router', '1,680 kWh']]);
    assert.strictEqual(D.fmtPct(r[0].mWh, w.totalMWh), '57,14%');
    assert.strictEqual(w.coverageMin, 1);
  });
  await t('AT-05b', 'Household base: no change alert, continuous assets give no outside-use finding, no schedule/output prerequisite', () => {
    const ws = D.buildScenario('h-base');
    const ins = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25'));
    assert.strictEqual(ins.observations.length, 0);
    assert.strictEqual(ins.perAsset['asset-kulkas'].outside.state, 'unavailable');
    assert.match(ins.perAsset['asset-kulkas'].outside.reason, /terus menyala/);
    assert.match(ins.perAsset['asset-tv'].outside.reason, /Tidak ada jadwal/);
    assert.strictEqual(ins.perAsset['asset-tv'].energy.state, 'noChange');
    assert.strictEqual(ws.metric, null); assert.strictEqual(ws.schedules.length, 0);
  });
  await t('AT-17', 'Household change: TV +1,400 kWh (55,56%) qualifies under shared rule; site 16,100 kWh/Rp24.150', () => {
    const ws = D.buildScenario('h-change');
    const w = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(kwh(w.totalMWh), '16,100 kWh'); assert.strictEqual(rp(w), 'Rp24.150');
    const ins = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25'));
    assert.strictEqual(ins.observations.length, 1);
    const ev = ins.observations[0].evidence;
    assert.strictEqual(ev.assetName, 'TV'); assert.strictEqual(kwh(ev.currentMaskMWh), '3,920 kWh'); assert.strictEqual(kwh(ev.baselineMWh), '2,520 kWh');
    assert.strictEqual(D.fmtSignedKwh(ev.deltaMWh), '+1,400 kWh'); assert.strictEqual(ev.pct, '+55,56%');
    assert.strictEqual(ev.resolutionMWh, 168000); assert.strictEqual(ev.thresholdMWh, 840000);
    assert.strictEqual(ins.perAsset['asset-tv'].outside.state, 'unavailable');
    assert.match(ins.observations[0].copy.unknown, /Penyebab perubahan belum diketahui/);
  });
  await t('AT-06', 'Industry I daily/week/four-week, Oven 50%, Sunday measured zero', () => {
    const ws = D.buildScenario('i-base');
    const d = P(ws, '2026-10-19'); assert.strictEqual(kwh(d.totalMWh), '24,000 kWh'); assert.strictEqual(rp(d), 'Rp36.000');
    const w = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(kwh(w.totalMWh), '144,000 kWh'); assert.strictEqual(rp(w), 'Rp216.000');
    const f = P(ws, '2026-09-28', '2026-10-25'); assert.strictEqual(kwh(f.totalMWh), '576,000 kWh'); assert.strictEqual(rp(f), 'Rp864.000');
    const r = D.ranking(w); assert.deepStrictEqual(r.map((x) => kwh(x.mWh)), ['72,000 kWh', '36,000 kWh', '24,000 kWh', '12,000 kWh']);
    assert.strictEqual(r[0].name, 'Oven'); assert.strictEqual(D.fmtPct(r[0].mWh, w.totalMWh), '50,00%');
    const sun = P(ws, '2026-10-25'); assert.strictEqual(sun.totalMWh, 0); assert.strictEqual(sun.coverageMin, 1);
    assert.strictEqual(D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25')).observations.length, 0);
  });
  await t('AT-22', 'Industry optional: schedule outside energy exactly zero; actual output 0,050 kWh/unit', () => {
    const ws = D.buildScenario('i-optional');
    const w = P(ws, '2026-10-19', '2026-10-25');
    let outside = 0; w.rows.forEach((r) => { outside += D.outsideSplit(ws.schedules[0].windows, w.window.startMs, w.window.endMs, TZ, r.parts).outside; });
    assert.strictEqual(outside, 0);
    const m = D.computeMetric(ws, ws.metric); assert.ok(m.ok); assert.strictEqual(m.intensity.toFixed(3), '0.050');
    const off = Object.assign({}, ws, { metric: null }); assert.strictEqual(kwh(P(off, '2026-10-19', '2026-10-25').totalMWh), '144,000 kWh');
  });
  await t('AT-18', 'Industry outside-window: +3,000 kWh, zero baseline, no percent; total 147/Rp220.500; energy change not alerted', () => {
    const ws = D.buildScenario('i-change');
    const w = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(kwh(w.totalMWh), '147,000 kWh'); assert.strictEqual(rp(w), 'Rp220.500');
    const ins = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25'));
    assert.strictEqual(ins.observations.length, 1);
    const o = ins.observations[0]; assert.strictEqual(o.kind, 'outside'); assert.strictEqual(o.evidence.baselineMWh, 0);
    assert.strictEqual(D.fmtSignedKwh(o.evidence.deltaMWh), '+3,000 kWh'); assert.strictEqual(o.evidence.pct, null);
    assert.match(o.copy.pctNote, /Persentase tidak tersedia karena nilai pembanding nol/);
    assert.ok(!/boros|pemborosan yang|kerusakan/.test(o.copy.title));
    assert.strictEqual(ins.perAsset['asset-kompresor'].energy.state, 'noChange');
  });
  await t('FX-CUR', 'Current-period scenario (21 Oktober 12.00): today and Monday-to-now', () => {
    const h = D.buildScenario('h-current');
    const ht = P(h, '2026-10-21'); assert.strictEqual(kwh(ht.totalMWh), '0,870 kWh'); assert.strictEqual(rp(ht), 'Rp1.305'); assert.strictEqual(ht.window.clipped, true); assert.strictEqual(ht.coverageMin, 1);
    const hw = P(h, '2026-10-19', '2026-10-21'); assert.strictEqual(kwh(hw.totalMWh), '5,070 kWh'); assert.strictEqual(rp(hw), 'Rp7.605');
    const i = D.buildScenario('i-current');
    const it = P(i, '2026-10-21'); assert.strictEqual(kwh(it.totalMWh), '13,000 kWh'); assert.strictEqual(rp(it), 'Rp19.500');
    const iw = P(i, '2026-10-19', '2026-10-21'); assert.strictEqual(kwh(iw.totalMWh), '61,000 kWh'); assert.strictEqual(rp(iw), 'Rp91.500');
    assert.strictEqual(D.evaluateInsights(h, Q(h, '2026-10-21')).observations.length, 0);
  });
  await t('FX-NOW', 'Virtual Monday 26 Oktober: "Hari ini" is empty (no future rows), not zero', () => {
    const ws = D.buildScenario('h-base');
    const s = P(ws, '2026-10-26'); assert.strictEqual(s.hasData, false); assert.strictEqual(s.totalMWh, null); assert.strictEqual(s.window.elapsedMs, 0);
  });
  await t('AT-36', 'Parent 10 kWh + child 1 kWh: never 11; each view valid', () => {
    const ws = D.buildScenario('h-scope');
    ws.assets.find((a) => a.id === 'asset-kulkas').altPending = null;
    ws.assets.find((a) => a.id === 'asset-kulkas').bindings = [{ sourceId: 'src-kulkas', fromMs: -Infinity, toMs: null }];
    const both = P(ws, '2026-10-25', null, ['asset-meter', 'asset-kulkas']); assert.strictEqual(both.totalMWh, null); assert.strictEqual(both.scopeValid, false);
    assert.strictEqual(kwh(P(ws, '2026-10-25', null, ['asset-meter']).totalMWh), '10,000 kWh');
    assert.strictEqual(kwh(P(ws, '2026-10-25', null, ['asset-kulkas']).totalMWh), '1,000 kWh');
  });
  await t('AT-35', 'Alternative sources for one load: 2 kWh never 4; unresolved blocks the asset value', () => {
    const ws = D.buildScenario('h-scope');
    const k = ws.assets.find((a) => a.id === 'asset-kulkas');
    const before = P(ws, '2026-10-24', '2026-10-25', ['asset-kulkas']); assert.strictEqual(before.totalMWh, null);
    assert.strictEqual(before.rows[0].bySource['src-kulkas'], 2000000); assert.strictEqual(before.rows[0].bySource['src-kulkas-plug'], 2000000);
    k.altPending = null; k.bindings = [{ sourceId: 'src-kulkas-plug', fromMs: -Infinity, toMs: null }]; ws.revision++;
    assert.strictEqual(kwh(P(ws, '2026-10-24', '2026-10-25', ['asset-kulkas']).totalMWh), '2,000 kWh');
  });
  await t('AT-36b', 'Unknown overlap refuses only the combined total; individual values remain', () => {
    const ws = D.buildScenario('h-scope');
    const s = P(ws, '2026-10-25', null, ['asset-meter', 'asset-pompa']);
    assert.strictEqual(s.totalMWh, null); assert.ok(s.issues.some((i) => i.type === 'unknown'));
    assert.strictEqual(kwh(s.rows.find((r) => r.asset.id === 'asset-pompa').mWh), '0,300 kWh');
  });
  await t('AT-27a', 'Average power 100 W for 30 min = 50 Wh; instantaneous power blocked', () => {
    const ws = D.emptyWorkspace('local');
    const p = D.parseCsv('interval_start,interval_end,asset,average_power_w\n2026-10-20T00:00:00+07:00,2026-10-20T00:30:00+07:00,Pompa,100\n', 'daya.csv');
    const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint';
    assert.strictEqual(D.buildPreview(ws, p, mp).blocked, true);
    mp.powerMeaning = 'instant'; assert.ok(D.buildPreview(ws, p, mp).mappingIssues.some((i) => /sesaat tidak dapat/.test(i.message)));
    mp.powerMeaning = 'average'; const pv = D.buildPreview(ws, p, mp);
    assert.strictEqual(pv.blocked, false); assert.strictEqual(pv.acceptedReadings[0].mWh, 50000);
  });
  await t('AT-27b', 'Counter 100 → 130 → 5 Wh with reset: 30 Wh valid, reset interval unknown', () => {
    const ws = D.emptyWorkspace('local');
    const p = D.parseCsv('timestamp,perangkat,cumulative_wh\n2026-10-20 00:00,Mesin,100\n2026-10-20 01:00,Mesin,130\n2026-10-20 02:00,Mesin,5\n', 'counter.csv');
    const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint'; mp.tzConfirmed = true;
    const pv = D.buildPreview(ws, p, mp);
    assert.strictEqual(pv.acceptedReadings.length, 1); assert.strictEqual(pv.acceptedReadings[0].mWh, 30000);
    assert.ok(pv.assumptions.some((a) => /tidak diketahui/.test(a)));
    assert.ok(!pv.acceptedReadings.some((r) => r.mWh < 0 || r.mWh === 125000));
  });
  await t('AT-13', 'Overnight Monday 22.00–Tuesday 06.00: 10 kWh gives 8 inside / 2 outside', () => {
    const mon = D.localMidnight('2026-10-19', TZ);
    const parts = []; for (let h = 21; h < 31; h++) parts.push([mon + h * D.HOUR, mon + (h + 1) * D.HOUR, 1e6]);
    const sp = D.outsideSplit([{ days: [0], start: '22:00', end: '06:00', nextDay: true }], mon, mon + 2 * D.DAY, TZ, parts);
    assert.strictEqual(sp.inside, 8e6); assert.strictEqual(sp.outside, 2e6);
    assert.strictEqual(D.validateWindows([{ days: [0], start: '22:00', end: '06:00', nextDay: false }]).length, 1);
    assert.strictEqual(D.validateWindows([{ days: [0], start: '08:00', end: '08:00' }]).length, 1);
    assert.strictEqual(D.validateWindows([{ days: [0], allDay: true }]).length, 0);
  });
  await t('AT-15', 'Interval 16.30–17.30 60 Wh, schedule ends 17.00: 30/30 estimated, conserved', () => {
    const mon = D.localMidnight('2026-10-19', TZ);
    const sp = D.outsideSplit([{ days: [0], start: '07:00', end: '17:00' }], mon, mon + D.DAY, TZ, [[mon + 16.5 * D.HOUR, mon + 17.5 * D.HOUR, 60000]]);
    assert.strictEqual(sp.inside, 30000); assert.strictEqual(sp.outside, 30000); assert.strictEqual(sp.estimated, true);
  });
  await t('AT-12', 'Overlapping windows merge; shared minutes counted once', () => {
    const mon = D.localMidnight('2026-10-19', TZ);
    const iv = D.expandWindows([{ days: [0], start: '07:00', end: '12:00' }, { days: [0], start: '10:00', end: '17:00' }], mon, mon + D.DAY, TZ);
    assert.strictEqual(iv.filter((x) => x[0] >= mon && x[1] <= mon + D.DAY).reduce((s, x) => s + x[1] - x[0], 0), 10 * D.HOUR);
  });
  await t('AT-19', 'Half of an asset day missing: 50% coverage, recorded partial, no matched alert', () => {
    const ws = D.buildScenario('h-base');
    const day = D.localMidnight('2026-10-25', TZ);
    ws.readings = ws.readings.filter((r) => !(r.a === 'asset-kulkas' && r.t0 >= day + 12 * D.HOUR && r.t0 < day + D.DAY)); ws.revision++;
    const s = P(ws, '2026-10-25', null, ['asset-kulkas']); assert.strictEqual(s.coverageMin, 0.5); assert.strictEqual(kwh(s.totalMWh), '0,600 kWh');
    const c = D.compareAsset(ws, D.assetById(ws, 'asset-kulkas'), day, day + D.DAY, 'energy'); assert.strictEqual(c.state, 'notComparable');
  });
  await t('AT-16', 'Learning + no tariff + partial combination', () => {
    const ws = D.buildScenario('h-learning-partial');
    const s = P(ws, '2026-10-19', '2026-10-25');
    assert.strictEqual(s.cost.available, false); assert.strictEqual(s.cost.reason, 'missing_tariff');
    assert.ok(s.totalMWh > 0); assert.ok(s.coverageMin < 0.9);
    const ins = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25'));
    assert.ok(ins.learning >= 1); assert.strictEqual(ins.observations.length, 0);
    assert.ok(ins.notices.some((n) => n.kind === 'partial' && /Pompa Air/.test(n.title) && /24–25 Oktober 2026/.test(n.body)));
    const k = s.rows.find((r) => r.asset.id === 'asset-kulkas'); assert.deepStrictEqual(k.gaps.map((g) => D.fmtGap(g[0], g[1], TZ)), ['22 Oktober 2026 14.00–16.00']);
  });
  await t('AT-21', 'All-zero readings with full coverage: valid 0, no percentages, no division error', () => {
    const ws = D.buildScenario('h-zero');
    const s = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(s.totalMWh, 0); assert.strictEqual(s.coverageMin, 1);
    assert.strictEqual(D.fmtPct(0, s.totalMWh), null); assert.strictEqual(s.cost.reason, 'missing_tariff');
    const ins = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25')); assert.strictEqual(ins.observations.length, 0);
  });
  await t('AT-38', 'Stale simulated source + client offline are separate facts; retry cannot fabricate a reading', async () => {
    const ws = D.buildScenario('h-stale-offline');
    assert.strictEqual(D.staleSources(ws).length, 1); assert.strictEqual(ws.client.offline, true);
    await assert.rejects(D.api.refresh(ws), (e) => e.code === 'offline');
    ws.client.offline = false; const n = ws.readings.length;
    const r = await D.api.checkSource(ws, 'src-router'); assert.strictEqual(r.newReadings, 0); assert.strictEqual(ws.readings.length, n);
  });
  await t('AT-09', 'Effective-dated tariff split: Rp3.000, not retroactive Rp4.000', () => {
    const ws = D.emptyWorkspace('local');
    const T = D.localMidnight('2026-10-20', TZ);
    ws.tariffs = [{ fromMs: -Infinity, mRpPerKwh: 1000000, source: 'user' }, { fromMs: T, mRpPerKwh: 2000000, source: 'user' }];
    const c = D.costOfParts(ws, [[T - D.HOUR, T, 1e6], [T, T + D.HOUR, 1e6]]); assert.strictEqual(D.fmtRp(c.nano), 'Rp3.000');
  });
  await t('AT-08', 'Explicit zero tariff is valid Rp0; missing tariff is unknown', () => {
    const ws = D.buildScenario('h-notariff');
    assert.strictEqual(P(ws, '2026-10-19', '2026-10-25').cost.reason, 'missing_tariff');
    ws.tariffs = [{ fromMs: -Infinity, mRpPerKwh: 0, source: 'user' }];
    const s = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(s.cost.available, true); assert.strictEqual(D.fmtRp(s.cost.nano), 'Rp0');
  });
  await t('AT-23', 'Zero/negative/missing output never yields intensity', () => {
    const ws = D.buildScenario('i-optional');
    assert.strictEqual(D.computeMetric(ws, Object.assign({}, ws.metric, { quantity: 0 })).reason, 'Tidak dapat dihitung: keluaran nol.');
    assert.strictEqual(D.computeMetric(ws, Object.assign({}, ws.metric, { quantity: -5 })).ok, false);
    assert.strictEqual(D.computeMetric(ws, Object.assign({}, ws.metric, { quantity: null })).ok, false);
  });
  await t('AT-24', 'Estimated partial output: complete days only unless windows + uniform confirmation', () => {
    const ws = D.buildScenario('i-current');
    const def = { assetIds: ws.assets.map((a) => a.id), unit: 'unit', method: 'estimated', perDay: 480, periodStart: '2026-10-19', periodEnd: '2026-10-21' };
    const a = D.computeMetric(ws, def); assert.ok(a.ok); assert.strictEqual(a.output, 960); assert.strictEqual(a.energyMWh, 48e6);
    const b = D.computeMetric(ws, Object.assign({}, def, { uniformConfirmed: true, outputWindows: [{ days: [2], start: '08:00', end: '16:00' }] }));
    assert.strictEqual(b.output, 960 + 480 * 4 / 8); assert.strictEqual(b.energyMWh, 61e6);
  });
  const CSV10 = (bad) => 'timestamp,perangkat,energi_wh\n' + Array.from({ length: 10 }, (_, i) => '2026-10-20 ' + String(i).padStart(2, '0') + ':00,Router,' + (i < bad ? '-1' : '10')).join('\n') + '\n';
  await t('AT-30', '2/10 invalid needs acknowledgement and imports 8; 3/10 blocked; counts reconcile', () => {
    const ws = D.emptyWorkspace('local');
    const p2 = D.parseCsv(CSV10(2), 'a.csv'); const m2 = D.defaultMapping(ws, p2); m2.scope = 'disjoint'; m2.tzConfirmed = true;
    const v2 = D.buildPreview(ws, p2, m2);
    assert.strictEqual(v2.accepted, 8); assert.strictEqual(v2.invalid, 2); assert.strictEqual(v2.needsAck, true); assert.strictEqual(v2.blocked, false);
    assert.strictEqual(v2.accepted + v2.invalid + v2.duplicates + v2.conflicts, v2.totalRows);
    assert.strictEqual(v2.errors[0].message, 'Baris data 1, energi_wh: gunakan angka 0 atau lebih.');
    const p3 = D.parseCsv(CSV10(3), 'b.csv'); const m3 = D.defaultMapping(ws, p3); m3.scope = 'disjoint'; m3.tzConfirmed = true;
    const v3 = D.buildPreview(ws, p3, m3); assert.strictEqual(v3.blocked, true); assert.ok(v3.blockReasons.includes('Impor diblokir: 3 dari 10 baris tidak valid.'));
  });
  await t('AT-28', 'Semicolon, decimal comma, quoted name with delimiter, BOM, CRLF, blank line', () => {
    const ws = D.emptyWorkspace('local');
    const p = D.parseCsv('﻿waktu;alat;wh\r\n2026-10-20 00:00;"Lampu; Gudang";12,5\r\n\r\n2026-10-20 01:00;"Lampu; Gudang";1.250,5\r\n', 'semi.csv');
    assert.ok(p.ok, JSON.stringify(p.errors)); assert.strictEqual(p.delimiter, ';'); assert.deepStrictEqual(p.assetNames, ['Lampu; Gudang']); assert.strictEqual(p.blankLines, 1);
    const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint'; mp.tzConfirmed = true;
    const pv = D.buildPreview(ws, p, mp); assert.deepStrictEqual(pv.acceptedReadings.map((r) => r.mWh), [12500, 1250500]);
    const q = D.parseCsv('timestamp,asset,energy_wh\n2026-10-20 00:00,A,"12,5"\n2026-10-20 01:00,A,12,5\n', 'c.csv');
    assert.ok(!q.ok || D.buildPreview(ws, q, Object.assign(D.defaultMapping(ws, q), { scope: 'disjoint', tzConfirmed: true })).invalid >= 1);
  });
  await t('AT-29', 'Bad header, impossible date, non-numeric value give actionable messages', () => {
    const ws = D.emptyWorkspace('local');
    assert.ok(!D.parseCsv('foo,bar\n1,2\n').ok);
    const p = D.parseCsv('timestamp,asset,energy_wh\n2026-02-30 00:00,A,1\n2026-10-20 01:00,A,dua\n2026-10-20 02:00,A,1\n2026-10-20 03:00,A,1\n2026-10-20 04:00,A,1\n', 'x.csv');
    const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint'; mp.tzConfirmed = true;
    const pv = D.buildPreview(ws, p, mp);
    assert.ok(pv.errors.some((e) => /tidak ada/.test(e.message))); assert.ok(pv.errors.some((e) => /bukan angka/.test(e.message)));
  });
  await t('AT-31', 'One-row and irregular timestamp-only streams require explicit interval', () => {
    const ws = D.emptyWorkspace('local');
    const p = D.parseCsv('timestamp,asset,energy_wh\n2026-10-20 00:00,A,1\n', 'one.csv');
    const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint'; mp.tzConfirmed = true;
    assert.ok(D.buildPreview(ws, p, mp).mappingIssues.some((i) => i.id === 'map-interval'));
    mp.intervalMinutes = '60'; assert.strictEqual(D.buildPreview(ws, p, mp).blocked, false);
    const irr = D.parseCsv('timestamp,asset,energy_wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n2026-10-20 01:15,A,1\n2026-10-20 03:00,A,1\n', 'irr.csv');
    assert.strictEqual(irr.cadence.a, null);
    const reg = D.parseCsv('timestamp,asset,energy_wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n2026-10-20 05:00,A,1\n2026-10-20 06:00,A,1\n2026-10-20 07:00,A,1\n2026-10-20 08:00,A,1\n2026-10-20 09:00,A,1\n2026-10-20 10:00,A,1\n2026-10-20 11:00,A,1\n2026-10-20 12:00,A,1\n2026-10-20 13:00,A,1\n', 'gap.csv');
    assert.strictEqual(reg.cadence.a, D.HOUR);
  });
  await t('AT-32', 'Name limit 60 without silent truncation; row limit reported', () => {
    const ws = D.emptyWorkspace('local');
    const long = 'X'.repeat(61);
    const p = D.parseCsv('interval_start,interval_end,asset,energy_wh\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,' + long + ',1\n', 'n.csv');
    const pv = D.buildPreview(ws, p, Object.assign(D.defaultMapping(ws, p), { scope: 'disjoint' }));
    assert.strictEqual(pv.invalid, 1); assert.match(pv.errors[0].message, /tidak dipotong/);
    const big = 'timestamp,asset,energy_wh\n' + '2026-10-20 00:00,A,1\n'.repeat(150001);
    assert.ok(D.parseCsv(big).errors.some((e) => /150\.000/.test(e.message)));
  });
  await t('AT-33/34', 'Commit is atomic, retry is idempotent, interrupted result is looked up, reimport adds nothing', async () => {
    const ws = D.emptyWorkspace('local');
    const p = D.parseCsv(CSV10(0), 'r.csv'); const mp = D.defaultMapping(ws, p); mp.scope = 'disjoint'; mp.tzConfirmed = true;
    const pv = D.buildPreview(ws, p, mp);
    ws.failNext.import = 'reject';
    await assert.rejects(D.api.commitImport(ws, pv), (e) => e.code === 'rejected');
    assert.strictEqual(ws.readings.length, 0); assert.strictEqual(ws.assets.length, 0);
    ws.failNext.import = 'interrupt';
    await assert.rejects(D.api.commitImport(ws, pv), (e) => e.code === 'unknown');
    const st = await D.api.checkOperation(ws, pv.opKey); assert.strictEqual(st.status, 'committed'); assert.strictEqual(st.added, 10);
    const again = await D.api.commitImport(ws, pv); assert.strictEqual(again.replayed, true); assert.strictEqual(ws.readings.length, 10);
    const p2 = D.parseCsv(CSV10(0), 'r.csv'); const pv2 = D.buildPreview(ws, p2, Object.assign(D.defaultMapping(ws, p2), { scope: 'disjoint', tzConfirmed: true }));
    assert.strictEqual(pv2.duplicates, 10); assert.strictEqual(pv2.acceptedReadings.length, 0);
    const conflict = D.parseCsv(CSV10(0).replace('00:00,Router,10', '00:00,Router,11'), 'k.csv');
    const pv3 = D.buildPreview(ws, conflict, Object.assign(D.defaultMapping(ws, conflict), { scope: 'disjoint', tzConfirmed: true }));
    assert.strictEqual(pv3.conflicts, 1); assert.strictEqual(pv3.blocked, true);
  });
  await t('AT-53', 'Composition: core-only keeps identical energy, rejects disabled capability at mock boundary', async () => {
    const full = D.buildScenario('i-optional'), core = D.buildScenario('i-optional'); core.composition = 'core';
    assert.strictEqual(P(core, '2026-10-19', '2026-10-25').totalMWh, P(full, '2026-10-19', '2026-10-25').totalMWh);
    assert.strictEqual(P(core, '2026-10-19', '2026-10-25').cost.reason, 'capability_disabled');
    assert.strictEqual(D.computeMetric(core, core.metric).ok, false);
    await assert.rejects(D.api.saveSettings(core, { schedules: [] }), (e) => e.code === 'capability_disabled');
    await assert.rejects(D.api.saveMetric(core, core.metric), (e) => e.code === 'capability_disabled');
    assert.strictEqual(D.validateComposition(['cost']).ok, false); assert.strictEqual(D.validateComposition(['core', 'teleport']).ok, false);
    assert.strictEqual(D.validateComposition(['core', 'cost']).ok, true);
  });
  await t('AT-39', 'Feedback: hide/snooze/restore persists per revision and never touches readings', async () => {
    const ws = D.buildScenario('h-change'); const n = ws.readings.length;
    const obs = D.evaluateInsights(ws, Q(ws, '2026-10-19', '2026-10-25')).observations[0];
    ws.failNext.feedback = 'reject'; await assert.rejects(D.api.saveFeedback(ws, obs, 'hide'));
    assert.strictEqual(D.feedbackState(ws, obs).visible, true);
    await D.api.saveFeedback(ws, obs, 'hide'); assert.strictEqual(D.feedbackState(ws, obs).hidden, true);
    await D.api.saveFeedback(ws, obs, 'snooze'); const fs = D.feedbackState(ws, obs); assert.strictEqual(fs.snoozed, true);
    assert.strictEqual(D.fmtDateTime(fs.f.untilMs, TZ), '27 Oktober 2026 00.00');
    await D.api.saveFeedback(ws, obs, 'restore'); assert.strictEqual(D.feedbackState(ws, obs).visible, true);
    assert.strictEqual(ws.readings.length, n);
  });
  await t('AT-40', 'Rejected/expired settings save keeps confirmed values', async () => {
    const ws = D.buildScenario('i-change'); const before = JSON.stringify(ws.schedules);
    ws.failNext.settings = 'reject'; await assert.rejects(D.api.saveSettings(ws, { schedules: [] }));
    ws.failNext.settings = 'expired'; await assert.rejects(D.api.saveSettings(ws, { schedules: [] }), (e) => e.code === 'session_expired');
    assert.strictEqual(JSON.stringify(ws.schedules), before);
    ws.client.offline = true; await assert.rejects(D.api.saveSettings(ws, { tariffs: [] }), (e) => e.code === 'offline'); assert.strictEqual(ws.tariffs.length, 1);
  });
  await t('AT-51', 'Timezone change recomputes local-day boundaries without rewriting UTC readings', () => {
    const ws = D.buildScenario('h-base'); const first = ws.readings[0].t0;
    ws.site.tz = 'Asia/Makassar'; ws.revision++;
    assert.strictEqual(ws.readings[0].t0, first);
    const s = P(ws, '2026-10-19', '2026-10-25'); assert.strictEqual(s.totalMWh, 14.7e6); // shifted window, same hourly pattern sum
    assert.notStrictEqual(D.periodBounds({ start: '2026-10-19', end: '2026-10-19' }, 'Asia/Makassar').start, D.periodBounds({ start: '2026-10-19', end: '2026-10-19' }, TZ).start);
  });
  await t('AT-42', 'Simulated source setup retry reuses operation identity (no duplicate asset/binding)', async () => {
    const ws = D.buildScenario('h-base'); const na = ws.assets.length;
    const reading = await D.api.firstReading(ws, 'op-1');
    const d = { opKey: 'op-1', name: 'Dispenser', kind: 'device', assetId: 'new', effectiveFromMs: ws.nowMs - D.HOUR, reading };
    const r1 = await D.api.saveSource(ws, d); const r2 = await D.api.saveSource(ws, d);
    assert.strictEqual(r2.replayed, true); assert.strictEqual(ws.assets.length, na + 1); assert.strictEqual(r1.assetId, r2.assetId);
  });

  const pass = results.filter((r) => r.status === 'pass').length;
  results.forEach((r) => console.log((r.status === 'pass' ? 'PASS ' : 'FAIL ') + r.id + ' ' + r.name + (r.error ? '\n     ' + r.error : '')));
  console.log('\n' + pass + '/' + results.length + ' passed · node ' + process.version + ' · ' + new Date().toISOString());
  if (process.argv.includes('--json')) require('fs').writeFileSync(process.argv[process.argv.indexOf('--json') + 1], JSON.stringify({ runtime: 'node ' + process.version, at: new Date().toISOString(), results }, null, 2));
  process.exit(pass === results.length ? 0 : 1);
})();
