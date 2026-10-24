/* HematDaya prototype domain - the one accepted-data authority for every screen.
   Plain ES2017, no dependencies. Browser: window.HematDomain. Node: require('./hematdaya-domain.js').
   Units: energy in integer milli-watt-hours (mWh), tariff in integer milli-rupiah per kWh, cost in BigInt nano-rupiah.
   Display rounding happens only in the fmt* helpers. This is a browser simulation of the future server contract
   ("Backend simulasi"); it is not a saved service, not authentication and not a live meter adapter. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.HematDomain = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var MIN = 60000, HOUR = 3600000, DAY = 86400000, WEEK = 7 * DAY;
  var VERSION = {
    schema_version: 1, source_release: 'hematdaya-proto-0.1.0', calc: 'hd-calc-1',
    policy: { baseline: 'hd-baseline-1', change: 'hd-change-1', stale: 'hd-stale-1' }, fixtures: 'hd-fixtures-1 (PRD Generic 1.2 §19)'
  };
  var TZ = { 'Asia/Jakarta': 7, 'Asia/Makassar': 8, 'Asia/Jayapura': 9 };
  var TZ_LABEL = { 'Asia/Jakarta': 'Asia/Jakarta (WIB, UTC+7)', 'Asia/Makassar': 'Asia/Makassar (WITA, UTC+8)', 'Asia/Jayapura': 'Asia/Jayapura (WIT, UTC+9)' };
  var MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
  var DAYS = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];
  var DAYS_SHORT = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];

  /* ---------------- time ---------------- */
  function off(tz) { return (TZ[tz] || 7) * HOUR; }
  function localMidnight(iso, tz) { var p = iso.split('-').map(Number); return Date.UTC(p[0], p[1] - 1, p[2]) - off(tz); }
  function localDate(ms, tz) { return new Date(ms + off(tz)).toISOString().slice(0, 10); }
  function localHHMM(ms, tz) { return new Date(ms + off(tz)).toISOString().slice(11, 16).replace(':', '.'); }
  function weekday(ms, tz) { return (new Date(ms + off(tz)).getUTCDay() + 6) % 7; }
  function addDays(iso, n) { var d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function hm(s) { var p = s.split(/[:.]/).map(Number); return p[0] * HOUR + p[1] * MIN; }
  function periodBounds(period, tz) { return { start: localMidnight(period.start, tz), end: localMidnight(addDays(period.end, 1), tz) }; }

  var NOW_MAIN = Date.UTC(2026, 9, 26) - 7 * HOUR;               // 2026-10-26 00.00 Asia/Jakarta
  var NOW_CURRENT = Date.UTC(2026, 9, 21, 12) - 7 * HOUR;        // 2026-10-21 12.00 Asia/Jakarta
  var FIX_START = Date.UTC(2026, 8, 28) - 7 * HOUR;              // 2026-09-28 00.00, a Monday
  var FIX_HOURS = 28 * 24;

  /* ---------------- formatting (Indonesian display only) ---------------- */
  function group(intStr) { return intStr.replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function fmtKwh(mWh, unit) {
    if (mWh == null) return null;
    var wh = Math.round(Math.abs(mWh) / 1000);
    return (mWh < 0 && wh > 0 ? '−' : '') + group(String(Math.floor(wh / 1000))) + ',' + String(wh % 1000).padStart(3, '0') + (unit === false ? '' : ' kWh');
  }
  function fmtSignedKwh(mWh) { return mWh == null ? null : (mWh > 0 ? '+' : mWh < 0 ? '−' : '') + fmtKwh(Math.abs(mWh)); }
  function nanoToRp(nano) { var n = typeof nano === 'bigint' ? nano : BigInt(nano); return Number((n + 500000000n) / 1000000000n); }
  function fmtRp(nano) { return nano == null ? null : 'Rp' + group(String(nanoToRp(nano))); }
  function fmtRpPlain(rp) { return 'Rp' + group(String(Math.round(rp))); }
  function fmtTariff(mRp) { var r = mRp / 1000; var s = Number.isInteger(r) ? group(String(r)) : group(String(Math.floor(r))) + ',' + String(mRp % 1000).padStart(3, '0').replace(/0+$/, ''); return 'Rp' + s + '/kWh'; }
  function fmtPct(part, whole) { if (!whole) return null; return (Math.round(part / whole * 10000) / 100).toFixed(2).replace('.', ',') + '%'; }
  function fmtSignedPct(delta, ref) { if (!ref) return null; var s = fmtPct(Math.abs(delta), ref); return (delta > 0 ? '+' : delta < 0 ? '−' : '') + s; }
  function fmtDate(iso) { var p = iso.split('-').map(Number); return p[2] + ' ' + MONTHS[p[1] - 1] + ' ' + p[0]; }
  function fmtRange(a, b) {
    if (!b || a === b) return fmtDate(a);
    var pa = a.split('-').map(Number), pb = b.split('-').map(Number);
    if (pa[0] === pb[0] && pa[1] === pb[1]) return pa[2] + '–' + pb[2] + ' ' + MONTHS[pb[1] - 1] + ' ' + pb[0];
    if (pa[0] === pb[0]) return pa[2] + ' ' + MONTHS[pa[1] - 1] + '–' + pb[2] + ' ' + MONTHS[pb[1] - 1] + ' ' + pb[0];
    return fmtDate(a) + '–' + fmtDate(b);
  }
  function fmtDateTime(ms, tz) { return fmtDate(localDate(ms, tz)) + ' ' + localHHMM(ms, tz); }
  function fmtGap(a, b, tz) {
    if (localHHMM(a, tz) === '00.00' && localHHMM(b, tz) === '00.00') return fmtRange(localDate(a, tz), localDate(b - 1, tz));
    if (localDate(a, tz) === localDate(b - 1, tz)) { var e = localHHMM(b, tz); return fmtDate(localDate(a, tz)) + ' ' + localHHMM(a, tz) + '–' + (e === '00.00' ? '24.00' : e); }
    return fmtDateTime(a, tz) + '–' + fmtDateTime(b, tz);
  }
  function fmtCoverage(c) { return c == null ? null : (Math.floor(c * 1000) / 10).toString().replace('.', ',') + '%'; }

  /* ---------------- small helpers ---------------- */
  function fnv(str) { var h = 0x811c9dc5; for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(36); }
  function median(xs) { if (!xs.length) return null; var s = xs.slice().sort(function (a, b) { return a - b; }); var m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
  function unionIntervals(ints) {
    var s = ints.slice().sort(function (x, y) { return x[0] - y[0]; }), out = [];
    s.forEach(function (iv) { if (out.length && iv[0] <= out[out.length - 1][1]) out[out.length - 1][1] = Math.max(out[out.length - 1][1], iv[1]); else out.push([iv[0], iv[1]]); });
    return out;
  }
  function totalLen(ints) { return ints.reduce(function (t, iv) { return t + iv[1] - iv[0]; }, 0); }
  function overlapLen(ints, a, b) { var t = 0; ints.forEach(function (iv) { var s = Math.max(a, iv[0]), e = Math.min(b, iv[1]); if (e > s) t += e - s; }); return t; }
  function complement(ints, a, b) { var out = [], cur = a; ints.forEach(function (iv) { if (iv[0] > cur) out.push([cur, Math.min(iv[0], b)]); cur = Math.max(cur, iv[1]); }); if (cur < b) out.push([cur, b]); return out.filter(function (g) { return g[1] > g[0]; }); }
  function err(code, message, extra) { var e = new Error(message); e.code = code; if (extra) Object.assign(e, extra); return e; }

  /* ---------------- workspace, fixtures, scenarios ---------------- */
  var KIND_LABEL = { device: 'Perangkat', group: 'Grup', circuit: 'Sirkuit', site_total: 'Meter lokasi' };
  var CONTEXT_LABEL = { household: 'Rumah tangga', business: 'Usaha', industry: 'Industri', unspecified: 'Belum memilih' };

  function emptyWorkspace(mode) {
    return {
      mode: mode, scenarioId: null, scenarioName: mode === 'local' ? 'Ruang kerja lokal (kosong)' : null,
      site: { name: 'Lokasi saya', context: 'unspecified', tz: 'Asia/Jakarta' },
      nowMs: NOW_MAIN, assets: [], sources: [], readings: [], tariffs: [], schedules: [], relations: [], selection: [],
      metric: null, feedback: {}, operations: {}, audit: [], notifications: { enabled: false },
      client: { offline: false, cachedAtMs: null }, failNext: {}, composition: 'full',
      initialPeriod: { preset: 'last7', start: '2026-10-19', end: '2026-10-25' }, revision: 1
    };
  }
  function addAsset(ws, a) {
    var asset = Object.assign({ kind: 'device', category: '', location: '', profile: 'unknown', scheduleMode: 'inherit', customWindows: [], archived: false, bindings: [], altPending: null }, a);
    ws.assets.push(asset); ws.selection.push(asset.id); return asset;
  }
  function addSource(ws, s) {
    var src = Object.assign({ origin: 'simulated', kind: 'interval_energy', cadenceMs: HOUR, resolutionMWh: 1000, transport: 'none', status: 'simulated', lastCaptureMs: null }, s);
    ws.sources.push(src); return src;
  }
  function bind(ws, asset, src, fromMs) { asset.bindings.push({ sourceId: src.id, fromMs: fromMs == null ? -Infinity : fromMs, toMs: null }); }
  function pushHourly(ws, asset, src, whFn, opts) {
    opts = opts || {};
    for (var i = 0; i < FIX_HOURS; i++) {
      var t0 = FIX_START + i * HOUR;
      if (opts.from && t0 < opts.from) continue;
      if (opts.until && t0 >= opts.until) continue;
      if (opts.skip && opts.skip(t0)) continue;
      var wh = whFn(new Date(t0 + 7 * HOUR).getUTCHours(), weekday(t0, 'Asia/Jakarta'), localDate(t0, 'Asia/Jakarta'));
      ws.readings.push({ s: src.id, a: asset.id, t0: t0, t1: t0 + HOUR, mWh: wh * 1000 });
    }
  }
  function inWeek(iso) { return iso >= '2026-10-19' && iso <= '2026-10-25'; }
  var HOUSE = [
    { key: 'kulkas', name: 'Kulkas', category: 'Pendingin makanan', location: 'Dapur', profile: 'continuous', wh: function () { return 50; } },
    { key: 'router', name: 'Router', category: 'Elektronik/TI', location: 'Ruang tengah', profile: 'continuous', wh: function () { return 10; } },
    { key: 'pompa', name: 'Pompa Air', category: 'Pompa', location: 'Halaman belakang', profile: 'intermittent', wh: function (h) { return h === 6 || h === 18 ? 150 : 0; } },
    { key: 'tv', name: 'TV', category: 'Elektronik/TI', location: 'Ruang tengah', profile: 'intermittent', wh: function (h) { return h >= 20 && h <= 22 ? 120 : 0; } }
  ];
  var FACTORY = [
    { key: 'oven', name: 'Oven', category: 'Pemanas/memasak', location: 'Area produksi', wh: function (h, wd) { return wd <= 5 && h >= 8 && h <= 13 ? 2000 : 0; } },
    { key: 'kompresor', name: 'Kompresor', category: 'Motor/proses', location: 'Area produksi', wh: function (h, wd) { return wd <= 5 && h >= 8 && h <= 13 ? 1000 : 0; } },
    { key: 'press', name: 'Mesin Press', category: 'Motor/proses', location: 'Area produksi', wh: function (h, wd) { return wd <= 5 && h >= 13 && h <= 16 ? 1000 : 0; } },
    { key: 'lampu', name: 'Lampu Area', category: 'Penerangan', location: 'Area produksi', wh: function (h, wd) { return wd <= 5 && h >= 7 && h <= 16 ? 200 : 0; } }
  ];
  var INDUSTRY_SCHEDULE = [{ days: [0, 1, 2, 3, 4, 5], start: '07:00', end: '17:00', nextDay: false, allDay: false }];
  var SYNTHETIC_TARIFF = { fromMs: -Infinity, mRpPerKwh: 1500000, source: 'synthetic', label: 'Tarif simulasi, bukan tarif PLN' };

  var SCENARIOS = [
    { id: 'h-base', segment: 'household', name: 'Rumah tangga · dasar', desc: '4 perangkat tanpa AC, tarif simulasi Rp1.500/kWh, tanpa jadwal atau output.' },
    { id: 'h-notariff', segment: 'household', name: 'Rumah tangga · tanpa tarif', desc: 'Data sama; tarif belum diatur, biaya tidak dihitung.' },
    { id: 'h-change', segment: 'household', name: 'Rumah tangga · perubahan TV', desc: '+200 Wh pada TV pukul 19.00 selama 19–25 Oktober.' },
    { id: 'h-current', segment: 'household', name: 'Rumah tangga · periode berjalan', desc: 'Waktu virtual Rabu 21 Oktober 2026 12.00.' },
    { id: 'h-learning-partial', segment: 'household', name: 'Belajar + tanpa tarif + sebagian data', desc: 'Riwayat mulai 12 Oktober, Pompa Air tanpa data 24–25 Oktober, Kulkas tanpa data 22 Oktober 14.00–16.00.' },
    { id: 'h-zero', segment: 'household', name: 'Nol terukur + tanpa tarif', desc: 'Semua interval tercatat 0 Wh dengan data lengkap.' },
    { id: 'h-stale-offline', segment: 'household', name: 'Sumber tidak diperbarui + offline', desc: 'Router (simulasi koneksi) terakhir 25 Oktober 18.00; perangkat Anda offline.' },
    { id: 'h-historical-offline', segment: 'household', name: 'Data historis impor + offline', desc: 'Data rumah tangga berasal dari impor CSV; perangkat Anda offline.' },
    { id: 'h-scope', segment: 'household', name: 'Meter utama, sumber ganda, tumpang tindih', desc: 'Meter utama mencakup Kulkas, Router dan TV; Kulkas punya dua sumber; hubungan Pompa Air dengan Meter utama belum diketahui.' },
    { id: 'i-base', segment: 'industry', name: 'Industri · dasar', desc: 'Oven, Kompresor, Mesin Press, Lampu Area; tanpa jadwal dan tanpa output.' },
    { id: 'i-optional', segment: 'industry', name: 'Industri · jadwal + output aktual', desc: 'Jadwal Senin–Sabtu 07.00–17.00 dan 2.880 unit per minggu.' },
    { id: 'i-change', segment: 'industry', name: 'Industri · kompresor di luar jadwal', desc: '+500 Wh Kompresor pukul 18.00 pada enam hari produksi 19–24 Oktober; jadwal aktif.' },
    { id: 'i-current', segment: 'industry', name: 'Industri · periode berjalan', desc: 'Waktu virtual Rabu 21 Oktober 2026 12.00.' }
  ];

  function buildScenario(id) {
    var ws = emptyWorkspace('demo');
    var sc = SCENARIOS.filter(function (s) { return s.id === id; })[0];
    if (!sc) throw err('unknown_scenario', 'Skenario tidak dikenal.');
    ws.scenarioId = id; ws.scenarioName = sc.name;
    var industry = sc.segment === 'industry';
    ws.site = { name: industry ? 'Bengkel Roti Sejahtera (demo)' : 'Rumah Bandung (demo)', context: industry ? 'industry' : 'household', tz: 'Asia/Jakarta' };
    var defs = industry ? FACTORY : HOUSE;
    var origin = id === 'h-historical-offline' ? 'import' : 'simulated';
    defs.forEach(function (d) {
      var asset = addAsset(ws, { id: 'asset-' + d.key, name: d.name, category: d.category, location: d.location, profile: d.profile || 'unknown',
        scheduleMode: d.profile === 'continuous' ? 'continuous' : 'inherit' });
      var src = addSource(ws, { id: 'src-' + d.key, assetId: asset.id, label: origin === 'import' ? 'Impor CSV · energi-rumah.csv' : 'Sumber demo (simulasi)', origin: origin,
        status: origin === 'import' ? 'historical' : 'simulated', lastCaptureMs: NOW_MAIN });
      bind(ws, asset, src);
      var fn = d.wh, opts = {};
      if (id === 'h-change' && d.key === 'tv') fn = function (h, wd, iso) { return (h >= 20 && h <= 22 ? 120 : 0) + (h === 19 && inWeek(iso) ? 200 : 0); };
      if (id === 'i-change' && d.key === 'kompresor') fn = function (h, wd, iso) { return d.wh(h, wd) + (h === 18 && wd <= 5 && inWeek(iso) ? 500 : 0); };
      if (id === 'h-zero') fn = function () { return 0; };
      if (id === 'h-learning-partial') {
        opts.from = Date.UTC(2026, 9, 12) - 7 * HOUR;
        if (d.key === 'pompa') opts.until = Date.UTC(2026, 9, 24) - 7 * HOUR;
        if (d.key === 'kulkas') opts.skip = function (t0) { return t0 >= Date.UTC(2026, 9, 22, 14) - 7 * HOUR && t0 < Date.UTC(2026, 9, 22, 16) - 7 * HOUR; };
      }
      if (id === 'h-stale-offline' && d.key === 'router') {
        opts.until = Date.UTC(2026, 9, 25, 18) - 7 * HOUR;
        src.transport = 'simulated_live'; src.label = 'Simulasi koneksi · colokan Router'; src.lastCaptureMs = opts.until;
      }
      pushHourly(ws, asset, src, fn, opts);
    });
    if (id === 'h-base' || id === 'h-change' || id === 'h-current' || id === 'h-stale-offline' || id === 'h-historical-offline' || id === 'h-scope' || industry) ws.tariffs = [Object.assign({}, SYNTHETIC_TARIFF)];
    if (id === 'h-current' || id === 'i-current') { ws.nowMs = NOW_CURRENT; ws.initialPeriod = { preset: 'today', start: '2026-10-21', end: '2026-10-21' }; }
    if (id === 'h-stale-offline' || id === 'h-historical-offline') ws.client = { offline: true, cachedAtMs: NOW_MAIN };
    if (id === 'i-optional' || id === 'i-change') ws.schedules = [{ id: 'sched-1', fromMs: -Infinity, windows: INDUSTRY_SCHEDULE.slice(), label: 'Jadwal lokasi v1' }];
    if (id === 'i-optional') ws.metric = { name: 'Energi per roti', assetIds: ws.assets.map(function (a) { return a.id; }), unit: 'unit', product: 'Roti tawar', method: 'actual',
      quantity: 2880, periodStart: '2026-10-19', periodEnd: '2026-10-25', enabled: true };
    if (id === 'h-scope') buildScopeExtras(ws);
    return ws;
  }
  function buildScopeExtras(ws) {
    // Meter utama measures the whole house 10 kWh/day and contains Kulkas (1 kWh/day). Kulkas also has a second,
    // alternative source with identical values; Pompa Air physical overlap with Meter utama is unknown.
    var kulkas = ws.assets.filter(function (a) { return a.id === 'asset-kulkas'; })[0];
    ws.readings = ws.readings.filter(function (r) { return r.a !== 'asset-kulkas'; });
    var kSrc = ws.sources.filter(function (s) { return s.id === 'src-kulkas'; })[0];
    pushHourly(ws, kulkas, kSrc, function (h) { return h < 20 ? 50 : 0; });
    var alt = addSource(ws, { id: 'src-kulkas-plug', assetId: kulkas.id, label: 'Colokan simulasi Kulkas (sumber kedua)' });
    kulkas.bindings.push({ sourceId: alt.id, fromMs: -Infinity, toMs: null }); kulkas.altPending = ['src-kulkas', 'src-kulkas-plug'];
    pushHourly(ws, kulkas, alt, function (h) { return h < 20 ? 50 : 0; });
    var main = addAsset(ws, { id: 'asset-meter', name: 'Meter utama', kind: 'site_total', category: 'Meter rumah', location: 'Teras', profile: 'unknown' });
    var mSrc = addSource(ws, { id: 'src-meter', assetId: main.id, label: 'Sumber demo (simulasi)' });
    bind(ws, main, mSrc);
    pushHourly(ws, main, mSrc, function (h) { return h < 20 ? 400 : 500; });
    ws.relations = [{ a: 'asset-meter', b: 'asset-kulkas', type: 'contains' }, { a: 'asset-meter', b: 'asset-router', type: 'contains' }, { a: 'asset-meter', b: 'asset-tv', type: 'contains' }, { a: 'asset-meter', b: 'asset-pompa', type: 'unknown' }];
    ws.initialPeriod = { preset: 'range', start: '2026-10-25', end: '2026-10-25' };
  }

  /* ---------------- readings index ---------------- */
  function index(ws) {
    if (ws._idx && ws._idx.rev === ws.revision && ws._idx.n === ws.readings.length) return ws._idx;
    var byAsset = {}, bySource = {};
    ws.readings.forEach(function (r) { (byAsset[r.a] = byAsset[r.a] || []).push(r); (bySource[r.s] = bySource[r.s] || []).push(r); });
    Object.keys(byAsset).forEach(function (k) { byAsset[k].sort(function (x, y) { return x.t0 - y.t0 || (x.s < y.s ? -1 : 1); }); });
    ws._idx = { rev: ws.revision, n: ws.readings.length, byAsset: byAsset, bySource: bySource };
    return ws._idx;
  }
  function assetById(ws, id) { return ws.assets.filter(function (a) { return a.id === id; })[0]; }
  function sourceById(ws, id) { return ws.sources.filter(function (s) { return s.id === id; })[0]; }
  function bound(asset, r) { return asset.bindings.some(function (b) { return b.sourceId === r.s && b.fromMs <= r.t0 && (b.toMs == null || r.t0 < b.toMs); }); }
  function lowerBound(arr, t) { var lo = 0, hi = arr.length; while (lo < hi) { var m = (lo + hi) >> 1; if (arr[m].t0 < t) lo = m + 1; else hi = m; } return lo; }

  /* One asset, one window [a, b): bound readings fully inside count fully, crossing a period boundary are allocated
     proportionally (flagged estimate), readings that end after virtual now are excluded (future / unfinished). */
  function assetSlice(ws, asset, a, b) {
    var res = { mWh: 0, parts: [], covered: [], latestEnd: null, allocated: false, origins: {}, resolution: 0, resolutionKnown: true, conflict: !!(asset.altPending && asset.altPending.length > 1), bySource: {} };
    var end = Math.min(b, ws.nowMs);
    var rs = index(ws).byAsset[asset.id] || [];
    for (var i = lowerBound(rs, a - DAY); i < rs.length; i++) {
      var r = rs[i];
      if (r.t0 >= end) break;
      if (r.t1 <= a || r.t1 > ws.nowMs || !bound(asset, r)) continue;
      var s = Math.max(a, r.t0), e = Math.min(end, r.t1);
      var part = s === r.t0 && e === r.t1 ? r.mWh : r.mWh * (e - s) / (r.t1 - r.t0);
      if (part !== r.mWh) res.allocated = true;
      res.bySource[r.s] = (res.bySource[r.s] || 0) + part;
      if (res.conflict) continue;
      var src = sourceById(ws, r.s);
      res.mWh += part; res.parts.push([s, e, part]); res.covered.push([s, e]);
      res.latestEnd = Math.max(res.latestEnd || 0, r.t1);
      res.origins[src ? src.origin : 'unknown'] = true;
      if (src && src.resolutionMWh != null) res.resolution += src.resolutionMWh; else res.resolutionKnown = false;
    }
    res.covered = unionIntervals(res.covered);
    res.window = [a, end]; res.elapsed = Math.max(0, end - a);
    res.coverage = res.elapsed > 0 ? totalLen(res.covered) / res.elapsed : null;
    res.gaps = res.elapsed > 0 ? complement(res.covered, a, end) : [];
    if (res.conflict) { res.mWh = null; res.coverage = null; res.gaps = []; }
    return res;
  }

  function scopeIssues(ws, ids) {
    var issues = [];
    ws.relations.forEach(function (rel) {
      if (ids.indexOf(rel.a) < 0 || ids.indexOf(rel.b) < 0) return;
      var A = assetById(ws, rel.a), B = assetById(ws, rel.b);
      if (!A || !B || A.archived || B.archived) return;
      issues.push(rel.type === 'contains'
        ? { type: 'parentChild', a: rel.a, b: rel.b, text: A.name + ' sudah mencakup ' + B.name + '. Keduanya tidak dapat dijumlahkan.' }
        : { type: 'unknown', a: rel.a, b: rel.b, text: 'Belum diketahui apakah ' + A.name + ' dan ' + B.name + ' mengukur beban yang terpisah.' });
    });
    ids.forEach(function (id) { var A = assetById(ws, id); if (A && A.altPending && A.altPending.length > 1) issues.push({ type: 'altSource', a: id, text: A.name + ' memiliki dua sumber untuk beban yang sama. Pilih sumber acuan; nilainya tidak dijumlahkan.' }); });
    return issues;
  }
  function activeSelection(ws, ids) { return (ids || ws.selection).filter(function (id) { var a = assetById(ws, id); return a && !a.archived; }); }

  function tariffAt(ws, t) { var cur = null; ws.tariffs.forEach(function (tr) { if (tr.fromMs <= t) cur = tr; }); return cur; }
  function costOfParts(ws, parts) {
    var nano = 0n, coveredMWh = 0, uncoveredMWh = 0, split = false, used = {};
    var bounds = ws.tariffs.map(function (t) { return t.fromMs; }).filter(isFinite);
    parts.forEach(function (p) {
      var cuts = [p[0]].concat(bounds.filter(function (x) { return x > p[0] && x < p[1]; }), [p[1]]);
      if (cuts.length > 2) split = true;
      for (var i = 0; i < cuts.length - 1; i++) {
        var seg = p[2] * (cuts[i + 1] - cuts[i]) / (p[1] - p[0]);
        var tr = tariffAt(ws, cuts[i]);
        if (!tr) { uncoveredMWh += seg; continue; }
        used[tr.fromMs] = tr; coveredMWh += seg;
        nano += Number.isInteger(seg) ? BigInt(seg) * BigInt(tr.mRpPerKwh) : BigInt(Math.round(seg * tr.mRpPerKwh));
      }
    });
    return { nano: nano, coveredMWh: coveredMWh, uncoveredMWh: uncoveredMWh, split: split, tariffs: Object.keys(used).map(function (k) { return used[k]; }) };
  }

  /* Site/scope summary for a committed period. Unavailable values are null with a reason, never 0. */
  function summarize(ws, q) {
    var ids = activeSelection(ws, q.assetIds);
    var issues = scopeIssues(ws, ids);
    var end = Math.min(q.endMs, ws.nowMs);
    var rows = ids.map(function (id) { var A = assetById(ws, id); var s = assetSlice(ws, A, q.startMs, q.endMs); s.asset = A; return s; });
    var anyData = rows.some(function (r) { return r.conflict ? Object.keys(r.bySource).length > 0 : r.covered.length > 0; });
    var valid = issues.length === 0;
    var total = null, parts = [];
    if (valid && anyData) { total = 0; rows.forEach(function (r) { total += r.mWh; parts = parts.concat(r.parts); }); }
    var cov = rows.filter(function (r) { return r.coverage != null; }).map(function (r) { return r.coverage; });
    var coverageMin = cov.length ? Math.min.apply(null, cov) : null;
    var concurrent = null;
    if (rows.length && end > q.startMs && !rows.some(function (r) { return r.conflict; })) {
      var inter = [[q.startMs, end]];
      rows.forEach(function (r) { var next = []; inter.forEach(function (iv) { r.covered.forEach(function (c) { var s = Math.max(iv[0], c[0]), e = Math.min(iv[1], c[1]); if (e > s) next.push([s, e]); }); }); inter = next; });
      concurrent = totalLen(inter) / (end - q.startMs);
    }
    var cost;
    if (ws.composition === 'core') cost = { available: false, reason: 'capability_disabled' };
    else if (!ws.tariffs.length) cost = { available: false, reason: 'missing_tariff' };
    else if (total == null) cost = { available: false, reason: anyData ? 'scope_conflict' : 'no_data' };
    else { cost = costOfParts(ws, parts); cost.available = cost.uncoveredMWh === 0; cost.partialTariff = cost.uncoveredMWh > 0; }
    var latest = rows.reduce(function (m, r) { return Math.max(m, r.latestEnd || 0); }, 0) || null;
    var origins = {}; rows.forEach(function (r) { Object.keys(r.origins).forEach(function (o) { origins[o] = true; }); });
    return {
      window: { startMs: q.startMs, endMs: q.endMs, effectiveEndMs: end, elapsedMs: Math.max(0, end - q.startMs), tz: ws.site.tz, clipped: end < q.endMs },
      assetIds: ids, excluded: ws.assets.filter(function (a) { return ids.indexOf(a.id) < 0; }).map(function (a) { return { id: a.id, name: a.name, reason: a.archived ? 'Diarsipkan' : 'Tidak dipilih dalam cakupan' }; }),
      issues: issues, scopeValid: valid, hasData: anyData, totalMWh: total, rows: rows,
      coverageMin: coverageMin, concurrentCoverage: concurrent, allocated: rows.some(function (r) { return r.allocated; }),
      cost: cost, latestMs: latest, origins: Object.keys(origins), revision: ws.revision
    };
  }
  function ranking(summary) {
    return summary.rows.filter(function (r) { return !r.conflict && r.covered.length; })
      .map(function (r) { return { id: r.asset.id, name: r.asset.name, mWh: r.mWh, coverage: r.coverage }; })
      .sort(function (x, y) { return y.mWh - x.mWh || (x.name < y.name ? -1 : x.name > y.name ? 1 : 0) || (x.id < y.id ? -1 : 1); });
  }

  /* Daily (or hourly for a one-day period) buckets from the same slices. null = no valid data in the bucket. */
  function history(ws, q) {
    var tz = ws.site.tz, ids = activeSelection(ws, q.assetIds), points = [];
    var oneDay = q.endMs - q.startMs <= DAY;
    var step = oneDay ? HOUR : DAY;
    for (var t = q.startMs; t < q.endMs; t += step) {
      if (t >= ws.nowMs) { points.push({ startMs: t, endMs: t + step, mWh: null, future: true, coverage: null, ref: null }); continue; }
      var sum = 0, covered = 0, el = 0, any = false;
      ids.forEach(function (id) { var s = assetSlice(ws, assetById(ws, id), t, t + step); if (s.conflict) return; if (s.covered.length) { any = true; sum += s.mWh; } covered += totalLen(s.covered); el += s.elapsed; });
      var refs = [1, 2, 3].map(function (k) {
        var tot = 0, ok = true; ids.forEach(function (id) { var s = assetSlice(ws, assetById(ws, id), t - k * WEEK, t + step - k * WEEK); if (s.conflict || !s.covered.length || s.coverage < 0.9) ok = false; else tot += s.mWh; });
        return ok ? tot : null;
      }).filter(function (v) { return v != null; });
      points.push({ startMs: t, endMs: t + step, mWh: any ? sum : null, coverage: el ? covered / el : null, ref: refs.length >= 2 ? median(refs) : null,
        label: oneDay ? localHHMM(t, tz) : DAYS_SHORT[weekday(t, tz)] + ' ' + Number(localDate(t, tz).slice(8)) });
    }
    return points;
  }

  /* ---------------- schedules ---------------- */
  function validateWindows(windows) {
    var errors = [];
    windows.forEach(function (w, i) {
      if (!w.days || !w.days.length) errors.push({ index: i, field: 'days', message: 'Jendela ' + (i + 1) + ': pilih minimal satu hari.' });
      if (w.allDay) return;
      if (!/^\d{2}[:.]\d{2}$/.test(w.start || '') || !/^\d{2}[:.]\d{2}$/.test(w.end || '')) { errors.push({ index: i, field: 'time', message: 'Jendela ' + (i + 1) + ': isi jam mulai dan selesai.' }); return; }
      var s = hm(w.start), e = hm(w.end);
      if (s === e) errors.push({ index: i, field: 'end', message: 'Jendela ' + (i + 1) + ': jam mulai dan selesai sama. Ubah jamnya atau pilih "24 jam".' });
      else if (!w.nextDay && e < s) errors.push({ index: i, field: 'end', message: 'Jendela ' + (i + 1) + ': jam selesai lebih awal dari jam mulai. Centang "Berakhir hari berikutnya" bila jendela melewati tengah malam.' });
      else if (w.nextDay && e > s) errors.push({ index: i, field: 'end', message: 'Jendela ' + (i + 1) + ': jendela lebih dari 24 jam. Pilih "24 jam" atau ubah jam selesai.' });
    });
    return errors;
  }
  function expandWindows(windows, a, b, tz) {
    var out = [], d0 = localDate(a - DAY, tz), n = Math.ceil((b - a) / DAY) + 3;
    for (var i = 0; i < n; i++) {
      var iso = addDays(d0, i), m = localMidnight(iso, tz), wd = weekday(m, tz);
      windows.forEach(function (w) {
        if (w.days.indexOf(wd) < 0) return;
        if (w.allDay) out.push([m, m + DAY]);
        else out.push([m + hm(w.start), m + hm(w.end) + (w.nextDay ? DAY : 0)]);
      });
    }
    return unionIntervals(out);
  }
  function describeWindow(w) {
    var days = w.days.slice().sort().map(function (d) { return DAYS[d]; });
    var dayText = days.length === 7 ? 'Setiap hari' : days.length > 2 && w.days.slice().sort().every(function (d, i, arr) { return i === 0 || d === arr[i - 1] + 1; }) ? days[0] + '–' + days[days.length - 1] : days.join(', ');
    if (w.allDay) return dayText + ' · 24 jam';
    var s = w.start.replace(':', '.'), e = w.end.replace(':', '.');
    if (w.nextDay) return dayText + ' ' + s + ' → hari berikutnya ' + e + ' (dihitung pada hari mulai)';
    return dayText + ' ' + s + '–' + e;
  }
  /* Effective expected use: continuous override > asset schedule > site schedule > unspecified. */
  function effectiveSchedule(ws, asset, t) {
    if (asset.scheduleMode === 'continuous') return { mode: 'continuous', label: 'Diharapkan terus menyala' };
    if (asset.scheduleMode === 'none') return { mode: 'none', label: 'Tanpa jadwal (pewarisan dimatikan)' };
    if (asset.scheduleMode === 'custom') return asset.customWindows.length ? { mode: 'windows', windows: asset.customWindows, versionId: 'asset:' + asset.id + ':' + fnv(JSON.stringify(asset.customWindows)), label: 'Jadwal khusus perangkat' } : { mode: 'unspecified', label: 'Jadwal khusus belum diisi' };
    var v = null; ws.schedules.forEach(function (s) { if (s.fromMs <= t) v = s; });
    return v ? { mode: 'windows', windows: v.windows, versionId: v.id, label: 'Ikut jadwal lokasi (' + v.label + ')' } : { mode: 'unspecified', label: 'Jadwal belum diatur' };
  }
  function outsideSplit(windows, a, b, tz, parts) {
    var iv = expandWindows(windows, a, b, tz), inside = 0, outside = 0, estimated = false;
    parts.forEach(function (p) {
      var dur = p[1] - p[0], ins = overlapLen(iv, p[0], p[1]);
      if (ins > 0 && ins < dur) estimated = true;
      var inE = p[2] * ins / dur; inside += inE; outside += p[2] - inE;
    });
    return { inside: inside, outside: outside, estimated: estimated };
  }

  /* ---------------- matched baseline and insights ---------------- */
  function slots(ws, asset, a, b, windows) {
    var map = {}, dur = 0, rs = index(ws).byAsset[asset.id] || [];
    var iv = windows ? expandWindows(windows, a, b, ws.site.tz) : null;
    for (var i = lowerBound(rs, a); i < rs.length; i++) {
      var r = rs[i]; if (r.t0 >= b) break;
      if (r.t1 > b || r.t1 > ws.nowMs || !bound(asset, r)) continue;
      var src = sourceById(ws, r.s);
      var o = { mWh: r.mWh, dur: r.t1 - r.t0, res: src && src.resolutionMWh != null ? src.resolutionMWh : null };
      if (iv) o.outside = r.mWh * (o.dur - overlapLen(iv, r.t0, r.t1)) / o.dur;
      map[(r.t0 - a) + ':' + o.dur] = o; dur += o.dur;
    }
    return { map: map, coverage: (b - a) > 0 ? dur / (b - a) : 0 };
  }
  var RULE_TEXT = 'Kenaikan dihitung bila C − B > 0 dan C − B ≥ maks(30% × B; 3 × MAD; 5 × r).';
  function compareAsset(ws, asset, a, b, kind) {
    var tz = ws.site.tz, el = Math.min(b, ws.nowMs) - a;
    if (el <= 0) return { state: 'unavailable', reason: 'Periode ini belum memiliki waktu yang sudah berlalu.' };
    if (el > WEEK) return { state: 'unavailable', reason: 'Belum dapat dibandingkan: pilih periode paling lama 7 hari.' };
    if (asset.altPending && asset.altPending.length > 1) return { state: 'unavailable', reason: 'Belum dapat dibandingkan: sumber acuan belum dipilih.' };
    var end = a + el, sched = null;
    if (kind === 'outside') {
      sched = effectiveSchedule(ws, asset, a);
      if (sched.mode !== 'windows') return { state: 'unavailable', reason: sched.mode === 'continuous' ? 'Diharapkan terus menyala: tidak ada pemakaian di luar jadwal.' : 'Tidak ada jadwal yang diatur.' };
      for (var k = 0; k <= 3; k++) { var sk = effectiveSchedule(ws, asset, a - k * WEEK); if (sk.versionId !== sched.versionId) return { state: 'unavailable', reason: 'Belum dapat dibandingkan: jadwal pada periode pembanding berbeda.' }; }
    }
    var win = sched ? sched.windows : null;
    var cur = slots(ws, asset, a, end, win);
    var hist = [1, 2, 3].map(function (k) { var h = slots(ws, asset, a - k * WEEK, end - k * WEEK, win); h.k = k; h.startMs = a - k * WEEK; h.endMs = end - k * WEEK; return h; });
    var eligible = hist.filter(function (h) { return h.coverage >= 0.9; });
    if (cur.coverage < 0.9) return { state: 'notComparable', reason: 'Belum dapat dibandingkan: kelengkapan data periode ini ' + fmtCoverage(cur.coverage) + ', di bawah 90%.', hist: hist, cur: cur };
    if (eligible.length < 2) return { state: 'learning', reason: 'Belum cukup periode pembanding: perlu minimal 2 dari 3 minggu sebelumnya dengan kelengkapan data ≥ 90%; tersedia ' + eligible.length + '.', hist: hist, cur: cur };
    var keys = Object.keys(cur.map).filter(function (key) { return eligible.every(function (h) { return h.map[key]; }); });
    var maskDur = keys.reduce(function (t, key) { return t + cur.map[key].dur; }, 0);
    var maskCov = maskDur / el;
    if (maskCov < 0.9) return { state: 'notComparable', reason: 'Belum dapat dibandingkan: waktu dengan data di semua periode hanya ' + fmtCoverage(maskCov) + '.', hist: hist, cur: cur };
    var field = kind === 'outside' ? 'outside' : 'mWh';
    function sumMask(m) { return keys.reduce(function (t, key) { return t + m[key][field]; }, 0); }
    function resMask(m) { var t = 0; for (var i = 0; i < keys.length; i++) { var r = m[keys[i]].res; if (r == null) return null; t += r; } return t; }
    var C = sumMask(cur.map), Hs = eligible.map(function (h) { return sumMask(h.map); });
    var B = median(Hs), MAD = median(Hs.map(function (x) { return Math.abs(x - B); }));
    var rc = resMask(cur.map), rh = eligible.map(function (h) { return resMask(h.map); });
    var r = rc == null || rh.some(function (x) { return x == null; }) ? null : Math.max.apply(null, [rc].concat(rh));
    var delta = C - B, threshold = r == null ? null : Math.max(0.3 * B, 3 * MAD, 5 * r);
    var qualifies = r != null && Math.abs(delta) > 0 && Math.abs(delta) >= threshold - 1e-9;
    var full = assetSlice(ws, asset, a, end);
    var ev = {
      kind: kind, assetId: asset.id, assetName: asset.name, startMs: a, endMs: end, elapsedMs: el, currentFullMWh: full.mWh, currentMaskMWh: C,
      historical: eligible.map(function (h, i) { return { startMs: h.startMs, endMs: h.endMs, maskMWh: Hs[i], coverage: h.coverage }; }),
      skipped: hist.filter(function (h) { return h.coverage < 0.9; }).map(function (h) { return { startMs: h.startMs, endMs: h.endMs, coverage: h.coverage }; }),
      baselineMWh: B, madMWh: MAD, resolutionMWh: r, thresholdMWh: threshold, deltaMWh: delta,
      pct: B > 0 ? fmtSignedPct(delta, B) : null, maskCoverage: maskCov, currentCoverage: cur.coverage, maskSlots: keys.length,
      schedule: sched ? sched.label + ': ' + sched.windows.map(describeWindow).join('; ') : null, policy: VERSION.policy.change, calc: VERSION.calc,
      generatedAtMs: ws.nowMs, origins: Object.keys(full.origins)
    };
    ev.revision = fnv([kind, asset.id, a, end, C, Hs.join(','), r, ev.schedule].join('|'));
    if (r == null) return { state: 'descriptive', reason: 'Resolusi sumber tidak diketahui: perbandingan hanya deskriptif, tanpa saran otomatis.', evidence: ev };
    return { state: qualifies ? (delta > 0 ? 'increase' : 'decrease') : 'noChange', evidence: ev };
  }
  function insightCopy(ev, tz) {
    var period = fmtRange(localDate(ev.startMs, tz), localDate(ev.endMs - 1, tz));
    var hist = ev.historical.map(function (h) { return fmtRange(localDate(h.startMs, tz), localDate(h.endMs - 1, tz)) + ': ' + fmtKwh(h.maskMWh); }).join('; ');
    if (ev.kind === 'outside') {
      return {
        title: 'Energi ' + ev.assetName + ' di luar jadwal ' + (ev.deltaMWh > 0 ? 'bertambah ' : 'berkurang ') + fmtKwh(Math.abs(ev.deltaMWh)),
        observed: 'Energi ' + ev.assetName + ' di luar jadwal pada ' + period + ': ' + fmtKwh(ev.currentMaskMWh) + '. Median ' + ev.historical.length + ' minggu pembanding: ' + fmtKwh(ev.baselineMWh) + '. Perubahan tercatat ' + fmtSignedKwh(ev.deltaMWh) + '.',
        pctNote: ev.pct ? 'Perubahan relatif ' + ev.pct + '.' : 'Persentase tidak tersedia karena nilai pembanding nol.',
        comparison: 'Jam yang sama pada ' + ev.historical.length + ' minggu sebelumnya (' + hist + '). ' + ev.schedule + '.',
        unknown: 'Penyebab perubahan belum diketahui. Pemakaian di luar jadwal belum tentu pemborosan dan belum tentu dapat dihindari.',
        step: 'Periksa apakah ada kegiatan yang memang memerlukan pemakaian tersebut, misalnya lembur atau pengisian tangki udara.',
        period: period
      };
    }
    var up = ev.deltaMWh > 0;
    return {
      title: ev.assetName + (up ? ' naik ' : ' turun ') + fmtKwh(Math.abs(ev.deltaMWh)) + (ev.pct ? ' (' + ev.pct + ')' : ''),
      observed: ev.assetName + ' memakai ' + fmtKwh(ev.currentMaskMWh) + ' pada ' + period + '. Median ' + ev.historical.length + ' minggu pembanding: ' + fmtKwh(ev.baselineMWh) + '. ' + (up ? 'Kenaikan' : 'Penurunan') + ' tercatat ' + fmtKwh(Math.abs(ev.deltaMWh)) + (ev.pct ? ' (' + ev.pct.replace(/^[+−]/, '') + ')' : '') + '.',
      pctNote: ev.pct ? null : 'Persentase tidak tersedia karena nilai pembanding nol.',
      comparison: 'Hari dan jam yang sama pada ' + ev.historical.length + ' minggu sebelumnya (' + hist + ').',
      unknown: 'Penyebab perubahan belum diketahui. ' + (up ? 'Kenaikan ini bukan diagnosis kerusakan.' : 'Penurunan ini bukan bukti penghematan.'),
      step: 'Periksa apakah waktu pemakaian berubah.', period: period
    };
  }
  function staleSources(ws) {
    return ws.sources.filter(function (s) { return s.transport === 'simulated_live' && s.lastCaptureMs != null && ws.nowMs - s.lastCaptureMs > 2 * s.cadenceMs; });
  }
  function evaluateInsights(ws, q) {
    var tz = ws.site.tz, out = { observations: [], notices: [], perAsset: {}, learning: 0, comparable: 0 };
    var sum = summarize(ws, q);
    if (sum.issues.length) out.notices.push({ id: 'scope', kind: 'scope', tone: 'attention', title: 'Total gabungan belum dapat dihitung', body: sum.issues.map(function (i) { return i.text; }).join(' '), action: 'scope' });
    sum.rows.forEach(function (r) {
      if (r.coverage != null && r.coverage < 0.9 && r.elapsed > 0) out.notices.push({ id: 'partial:' + r.asset.id, kind: 'partial', tone: 'attention', assetId: r.asset.id, title: 'Sebagian data belum tersedia · ' + r.asset.name,
        body: 'Kelengkapan data: ' + fmtCoverage(r.coverage) + ' periode. ' + r.gaps.slice(0, 3).map(function (g) { return 'Data ' + fmtGap(g[0], g[1], tz) + ' belum tersedia.'; }).join(' '), action: 'history' });
    });
    staleSources(ws).forEach(function (s) {
      var A = assetById(ws, s.assetId);
      out.notices.push({ id: 'stale:' + s.id, kind: 'stale', tone: 'attention', assetId: s.assetId, title: 'Data belum diperbarui · ' + (A ? A.name : s.label),
        body: 'Pembacaan terakhir ' + fmtDateTime(s.lastCaptureMs, tz) + ' (interval ' + (s.cadenceMs / HOUR) + ' jam). Ini bukan tanda perangkat mati.', action: 'source' });
    });
    activeSelection(ws, ws.assets.map(function (a) { return a.id; })).forEach(function (id) {
      var A = assetById(ws, id);
      var energy = compareAsset(ws, A, q.startMs, q.endMs, 'energy');
      var outside = ws.composition === 'core' ? { state: 'unavailable', reason: 'Analisis jadwal tidak aktif pada komposisi Inti saja.' } : compareAsset(ws, A, q.startMs, q.endMs, 'outside');
      out.perAsset[id] = { energy: energy, outside: outside };
      if (energy.state === 'learning') out.learning++;
      if (energy.evidence) out.comparable++;
      [energy, outside].forEach(function (c) {
        if (c.state !== 'increase' && c.state !== 'decrease') return;
        var ev = c.evidence, copy = insightCopy(ev, tz);
        out.observations.push({ id: (ev.kind === 'outside' ? 'out:' : 'chg:') + id + ':' + localDate(ev.startMs, tz), revision: ev.revision, kind: ev.kind, direction: c.state, assetId: id, evidence: ev, copy: copy });
      });
    });
    out.observations.sort(function (x, y) { return y.evidence.deltaMWh - x.evidence.deltaMWh || y.evidence.endMs - x.evidence.endMs || (x.id < y.id ? -1 : 1); });
    return out;
  }
  function feedbackState(ws, obs) {
    var f = ws.feedback[obs.id];
    if (!f) return { visible: true };
    var superseded = f.revision !== obs.revision;
    if (superseded) return { visible: true, superseded: true, previous: f };
    if (f.action === 'hide') return { visible: false, hidden: true, f: f };
    if (f.action === 'snooze' && ws.nowMs < f.untilMs) return { visible: false, snoozed: true, f: f };
    return { visible: true, f: f };
  }

  /* ---------------- optional output metric ---------------- */
  function computeMetric(ws, def) {
    if (ws.composition === 'core') return { ok: false, reason: 'Metrik keluaran tidak aktif pada komposisi Inti saja.' };
    if (!def || !def.assetIds || !def.assetIds.length) return { ok: false, reason: 'Pilih perangkat pembilang.' };
    var tz = ws.site.tz, b = periodBounds({ start: def.periodStart, end: def.periodEnd }, tz);
    var completeEnd = Math.min(b.end, localMidnight(localDate(ws.nowMs, tz), tz));
    var partialDay = ws.nowMs < b.end && ws.nowMs > completeEnd;
    var sum = summarize(ws, { startMs: b.start, endMs: b.end, assetIds: def.assetIds });
    if (!sum.scopeValid) return { ok: false, reason: 'Cakupan pembilang tumpang tindih. Pilih perangkat yang tidak saling mencakup.' };
    if (sum.totalMWh == null) return { ok: false, reason: 'Belum ada data energi untuk pembilang pada periode ini.' };
    var energy = sum.totalMWh, output, method = def.method, note = [];
    if (method === 'actual') {
      output = def.quantity;
      if (output == null || !isFinite(output)) return { ok: false, field: 'quantity', reason: 'Isi jumlah keluaran aktual untuk periode yang sama.' };
      if (output < 0) return { ok: false, field: 'quantity', reason: 'Jumlah keluaran tidak boleh negatif.' };
      if (output === 0) return { ok: false, field: 'quantity', reason: 'Tidak dapat dihitung: keluaran nol.' };
      if (partialDay) note.push('Periode masih berjalan: keluaran aktual harus mencakup periode yang sama sampai ' + localHHMM(ws.nowMs, tz) + '.');
    } else {
      var per = def.perDay;
      if (per == null || !isFinite(per) || per <= 0) return { ok: false, field: 'perDay', reason: per === 0 ? 'Tidak dapat dihitung: keluaran nol.' : 'Isi rata-rata keluaran per hari produksi (lebih dari 0).' };
      var days = [], d = def.periodStart;
      while (d <= def.periodEnd) { var m = localMidnight(d, tz); if (m + DAY <= ws.nowMs && (def.outputDays || [0, 1, 2, 3, 4, 5]).indexOf(weekday(m, tz)) >= 0) days.push(d); d = addDays(d, 1); }
      output = per * days.length;
      var partialOut = 0;
      if (partialDay) {
        if (def.uniformConfirmed && def.outputWindows && def.outputWindows.length) {
          var iv = expandWindows(def.outputWindows, completeEnd, completeEnd + DAY, tz), total = overlapLen(iv, completeEnd, completeEnd + DAY);
          if (total > 0) { partialOut = per * overlapLen(iv, completeEnd, ws.nowMs) / total; output += partialOut; note.push('Hari berjalan dihitung ' + fmtCoverage(overlapLen(iv, completeEnd, ws.nowMs) / total) + ' dari jendela keluaran, dengan anggapan keluaran merata yang Anda konfirmasi.'); }
        } else {
          var cs = summarize(ws, { startMs: b.start, endMs: completeEnd, assetIds: def.assetIds });
          energy = cs.totalMWh; note.push('Hanya hari lengkap yang dihitung; energi hari berjalan tidak dibagi dengan keluaran sehari penuh.');
        }
      }
      if (!output) return { ok: false, reason: 'Belum ada hari produksi lengkap pada periode ini. Isi keluaran aktual untuk periode berjalan.' };
      note.push('Estimasi: ' + group(String(per)) + ' ' + def.unit + ' per hari produksi × ' + days.length + ' hari' + (partialOut ? ' + hari berjalan' : '') + '.');
    }
    if (sum.coverageMin != null && sum.coverageMin < 1) note.push('Sementara: energi pembilang belum lengkap (' + fmtCoverage(sum.coverageMin) + ').');
    return { ok: true, energyMWh: energy, output: output, unit: def.unit, method: method, intensity: energy / 1e6 / output, provisional: sum.coverageMin < 1, notes: note,
      periodLabel: fmtRange(def.periodStart, def.periodEnd) };
  }

  /* ---------------- composition / capability manifest ---------------- */
  var COMPOSITIONS = {
    full: { id: 'hd-core-plus-optional', version: 1, capabilities: ['core', 'cost', 'schedule', 'output'], label: 'Inti + analisis opsional' },
    core: { id: 'hd-core-only', version: 1, capabilities: ['core'], label: 'Inti saja' }
  };
  var KNOWN_CAPS = ['core', 'cost', 'schedule', 'output'];
  function validateComposition(caps) {
    var bad = caps.filter(function (c) { return KNOWN_CAPS.indexOf(c) < 0; });
    if (bad.length) return { ok: false, reason: 'Kemampuan tidak didukung: ' + bad.join(', ') };
    if (caps.indexOf('core') < 0) return { ok: false, reason: 'Inti pengukuran, cakupan, kualitas dan bukti wajib ada.' };
    return { ok: true };
  }
  function manifest(ws) {
    var c = COMPOSITIONS[ws.composition];
    return { schema_version: 1, source_release: VERSION.source_release, composition: { id: c.id, version: c.version }, capabilities: c.capabilities,
      adapters: [{ id: 'demo', status: 'simulated' }, { id: 'csv', status: 'implemented (browser simulation)' }, { id: 'shelly-plug-pm-gen3', status: 'planned' }, { id: 'tp-link', status: 'planned' }],
      policies: VERSION.policy, calc: VERSION.calc };
  }
  function requireCap(ws, cap) {
    if (COMPOSITIONS[ws.composition].capabilities.indexOf(cap) < 0) throw err('capability_disabled', 'Kemampuan "' + cap + '" tidak aktif pada komposisi ' + COMPOSITIONS[ws.composition].label + '. Data energi tidak berubah.');
  }

  /* ---------------- CSV parsing and preview ---------------- */
  var LIMITS = { bytes: 10 * 1024 * 1024, rows: 150000, nameLength: 60, maxInvalidShare: 0.2 };
  var ALIASES = {
    ts: ['timestamp', 'waktu', 'tanggal', 'datetime', 'time'], start: ['interval_start'], end: ['interval_end'],
    asset: ['asset', 'perangkat', 'mesin', 'device', 'nama', 'alat'], wh: ['energy_wh', 'energi_wh', 'wh', 'energi'],
    w: ['average_power_w', 'daya_w', 'watt', 'daya', 'power_w'], cum: ['cumulative_wh'], source: ['source', 'sumber', 'source_id']
  };
  function tokenize(text, delim) {
    var recs = [], fields = [], quoted = [], f = '', q = false, inQ = false, line = 1, recLine = 1, i = 0;
    function endField() { fields.push(f); quoted.push(q); f = ''; q = false; }
    function endRec() { endField(); recs.push({ line: recLine, fields: fields, quoted: quoted }); fields = []; quoted = []; recLine = line; }
    for (; i < text.length; i++) {
      var c = text[i];
      if (inQ) {
        if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else inQ = false; }
        else { if (c === '\n') line++; f += c; }
      } else if (c === '"' && f === '') { inQ = true; q = true; }
      else if (c === delim) endField();
      else if (c === '\r') { if (text[i + 1] === '\n') i++; line++; endRec(); }
      else if (c === '\n') { line++; endRec(); }
      else f += c;
    }
    if (inQ) return { error: 'Tanda kutip tidak ditutup mulai baris file ' + recLine + '.' };
    if (f !== '' || fields.length) endRec();
    return { recs: recs };
  }
  function detectDelimiter(text) {
    var first = text.split(/\r?\n/).filter(function (l) { return l.trim() !== ''; })[0] || '';
    var stripped = first.replace(/"[^"]*"/g, '');
    var c = (stripped.match(/,/g) || []).length, s = (stripped.match(/;/g) || []).length;
    if (c && s) return { error: 'Pemisah kolom ambigu: header memakai koma dan titik koma. Gunakan salah satu, misalnya "timestamp;perangkat;energi_wh".' };
    if (!c && !s) return { error: 'Header hanya memiliki satu kolom. Pisahkan kolom dengan koma atau titik koma.' };
    return { delim: s ? ';' : ',' };
  }
  function parseDecimal(raw, delim, quoted) {
    var s = (raw || '').trim();
    if (s === '') return { empty: true };
    if (delim === ';') {
      if (/^-?\d{1,3}(\.\d{3})+(,\d+)?$/.test(s)) s = s.replace(/\./g, '').replace(',', '.');
      else if (/^-?\d+(,\d+)?$/.test(s)) s = s.replace(',', '.');
      else if (/^-?\d+\.\d+$/.test(s)) return { error: 'angka "' + raw.trim() + '" ambigu pada berkas titik koma. Gunakan koma desimal, misalnya 12,5.' };
      else return { error: '"' + raw.trim() + '" bukan angka.' };
    } else {
      if (quoted && /^-?\d+,\d+$/.test(s)) s = s.replace(',', '.');
      else if (!/^-?\d+(\.\d+)?$/.test(s)) return { error: /^-?\d+,\d+$/.test(s) ? 'koma desimal pada berkas berpemisah koma harus diberi tanda kutip, misalnya "12,5".' : '"' + raw.trim() + '" bukan angka.' };
    }
    var neg = s[0] === '-'; if (neg) s = s.slice(1);
    var p = s.split('.'), dec = p[1] || '';
    if (dec.length > 3) return { error: 'gunakan paling banyak 3 angka desimal.' };
    var milli = Number(p[0]) * 1000 + Number((dec + '000').slice(0, 3));
    if (!isFinite(milli)) return { error: 'angka tidak terhingga tidak diterima.' };
    return { milli: neg ? -milli : milli };
  }
  function parseTime(str, tz) {
    var m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2})[:.](\d{2})(?:[:.](\d{2}))?(?:\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})?$/.exec((str || '').trim());
    if (!m) return { error: 'format waktu tidak dikenali. Gunakan 2026-10-20 00:00 atau 2026-10-20T00:00:00+07:00.' };
    var y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5], s = +(m[6] || 0);
    var dim = new Date(Date.UTC(y, mo, 0)).getUTCDate();
    if (mo < 1 || mo > 12 || d < 1 || d > dim || h > 23 || mi > 59 || s > 59) return { error: 'tanggal atau jam tidak ada (' + str.trim() + ').' };
    var offMs, naive = !m[7];
    if (naive) offMs = off(tz);
    else if (m[7] === 'Z') offMs = 0;
    else { var o = m[7].replace(':', ''); offMs = (o[0] === '-' ? -1 : 1) * (+o.slice(1, 3) * HOUR + +o.slice(3, 5) * MIN); }
    return { ms: Date.UTC(y, mo - 1, d, h, mi, s) - offMs, naive: naive };
  }
  function byteLength(text) { return typeof TextEncoder !== 'undefined' ? new TextEncoder().encode(text).length : text.length; }

  function parseCsv(text, fileName) {
    var out = { ok: false, fileName: fileName || 'tempelan.csv', errors: [], textHash: fnv(text || ''), text: text };
    if (!text || !text.trim()) { out.errors.push({ id: 'csv-input', message: 'Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.' }); return out; }
    var bytes = byteLength(text);
    if (bytes > LIMITS.bytes) { out.errors.push({ id: 'csv-input', message: 'Ukuran ' + (Math.round(bytes / 1048576 * 10) / 10).toString().replace('.', ',') + ' MiB melebihi batas 10 MiB.' }); return out; }
    if (text.charCodeAt(0) === 0xFEFF) { text = text.slice(1); out.bom = true; }
    var dd = detectDelimiter(text);
    if (dd.error) { out.errors.push({ id: 'csv-input', message: dd.error }); return out; }
    out.delimiter = dd.delim;
    var tk = tokenize(text, dd.delim);
    if (tk.error) { out.errors.push({ id: 'csv-input', message: tk.error }); return out; }
    var recs = tk.recs.filter(function (r) { return !(r.fields.length === 1 && r.fields[0].trim() === ''); });
    out.blankLines = tk.recs.length - recs.length;
    var header = recs.shift();
    if (!header) { out.errors.push({ id: 'csv-input', message: 'Header tidak ditemukan.' }); return out; }
    out.headerLine = header.line;
    out.headers = header.fields.map(function (h) { return h.trim(); });
    var cols = {}, ignored = [];
    out.headers.forEach(function (h, i) {
      var key = h.toLowerCase(), role = null;
      Object.keys(ALIASES).forEach(function (r) { if (ALIASES[r].indexOf(key) >= 0) role = r; });
      if (!role) { ignored.push(h); return; }
      if (cols[role] != null) { out.errors.push({ id: 'csv-input', message: 'Kolom "' + out.headers[cols[role]] + '" dan "' + h + '" memiliki arti yang sama. Hapus salah satunya.' }); return; }
      cols[role] = i;
    });
    out.columns = cols; out.ignored = ignored;
    if (cols.asset == null) out.errors.push({ id: 'csv-input', message: 'Kolom perangkat tidak ditemukan. Gunakan header asset, perangkat, mesin, device, nama atau alat.' });
    if (cols.ts == null && (cols.start == null || cols.end == null)) out.errors.push({ id: 'csv-input', message: 'Kolom waktu tidak ditemukan. Gunakan timestamp (atau waktu/tanggal) atau pasangan interval_start dan interval_end.' });
    if (cols.wh == null && cols.w == null && cols.cum == null) out.errors.push({ id: 'csv-input', message: 'Kolom nilai tidak ditemukan. Gunakan energy_wh/energi_wh, average_power_w/daya_w, atau cumulative_wh.' });
    if (cols.cum != null && cols.ts == null) out.errors.push({ id: 'csv-input', message: 'Kolom cumulative_wh memerlukan kolom timestamp titik waktu.' });
    if (recs.length > LIMITS.rows) out.errors.push({ id: 'csv-input', message: recs.length + ' baris data melebihi batas 150.000 baris.' });
    if (!recs.length) out.errors.push({ id: 'csv-input', message: 'Tidak ada baris data setelah header.' });
    if (out.errors.length) return out;
    out.records = recs; out.totalRows = recs.length;
    out.valueKinds = ['wh', 'w', 'cum'].filter(function (k) { return cols[k] != null; });
    var names = {}, naive = false, perName = {};
    recs.forEach(function (r) {
      var n = (r.fields[cols.asset] || '').trim(); if (n) { names[n] = true; }
      var t = cols.ts != null ? r.fields[cols.ts] : r.fields[cols.start];
      if (t && /^\s*\d{4}-\d{2}-\d{2}[ T]\d{2}[:.]\d{2}([:.]\d{2})?(\.\d+)?\s*$/.test(t)) naive = true;
      if (n && cols.ts != null) { var pt = parseTime(t, 'Asia/Jakarta'); if (pt.ms != null) { var key = ((cols.source != null ? (r.fields[cols.source] || '').trim() : '') || n).toLowerCase(); (perName[key] = perName[key] || []).push(pt.ms); } }
    });
    out.assetNames = Object.keys(names); out.naive = naive;
    out.cadence = {};
    Object.keys(perName).forEach(function (k) { out.cadence[k] = inferCadence(perName[k]); });
    out.ok = true;
    return out;
  }
  function inferCadence(times) {
    var t = times.slice().sort(function (a, b) { return a - b; }), gaps = [];
    for (var i = 1; i < t.length; i++) if (t[i] > t[i - 1]) gaps.push(t[i] - t[i - 1]);
    if (!gaps.length) return null;
    var m = median(gaps), agree = gaps.filter(function (g) { return Math.abs(g - m) <= 1000; }).length;
    return agree / gaps.length >= 0.9 ? m : null;
  }
  function defaultMapping(ws, parsed) {
    var assetMap = {};
    parsed.assetNames.forEach(function (n) {
      var same = ws.assets.filter(function (a) { return a.name.toLowerCase() === n.toLowerCase() && !a.archived; });
      assetMap[n] = same.length === 1 ? same[0].id : same.length > 1 ? '' : 'new';
    });
    return { valueKind: parsed.valueKinds.length === 1 ? parsed.valueKinds[0] : '', powerMeaning: '', tz: ws.site.tz, tzConfirmed: !parsed.naive,
      intervalMinutes: '', assetMap: assetMap, scope: '' };
  }
  function sourceKeyFor(parsed, r) { var n = (r.fields[parsed.columns.asset] || '').trim(); return ((parsed.columns.source != null ? (r.fields[parsed.columns.source] || '').trim() : '') || n).toLowerCase(); }
  function mappingIssues(ws, parsed, mp) {
    var issues = [], cols = parsed.columns;
    if (!mp.valueKind) issues.push({ id: 'map-kind', message: 'Berkas memiliki lebih dari satu kolom nilai. Pilih satu jenis nilai; nilai energi dan daya tidak dijumlahkan.' });
    if (mp.valueKind === 'w' && mp.powerMeaning !== 'average') issues.push({ id: 'map-power', message: mp.powerMeaning === 'instant' ? 'Daya sesaat tidak dapat diubah menjadi energi. Impor diblokir; gunakan data energi interval atau daya rata-rata interval.' : 'Konfirmasi arti kolom daya: rata-rata selama interval atau daya sesaat.' });
    if (parsed.naive && !mp.tzConfirmed) issues.push({ id: 'map-tz', message: 'Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai ' + mp.tz + '.' });
    var explicit = mp.intervalMinutes !== '' && mp.intervalMinutes != null;
    if (explicit && !(+mp.intervalMinutes > 0 && +mp.intervalMinutes <= 1440 && Number.isInteger(+mp.intervalMinutes))) issues.push({ id: 'map-interval', message: 'Panjang interval harus bilangan bulat 1–1440 menit.' });
    if (cols.ts != null && mp.valueKind !== 'cum' && !explicit) {
      var missing = Object.keys(parsed.cadence).filter(function (k) { return !parsed.cadence[k]; });
      if (missing.length) issues.push({ id: 'map-interval', message: 'Interval tidak dapat disimpulkan untuk: ' + missing.join(', ') + ' (satu baris atau jarak tidak teratur). Isi panjang interval.' });
    }
    if (!mp.scope) issues.push({ id: 'map-scope', message: 'Pilih apakah beban perangkat dalam berkas ini terukur terpisah.' });
    parsed.assetNames.forEach(function (n, i) {
      var target = mp.assetMap[n];
      if (n.length > LIMITS.nameLength) return;
      if (!target) issues.push({ id: 'map-asset-' + i, message: 'Ada lebih dari satu perangkat bernama "' + n + '". Pilih perangkat yang dimaksud atau buat baru.' });
      else if (target !== 'new') {
        var A = assetById(ws, target);
        var key = 'src-csv-' + fnv(n.toLowerCase());
        if (A && A.bindings.some(function (b) { return b.sourceId !== key && (index(ws).bySource[b.sourceId] || []).length; }))
          issues.push({ id: 'map-asset-' + i, message: A.name + ' sudah memiliki sumber lain. Sumber ganda untuk satu beban tidak dijumlahkan; pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.' });
      }
    });
    return issues;
  }
  function buildPreview(ws, parsed, mp) {
    var issues = mappingIssues(ws, parsed, mp);
    var cols = parsed.columns, tz = mp.tz || ws.site.tz;
    var stored = {}; ws.readings.forEach(function (r) { stored[r.s + '|' + r.t0 + '|' + r.t1] = r.mWh; });
    var rows = [], errors = [];
    var explicitMs = mp.intervalMinutes !== '' && mp.intervalMinutes != null ? +mp.intervalMinutes * MIN : null;
    function bad(r, n, col, msg) { errors.push({ id: 'row-' + n, dataRow: n, fileLine: r.line, field: col, message: 'Baris data ' + n + (r.line !== n + parsed.headerLine ? ' (baris file ' + r.line + ')' : '') + ', ' + col + ': ' + msg }); return null; }
    var vcol = mp.valueKind === 'cum' ? cols.cum : mp.valueKind === 'w' ? cols.w : cols.wh;
    var vname = vcol != null ? parsed.headers[vcol] : '';
    var points = {};
    parsed.records.forEach(function (r, i) {
      var n = i + 1, f = r.fields;
      if (f.length !== parsed.headers.length) return rows.push(bad(r, n, 'baris', 'jumlah kolom ' + f.length + ' tidak sama dengan header (' + parsed.headers.length + ').' + (parsed.delimiter === ',' ? ' Koma desimal harus diberi tanda kutip, misalnya "12,5".' : '')));
      var name = (f[cols.asset] || '').trim();
      if (!name) return rows.push(bad(r, n, parsed.headers[cols.asset], 'nama perangkat kosong.'));
      if (name.length > LIMITS.nameLength) return rows.push(bad(r, n, parsed.headers[cols.asset], 'nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.'));
      if (vcol == null) return rows.push({ n: n, pending: true });
      var t0, t1;
      if (cols.ts != null) {
        var pt = parseTime(f[cols.ts], tz); if (pt.error) return rows.push(bad(r, n, parsed.headers[cols.ts], pt.error));
        t0 = pt.ms;
      } else {
        var ps = parseTime(f[cols.start], tz), pe = parseTime(f[cols.end], tz);
        if (ps.error) return rows.push(bad(r, n, parsed.headers[cols.start], ps.error));
        if (pe.error) return rows.push(bad(r, n, parsed.headers[cols.end], pe.error));
        if (pe.ms <= ps.ms) return rows.push(bad(r, n, parsed.headers[cols.end], 'akhir interval harus setelah awal interval.'));
        t0 = ps.ms; t1 = pe.ms;
      }
      var v = parseDecimal(f[vcol], parsed.delimiter, r.quoted[vcol]);
      if (v.empty) return rows.push(bad(r, n, vname, 'nilai kosong. Isi angka 0 atau lebih; kosong tidak dianggap 0.'));
      if (v.error) return rows.push(bad(r, n, vname, v.error));
      if (v.milli < 0) return rows.push(bad(r, n, vname, 'gunakan angka 0 atau lebih.'));
      var skey = sourceKeyFor(parsed, r);
      if (mp.valueKind === 'cum') { (points[skey] = points[skey] || []).push({ n: n, t: t0, milli: v.milli, name: name }); return rows.push({ n: n, counter: true }); }
      if (t1 == null) { var cad = explicitMs || parsed.cadence[skey]; if (!cad) return rows.push({ n: n, pending: true }); t1 = t0 + cad; }
      var mWh = mp.valueKind === 'w' ? Math.round(v.milli * (t1 - t0) / HOUR) : v.milli;
      rows.push({ n: n, name: name, skey: skey, t0: t0, t1: t1, mWh: mWh });
    });
    var counterNotes = [], counterReadings = [];
    Object.keys(points).forEach(function (k) {
      var ps = points[k].sort(function (a, b) { return a.t - b.t; });
      for (var i = 1; i < ps.length; i++) {
        if (ps[i].milli < ps[i - 1].milli) { counterNotes.push('Penghitung ' + ps[i].name + ' kembali ke nilai lebih kecil pada ' + fmtDateTime(ps[i].t, tz) + ': interval ' + fmtGap(ps[i - 1].t, ps[i].t, tz) + ' tidak diketahui (segmen baru).'); continue; }
        counterReadings.push({ n: ps[i].n, name: ps[i].name, skey: k, t0: ps[i - 1].t, t1: ps[i].t, mWh: ps[i].milli - ps[i - 1].milli });
      }
      counterNotes.push('Pembacaan pertama ' + ps[0].name + ' menjadi titik awal penghitung, bukan energi.');
    });
    var cand = rows.filter(function (r) { return r && r.t0 != null; }).concat(counterReadings);
    var groups = {}, accepted = [], dup = 0, conflictRows = {};
    cand.forEach(function (r) { r.sourceId = 'src-csv-' + fnv(r.skey); var key = r.sourceId + '|' + r.t0 + '|' + r.t1; (groups[key] = groups[key] || []).push(r); });
    Object.keys(groups).forEach(function (key) {
      var g = groups[key], same = g.every(function (r) { return r.mWh === g[0].mWh; });
      if (!same || (stored[key] != null && stored[key] !== g[0].mWh)) { g.forEach(function (r) { conflictRows[r.n] = true; }); return; }
      if (stored[key] != null) { dup += g.length; return; }
      accepted.push(g[0]); dup += g.length - 1;
    });
    var invalid = rows.filter(function (r) { return r === null; }).length;
    var pending = rows.filter(function (r) { return r && r.pending; }).length;
    var conflicts = Object.keys(conflictRows).length;
    var counterAnchors = mp.valueKind === 'cum' ? parsed.totalRows - invalid - counterReadings.length : 0;
    var total = parsed.totalRows;
    var acceptedRows = mp.valueKind === 'cum' ? total - invalid - dup - conflicts : accepted.length;
    var blockReasons = [];
    if (issues.length || pending) blockReasons.push('Lengkapi pemetaan terlebih dahulu.');
    var maxInvalid = Math.floor(total * LIMITS.maxInvalidShare + 1e-9);
    if (invalid > maxInvalid) blockReasons.push('Impor diblokir: ' + invalid + ' dari ' + total + ' baris tidak valid.');
    if (conflicts) blockReasons.push('Nilai berbeda ditemukan untuk sumber dan interval yang sama. Pilih sumber atau perbaiki data sebelum melanjutkan.');
    if (!accepted.length && !dup && !blockReasons.length) blockReasons.push('Tidak ada baris valid yang dapat diimpor.');
    var minT = Infinity, maxT = -Infinity; accepted.forEach(function (r) { minT = Math.min(minT, r.t0); maxT = Math.max(maxT, r.t1); });
    var assumptions = [];
    if (cols.ts != null && mp.valueKind !== 'cum') assumptions.push('Timestamp adalah awal interval; setiap baris mencakup ' + (explicitMs ? mp.intervalMinutes + ' menit (diisi)' : 'interval yang disimpulkan per sumber') + ', termasuk baris terakhir. Jeda panjang tetap menjadi data kosong.');
    if (parsed.naive) assumptions.push('Waktu tanpa offset dibaca sebagai ' + tz + '.');
    if (mp.valueKind === 'w') assumptions.push('Daya rata-rata interval × durasi = energi (100 W selama 30 menit = 50 Wh).');
    if (parsed.bom) assumptions.push('BOM UTF-8 dilewati.');
    assumptions.push('Pemisah kolom: ' + (parsed.delimiter === ';' ? 'titik koma; koma sebagai desimal.' : 'koma; titik sebagai desimal, koma desimal hanya dalam tanda kutip.'));
    if (parsed.ignored.length) assumptions.push('Kolom tidak dipakai: ' + parsed.ignored.join(', ') + '.');
    if (parsed.blankLines) assumptions.push(parsed.blankLines + ' baris kosong tidak dihitung sebagai baris data.');
    counterNotes.forEach(function (c) { assumptions.push(c); });
    var mapping = [['Perangkat', parsed.headers[cols.asset]], ['Waktu', cols.ts != null ? parsed.headers[cols.ts] + ' (awal interval)' : parsed.headers[cols.start] + ' → ' + parsed.headers[cols.end]], ['Nilai', vname + (mp.valueKind === 'w' ? ' (W rata-rata)' : mp.valueKind === 'cum' ? ' (Wh kumulatif)' : ' (Wh interval)')], ['Zona waktu', tz]];
    parsed.assetNames.forEach(function (nm) { var t = mp.assetMap[nm]; mapping.push(['"' + nm + '"', t === 'new' ? 'Perangkat baru' : t ? 'Perangkat ada: ' + (assetById(ws, t) || {}).name : 'Belum dipilih']); });
    var opKey = 'imp-' + fnv(parsed.textHash + JSON.stringify(mp));
    return {
      opKey: opKey, fileName: parsed.fileName, totalRows: total, accepted: acceptedRows, acceptedReadings: accepted, invalid: invalid, duplicates: dup, conflicts: conflicts,
      counterAnchors: counterAnchors, pending: pending, errors: errors, mappingIssues: issues, blocked: blockReasons.length > 0, blockReasons: blockReasons,
      needsAck: invalid > 0 && blockReasons.length === 0, assumptions: assumptions, mapping: mapping, scope: mp.scope,
      periodStartIso: isFinite(minT) ? localDate(minT, tz) : null, periodEndIso: isFinite(maxT) ? localDate(maxT - 1, tz) : null, assetMap: mp.assetMap, intervalNote: explicitMs
    };
  }
  /* Atomic apply: everything is computed on copies, then assigned at once. */
  function applyImport(ws, pv) {
    var assets = ws.assets.slice(), sources = ws.sources.slice(), readings = ws.readings.slice(), selection = ws.selection.slice(), relations = ws.relations.slice();
    var created = [], mapped = [], nameToAsset = {};
    Object.keys(pv.assetMap).forEach(function (nm) {
      var t = pv.assetMap[nm], A;
      if (t === 'new') {
        A = { id: 'asset-imp-' + fnv(nm.toLowerCase() + pv.opKey), name: nm, kind: 'device', category: '', location: '', profile: 'unknown', scheduleMode: 'inherit', customWindows: [], archived: false, bindings: [], altPending: null };
        assets.push(A); selection.push(A.id); created.push(nm);
      } else { A = assets.filter(function (a) { return a.id === t; })[0]; mapped.push(A.name); }
      nameToAsset[nm.toLowerCase()] = A;
    });
    pv.acceptedReadings.forEach(function (r) {
      var A = nameToAsset[r.name.toLowerCase()];
      if (!sources.some(function (s) { return s.id === r.sourceId; })) sources.push({ id: r.sourceId, assetId: A.id, label: 'Impor CSV · ' + pv.fileName, origin: 'import', kind: 'interval_energy', cadenceMs: r.t1 - r.t0, resolutionMWh: null, transport: 'none', status: 'historical', lastCaptureMs: null });
      if (!A.bindings.some(function (b) { return b.sourceId === r.sourceId; })) A.bindings = A.bindings.concat([{ sourceId: r.sourceId, fromMs: -Infinity, toMs: null }]);
      readings.push({ s: r.sourceId, a: A.id, t0: r.t0, t1: r.t1, mWh: r.mWh });
    });
    if (pv.scope === 'unknown') created.forEach(function (nm) {
      var A = nameToAsset[nm.toLowerCase()];
      selection.forEach(function (id) { if (id !== A.id && !relations.some(function (x) { return (x.a === id && x.b === A.id) || (x.a === A.id && x.b === id); })) relations.push({ a: id, b: A.id, type: 'unknown' }); });
    });
    var result = { opKey: pv.opKey, status: 'committed', added: pv.acceptedReadings.length, acceptedRows: pv.accepted, skippedInvalid: pv.invalid, duplicates: pv.duplicates, assetsCreated: created, assetsMapped: mapped,
      periodStartIso: pv.periodStartIso, periodEndIso: pv.periodEndIso, fileName: pv.fileName, committedAtMs: ws.nowMs };
    ws.assets = assets; ws.sources = sources; ws.readings = readings; ws.selection = selection; ws.relations = relations;
    ws.operations[pv.opKey] = result; ws.audit.push({ at: ws.nowMs, what: 'Impor ' + pv.fileName, detail: result.added + ' interval ditambahkan' }); ws.revision++;
    if (ws.mode === 'local' && ws.site.context === 'unspecified') ws.scenarioName = 'Ruang kerja lokal';
    return result;
  }

  /* ---------------- mock backend ("Backend simulasi") ---------------- */
  var DELAY = { value: 500 };
  function mock(ws, op, cap, fn) {
    return new Promise(function (resolve, reject) {
      setTimeout(function () {
        try {
          if (ws.client.offline) throw err('offline', 'Anda sedang offline. Perubahan belum dikirim; draf tetap tersimpan.');
          if (cap) requireCap(ws, cap);
          var fail = ws.failNext[op]; if (fail) delete ws.failNext[op];
          if (fail === 'expired') throw err('session_expired', 'Sesi berakhir. Layanan tersimpan belum tersedia di prototipe ini; draf tetap ada. Coba lagi secara eksplisit.');
          if (fail === 'reject') throw err('rejected', op === 'import' ? 'Impor belum dikonfirmasi. Data tersimpan sebelumnya tetap tersedia.' : 'Penyimpanan ditolak server simulasi. Nilai sebelumnya tetap berlaku; draf tetap ada.');
          var result = fn();
          if (fail === 'interrupt') throw err('unknown', op === 'import' ? 'Hasil impor belum diketahui. Periksa status sebelum mencoba lagi.' : 'Status penyimpanan belum diketahui. Periksa status sebelum mencoba lagi.');
          resolve(result);
        } catch (e) { reject(e); }
      }, DELAY.value);
    });
  }
  var api = {
    commitImport: function (ws, pv) {
      return mock(ws, 'import', null, function () {
        if (ws.operations[pv.opKey]) return Object.assign({ replayed: true }, ws.operations[pv.opKey]);
        if (pv.blocked) throw err('blocked', pv.blockReasons.join(' '));
        return applyImport(ws, pv);
      });
    },
    checkOperation: function (ws, opKey) {
      return new Promise(function (resolve, reject) { setTimeout(function () { if (ws.client.offline) return reject(err('offline', 'Tidak dapat memeriksa status: Anda sedang offline.')); resolve(ws.operations[opKey] || { opKey: opKey, status: 'not_found' }); }, DELAY.value); });
    },
    saveSettings: function (ws, d) {
      var caps = [];
      if (d.tariffs !== undefined) caps.push('cost');
      if (d.schedules !== undefined) caps.push('schedule');
      return mock(ws, 'settings', null, function () {
        caps.forEach(function (c) { requireCap(ws, c); });
        if (d.tariffs) d.tariffs.forEach(function (t) { if (!(t.mRpPerKwh >= 0) || !isFinite(t.mRpPerKwh)) throw err('invalid', 'Tarif harus angka 0 atau lebih.'); });
        if (d.schedules) d.schedules.forEach(function (s) { if (validateWindows(s.windows).length) throw err('invalid', 'Jadwal tidak valid.'); });
        if (d.site && d.site.tz && !TZ[d.site.tz]) throw err('invalid', 'Zona waktu tidak didukung.');
        if (d.site) ws.site = Object.assign({}, ws.site, d.site);
        if (d.tariffs !== undefined) ws.tariffs = d.tariffs;
        if (d.schedules !== undefined) ws.schedules = d.schedules;
        if (d.notifications) ws.notifications = d.notifications;
        ws.audit.push({ at: ws.nowMs, what: 'Pengaturan disimpan', detail: Object.keys(d).join(', ') }); ws.revision++;
        return { ok: true, revision: ws.revision };
      });
    },
    saveAsset: function (ws, id, patch) {
      return mock(ws, 'asset', patch.scheduleMode === 'custom' ? 'schedule' : null, function () {
        if (patch.name != null && (!patch.name.trim() || patch.name.length > 60)) throw err('invalid', 'Nama wajib diisi, paling banyak 60 karakter.');
        if (patch.customWindows && validateWindows(patch.customWindows).length) throw err('invalid', 'Jadwal khusus tidak valid.');
        ws.assets = ws.assets.map(function (a) { return a.id === id ? Object.assign({}, a, patch) : a; });
        ws.audit.push({ at: ws.nowMs, what: 'Perangkat diperbarui', detail: id }); ws.revision++;
        return assetById(ws, id);
      });
    },
    saveScope: function (ws, d) {
      return mock(ws, 'scope', null, function () {
        var issues = scopeIssues(Object.assign({}, ws, { relations: d.relations, assets: d.assets || ws.assets }), d.selection);
        if (issues.length) throw err('invalid', 'Cakupan masih tumpang tindih: ' + issues.map(function (i) { return i.text; }).join(' '));
        if (!d.selection.length) throw err('invalid', 'Pilih minimal satu perangkat.');
        ws.selection = d.selection.slice(); ws.relations = d.relations.slice(); if (d.assets) ws.assets = d.assets;
        ws.audit.push({ at: ws.nowMs, what: 'Cakupan disimpan', detail: d.selection.join(', ') }); ws.revision++;
        return { ok: true };
      });
    },
    saveFeedback: function (ws, obs, action) {
      return mock(ws, 'feedback', null, function () {
        var tz = ws.site.tz;
        if (action === 'restore') delete ws.feedback[obs.id];
        else ws.feedback[obs.id] = { action: action, revision: obs.revision, atMs: ws.nowMs, untilMs: action === 'snooze' ? localMidnight(addDays(localDate(ws.nowMs, tz), 1), tz) : null };
        return { ok: true, feedback: ws.feedback[obs.id] || null };
      });
    },
    saveMetric: function (ws, def) {
      return mock(ws, 'metric', 'output', function () {
        var m = computeMetric(ws, def); if (!m.ok) throw err('invalid', m.reason);
        ws.metric = Object.assign({}, def, { enabled: true }); ws.revision++; return m;
      });
    },
    disableMetric: function (ws) { return mock(ws, 'metric', null, function () { if (ws.metric) ws.metric = Object.assign({}, ws.metric, { enabled: false }); ws.revision++; return { ok: true }; }); },
    firstReading: function (ws, opKey) {
      return mock(ws, 'source', null, function () { return { opKey: opKey, t0: ws.nowMs - HOUR, t1: ws.nowMs, mWh: 50000, label: 'Simulasi koneksi' }; });
    },
    saveSource: function (ws, d) {
      return mock(ws, 'source', null, function () {
        if (ws.operations[d.opKey]) return Object.assign({ replayed: true }, ws.operations[d.opKey]);
        if (!d.name || !d.name.trim() || d.name.length > 60) throw err('invalid', 'Nama wajib diisi, paling banyak 60 karakter.');
        var A;
        if (d.assetId === 'new') {
          A = { id: 'asset-src-' + fnv(d.opKey), name: d.name.trim(), kind: d.kind, category: d.category || '', location: d.location || '', profile: 'unknown', scheduleMode: 'inherit', customWindows: [], archived: false, bindings: [], altPending: null };
          ws.assets = ws.assets.concat([A]); ws.selection = ws.selection.concat([A.id]);
          ws.selection.forEach(function (id) { if (id !== A.id) ws.relations.push({ a: id, b: A.id, type: 'unknown' }); });
        } else A = assetById(ws, d.assetId);
        var src = { id: 'src-sim-' + fnv(d.opKey), assetId: A.id, label: 'Simulasi koneksi · ' + d.name.trim(), origin: 'simulated', kind: 'interval_energy', cadenceMs: HOUR, resolutionMWh: 1000, transport: 'simulated_live', status: 'simulated', lastCaptureMs: d.reading.t1 };
        ws.sources = ws.sources.concat([src]);
        A.bindings = A.bindings.concat([{ sourceId: src.id, fromMs: d.effectiveFromMs, toMs: null }]);
        if (d.assetId !== 'new') A.bindings.forEach(function (b) { if (b.sourceId !== src.id && b.toMs == null) b.toMs = d.effectiveFromMs; });
        ws.readings = ws.readings.concat([{ s: src.id, a: A.id, t0: d.reading.t0, t1: d.reading.t1, mWh: d.reading.mWh }]);
        var result = { opKey: d.opKey, assetId: A.id, sourceId: src.id };
        ws.operations[d.opKey] = result; ws.revision++; return result;
      });
    },
    refresh: function (ws) {
      return new Promise(function (resolve, reject) { setTimeout(function () { if (ws.client.offline) return reject(err('offline', 'Data belum dapat dimuat: Anda sedang offline. Menampilkan data tersimpan.')); ws.client.cachedAtMs = ws.nowMs; resolve({ revision: ws.revision, newReadings: 0 }); }, DELAY.value); });
    },
    checkSource: function (ws, sourceId) {
      return new Promise(function (resolve, reject) { setTimeout(function () {
        if (ws.client.offline) return reject(err('offline', 'Tidak dapat memeriksa sumber: perangkat Anda offline.'));
        var s = sourceById(ws, sourceId); resolve({ lastCaptureMs: s.lastCaptureMs, newReadings: 0, message: 'Belum ada pembacaan baru dari sumber simulasi. Pembacaan terakhir tetap ' + fmtDateTime(s.lastCaptureMs, ws.site.tz) + '.' });
      }, DELAY.value); });
    }
  };

  return {
    VERSION: VERSION, HOUR: HOUR, DAY: DAY, WEEK: WEEK, NOW_MAIN: NOW_MAIN, NOW_CURRENT: NOW_CURRENT, FIX_START: FIX_START, LIMITS: LIMITS, TZ: TZ, TZ_LABEL: TZ_LABEL,
    DAYS: DAYS, KIND_LABEL: KIND_LABEL, CONTEXT_LABEL: CONTEXT_LABEL, SCENARIOS: SCENARIOS, COMPOSITIONS: COMPOSITIONS, RULE_TEXT: RULE_TEXT, DELAY: DELAY, SYNTHETIC_TARIFF: SYNTHETIC_TARIFF,
    localMidnight: localMidnight, localDate: localDate, localHHMM: localHHMM, weekday: weekday, addDays: addDays, periodBounds: periodBounds,
    fmtKwh: fmtKwh, fmtSignedKwh: fmtSignedKwh, fmtRp: fmtRp, fmtRpPlain: fmtRpPlain, nanoToRp: nanoToRp, fmtTariff: fmtTariff, fmtPct: fmtPct, fmtSignedPct: fmtSignedPct,
    fmtDate: fmtDate, fmtRange: fmtRange, fmtDateTime: fmtDateTime, fmtGap: fmtGap, fmtCoverage: fmtCoverage,
    emptyWorkspace: emptyWorkspace, buildScenario: buildScenario, assetById: assetById, sourceById: sourceById, index: index,
    assetSlice: assetSlice, summarize: summarize, ranking: ranking, history: history, scopeIssues: scopeIssues, activeSelection: activeSelection, costOfParts: costOfParts,
    validateWindows: validateWindows, expandWindows: expandWindows, describeWindow: describeWindow, effectiveSchedule: effectiveSchedule, outsideSplit: outsideSplit,
    compareAsset: compareAsset, evaluateInsights: evaluateInsights, insightCopy: insightCopy, feedbackState: feedbackState, staleSources: staleSources,
    computeMetric: computeMetric, manifest: manifest, validateComposition: validateComposition, requireCap: requireCap,
    parseCsv: parseCsv, parseDecimal: parseDecimal, parseTime: parseTime, inferCadence: inferCadence, defaultMapping: defaultMapping, buildPreview: buildPreview, applyImport: applyImport,
    api: api, median: median, fnv: fnv
  };
});
