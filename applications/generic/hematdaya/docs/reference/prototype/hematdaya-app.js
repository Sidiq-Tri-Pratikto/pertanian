/* HematDaya interactive prototype - one stateful app composed from HematDaya Design System 1.0.0-draft (window.HD).
   Every number comes from window.HematDomain (the accepted-data authority); this file only lays out screens S01-S12.
   Exposes window.HematDayaApp.App for the Design canvas (x-import) and the standalone test page. */
(function () {
  'use strict';
  var React = window.React, h = React.createElement, Fragment = React.Fragment;
  var useState = React.useState, useRef = React.useRef, useEffect = React.useEffect;
  var HD = window.HD, D = window.HematDomain;

  /* ---------------- small building blocks ---------------- */
  function Btn(variant, label, onClick, extra) { return h(HD.Button, Object.assign({ variant: variant, onClick: onClick }, extra || {}), label); }
  function P(text, cls, key) { return h('p', { className: cls || 'type-body', key: key }, text); }
  function Row() { return h.apply(null, ['div', { className: 'hd-row' }].concat([].slice.call(arguments))); }
  function Group() { return h.apply(null, ['div', { className: 'hd-group hd-stack' }].concat([].slice.call(arguments))); }
  function Section(title, children, id) {
    return h('section', { className: 'hd-stack', 'aria-labelledby': id }, h('h2', { id: id, className: 'type-section' }, title), children);
  }
  function KV(pairs) { return h('dl', { className: 'hd-kv type-label' }, pairs.map(function (p, i) { return h(Fragment, { key: i }, h('dt', null, p[0]), h('dd', null, p[1])); })); }
  var ORIGIN = { simulated: 'Simulasi', import: 'Impor CSV', dataset_replay: 'Putar ulang dataset', live: 'Langsung' };
  function provOf(ws) { return ws.mode === 'demo' ? 'demo' : ws.readings.length ? 'import' : undefined; }
  function kwh(m) { return m == null ? null : m / 1e6; }
  function opState(st, key) { return st.ops[key] || { state: null }; }

  var EXAMPLES = function (ctx) {
    var a = ctx === 'industry' || ctx === 'business' ? ['Mesin Jahit', 'Lampu Gudang'] : ['Lampu Teras', 'Dispenser'];
    function hourly(name, from, n, v) { var out = []; for (var i = 0; i < n; i++) out.push('2026-10-20 ' + String(from + i).padStart(2, '0') + ':00,' + name + ',' + (typeof v === 'function' ? v(i) : v)); return out; }
    return [
      { id: 'valid', label: 'Valid: dua perangkat, interval 1 jam', file: 'contoh-valid.csv', text: ['timestamp,perangkat,energi_wh'].concat(hourly(a[0], 6, 6, 40), hourly(a[1], 18, 6, 15)).join('\n') + '\n' },
      { id: 'two', label: '2 dari 10 baris tidak valid', file: 'contoh-2-salah.csv', text: ['timestamp,perangkat,energi_wh'].concat(hourly('Router Kantor', 0, 10, function (i) { return i === 3 ? 'dua' : i === 6 ? '-5' : '10'; })).join('\n') + '\n' },
      { id: 'three', label: '3 dari 10 baris tidak valid (diblokir)', file: 'contoh-3-salah.csv', text: ['timestamp,perangkat,energi_wh'].concat(hourly('Router Kantor', 0, 10, function (i) { return i === 1 || i === 4 ? '-1' : i === 7 ? '' : '10'; })).join('\n') + '\n' },
      { id: 'conflict', label: 'Nilai berbeda pada interval yang sama', file: 'contoh-konflik.csv', text: 'timestamp,perangkat,energi_wh\n2026-10-20 00:00,Pompa Sumur,120\n2026-10-20 01:00,Pompa Sumur,0\n2026-10-20 00:00,Pompa Sumur,150\n2026-10-20 02:00,Pompa Sumur,0\n' },
      { id: 'semi', label: 'Titik koma, koma desimal, nama berkutip', file: 'contoh-titik-koma.csv', text: '﻿waktu;alat;wh\n2026-10-20 07:00;"Lampu; Gudang";12,5\n2026-10-20 08:00;"Lampu; Gudang";12,5\n2026-10-20 09:00;"Lampu; Gudang";1.250,5\n' },
      { id: 'power', label: 'Daya rata-rata (power_w) dengan interval eksplisit', file: 'contoh-daya.csv', text: 'interval_start,interval_end,asset,power_w\n2026-10-20T08:00:00+07:00,2026-10-20T08:30:00+07:00,Pompa Air,100\n2026-10-20T08:30:00+07:00,2026-10-20T09:00:00+07:00,Pompa Air,0\n' },
      { id: 'counter', label: 'Penghitung kumulatif dengan reset', file: 'contoh-penghitung.csv', text: 'timestamp,perangkat,cumulative_wh\n2026-10-20 00:00,Mesin Cuci,100\n2026-10-20 01:00,Mesin Cuci,130\n2026-10-20 02:00,Mesin Cuci,5\n' },
      { id: 'one', label: 'Satu baris (interval wajib diisi)', file: 'contoh-satu-baris.csv', text: 'timestamp,asset,energy_wh\n2026-10-20 10:00,Pemanas Air,450\n' }
    ];
  };

  /* ---------------- the app ---------------- */
  function App(props) {
    var tick = useState(0);
    var S = useRef(null);
    if (!S.current) S.current = { wsKey: null, ws: { demo: null, local: null }, route: null, period: null, drafts: {}, ops: {}, flash: null, sheet: null,
      welcome: { context: 'unspecified', demoChoice: null }, prefs: { largeText: false, reduceMotion: false }, view: {}, cache: {} };
    var st = S.current;
    var scrollRef = useRef(null);
    function render() { tick[1](function (x) { return x + 1; }); }
    function upd(fn) { fn(st); render(); }
    var ws = st.wsKey ? st.ws[st.wsKey] : null;

    /* navigation: one stack per tab; detail routes push onto the current tab */
    function top() { var s = st.route.stacks[st.route.tab], e = s[s.length - 1]; if (!e.params) e.params = {}; return e; }
    var useHist = !!(props && props.history);
    function pop() { var s = st.route.stacks[st.route.tab]; if (s.length > 1) s.pop(); st.restoreScroll = true; }
    function popRoute() { if (useHist) { st.keepFlash = true; } if (useHist) setTimeout(function () { try { history.back(); } catch (e) { upd(pop); } }); else pop(); }
    useEffect(function () {
      if (!useHist) return undefined;
      function onPop() { if (st.route) upd(function () { if (!st.keepFlash) st.flash = null; st.keepFlash = false; st.sheet = null; pop(); }); }
      window.addEventListener('popstate', onPop);
      return function () { window.removeEventListener('popstate', onPop); };
    }, []);
    function push(name, params) { if (useHist) { try { history.pushState({ hd: true }, ''); } catch (e) { /* sandboxed frame: visible back only */ } } upd(function () { st.flash = null; var s = st.route.stacks[st.route.tab]; s[s.length - 1].scrollTop = scrollRef.current ? scrollRef.current.scrollTop : 0; s.push({ name: name, params: params || {} }); }); }
    function back() { if (useHist && history.state && history.state.hd) { history.back(); return; } upd(function () { st.flash = null; pop(); }); }
    function replace(name, params) { upd(function () { var s = st.route.stacks[st.route.tab]; s[s.length - 1] = { name: name, params: params || {} }; }); }
    function goTab(tab) { upd(function () { st.flash = null; if (st.route.tab === tab) st.route.stacks[tab].splice(1); st.route.tab = tab; st.restoreScroll = true; }); }
    function freshRoute() { return { tab: 'beranda', stacks: { beranda: [{ name: 'home' }], perangkat: [{ name: 'assets' }], saran: [{ name: 'saran' }] } }; }
    function openWorkspace(key, w) {
      st.ws[key] = w; st.wsKey = key; st.period = Object.assign({}, w.initialPeriod); st.route = freshRoute(); st.drafts = {}; st.ops = {}; st.flash = null; st.cache = {};
    }

    var routeKey = st.wsKey ? st.wsKey + ':' + st.route.tab + ':' + st.route.stacks[st.route.tab].length + ':' + top().name + ':' + (top().params.id || '') : 'welcome';
    useEffect(function () {
      var el = scrollRef.current; if (!el) return;
      var entry = st.wsKey ? top() : null;
      if (st.restoreScroll && entry && entry.scrollTop != null) el.scrollTop = entry.scrollTop; else el.scrollTop = 0;
      st.restoreScroll = false;
      var h1 = el.querySelector('h1'); if (h1) { h1.setAttribute('tabindex', '-1'); try { h1.focus({ preventScroll: true }); } catch (e) { h1.focus(); } }
    }, [routeKey]);
    useEffect(function () {
      var root = document.documentElement;
      root.classList.toggle('hd-large-text', !!st.prefs.largeText);
      if (scrollRef.current) scrollRef.current.classList.toggle('hd-reduce-motion', !!st.prefs.reduceMotion);
    });

    /* async operation wrapper: pending -> success | failure | unknown, status stays inspectable */
    function run(key, promise, onOk, onFail) {
      upd(function () { st.ops[key] = { state: 'saving' }; });
      return promise.then(function (res) { upd(function () { st.ops[key] = { state: 'success', result: res }; if (onOk) onOk(res); }); return res; },
        function (e) { upd(function () { st.ops[key] = { state: e.code === 'unknown' ? 'unknown' : 'failure', message: e.message, code: e.code }; if (onFail) onFail(e); }); });
    }

    /* ------------ derived data from the one authority, cached per revision ------------ */
    function derived() {
      var b = D.periodBounds(st.period, ws.site.tz);
      var key = [st.wsKey, ws.revision, ws.composition, ws.nowMs, ws.site.tz, st.period.start, st.period.end, ws.selection.join(',')].join('|');
      if (st.cache.key === key) return st.cache;
      var q = { startMs: b.start, endMs: b.end };
      var sum = D.summarize(ws, q);
      st.cache = { key: key, q: q, sum: sum, rank: D.ranking(sum), ins: D.evaluateInsights(ws, q) };
      return st.cache;
    }
    function periodLabel() {
      var lbl = D.fmtRange(st.period.start, st.period.end);
      var b = D.periodBounds(st.period, ws.site.tz);
      if (b.end > ws.nowMs && b.start < ws.nowMs) lbl += ' · sampai ' + D.localHHMM(ws.nowMs, ws.site.tz) + ' (berjalan)';
      return lbl;
    }
    function today() { return D.localDate(ws.nowMs, ws.site.tz); }
    function setPeriod(p) { upd(function () { st.period = { preset: p.preset, start: p.start, end: p.end }; }); }
    function dataRange(assetIds) {
      var ids = assetIds || ws.selection, min = Infinity, max = -Infinity;
      ws.readings.forEach(function (r) { if (ids.indexOf(r.a) >= 0 && r.t1 <= ws.nowMs) { min = Math.min(min, r.t0); max = Math.max(max, r.t1); } });
      if (!isFinite(min)) return null;
      var end = D.localDate(max - 1, ws.site.tz), start = D.addDays(end, -6), first = D.localDate(min, ws.site.tz);
      return { preset: 'range', start: start < first ? first : start, end: end };
    }
    function viewDataPeriod(assetIds) { var r = dataRange(assetIds); if (r) setPeriod(r); }

    /* ------------ shared pieces ------------ */
    function SettingsLink() { return Row(Btn('text', 'Pengaturan', function () { push('settings'); }), ws.mode === 'demo' ? Btn('text', 'Tentang demo', function () { push('demo'); }) : null); }
    function PeriodBlock(compact) {
      var open = st.view.periodOpen || !compact;
      return h('div', { className: 'hd-stack hd-stack--tight' },
        compact && h(Fragment, null, P('Periode: ' + periodLabel() + ' · ' + ws.site.tz, 'type-label-strong'),
          Btn('text', open ? 'Tutup pilihan periode' : 'Ubah periode', function () { upd(function () { st.view.periodOpen = !open; }); }, { icon: 'calendar' })),
        open && h(HD.PeriodSelector, { value: st.period, today: today(), timezone: ws.site.tz, onCommit: setPeriod }),
        open && Row(Btn('text', 'Minggu ini (Senin sampai sekarang)', function () {
          var t = today(), wd = D.weekday(ws.nowMs, ws.site.tz); setPeriod({ preset: 'range', start: D.addDays(t, -wd), end: t });
        })),
        P('Waktu ' + (ws.mode === 'demo' ? 'virtual demo' : 'perangkat') + ': ' + D.DAYS[D.weekday(ws.nowMs, ws.site.tz)] + ', ' + D.fmtDateTime(ws.nowMs, ws.site.tz) + ' ' + ws.site.tz + '. Batas periode memakai hari lokal.', 'type-label hd-secondary'));
    }
    function scopeLabel(sum) { return 'Cakupan pengukuran: ' + sum.assetIds.length + ' perangkat'; }
    function costBlock(sum, onSet) {
      var c = sum.cost;
      if (c.reason === 'capability_disabled') return h(HD.Notice, { tone: 'neutral', title: 'Estimasi biaya tidak aktif' }, 'Komposisi Inti saja tidak memuat modul biaya. Energi tetap dihitung sama.');
      var single = ws.tariffs.length === 1 && c.available && !c.split;
      var detail = h(HD.Disclosure, { summary: 'Detail biaya' }, KV([
        ['Tarif', ws.tariffs.length ? ws.tariffs.map(function (t) { return D.fmtTariff(t.mRpPerKwh) + (isFinite(t.fromMs) ? ' mulai ' + D.fmtDateTime(t.fromMs, ws.site.tz) : ' untuk seluruh data') + ' · ' + (t.source === 'synthetic' ? 'tarif simulasi, bukan tarif PLN' : 'diisi pengguna'); }).join('; ') : 'Belum diatur'],
        ['Energi yang dihitung', c.coveredMWh != null ? D.fmtKwh(c.coveredMWh) + (c.uncoveredMWh ? ' · ' + D.fmtKwh(c.uncoveredMWh) + ' tanpa tarif' : '') : '—'],
        ['Cara hitung', 'Jumlah energi tiap interval × tarif yang berlaku pada interval itu; dibulatkan sekali untuk tampilan.' + (c.split ? ' Interval yang melewati perubahan tarif dibagi proporsional (estimasi).' : '')],
        ['Batasan', 'Estimasi ini tidak sama dengan tagihan listrik. Pajak, biaya beban, daya reaktif dan komponen tagihan lain tidak termasuk.']]));
      if (single || c.reason === 'missing_tariff' || c.reason === 'no_data' || c.reason === 'scope_conflict')
        return h('div', { className: 'hd-stack hd-stack--tight' }, h(HD.CostEstimate, { kwh: c.reason === 'scope_conflict' || c.reason === 'no_data' ? null : kwh(sum.totalMWh), tariff: single ? ws.tariffs[0].mRpPerKwh / 1000 : null,
          tariffSource: single && ws.tariffs[0].source === 'synthetic' ? 'synthetic' : 'user', partial: sum.coverageMin != null && sum.coverageMin < 1, onSetTariff: onSet }), ws.tariffs.length ? detail : null);
      return h('section', { className: 'hd-stack hd-stack--tight', 'aria-label': 'Estimasi biaya energi terpantau' },
        P('Estimasi biaya energi terpantau', 'type-label-strong'),
        P(c.available ? D.fmtRp(c.nano) : 'Biaya sebagian: ' + D.fmtRp(c.nano), 'type-title hd-num'),
        c.split && P('Tarif berubah dalam periode ini; biaya dihitung per interval.', 'type-label'),
        c.partialTariff && P('Biaya hanya untuk ' + D.fmtKwh(c.coveredMWh) + '; ' + D.fmtKwh(c.uncoveredMWh) + ' berada sebelum tarif pertama berlaku.', 'hd-qualifier type-label-strong'),
        P('Estimasi ini tidak sama dengan tagihan listrik.', 'type-label hd-secondary'), detail);
    }
    function qualityBlock(sum, assetIds) {
      var tz = ws.site.tz;
      var stale = D.staleSources(ws).filter(function (s) { return (assetIds || sum.assetIds).indexOf(s.assetId) >= 0; });
      var origins = sum.origins;
      var gaps = [];
      sum.rows.forEach(function (r) { r.gaps.slice(0, 2).forEach(function (g) { gaps.push((sum.rows.length > 1 ? r.asset.name + ' ' : '') + D.fmtGap(g[0], g[1], tz)); }); });
      var range = dataRange(assetIds || sum.assetIds);
      var fresh = stale.length ? { state: 'stale', lastMeasurement: D.fmtDateTime(stale[0].lastCaptureMs, tz) + ' (' + stale[0].label + ')' }
        : origins.indexOf('import') >= 0 ? { state: 'historical', importRange: range ? D.fmtRange(D.localDate(firstReading(assetIds || sum.assetIds), tz), range.end) : '' }
        : sum.latestMs ? { state: 'fresh', lastMeasurement: D.fmtDateTime(sum.latestMs, tz) + (origins.indexOf('simulated') >= 0 ? ' (data simulasi)' : '') } : null;
      return h(HD.DataQuality, { completeness: sum.coverageMin, gaps: gaps.length ? gaps.join('; ') : undefined, freshness: fresh || undefined,
        client: ws.client.offline ? 'offline' : 'online', cachedAge: ws.client.cachedAtMs ? 'tersimpan ' + D.fmtDateTime(ws.client.cachedAtMs, tz) : '',
        source: origins.indexOf('import') >= 0 ? 'import' : origins.length ? 'demo' : undefined,
        onCheckSource: stale.length ? function () { run('check:' + stale[0].id, D.api.checkSource(ws, stale[0].id)); } : undefined,
        checkingSource: stale.length ? opState(st, 'check:' + stale[0].id).state === 'saving' : false,
        onViewPeriod: range ? function () { viewDataPeriod(assetIds); } : undefined });
    }
    function firstReading(ids) { var m = Infinity; ws.readings.forEach(function (r) { if (ids.indexOf(r.a) >= 0) m = Math.min(m, r.t0); }); return m; }
    function checkStatus(key) {
      var o = st.ops[key]; if (!o || !o.state || o.state === 'saving') return null;
      return h(HD.ProgressStatus, { state: o.state === 'success' ? null : o.state, label: o.state === 'failure' ? 'Belum berhasil' : undefined, detail: o.result && o.result.message || o.message });
    }
    function flashBlock() {
      if (!st.flash) return null;
      var f = st.flash;
      return h(HD.Notice, { tone: f.tone || 'success', title: f.title, live: true, action: f.action ? Btn('text', f.action.label, f.action.onClick) : null }, f.body);
    }

    var exploredKey = 'hematdaya.welcome.explored.v1';
    function rememberExploration() {
      try { window.localStorage.setItem(exploredKey, 'true'); } catch (e) { /* continue when browser storage is unavailable */ }
    }
    function openEmptyHome() {
      var local = st.ws.local || D.emptyWorkspace('local');
      local.nowMs = Date.now();
      local.site.context = st.welcome.context;
      var date = D.localDate(local.nowMs, local.site.tz);
      local.initialPeriod = { preset: 'last7', start: D.addDays(date, -7), end: D.addDays(date, -1) };
      openWorkspace('local', local);
    }
    useEffect(function () {
      var explored = false;
      try { explored = window.localStorage.getItem(exploredKey) === 'true'; } catch (e) { /* show Welcome */ }
      if (explored && !st.wsKey) upd(openEmptyHome);
    }, []);

    /* ======================= S01 Welcome ======================= */
    function Welcome() {
      var w = st.welcome;
      function open(kind) {
        upd(function () { st.ops.demo = { state: 'loading' }; });
        setTimeout(function () {
          try { rememberExploration(); var nw = D.buildScenario(kind === 'industry' ? 'i-base' : 'h-base'); upd(function () { st.ops.demo = { state: null }; st.sheet = null; openWorkspace('demo', nw); }); }
          catch (e) { upd(function () { st.ops.demo = { state: 'failure', message: e.message }; }); }
        }, 300);
      }
      var demoDefault = w.context === 'industry' || w.context === 'business' ? 'industry' : 'household';
      return h(Fragment, null,
        h(HD.Screen, { title: 'Selamat datang' },
          P('Lihat pemakaian listrik dan apa yang berubah.', 'type-section'),
          P('Coba dengan data contoh. HematDaya hanya membaca data, tanpa mengendalikan perangkat.', 'type-body'),
          h('div', { className: 'hd-stack hd-stack--tight' },
            Btn('primary', 'Coba demo', function () { upd(function () { st.sheet = 'demo'; w.demoChoice = w.demoChoice || demoDefault; }); }, { fullWidth: true }),
            Btn('secondary', 'Lanjut tanpa data', function () { rememberExploration(); upd(openEmptyHome); }, { fullWidth: true }))),
        DemoSheet(open));
    }
    function DemoSheet(open) {
      var w = st.welcome, o = opState(st, 'demo');
      return h(HD.SheetDialog, { open: st.sheet === 'demo', title: 'Pilih data demo', onClose: function () { upd(function () { st.sheet = null; }); },
        footer: h(Fragment, null, Btn('primary', 'Buka demo', function () { open(w.demoChoice || 'household'); }, { loading: o.state === 'loading', loadingLabel: 'Menyiapkan data demo…', fullWidth: true }),
          Btn('text', 'Batal', function () { upd(function () { st.sheet = null; }); }, { fullWidth: true })) },
        h('div', { className: 'hd-stack' },
          h(HD.ChoiceGroup, { legend: 'Data simulasi', value: w.demoChoice || 'household', onChange: function (v) { upd(function () { w.demoChoice = v; }); }, options: [
            { value: 'household', label: 'Rumah tangga', description: 'Kulkas, Router, Pompa Air dan TV. Tanpa AC, jadwal atau data produksi.' },
            { value: 'industry', label: 'Industri', description: 'Oven, Kompresor, Mesin Press dan Lampu Area. Jadwal dan output tetap opsional.' }] }),
          P('Demo · Data simulasi. Terpisah dari data impor Anda; reset hanya memengaruhi demo.', 'type-label hd-secondary'),
          h(HD.ProgressStatus, { state: o.state === 'failure' ? 'failure' : o.state === 'loading' ? 'loading' : null, label: o.state === 'loading' ? 'Menyiapkan data demo…' : undefined, detail: o.message, onRetry: function () { open(w.demoChoice || 'household'); } })));
    }

    /* ======================= S02 / S03 Beranda ======================= */
    function Beranda() {
      if (!ws.readings.length) return Empty();
      var d = derived(), sum = d.sum, tz = ws.site.tz;
      var quality = !sum.hasData ? 'unavailable' : sum.coverageMin != null && sum.coverageMin < 1 ? 'partial' : 'complete';
      var featured = d.ins.observations.filter(function (o) { return D.feedbackState(ws, o).visible; })[0];
      var conflict = !sum.scopeValid;
      var refresh = opState(st, 'refresh');
      var metric = ws.metric && ws.metric.enabled ? D.computeMetric(ws, ws.metric) : null;
      var parentIssue = sum.issues.filter(function (i) { return i.type === 'parentChild'; })[0];
      var unknownIssue = sum.issues.filter(function (i) { return i.type === 'unknown'; })[0];
      var emptyDetail = conflict ? 'Total gabungan tidak ditampilkan karena cakupan tumpang tindih. Nilai masing-masing perangkat tetap tersedia di Perangkat.'
        : sum.window.elapsedMs === 0 ? 'Periode ini belum dimulai pada waktu ' + (ws.mode === 'demo' ? 'virtual' : 'perangkat') + ' ' + D.fmtDateTime(ws.nowMs, tz) + '. Tidak ditampilkan sebagai 0 kWh.'
        : 'Belum ada pengukuran pada periode ini. Tidak ditampilkan sebagai 0 kWh.';
      var supporting = h(Fragment, null,
        sum.scopeValid && sum.hasData && h('div', { className: 'hd-group hd-stack' },
          h(HD.ContributionRanking, { items: d.rank.map(function (r) { return { name: r.name, kwh: kwh(r.mWh) }; }), periodLabel: periodLabel(), denominatorLabel: d.rank.length + ' perangkat yang dipantau' }),
          d.rank.length && sum.totalMWh > 0 ? Btn('primary', 'Lihat perangkat terbesar', function () { push('asset', { id: d.rank[0].id }); }, { icon: 'chevronRight' }) : null,
          rankingAlt(d, sum)),
        metric && metric.ok && h('div', { className: 'hd-group' }, h(HD.OutputMetricPreview, { enabled: true, energyKwh: kwh(metric.energyMWh), output: metric.output, unit: metric.unit, method: metric.method, periodLabel: metric.periodLabel })),
        h('div', { className: 'hd-stack hd-stack--tight' },
          featured ? h(HD.InsightSummary, { kind: 'change', title: featured.copy.title, periodLabel: featured.copy.period, comparison: { eligible: true, label: 'dibanding median ' + featured.evidence.historical.length + ' minggu sebelumnya' },
            cause: 'Penyebab perubahan belum diketahui.', qualification: featured.kind === 'outside' ? 'Pemakaian di luar jadwal belum tentu pemborosan.' : undefined,
            onOpenEvidence: function () { push('insight', { id: featured.id }); }, evidenceLabel: 'Lihat dasar saran' })
            : d.ins.learning > 0 && d.ins.comparable === 0 ? h(HD.InsightSummary, { kind: 'learning', detail: 'Total terukur ' + periodLabel() + ' tetap tersedia. Perbandingan memerlukan minimal 2 minggu sebelumnya yang lengkap.' })
            : h(HD.InsightSummary, { kind: 'none', periodLabel: 'Belum ada perubahan yang memenuhi kriteria pada periode ini' }),
          Row(Btn('text', 'Lihat semua saran', function () { goTab('saran'); }, { icon: 'chevronRight' }))));
      return h(HD.Screen, { title: 'Beranda', subtitle: ws.site.name + ' · ' + tz, provenance: provOf(ws), current: 'beranda', onNavigate: goTab, aside: supporting },
        SettingsLink(), Btn('text', 'Tambah data', function () { push('import'); }), flashBlock(),
        PeriodBlock(false),
        h('div', { className: 'hd-stack hd-stack--tight' },
          h(HD.ScopeSummary, { included: sum.rows.map(function (r) { return r.asset.name; }), excluded: sum.excluded.map(function (x) { return x.name; }), overlap: unknownIssue && !parentIssue ? 'unknown' : 'none',
            values: unknownIssue && !parentIssue ? sum.rows.filter(function (r) { return !r.conflict && r.covered.length; }).map(function (r) { return { name: r.asset.name, kwh: kwh(r.mWh) }; }) : undefined }),
          parentIssue && h(HD.Notice, { tone: 'info', title: 'Ada meter yang mencakup perangkat lain' }, sum.issues.map(function (i) { return i.text; }).join(' ') + ' Pilih satu tampilan yang dapat dijumlahkan.'),
          P('Hanya mencakup sumber yang dipilih.', 'type-label hd-secondary'),
          Row(Btn('text', 'Ubah cakupan', function () { push('scope'); }, { icon: 'scope' }))),
        h('div', { className: 'hd-group hd-stack hd-stack--section' },
          conflict ? h('section', { className: 'hd-stack hd-stack--tight', 'aria-labelledby': 'conf-h' },
            h('h2', { id: 'conf-h', className: 'type-label-strong' }, 'Energi yang dipantau'),
            P(periodLabel() + ' · ' + scopeLabel(sum), 'type-label'),
            P('Total gabungan belum dapat dihitung', 'type-section'),
            P('Cakupan tumpang tindih atau sumber acuan belum dipilih, sehingga nilai tidak dijumlahkan. Nilai masing-masing perangkat tetap tersedia di Perangkat.', 'type-body'),
            Row(Btn('secondary', 'Pilih cakupan', function () { push('scope'); }, { icon: 'scope' }))) :
          h(HD.EnergyMetric, { kwh: conflict ? null : kwh(sum.totalMWh), quality: conflict ? 'unavailable' : quality, completeness: sum.coverageMin == null ? undefined : sum.coverageMin,
            gapLabel: quality === 'partial' ? firstGap(sum) : undefined, periodLabel: periodLabel(), scopeLabel: scopeLabel(sum), provenance: provOf(ws),
            emptyDetail: emptyDetail,
            emptyAction: conflict ? Btn('secondary', 'Pilih cakupan', function () { push('scope'); }, { icon: 'scope' }) : dataRange() ? Btn('secondary', 'Lihat periode data', function () { viewDataPeriod(); }, { icon: 'calendar' }) : null }),
          sum.allocated && P('Sebagian interval melewati batas periode dan dibagi proporsional (estimasi).', 'type-label'),
          conflict ? P('Estimasi biaya energi terpantau: belum dihitung karena total gabungan belum tersedia.', 'type-label') : costBlock(sum, function () { push('settings', { focus: 'tariff' }); })),
        h('div', { className: 'hd-group' }, qualityBlock(sum)),
        Row(Btn('text', 'Perbarui', function () { run('refresh', D.api.refresh(ws)); }, { icon: 'refresh', loading: refresh.state === 'saving', loadingLabel: 'Memeriksa pembaruan…' })),
        refresh.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Data belum dapat dimuat', detail: refresh.message + (ws.client.cachedAtMs ? ' Data tersimpan: ' + D.fmtDateTime(ws.client.cachedAtMs, tz) + '.' : ''), onRetry: function () { run('refresh', D.api.refresh(ws)); } }),
        refresh.state === 'success' && P('Diperbarui. Tidak ada pembacaan baru; data terkonfirmasi tetap sama.', 'type-label hd-secondary'));
    }
    function rowOf(sum, id) { return sum.rows.filter(function (r) { return r.asset.id === id; })[0] || { mWh: null }; }
    function firstGap(sum) { var g = []; sum.rows.forEach(function (r) { if (r.gaps.length) g.push(r.asset.name + ': ' + D.fmtGap(r.gaps[0][0], r.gaps[0][1], ws.site.tz)); }); return g.slice(0, 2).join('; '); }
    function rankingAlt(d, sum) {
      return h(HD.ChartDataAlternative, { caption: 'Energi per perangkat, ' + periodLabel() + ', ' + ws.site.tz, collapsed: true, toggleLabel: 'Lihat data',
        summary: d.rank.length && sum.totalMWh > 0 ? d.rank[0].name + ' mencatat energi terbesar: ' + D.fmtKwh(d.rank[0].mWh, false) + ' dari ' + D.fmtKwh(sum.totalMWh) + ' pada ' + periodLabel() + '. Angka ini hanya mencakup ' + d.rank.length + ' sumber yang dipilih.' : 'Semua perangkat mencatat 0 kWh dengan data lengkap; tidak ada persentase kontribusi.',
        columns: [{ key: 'name', label: 'Perangkat' }, { key: 'kwh', label: 'Energi', numeric: true, format: String }, { key: 'share', label: 'Porsi', numeric: true, format: String }, { key: 'cov', label: 'Kelengkapan data', numeric: true, format: String }],
        rows: d.rank.map(function (r) { return { name: r.name, kwh: D.fmtKwh(r.mWh), share: D.fmtPct(r.mWh, sum.totalMWh) || '—', cov: D.fmtCoverage(r.coverage) }; }) });
    }
    function Empty() {
      var load = opState(st, 'refresh');
      return h(Fragment, null, h(HD.Screen, { title: 'Beranda', subtitle: ws.site.name + ' · ' + ws.site.tz, current: 'beranda', onNavigate: goTab },
        SettingsLink(), flashBlock(),
        h('section', { className: 'hd-stack', 'aria-labelledby': 'empty-h' },
          h('h2', { id: 'empty-h', className: 'type-section' }, 'Belum ada data energi'),
          P('HematDaya membaca energi dari berkas CSV atau dari sumber pengukuran yang didukung. Ruang kerja ini belum memiliki sumber.'),
          Btn('primary', 'Coba demo', function () { upd(function () { st.sheet = 'demo'; st.welcome.demoChoice = st.welcome.demoChoice || (st.welcome.context === 'industry' || st.welcome.context === 'business' ? 'industry' : 'household'); }); }),
          Btn('secondary', 'Tambah data', function () { push('import'); }, { icon: 'upload' }),
          Btn('text', 'Lihat meter yang didukung', function () { push('source'); })),
        load.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Data belum dapat dimuat', detail: load.message, onRetry: function () { run('refresh', D.api.refresh(ws)); } })),
        DemoSheet(function (kind) { upd(function () { st.ops.demo = { state: 'loading' }; }); setTimeout(function () { upd(function () { st.sheet = null; st.ops.demo = { state: null }; openWorkspace('demo', D.buildScenario(kind === 'industry' ? 'i-base' : 'h-base')); }); }, 300); }));
    }

    /* ======================= S04 Perangkat ======================= */
    function Assets() {
      if (!ws.readings.length && !ws.assets.length) return h(HD.Screen, { title: 'Perangkat', current: 'perangkat', onNavigate: goTab },
        SettingsLink(), h(HD.Notice, { tone: 'neutral', title: 'Belum ada perangkat' }, 'Tambahkan data dengan impor CSV atau coba demo.'),
        Btn('secondary', 'Tambah data', function () { push('import'); }, { icon: 'upload' }), Btn('secondary', 'Tambah sumber', function () { push('source'); }));
      var d = derived(), tz = ws.site.tz;
      var active = ws.assets.filter(function (a) { return !a.archived; }), archived = ws.assets.filter(function (a) { return a.archived; });
      var rows = active.map(function (a) { var s = D.assetSlice(ws, a, d.q.startMs, d.q.endMs); return { a: a, s: s }; })
        .sort(function (x, y) { return (y.s.mWh == null ? -1 : y.s.mWh) - (x.s.mWh == null ? -1 : x.s.mWh) || (x.a.name < y.a.name ? -1 : 1) || (x.a.id < y.a.id ? -1 : 1); });
      var stale = D.staleSources(ws).map(function (s) { return s.assetId; });
      var supporting = h(Fragment, null, SettingsLink(),
        archived.length > 0 && Section('Diarsipkan', h('ul', { className: 'hd-stack hd-stack--tight' }, archived.map(function (a) {
          return h('li', { key: a.id, className: 'hd-row' }, P(a.name + ' · riwayat tetap tersimpan', 'type-body'),
            Btn('text', 'Pulihkan', function () { run('restore:' + a.id, D.api.saveAsset(ws, a.id, { archived: false })); }, { loading: opState(st, 'restore:' + a.id).state === 'saving', loadingLabel: 'Memulihkan…' }));
        })), 'arch-h'));
      return h(HD.Screen, { title: 'Perangkat', subtitle: 'Perangkat, grup, sirkuit dan meter lokasi', provenance: provOf(ws), current: 'perangkat', onNavigate: goTab, aside: supporting },
        flashBlock(), PeriodBlock(true),
        !d.sum.scopeValid && h(HD.Notice, { tone: 'attention', title: 'Total gabungan belum dapat dihitung', action: Btn('text', 'Pilih cakupan', function () { push('scope'); }) }, d.sum.issues.map(function (i) { return i.text; }).join(' ') + ' Nilai masing-masing tetap ditampilkan.'),
        Row(Btn('primary', 'Tambah sumber', function () { push('source'); }), Btn('secondary', 'Tambah data', function () { push('import'); }, { icon: 'upload' })),
        h('ul', { className: 'hd-stack hd-stack--tight', 'aria-label': 'Daftar perangkat, urut energi tercatat' }, rows.map(function (r) {
          var a = r.a, s = r.s, inScope = ws.selection.indexOf(a.id) >= 0;
          var q = s.conflict ? 'unavailable' : stale.indexOf(a.id) >= 0 ? 'stale' : !s.covered.length ? 'unavailable' : s.coverage < 1 ? 'partial' : 'complete';
          var ql = s.conflict ? 'Dua sumber · pilih sumber acuan' : q === 'stale' ? 'Data belum diperbarui' : q === 'unavailable' ? 'Belum ada data pada periode ini' : q === 'partial' ? 'Kelengkapan data: ' + D.fmtCoverage(s.coverage) + ' periode' : undefined;
          return h('li', { key: a.id }, h(HD.AssetRow, { name: a.name, kind: a.kind === 'site_total' ? 'meter' : a.kind, location: [a.location, D.KIND_LABEL[a.kind], inScope ? null : 'di luar cakupan'].filter(Boolean).join(' · '),
            kwh: s.conflict || !s.covered.length ? null : kwh(s.mWh), quality: q, qualityLabel: ql, onOpen: function () { push('asset', { id: a.id }); } }));
        })),
        P('Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat.', 'type-label hd-secondary'));
    }

    /* ======================= S05 Source setup ======================= */
    function Source() {
      var dr = st.drafts.source || (st.drafts.source = { step: 'catalog', opKey: 'src-' + Date.now().toString(36), name: '', category: '', location: '', kind: 'device', assetId: 'new' });
      function step(s) { upd(function () { dr.step = s; }); }
      var order = ['catalog', 'capability', 'connect', 'review'];
      var backTo = dr.step === 'planned' ? 'catalog' : order[order.indexOf(dr.step) - 1];
      var screenBack = { label: 'Kembali', onClick: function () { if (backTo) step(backTo); else back(); } };
      var body;
      if (dr.step === 'catalog') body = h(Fragment, null,
        P('Pilih cara data energi masuk. Hanya impor CSV dan sumber simulasi yang berfungsi pada prototipe ini.'),
        h('div', { className: 'hd-catalog' },
          catalogItem('Impor CSV', 'Tersedia · data historis dari berkas', function () { replace('import'); }),
          catalogItem('Sumber simulasi (demo)', 'Simulasi koneksi · colokan, energi per jam', function () { upd(function () { dr.provider = 'sim'; dr.step = 'capability'; }); }),
          catalogItem('Shelly Plug PM Gen3', 'Direncanakan · belum ada adaptor terverifikasi', function () { upd(function () { dr.provider = 'Shelly Plug PM Gen3'; dr.step = 'planned'; }); }),
          catalogItem('TP-Link (colokan pintar)', 'Direncanakan · belum ada adaptor terverifikasi', function () { upd(function () { dr.provider = 'TP-Link'; dr.step = 'planned'; }); })),
        P('Tidak ada kredensial yang diminta. Pemasangan pada instalasi listrik tetap dilakukan oleh tenaga yang berwenang; aplikasi tidak memberi petunjuk mengubah kabel.', 'type-label hd-secondary'));
      else if (dr.step === 'planned') body = h(Fragment, null,
        h(HD.Notice, { tone: 'info', title: 'Integrasi belum tersedia pada prototipe ini' }, dr.provider + ' masih direncanakan. Tidak ada koneksi yang dibuat dan tidak ada status "Terhubung". Draf nama dan lokasi Anda tetap tersimpan.'),
        Btn('primary', 'Impor data', function () { replace('import'); }, { icon: 'upload' }), Btn('text', 'Kembali ke katalog', function () { step('catalog'); }));
      else if (dr.step === 'capability') body = h(Fragment, null,
        KV([['Status', 'Simulasi koneksi (bukan perangkat nyata)'], ['Jenis pengukuran', 'Energi interval (Wh)'], ['Interval', '1 jam'], ['Resolusi', '1 Wh'], ['Cakupan fisik', 'Satu colokan: hanya beban yang tersambung, bukan seluruh lokasi']]),
        Btn('primary', 'Lanjut', function () { step('connect'); }));
      else if (dr.step === 'connect') {
        var o = opState(st, 'first:' + dr.opKey);
        body = h(Fragment, null,
          P('Sumber simulasi membuat satu pembacaan pertama. Pada layanan nyata, sumber hanya dikonfirmasi setelah pendaftaran terverifikasi dan pembacaan pertama yang valid.'),
          dr.reading ? h(HD.Notice, { tone: 'info', title: 'Simulasi koneksi · pembacaan pertama diterima' }, D.fmtKwh(dr.reading.mWh) + ' untuk ' + D.fmtGap(dr.reading.t0, dr.reading.t1, ws.site.tz) + '. Ini data simulasi.')
            : Btn('primary', 'Simulasikan pembacaan pertama', function () { run('first:' + dr.opKey, D.api.firstReading(ws, dr.opKey), function (r) { dr.reading = r; }); }, { loading: o.state === 'saving', loadingLabel: 'Menunggu pembacaan…' }),
          o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Pembacaan belum diterima', detail: o.message, onRetry: function () { run('first:' + dr.opKey, D.api.firstReading(ws, dr.opKey), function (r) { dr.reading = r; }); } }),
          dr.reading && Btn('primary', 'Lanjut', function () { step('review'); }));
      } else {
        var so = opState(st, 'save:' + dr.opKey), errs = [];
        if (dr.submitted && !dr.name.trim()) errs.push({ targetId: 'src-name', text: 'Isi nama sumber.' });
        if (dr.submitted && dr.name.length > 60) errs.push({ targetId: 'src-name', text: 'Nama paling banyak 60 karakter.' });
        body = h(Fragment, null,
          h(HD.ErrorSummary, { errors: errs, submitCount: dr.submitCount || 0 }),
          h(HD.TextField, { id: 'src-name', label: 'Nama', required: true, value: dr.name, onChange: function (v) { upd(function () { dr.name = v; }); }, error: errs.length ? errs[0].text : null }),
          h(HD.TextField, { label: 'Kategori', optional: true, value: dr.category, onChange: function (v) { upd(function () { dr.category = v; }); }, help: 'Kategori hanya label; tidak menentukan perilaku atau jadwal.' }),
          h(HD.TextField, { label: 'Lokasi', optional: true, value: dr.location, onChange: function (v) { upd(function () { dr.location = v; }); } }),
          h(HD.ChoiceGroup, { legend: 'Jenis cakupan', value: dr.kind, onChange: function (v) { upd(function () { dr.kind = v; }); }, options: [{ value: 'device', label: 'Perangkat' }, { value: 'group', label: 'Grup' }, { value: 'circuit', label: 'Sirkuit' }, { value: 'site_total', label: 'Meter lokasi' }] }),
          h(HD.ChoiceGroup, { type: 'select', legend: 'Hubungkan ke', value: dr.assetId, onChange: function (v) { upd(function () { dr.assetId = v; }); },
            options: [{ value: 'new', label: 'Perangkat baru' }].concat(ws.assets.filter(function (a) { return !a.archived; }).map(function (a) { return { value: a.id, label: a.name + ' · ' + D.KIND_LABEL[a.kind] + (a.location ? ' · ' + a.location : '') }; })),
            help: dr.assetId === 'new' ? 'Perangkat baru belum diketahui terpisah dari perangkat lain; tinjau di Cakupan & sumber.' : 'Sumber ini menjadi acuan mulai ' + D.fmtDateTime(ws.nowMs - D.HOUR, ws.site.tz) + '; sumber lama berhenti dipakai sejak saat itu. Riwayat lama tetap tersimpan.' }),
          P('Berlaku mulai: ' + D.fmtDateTime(ws.nowMs - D.HOUR, ws.site.tz) + ' (awal pembacaan pertama).', 'type-label'),
          Btn('primary', 'Simpan sumber simulasi', function () {
            upd(function () { dr.submitted = true; dr.submitCount = (dr.submitCount || 0) + 1; });
            if (!dr.name.trim() || dr.name.length > 60) return;
            run('save:' + dr.opKey, D.api.saveSource(ws, { opKey: dr.opKey, name: dr.name, category: dr.category, location: dr.location, kind: dr.kind, assetId: dr.assetId, effectiveFromMs: ws.nowMs - D.HOUR, reading: dr.reading }),
              function (res) { st.drafts.source = null; st.flash = { title: 'Sumber simulasi disimpan', body: 'Status: Simulasi koneksi. Ini bukan sambungan meter nyata.' }; var s = st.route.stacks[st.route.tab]; s[s.length - 1] = { name: 'asset', params: { id: res.assetId } }; });
          }, { loading: so.state === 'saving', loadingLabel: 'Menyimpan…' }),
          so.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Belum tersimpan', detail: so.message + ' Mencoba lagi memakai operasi yang sama; tidak membuat perangkat ganda.', onRetry: function () { run('save:' + dr.opKey, D.api.saveSource(ws, { opKey: dr.opKey, name: dr.name, category: dr.category, location: dr.location, kind: dr.kind, assetId: dr.assetId, effectiveFromMs: ws.nowMs - D.HOUR, reading: dr.reading }), function (res) { st.drafts.source = null; var s = st.route.stacks[st.route.tab]; s[s.length - 1] = { name: 'asset', params: { id: res.assetId } }; }); } }),
          so.state === 'unknown' && h(HD.ProgressStatus, { state: 'unknown', onCheck: function () { run('save:' + dr.opKey, D.api.saveSource(ws, { opKey: dr.opKey, reading: dr.reading }), function (res) { st.drafts.source = null; var s = st.route.stacks[st.route.tab]; s[s.length - 1] = { name: 'asset', params: { id: res.assetId } }; }); } }));
      }
      var labels = { catalog: 'Langkah 1 dari 4 · Penyedia', capability: 'Langkah 2 dari 4 · Kemampuan', connect: 'Langkah 3 dari 4 · Pembacaan pertama', review: 'Langkah 4 dari 4 · Nama dan cakupan', planned: 'Penyedia direncanakan' };
      return h(HD.Screen, { title: 'Tambah sumber', subtitle: labels[dr.step], back: screenBack, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        body, Btn('text', 'Tutup', function () { back(); }));
    }
    function catalogItem(title, desc, onClick) { return h(HD.Button, { variant: 'secondary', fullWidth: true, onClick: onClick }, h('span', { className: 'hd-stack hd-stack--tight', style: { textAlign: 'left' } }, h('span', { className: 'type-body-strong' }, title), h('span', { className: 'type-label' }, desc))); }

    /* ======================= S06 Asset detail ======================= */
    function Asset(params) {
      var a = D.assetById(ws, params.id);
      if (!a) return h(HD.Screen, { title: 'Perangkat tidak ditemukan', back: { label: 'Kembali', onClick: back } }, P('Perangkat ini tidak ada di ruang kerja aktif.'));
      var d = derived(), tz = ws.site.tz, sum = D.summarize(ws, { startMs: d.q.startMs, endMs: d.q.endMs, assetIds: [a.id] }), s = sum.rows[0];
      var v = st.view['asset:' + a.id] || (st.view['asset:' + a.id] = {});
      var quality = s.conflict ? 'unavailable' : !s.covered.length ? 'unavailable' : s.coverage < 1 ? 'partial' : 'complete';
      var related = d.ins.observations.filter(function (o) { return o.assetId === a.id && D.feedbackState(ws, o).visible; });
      var per = d.ins.perAsset[a.id];
      var sched = D.effectiveSchedule(ws, a, d.q.startMs);
      var pts = v.history ? D.history(ws, { startMs: d.q.startMs, endMs: d.q.endMs, assetIds: [a.id] }) : [];
      var oneDay = d.q.endMs - d.q.startMs <= D.DAY;
      var gapPts = pts.filter(function (p) { return p.mWh == null && !p.future; });
      var maxPt = pts.filter(function (p) { return p.mWh != null; }).sort(function (x, y) { return y.mWh - x.mWh; })[0];
      var srcs = ws.sources.filter(function (x) { return a.bindings.some(function (b) { return b.sourceId === x.id; }); });
      return h(Fragment, null, h(HD.Screen, { title: a.name, subtitle: [D.KIND_LABEL[a.kind], a.location, a.category].filter(Boolean).join(' · '), back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        flashBlock(), PeriodBlock(true),
        s.conflict && h(HD.Notice, { tone: 'attention', title: 'Dua sumber untuk beban yang sama', action: Btn('text', 'Pilih sumber acuan', function () { push('scope'); }) },
          'Nilai tidak dijumlahkan. ' + Object.keys(s.bySource).map(function (k) { return D.sourceById(ws, k).label + ': ' + D.fmtKwh(s.bySource[k]); }).join('; ') + '.'),
        h('div', { className: 'hd-group hd-stack hd-stack--section' },
          h(HD.EnergyMetric, { kwh: quality === 'unavailable' ? null : kwh(s.mWh), quality: quality, completeness: s.coverage == null ? undefined : s.coverage, gapLabel: s.gaps.length ? D.fmtGap(s.gaps[0][0], s.gaps[0][1], tz) : undefined,
            periodLabel: periodLabel(), scopeLabel: 'Cakupan pengukuran: 1 ' + D.KIND_LABEL[a.kind].toLowerCase() + (a.kind === 'device' ? ' (hanya beban yang diukur sumber ini)' : ''), provenance: provOf(ws),
            emptyDetail: s.conflict ? 'Pilih sumber acuan untuk menampilkan nilai.' : 'Belum ada pengukuran pada periode ini. Tidak ditampilkan sebagai 0 kWh.',
            emptyAction: !s.conflict && dataRange([a.id]) ? Btn('secondary', 'Lihat periode data', function () { viewDataPeriod([a.id]); }, { icon: 'calendar' }) : null }),
          costBlock(sum, function () { push('settings', { focus: 'tariff' }); })),
        h('div', { className: 'hd-group' }, qualityBlock(sum, [a.id])),
        Btn('primary', v.history ? 'Sembunyikan riwayat' : 'Lihat riwayat', function () { upd(function () { v.history = !v.history; }); }, { icon: 'calendar' }),
        v.history && h('div', { className: 'hd-group hd-stack' },
          h(HD.HistoryChart, { title: 'Riwayat ' + a.name, unit: 'kWh', periodLabel: periodLabel() + ' · ' + tz, scopeLabel: a.name, dense: oneDay,
            currentLabel: 'Periode terpilih', referenceLabel: 'Median 3 minggu sebelumnya',
            points: pts.map(function (p, i) { return { label: oneDay ? (i % 6 === 0 ? p.label : '') : p.label, current: p.future ? null : kwh(p.mWh), reference: kwh(p.ref) }; }),
            summary: maxPt ? 'Nilai ' + (oneDay ? 'per jam' : 'harian') + ' tertinggi ' + D.fmtKwh(maxPt.mWh) + ' pada ' + (oneDay ? maxPt.label : D.fmtDate(D.localDate(maxPt.startMs, tz))) + '. Total ' + D.fmtKwh(s.mWh) + '.' : 'Belum ada data pada periode ini.',
            gapNote: gapPts.length ? 'Tidak ada data: ' + gapPts.map(function (p) { return D.fmtGap(p.startMs, p.endMs, tz); }).join('; ') + '. Kosong bukan 0 kWh.' : undefined }),
          h(HD.ChartDataAlternative, { caption: 'Energi ' + a.name + ' ' + (oneDay ? 'per jam' : 'per hari') + ', ' + periodLabel(), collapsed: true, toggleLabel: 'Lihat data',
            columns: [{ key: 'when', label: oneDay ? 'Jam' : 'Tanggal' }, { key: 'cur', label: 'Energi', numeric: true, format: String }, { key: 'ref', label: 'Median 3 minggu sebelumnya', numeric: true, format: String }, { key: 'q', label: 'Kualitas' }],
            rows: pts.map(function (p) { return { when: oneDay ? D.fmtGap(p.startMs, p.endMs, tz) : D.fmtDate(D.localDate(p.startMs, tz)), cur: p.future ? 'Belum terjadi' : p.mWh == null ? 'Tidak ada data' : D.fmtKwh(p.mWh), ref: p.ref == null ? 'Tidak tersedia' : D.fmtKwh(p.ref), q: p.future ? '—' : p.mWh == null ? 'Data belum tersedia' : p.coverage < 1 ? 'Sebagian (' + D.fmtCoverage(p.coverage) + ')' : p.mWh === 0 ? '0 kWh terukur' : 'Lengkap' }; }) })),
        Section('Sumber data', h('ul', { className: 'hd-stack hd-stack--tight' }, srcs.map(function (x) {
          var b = a.bindings.filter(function (bb) { return bb.sourceId === x.id; })[0];
          return h('li', { key: x.id }, KV([['Sumber', x.label], ['Asal', ORIGIN[x.origin] + (x.transport === 'simulated_live' ? ' · Simulasi koneksi' : x.origin === 'import' ? ' · Data historis' : '')],
            ['Interval dan resolusi', (x.cadenceMs / 60000) + ' menit · ' + (x.resolutionMWh == null ? 'resolusi tidak diketahui' : D.fmtKwh(x.resolutionMWh).replace(' kWh', ' kWh') + ' per interval')],
            ['Berlaku', (isFinite(b.fromMs) ? 'mulai ' + D.fmtDateTime(b.fromMs, tz) : 'sejak data pertama') + (b.toMs != null ? ' sampai ' + D.fmtDateTime(b.toMs, tz) : '')],
            ['Pengukuran terakhir', x.lastCaptureMs ? D.fmtDateTime(x.lastCaptureMs, tz) : '—']]));
        })), 'src-h'),
        Section('Saran terkait', related.length ? related.map(function (o) {
          return h(HD.InsightSummary, { key: o.id, kind: 'change', title: o.copy.title, periodLabel: o.copy.period, comparison: { eligible: true, label: 'dibanding median minggu sebelumnya' }, onOpenEvidence: function () { push('insight', { id: o.id }); } });
        }) : per && per.energy.state === 'learning' ? h(HD.InsightSummary, { kind: 'learning', detail: per.energy.reason }) : h(HD.InsightSummary, { kind: 'none', periodLabel: per && per.energy.reason ? per.energy.reason : 'Belum ada perubahan yang memenuhi kriteria pada periode ini' }), 'rel-h'),
        Section('Opsional', h('div', { className: 'hd-stack hd-stack--tight' },
          P('Pola pemakaian: ' + sched.label + (sched.windows ? ' · ' + sched.windows.map(D.describeWindow).join('; ') : ''), 'type-label'),
          Row(Btn('secondary', 'Atur pola pemakaian', function () { upd(function () { st.drafts.profile = { id: a.id, mode: a.scheduleMode === 'custom' ? 'windows' : a.scheduleMode, windows: (a.customWindows || []).map(cloneW) }; st.sheet = 'profile'; }); }),
            Btn('secondary', 'Atur metrik keluaran', function () { push('metric', { assetId: a.id }); })),
          Row(Btn('text', 'Ubah detail', function () { upd(function () { st.drafts.edit = st.drafts.edit && st.drafts.edit.id === a.id ? st.drafts.edit : { id: a.id, name: a.name, category: a.category, location: a.location }; st.sheet = 'edit'; }); }),
            Btn('text', 'Arsipkan', function () { upd(function () { st.sheet = 'archive'; }); }))), 'opt-h')),
        EditSheet(a), ArchiveSheet(a), ProfileSheet(a));
    }
    function cloneW(w) { return { days: w.days.slice(), start: w.start, end: w.end, nextDay: !!w.nextDay, allDay: !!w.allDay }; }
    function EditSheet(a) {
      var dr = st.drafts.edit, o = opState(st, 'edit:' + a.id);
      if (!dr || dr.id !== a.id) return null;
      var nameErr = dr.tried && (!dr.name.trim() ? 'Isi nama perangkat.' : dr.name.length > 60 ? 'Nama paling banyak 60 karakter.' : null);
      return h(HD.SheetDialog, { open: st.sheet === 'edit', title: 'Ubah detail perangkat', onClose: function () { upd(function () { st.sheet = null; }); },
        footer: h(Fragment, null, Btn('primary', 'Simpan', function () {
          upd(function () { dr.tried = true; }); if (!dr.name.trim() || dr.name.length > 60) return;
          run('edit:' + a.id, D.api.saveAsset(ws, a.id, { name: dr.name.trim(), category: dr.category, location: dr.location }), function () { st.drafts.edit = null; st.sheet = null; st.flash = { title: 'Detail perangkat disimpan', body: 'ID perangkat dan riwayat tidak berubah.' }; });
        }, { loading: o.state === 'saving', loadingLabel: 'Menyimpan…', fullWidth: true }), Btn('text', 'Batal', function () { upd(function () { st.sheet = null; }); }, { fullWidth: true }),
          dr.name !== a.name || dr.category !== a.category || dr.location !== a.location ? Btn('text', 'Buang draf', function () { upd(function () { st.drafts.edit = null; st.sheet = null; }); }, { fullWidth: true }) : null) },
        h('div', { className: 'hd-stack' },
          h(HD.TextField, { label: 'Nama perangkat', required: true, value: dr.name, error: nameErr, onChange: function (v) { upd(function () { dr.name = v; }); }, draftNote: dr.name !== a.name ? 'Draf belum disimpan' : undefined }),
          h(HD.TextField, { label: 'Kategori', optional: true, value: dr.category, onChange: function (v) { upd(function () { dr.category = v; }); } }),
          h(HD.TextField, { label: 'Lokasi', optional: true, value: dr.location, onChange: function (v) { upd(function () { dr.location = v; }); } }),
          o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Gagal menyimpan', detail: o.message, onRetry: function () { run('edit:' + a.id, D.api.saveAsset(ws, a.id, { name: dr.name.trim(), category: dr.category, location: dr.location }), function () { st.drafts.edit = null; st.sheet = null; }); } })));
    }
    function ArchiveSheet(a) {
      var o = opState(st, 'arch:' + a.id);
      return h(HD.SheetDialog, { open: st.sheet === 'archive', title: 'Arsipkan ' + a.name + '?', onClose: function () { upd(function () { st.sheet = null; }); },
        footer: h(Fragment, null, Btn('primary', 'Arsipkan', function () { run('arch:' + a.id, D.api.saveAsset(ws, a.id, { archived: true }), function () { st.sheet = null; st.flash = { title: a.name + ' diarsipkan', body: 'Riwayat tetap tersimpan. Pulihkan dari daftar Perangkat.' }; popRoute(); }); }, { loading: o.state === 'saving', loadingLabel: 'Mengarsipkan…', fullWidth: true }),
          Btn('text', 'Batal', function () { upd(function () { st.sheet = null; }); }, { fullWidth: true })) },
        P(a.name + ' tidak lagi dihitung dalam cakupan pengukuran. Riwayat dan sumber tidak dihapus, dan pengarsipan dapat dipulihkan.'),
        o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', detail: o.message }));
    }
    function WindowsEditor(list, onChange, idp) {
      var dayOpts = D.DAYS.map(function (n, i) { return { value: String(i), label: n.slice(0, 3) === 'Min' ? 'Min' : n.slice(0, 3) }; });
      var errs = D.validateWindows(list);
      return h('div', { className: 'hd-stack' }, list.map(function (w, i) {
        function set(patch) { var copy = list.map(cloneW); Object.assign(copy[i], patch); onChange(copy); }
        var e = errs.filter(function (x) { return x.index === i; }).map(function (x) { return x.message; }).join(' ');
        return h('div', { key: i, className: 'hd-window hd-stack hd-stack--tight', role: 'group', 'aria-label': 'Jendela ' + (i + 1) },
          h(HD.ChoiceGroup, { type: 'checkbox', inline: true, legend: 'Jendela ' + (i + 1) + ' · hari mulai', value: w.days.map(String), onChange: function (v) { set({ days: v.map(Number).sort() }); } , options: dayOpts }),
          h(HD.ChoiceGroup, { type: 'checkbox', inline: true, legend: 'Pilihan', value: [w.allDay ? 'all' : null, w.nextDay ? 'next' : null].filter(Boolean), onChange: function (v) { set({ allDay: v.indexOf('all') >= 0, nextDay: v.indexOf('next') >= 0 }); },
            options: [{ value: 'all', label: '24 jam' }, { value: 'next', label: 'Berakhir hari berikutnya', disabledReason: w.allDay ? 'Tidak berlaku untuk 24 jam.' : null }] }),
          !w.allDay && Row(h(HD.TextField, { id: idp + '-s-' + i, label: 'Mulai', type: 'time', value: w.start, onChange: function (v) { set({ start: v }); } }),
            h(HD.TextField, { id: idp + '-e-' + i, label: 'Selesai', type: 'time', value: w.end, error: e || null, onChange: function (v) { set({ end: v }); } })),
          w.allDay && e ? P(e, 'type-label hd-qualifier') : null,
          P(errs.some(function (x) { return x.index === i; }) ? '' : D.describeWindow(w), 'type-label hd-secondary'),
          Btn('text', 'Hapus jendela ' + (i + 1), function () { onChange(list.filter(function (_, j) { return j !== i; })); }));
      }), Btn('secondary', 'Tambah jendela', function () { onChange(list.concat([{ days: [0, 1, 2, 3, 4], start: '07:00', end: '17:00', nextDay: false, allDay: false }])); }));
    }
    function ProfileSheet(a) {
      var dr = st.drafts.profile; if (!dr || dr.id !== a.id) return null;
      var o = opState(st, 'profile:' + a.id);
      var errs = dr.mode === 'windows' ? D.validateWindows(dr.windows) : [];
      var hasSite = ws.schedules.length > 0;
      var modes = { none: 'none', continuous: 'continuous', inherit: 'inherit', windows: 'custom' };
      return h(HD.SheetDialog, { open: st.sheet === 'profile', title: 'Pola pemakaian ' + a.name, onClose: function () { upd(function () { st.sheet = null; }); },
        footer: h(Fragment, null, Btn('primary', 'Simpan pola', function () {
          if (errs.length || (dr.mode === 'windows' && !dr.windows.length)) { upd(function () { dr.tried = true; }); return; }
          run('profile:' + a.id, D.api.saveAsset(ws, a.id, { scheduleMode: modes[dr.mode], customWindows: dr.mode === 'windows' ? dr.windows : [] }), function () { st.sheet = null; st.drafts.profile = null; st.flash = { title: 'Pola pemakaian disimpan', body: 'Berlaku untuk perhitungan di luar jadwal mulai sekarang. Data pengukuran tidak berubah.' }; });
        }, { loading: o.state === 'saving', loadingLabel: 'Menyimpan…', fullWidth: true, disabledReason: ws.composition === 'core' && dr.mode === 'windows' ? 'Analisis jadwal tidak aktif pada komposisi Inti saja.' : null }),
          Btn('text', 'Batal', function () { upd(function () { st.sheet = null; }); }, { fullWidth: true })) },
        h('div', { className: 'hd-stack' },
          h(HD.ChoiceGroup, { legend: 'Pola yang diharapkan', value: dr.mode, onChange: function (v) { upd(function () { dr.mode = v; }); }, options: [
            { value: 'inherit', label: 'Ikuti jadwal lokasi', description: hasSite ? 'Memakai jadwal lokasi yang berlaku.' : 'Lokasi belum memiliki jadwal; analisis di luar jadwal tidak tersedia.' },
            { value: 'none', label: 'Tanpa jadwal', description: 'Mematikan pewarisan. Pemantauan inti tetap lengkap.' },
            { value: 'continuous', label: 'Diharapkan terus menyala', description: 'Untuk kulkas, router, server atau pendingin proses. Pemakaian terus-menerus bukan peringatan.' },
            { value: 'windows', label: 'Jadwal khusus', description: 'Jendela mingguan untuk perangkat ini saja.' }] }),
          dr.mode === 'windows' && WindowsEditor(dr.windows, function (w) { upd(function () { dr.windows = w; }); }, 'pw'),
          dr.tried && dr.mode === 'windows' && !dr.windows.length && P('Tambahkan minimal satu jendela.', 'hd-qualifier type-label-strong'),
          o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Gagal menyimpan', detail: o.message })));
    }

    /* ======================= S07 Saran ======================= */
    function Saran() {
      if (!ws.readings.length) return h(HD.Screen, { title: 'Saran', current: 'saran', onNavigate: goTab }, SettingsLink(),
        h(HD.Notice, { tone: 'neutral', title: 'Belum ada data energi' }, 'Saran hanya muncul dari data yang tercatat. Impor data atau coba demo.'), Btn('primary', 'Impor data', function () { push('import'); }, { icon: 'upload' }));
      var d = derived(), tz = ws.site.tz;
      var obs = d.ins.observations, vis = obs.filter(function (o) { return D.feedbackState(ws, o).visible; });
      var hidden = obs.filter(function (o) { return D.feedbackState(ws, o).hidden; }), snoozed = obs.filter(function (o) { return D.feedbackState(ws, o).snoozed; });
      var supporting = h(Fragment, null, SettingsLink(),
        d.ins.notices.length > 0 && Section('Catatan data', h('div', { className: 'hd-stack hd-stack--tight' }, d.ins.notices.map(function (n) {
          var act = n.action === 'scope' ? Btn('text', 'Pilih cakupan', function () { push('scope'); }) : n.action === 'history' ? Btn('text', 'Lihat riwayat', function () { st.view['asset:' + n.assetId] = { history: true }; push('asset', { id: n.assetId }); })
            : n.action === 'source' ? Btn('text', 'Periksa sumber', function () { run('check:' + n.id.slice(6), D.api.checkSource(ws, n.id.slice(6))); }) : null;
          return h('div', { key: n.id, className: 'hd-stack hd-stack--tight' }, h(HD.Notice, { tone: n.tone, title: n.title, action: act }, n.body), n.action === 'source' ? checkStatus('check:' + n.id.slice(6)) : null);
        })), 'notes-h'));
      return h(HD.Screen, { title: 'Saran', subtitle: 'Pengamatan berbasis bukti, bukan diagnosis', provenance: provOf(ws), current: 'saran', onNavigate: goTab, aside: supporting },
        flashBlock(), PeriodBlock(true),
        Section('Pengamatan', vis.length ? h('div', { className: 'hd-stack' }, vis.map(function (o) {
          var fs = D.feedbackState(ws, o);
          return h('div', { key: o.id, className: 'hd-group hd-stack hd-stack--tight' }, h(HD.InsightSummary, { kind: 'change', headingLevel: 3, title: o.copy.title, periodLabel: o.copy.period + ' · ' + o.evidence.assetName,
            comparison: { eligible: true, label: 'dibanding median ' + o.evidence.historical.length + ' minggu sebelumnya' }, qualification: o.kind === 'outside' ? 'Pemakaian di luar jadwal belum tentu pemborosan.' : undefined,
            onOpenEvidence: function () { push('insight', { id: o.id }); } }), fs.superseded ? P('Bukti diperbarui sejak umpan balik Anda; umpan balik lama tidak dipindahkan.', 'type-label hd-secondary') : null);
        })) : d.ins.learning > 0 && d.ins.comparable === 0
          ? h('div', { className: 'hd-stack hd-stack--tight' }, h(HD.InsightSummary, { kind: 'learning', detail: 'Belum cukup periode pembanding untuk ' + d.ins.learning + ' perangkat. Total dan riwayat tetap tersedia.' }), Btn('text', 'Lihat riwayat', function () { goTab('perangkat'); }))
          : h('div', { className: 'hd-stack hd-stack--tight' }, h(HD.InsightSummary, { kind: 'none', periodLabel: 'Belum ada perubahan yang memenuhi kriteria pada periode ini' }), Btn('text', 'Lihat riwayat', function () { goTab('perangkat'); })), 'obs-h'),
        snoozed.length > 0 && Section('Ditunda', h('ul', { className: 'hd-stack hd-stack--tight' }, snoozed.map(function (o) {
          var f = D.feedbackState(ws, o).f;
          return h('li', { key: o.id, className: 'hd-stack hd-stack--tight' }, P(o.copy.title + ' · kembali ' + D.fmtDateTime(f.untilMs, tz), 'type-body'), restoreBtn(o));
        })), 'snz-h'),
        Btn('secondary', 'Saran tersembunyi (' + hidden.length + ')', function () { push('hidden'); }),
        Section('Saran umum', h('ul', { className: 'hd-stack hd-stack--tight type-body' },
          h('li', null, 'Bandingkan jam pemakaian dengan kebiasaan atau jadwal kerja; perubahan rutinitas sering menjelaskan perubahan energi.'),
          h('li', null, 'Beban yang memang perlu menyala terus, seperti kulkas, router, server atau pendingin proses, tidak perlu dimatikan hanya karena menyala terus.'),
          h('li', null, 'Periksa kelengkapan data sebelum menarik kesimpulan dari angka yang turun atau naik.')), 'gen-h'),
        P('Saran umum bukan hasil analisis perangkat Anda dan tidak mendiagnosis kerusakan.', 'type-label hd-secondary'));
    }
    function restoreBtn(o) {
      var k = 'fb:restore:' + o.id;
      return h(Fragment, null, Btn('text', 'Pulihkan', function () { run(k, D.api.saveFeedback(ws, o, 'restore'), function () { st.flash = { title: 'Saran dipulihkan', body: o.copy.title }; }); }, { loading: opState(st, k).state === 'saving', loadingLabel: 'Memulihkan…' }),
        opState(st, k).state === 'failure' && h(HD.ProgressStatus, { state: 'failure', detail: opState(st, k).message, onRetry: function () { run(k, D.api.saveFeedback(ws, o, 'restore')); } }));
    }
    function Hidden() {
      var d = derived(), hidden = d.ins.observations.filter(function (o) { return D.feedbackState(ws, o).hidden; });
      return h(HD.Screen, { title: 'Saran tersembunyi', back: { label: 'Kembali', onClick: back }, current: 'saran', onNavigate: goTab }, flashBlock(),
        hidden.length ? h('ul', { className: 'hd-stack' }, hidden.map(function (o) { return h('li', { key: o.id, className: 'hd-group hd-stack hd-stack--tight' }, P(o.copy.title, 'type-body-strong'), P(o.copy.period, 'type-label'), restoreBtn(o)); }))
          : h(HD.Notice, { tone: 'neutral', title: 'Tidak ada saran tersembunyi' }, 'Saran yang Anda sembunyikan akan muncul di sini dan dapat dipulihkan.'));
    }

    /* ======================= S08 Evidence ======================= */
    function Insight(params) {
      var d = derived(), tz = ws.site.tz;
      var o = d.ins.observations.filter(function (x) { return x.id === params.id; })[0];
      if (!o) return h(HD.Screen, { title: 'Bukti saran', back: { label: 'Kembali', onClick: back } },
        h(HD.Notice, { tone: 'neutral', title: 'Saran ini tidak berlaku untuk periode atau data saat ini' }, 'Periode, cakupan atau data berubah sehingga bukti tidak lagi memenuhi kriteria. Bukti lama tidak ditulis ulang.'));
      var ev = o.evidence, c = o.copy, fs = D.feedbackState(ws, o), A = D.assetById(ws, o.assetId);
      var fbKey = 'fb:' + o.id, fb = opState(st, fbKey), v = st.view['ins:' + o.id] || (st.view['ins:' + o.id] = {});
      function feedback(action, after) { upd(function () { v.lastAction = action; }); return run(fbKey, D.api.saveFeedback(ws, o, action), after); }
      var r = ev.resolutionMWh, B = ev.baselineMWh;
      var arith = 'C − B = ' + D.fmtKwh(ev.currentMaskMWh, false) + ' − ' + D.fmtKwh(B, false) + ' = ' + D.fmtSignedKwh(ev.deltaMWh) + ' ≥ maks(' + D.fmtKwh(0.3 * B, false) + '; ' + D.fmtKwh(3 * ev.madMWh, false) + '; ' + D.fmtKwh(5 * r, false) + ') = ' + D.fmtKwh(ev.thresholdMWh);
      var hp = o.kind === 'energy' && v.compare ? D.history(ws, { startMs: ev.startMs, endMs: ev.endMs, assetIds: [o.assetId] }) : [];
      return h(HD.Screen, { title: 'Dasar saran', subtitle: c.title, back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        P(c.period + ' · ' + ev.assetName + ' · asal data: ' + ev.origins.map(function (x) { return ORIGIN[x]; }).join(', '), 'type-label-strong'),
        fs.superseded && h(HD.Notice, { tone: 'info', title: 'Versi bukti diperbarui' }, 'Umpan balik Anda sebelumnya untuk versi bukti lama (' + fs.previous.revision + ') dan tidak dipindahkan ke bukti baru.'),
        h(HD.EvidencePanel, {
          observed: h(Fragment, null, P(c.observed), c.pctNote ? P(c.pctNote, 'type-label') : null),
          comparison: h(Fragment, null, P(c.comparison), P('Total tercatat penuh periode ini: ' + D.fmtKwh(ev.currentFullMWh) + '. Perbandingan memakai waktu yang memiliki data di semua periode (' + ev.maskSlots + ' interval).', 'type-label')),
          qualityScope: P('Cakupan: 1 perangkat (' + ev.assetName + '), hanya beban yang diukur sumber ini. Kelengkapan periode ini ' + D.fmtCoverage(ev.currentCoverage) + '; waktu bersama semua periode ' + D.fmtCoverage(ev.maskCoverage) + '. Resolusi sumber 1 Wh per interval.' + (ev.skipped.length ? ' ' + ev.skipped.length + ' minggu pembanding dilewati karena kelengkapan di bawah 90%.' : '')),
          unknown: P(c.unknown),
          guidance: P('Langkah pemeriksaan: ' + c.step),
          onFeedback: function (val) { feedback(val === 'helpful' ? 'useful' : 'not_relevant'); },
          feedbackState: fb.state && (v.lastAction === 'useful' || v.lastAction === 'not_relevant') ? fb.state : fs.f && (fs.f.action === 'useful' || fs.f.action === 'not_relevant') ? 'success' : null,
          feedbackChoice: v.lastAction === 'useful' ? 'helpful' : 'notHelpful',
          onFeedbackRetry: function () { feedback(v.lastAction); }, onFeedbackCheck: function () { feedback(v.lastAction); },
          metadata: [['Kebijakan', ev.policy + ' · ' + D.RULE_TEXT], ['Median B', D.fmtKwh(B) + ' dari ' + ev.historical.map(function (x) { return D.fmtKwh(x.maskMWh); }).join(', ')], ['MAD', D.fmtKwh(ev.madMWh)],
            ['Resolusi r', D.fmtKwh(r) + ' (jumlah resolusi ' + ev.maskSlots + ' interval)'], ['Aritmetika', arith], ['Jendela', D.fmtGap(ev.startMs, ev.endMs, tz) + ' dibanding ' + ev.historical.map(function (x) { return D.fmtGap(x.startMs, x.endMs, tz); }).join('; ')],
            ['Jadwal', ev.schedule || 'Tidak dipakai'], ['Versi bukti', ev.revision + ' · ' + ev.calc + ' · dibuat ' + D.fmtDateTime(ev.generatedAtMs, tz)]]
        }),
        Btn('primary', v.compare ? 'Sembunyikan data pembanding' : 'Lihat data pembanding', function () { upd(function () { v.compare = !v.compare; }); }),
        v.compare && h('div', { className: 'hd-group hd-stack' },
          o.kind === 'energy' && h(HD.HistoryChart, { title: 'Energi ' + ev.assetName + ' per hari', unit: 'kWh', periodLabel: c.period, scopeLabel: ev.assetName, currentLabel: 'Periode ini', referenceLabel: 'Median 3 minggu sebelumnya',
            points: hp.map(function (p) { return { label: p.label, current: kwh(p.mWh), reference: kwh(p.ref) }; }), summary: c.observed }),
          h(HD.ChartDataAlternative, { caption: (o.kind === 'outside' ? 'Energi di luar jadwal' : 'Energi') + ' ' + ev.assetName + ' per periode pembanding', collapsed: o.kind === 'energy', toggleLabel: 'Lihat data',
            columns: [{ key: 'p', label: 'Periode' }, { key: 'v', label: 'Energi pada waktu bersama', numeric: true, format: String }, { key: 'c', label: 'Kelengkapan', numeric: true, format: String }],
            rows: [{ p: 'Periode ini · ' + c.period, v: D.fmtKwh(ev.currentMaskMWh), c: D.fmtCoverage(ev.currentCoverage) }].concat(ev.historical.map(function (x) { return { p: D.fmtRange(D.localDate(x.startMs, tz), D.localDate(x.endMs - 1, tz)), v: D.fmtKwh(x.maskMWh), c: D.fmtCoverage(x.coverage) }; }), [{ p: 'Median pembanding', v: D.fmtKwh(B), c: '—' }]),
            summary: c.observed })),
        Section('Atur saran ini', h('div', { className: 'hd-stack hd-stack--tight' },
          P('Opsional dan dapat dibatalkan. Tidak mengubah data, tidak mengirim perintah ke perangkat.', 'type-label hd-secondary'),
          Row(Btn('secondary', 'Tunda hingga besok', function () { feedback('snooze', function (res) { st.flash = { title: 'Saran ditunda', body: 'Kembali ' + D.fmtDateTime(res.feedback.untilMs, tz) + '.', action: { label: 'Pulihkan', onClick: function () { run('fb:restore:' + o.id, D.api.saveFeedback(ws, o, 'restore')); st.flash = null; } } }; popRoute(); }); }, { loading: fb.state === 'saving' && v.lastAction === 'snooze', loadingLabel: 'Menyimpan…' }),
            Btn('secondary', 'Sembunyikan', function () { feedback('hide', function () { st.flash = { title: 'Saran disembunyikan', body: 'Data dan perangkat tidak berubah.', action: { label: 'Pulihkan', onClick: function () { run('fb:restore:' + o.id, D.api.saveFeedback(ws, o, 'restore')); st.flash = null; } } }; popRoute(); }); }, { loading: fb.state === 'saving' && v.lastAction === 'hide', loadingLabel: 'Menyimpan…' })),
          fb.state === 'failure' && (v.lastAction === 'snooze' || v.lastAction === 'hide') && h(HD.ProgressStatus, { state: 'failure', label: 'Belum tersimpan', detail: fb.message, onRetry: function () { feedback(v.lastAction); } })), 'fb-h'),
        A && Btn('text', 'Buka ' + A.name, function () { push('asset', { id: A.id }); }, { icon: 'chevronRight' }));
    }

    /* ======================= S09 Settings ======================= */
    function Settings(params) {
      var dr = st.drafts.settings;
      if (!dr) dr = st.drafts.settings = {
        name: ws.site.name, context: ws.site.context, tz: ws.site.tz,
        tariffText: ws.tariffs.length ? String(ws.tariffs[ws.tariffs.length - 1].mRpPerKwh / 1000).replace('.', ',') : '', tariffMode: 'all', tariffFrom: today(), tariffCleared: false,
        schedOn: ws.schedules.length > 0, windows: ws.schedules.length ? ws.schedules[ws.schedules.length - 1].windows.map(cloneW) : [], schedEffective: 'now',
        notify: ws.notifications.enabled, submitCount: 0
      };
      var o = opState(st, 'settings'), errs = [];
      var parsedTariff = HD.format.parseDecimal(dr.tariffText || '');
      if (dr.tried) {
        if (!dr.name.trim()) errs.push({ targetId: 'set-name', text: 'Isi nama lokasi.' });
        if (!parsedTariff.empty && !parsedTariff.valid) errs.push({ targetId: 'set-tariff', text: parsedTariff.error || 'Tarif harus angka 0 atau lebih, misalnya 1.444,70.' });
        if (!parsedTariff.empty && parsedTariff.valid && parsedTariff.value < 0) errs.push({ targetId: 'set-tariff', text: 'Tarif tidak boleh negatif.' });
        if (dr.schedOn) D.validateWindows(dr.windows).forEach(function (e) { errs.push({ targetId: 'sw-e-' + e.index, text: e.message }); });
        if (dr.schedOn && !dr.windows.length) errs.push({ targetId: 'set-sched', text: 'Tambahkan minimal satu jendela atau pilih "Tidak ada jadwal".' });
      }
      function buildPatch() {
        var p = { site: { name: dr.name.trim(), context: dr.context, tz: dr.tz }, notifications: { enabled: dr.notify } };
        var curText = ws.tariffs.length ? String(ws.tariffs[ws.tariffs.length - 1].mRpPerKwh / 1000).replace('.', ',') : '';
        if (dr.tariffText !== curText || dr.tariffCleared) {
          if (parsedTariff.empty) p.tariffs = [];
          else { var t = { fromMs: dr.tariffMode === 'all' ? -Infinity : D.localMidnight(dr.tariffFrom, dr.tz), mRpPerKwh: Math.round(parsedTariff.value * 1000), source: 'user' };
            p.tariffs = dr.tariffMode === 'all' ? [t] : ws.tariffs.filter(function (x) { return x.fromMs < t.fromMs; }).concat([t]); }
        }
        var curW = JSON.stringify(ws.schedules.length ? ws.schedules[ws.schedules.length - 1].windows : []);
        if ((dr.schedOn ? JSON.stringify(dr.windows) : '[]') !== curW) {
          if (!dr.schedOn) p.schedules = ws.schedules.length ? ws.schedules.concat([{ id: 'sched-' + (ws.schedules.length + 1), fromMs: ws.nowMs, windows: [], label: 'Jadwal dimatikan' }]).filter(function (s) { return s.windows.length || s.fromMs === ws.nowMs; }) : [];
          else { var v = { id: 'sched-' + (ws.schedules.length + 1), fromMs: dr.schedEffective === 'history' ? -Infinity : ws.nowMs, windows: dr.windows.map(cloneW), label: 'Jadwal lokasi v' + (ws.schedules.length + 1) + (dr.schedEffective === 'history' ? ' (koreksi historis)' : '') };
            p.schedules = dr.schedEffective === 'history' ? [v] : ws.schedules.concat([v]); }
          if (p.schedules) p.schedules = p.schedules.filter(function (s) { return s.windows.length; });
        }
        return p;
      }
      function save() {
        upd(function () { dr.tried = true; dr.submitCount++; });
        var e2 = []; if (!dr.name.trim()) e2.push(1); if (!parsedTariff.empty && (!parsedTariff.valid || parsedTariff.value < 0)) e2.push(1); if (dr.schedOn && (D.validateWindows(dr.windows).length || !dr.windows.length)) e2.push(1);
        if (e2.length) return;
        run('settings', D.api.saveSettings(ws, buildPatch()), function () { st.welcome.context = dr.context; st.welcome.demoChoice = null; st.drafts.settings = null; st.flash = { title: 'Pengaturan disimpan', body: 'Dikonfirmasi backend simulasi. Pengukuran tidak diubah.' }; popRoute(); });
      }
      var tzChanged = dr.tz !== ws.site.tz, ctxChanged = dr.context !== ws.site.context;
      var schedPreview = dr.schedOn && !D.validateWindows(dr.windows).length && dr.windows.length ? (function () {
        var d = derived(), parts = []; d.sum.rows.forEach(function (r) { if (!r.conflict && r.asset.scheduleMode === 'inherit') parts = parts.concat(r.parts); });
        var sp = D.outsideSplit(dr.windows, d.q.startMs, d.q.endMs, ws.site.tz, parts);
        return dr.schedEffective === 'history' ? 'Jika diterapkan ke riwayat, pada ' + periodLabel() + ': di dalam jadwal ' + D.fmtKwh(sp.inside) + ', di luar jadwal ' + D.fmtKwh(sp.outside) + (sp.estimated ? ' (sebagian interval dibagi proporsional, estimasi)' : '') + '. Perangkat "Diharapkan terus menyala" tidak dihitung sebagai di luar jadwal.'
          : 'Berlaku mulai ' + D.fmtDateTime(ws.nowMs, ws.site.tz) + '. Periode sebelumnya tidak dihitung ulang; perbandingan di luar jadwal menunggu periode yang memakai jadwal yang sama.';
      })() : null;
      var capCost = ws.composition !== 'core', capSched = ws.composition !== 'core';
      var pending = o.state === 'saving';
      return h(HD.Screen, { title: 'Pengaturan', subtitle: ws.mode === 'demo' ? 'Demo · perubahan hanya pada data demo' : 'Ruang kerja lokal', back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        h(HD.ErrorSummary, { errors: errs, submitCount: dr.submitCount, convention: undefined }),
        Section('Lokasi', h('div', { className: 'hd-stack' },
          h(HD.TextField, { id: 'set-name', label: 'Nama lokasi', required: true, value: dr.name, error: errs.filter(function (e) { return e.targetId === 'set-name'; })[0] ? 'Isi nama lokasi.' : null, onChange: function (v) { upd(function () { dr.name = v; }); } }),
          h(HD.ChoiceGroup, { legend: 'Konteks', value: dr.context, onChange: function (v) { upd(function () { dr.context = v; }); }, options: ['household', 'business', 'industry', 'unspecified'].map(function (k) { return { value: k, label: D.CONTEXT_LABEL[k] }; }),
            help: ctxChanged ? 'Pratinjau: contoh dan pilihan demo berubah. Data, tarif, jadwal dan metrik tetap sama.' : 'Hanya mengubah contoh.' }),
          h(HD.ChoiceGroup, { type: 'select', legend: 'Zona waktu', value: dr.tz, onChange: function (v) { upd(function () { dr.tz = v; }); }, options: Object.keys(D.TZ).map(function (k) { return { value: k, label: D.TZ_LABEL[k] }; }),
            help: tzChanged ? 'Konfirmasi: batas hari lokal dan perbandingan dihitung ulang. Pengukuran UTC tidak ditulis ulang; ' + D.fmtDate(st.period.start) + ' akan dimulai pukul 00.00 ' + dr.tz + '.' : 'Dipakai untuk batas hari, minggu dan jadwal.' })), 'loc-h'),
        Section('Tarif', capCost ? h('div', { className: 'hd-stack', id: 'tariff' },
          P(ws.tariffs.length ? 'Tarif aktif: ' + ws.tariffs.map(function (t) { return D.fmtTariff(t.mRpPerKwh) + (isFinite(t.fromMs) ? ' mulai ' + D.fmtDate(D.localDate(t.fromMs, ws.site.tz)) : ' untuk seluruh data') + (t.source === 'synthetic' ? ' (simulasi, bukan tarif PLN)' : ''); }).join('; ') : 'Tarif belum diatur. Energi tetap ditampilkan; biaya belum dihitung.', 'type-label'),
          h(HD.NumericField, { id: 'set-tariff', label: 'Tarif listrik', unit: 'Rp/kWh', optional: true, value: dr.tariffText, showErrors: dr.tried, onChange: function (t) { upd(function () { dr.tariffText = t; dr.tariffCleared = false; }); },
            help: 'Angka 0 berarti energi gratis yang Anda isi sendiri. Kosong berarti tarif belum diatur.' }),
          h(HD.ChoiceGroup, { legend: 'Berlaku', value: dr.tariffMode, onChange: function (v) { upd(function () { dr.tariffMode = v; }); }, options: [{ value: 'all', label: 'Untuk seluruh data (koreksi)', description: 'Biaya periode lama dihitung ulang dan dicatat.' }, { value: 'from', label: 'Mulai tanggal tertentu', description: 'Biaya sebelum tanggal itu tidak berubah.' }] }),
          dr.tariffMode === 'from' && h(HD.TextField, { label: 'Berlaku mulai', type: 'date', value: dr.tariffFrom, onChange: function (v) { upd(function () { dr.tariffFrom = v; }); } }),
          ws.tariffs.length > 0 && Btn('text', 'Hapus tarif', function () { upd(function () { dr.tariffText = ''; dr.tariffCleared = true; }); }))
          : h(HD.Notice, { tone: 'neutral', title: 'Modul biaya tidak aktif' }, 'Komposisi Inti saja. Permintaan menyimpan tarif ditolak dengan alasan yang sama walau dipanggil di luar layar ini.'), 'tar-h'),
        Section('Jadwal pemakaian lokasi (opsional)', capSched ? h('div', { className: 'hd-stack', id: 'set-sched', tabIndex: -1 },
          h(HD.ChoiceGroup, { legend: 'Jadwal lokasi', value: dr.schedOn ? 'on' : 'off', onChange: function (v) { upd(function () { dr.schedOn = v === 'on'; if (dr.schedOn && !dr.windows.length) dr.windows = [{ days: [0, 1, 2, 3, 4, 5], start: '07:00', end: '17:00', nextDay: false, allDay: false }]; }); },
            options: [{ value: 'off', label: 'Tidak ada jadwal', description: 'Analisis di luar jadwal tidak tersedia, bukan nol.' }, { value: 'on', label: 'Atur jendela mingguan', description: 'Boleh beberapa jendela, termasuk melewati tengah malam.' }] }),
          dr.schedOn && WindowsEditor(dr.windows, function (w) { upd(function () { dr.windows = w; }); }, 'sw'),
          dr.schedOn && h(HD.ChoiceGroup, { legend: 'Mulai berlaku', value: dr.schedEffective, onChange: function (v) { upd(function () { dr.schedEffective = v; }); }, options: [{ value: 'now', label: 'Mulai sekarang (' + D.fmtDateTime(ws.nowMs, ws.site.tz) + ')' }, { value: 'history', label: 'Koreksi data historis juga', description: 'Perhitungan lama diganti dengan definisi ini dan diberi versi baru.' }] }),
          schedPreview && h(HD.Notice, { tone: 'info', title: 'Pratinjau jadwal' }, dr.windows.map(D.describeWindow).join('; ') + '. ' + schedPreview),
          P('Perangkat dapat mengikuti jadwal lokasi, tanpa jadwal, diharapkan terus menyala, atau memakai jadwal khusus (atur di detail perangkat).', 'type-label hd-secondary'))
          : h(HD.Notice, { tone: 'neutral', title: 'Modul jadwal tidak aktif' }, 'Komposisi Inti saja.'), 'sch-h'),
        Section('Notifikasi (opsional)', h('div', { className: 'hd-stack hd-stack--tight' },
          h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Preferensi', value: dr.notify ? ['push'] : [], onChange: function (v) { upd(function () { dr.notify = v.length > 0; }); }, options: [{ value: 'push', label: 'Beri tahu saya bila ada saran baru' }] }),
          P('Mati sampai Anda menyetujuinya. Prototipe tidak meminta izin perangkat dan tidak mengirim notifikasi; hanya preferensi yang disimpan.', 'type-label hd-secondary')), 'not-h'),
        Section('Metrik energi per keluaran (opsional)', h('div', { className: 'hd-stack hd-stack--tight' },
          P(ws.metric && ws.metric.enabled ? 'Aktif: ' + ws.metric.name + ' (' + ws.metric.unit + ')' : 'Tidak aktif. Rumah tangga tidak memerlukan metrik ini.', 'type-label'),
          Btn('secondary', 'Atur metrik keluaran', function () { push('metric'); })), 'met-h'),
        Section('Tampilan', h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Tampilan di perangkat ini', value: [st.prefs.largeText ? 'big' : null, st.prefs.reduceMotion ? 'motion' : null].filter(Boolean),
          onChange: function (v) { upd(function () { st.prefs.largeText = v.indexOf('big') >= 0; st.prefs.reduceMotion = v.indexOf('motion') >= 0; }); },
          options: [{ value: 'big', label: 'Teks lebih besar (200%)' }, { value: 'motion', label: 'Kurangi gerakan' }], help: 'Langsung berlaku; tidak disimpan ke server.' }), 'tam-h'),
        h(HD.ProgressStatus, { state: o.state === 'saving' ? 'saving' : o.state === 'failure' ? 'failure' : o.state === 'unknown' ? 'unknown' : null, label: o.state === 'failure' && o.code === 'session_expired' ? 'Sesi berakhir' : undefined,
          detail: o.message ? o.message + ' Nilai terkonfirmasi sebelumnya tetap dipakai.' : undefined, onRetry: save, onCheck: function () { var same = JSON.stringify(ws.site.name) === JSON.stringify(dr.name.trim()); upd(function () { st.ops.settings = same ? { state: 'success' } : { state: 'failure', message: 'Perubahan belum tersimpan.' }; if (same) { st.drafts.settings = null; } }); } }),
        h('div', { className: 'hd-stack hd-stack--tight' },
          Btn('primary', 'Simpan perubahan', save, { loading: pending, loadingLabel: 'Menyimpan…', fullWidth: true }),
          Btn('text', 'Batal', back, { fullWidth: true }),
          Btn('text', 'Buang draf', function () { upd(function () { st.drafts.settings = null; st.ops.settings = null; }); }, { fullWidth: true })),
        Section('Lainnya', h('div', { className: 'hd-stack hd-stack--tight' },
          Btn('secondary', 'Tentang demo', function () { push('demo'); }),
          P('Backend simulasi di peramban · ' + D.VERSION.source_release + ' · HematDaya Design System 1.0.0-draft · PRD Generic 1.2', 'type-caption hd-secondary')), 'lain-h'));
    }

    /* ======================= Tentang demo (secondary) ======================= */
    function DemoInfo() {
      var dv = st.view.demo || (st.view.demo = { scenario: ws.scenarioId || 'h-base' });
      var m = D.manifest(ws);
      function failSel(op, label, opts) {
        return h(HD.ChoiceGroup, { key: op, type: 'select', legend: label, value: ws.failNext[op] || '', onChange: function (v) { upd(function () { if (v) ws.failNext[op] = v; else delete ws.failNext[op]; }); },
          options: [{ value: '', label: 'Normal' }].concat(opts) });
      }
      var REJ = { value: 'reject', label: 'Ditolak sebelum disimpan' }, INT = { value: 'interrupt', label: 'Terputus setelah tersimpan (status belum diketahui)' }, EXP = { value: 'expired', label: 'Sesi berakhir' };
      return h(Fragment, null, h(HD.Screen, { title: 'Tentang demo', back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        h(HD.Notice, { tone: 'info', title: ws.mode === 'demo' ? 'Demo · Data simulasi' : 'Ruang kerja lokal' }, 'Backend simulasi berjalan di peramban ini. Tidak ada akun, server tersimpan, meter langsung, notifikasi atau pengiriman data. Tarif Rp1.500/kWh adalah tarif simulasi, bukan tarif PLN.'),
        ws.mode === 'demo' && Section('Skenario demo', h('div', { className: 'hd-stack' },
          P('Aktif: ' + ws.scenarioName, 'type-label-strong'),
          h(HD.ChoiceGroup, { legend: 'Pilih skenario', value: dv.scenario, onChange: function (v) { upd(function () { dv.scenario = v; }); }, options: D.SCENARIOS.map(function (s) { return { value: s.id, label: s.name, description: s.desc }; }) }),
          Btn('primary', 'Muat skenario', function () { upd(function () { var nw = D.buildScenario(dv.scenario); openWorkspace('demo', nw); st.route.stacks.beranda = [{ name: 'home' }]; st.flash = { title: 'Skenario dimuat', body: nw.scenarioName + '. Hanya data demo yang berubah.' }; }); })), 'sc-h'),
        Section('Waktu dan koneksi', h('div', { className: 'hd-stack' },
          P('Waktu ' + (ws.mode === 'demo' ? 'virtual' : 'perangkat') + ': ' + D.fmtDateTime(ws.nowMs, ws.site.tz) + ' ' + ws.site.tz, 'type-label'),
          h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Koneksi aplikasi', value: ws.client.offline ? ['off'] : [], onChange: function (v) { upd(function () { ws.client.offline = v.length > 0; if (ws.client.offline && !ws.client.cachedAtMs) ws.client.cachedAtMs = ws.nowMs; ws.revision++; }); },
            options: [{ value: 'off', label: 'Simulasikan aplikasi offline', description: 'Membaca data tersimpan dan draf tetap bisa; penyimpanan menunggu online.' }] })), 'tc-h'),
        Section('Simulasi kegagalan berikutnya', h('div', { className: 'hd-stack' },
          failSel('import', 'Konfirmasi impor', [REJ, INT, EXP]), failSel('settings', 'Simpan pengaturan', [REJ, INT, EXP]), failSel('feedback', 'Umpan balik saran', [REJ]),
          failSel('scope', 'Simpan cakupan', [REJ]), failSel('asset', 'Simpan perangkat', [REJ]), failSel('source', 'Sumber simulasi', [REJ]), failSel('metric', 'Simpan metrik', [REJ]),
          P('Berlaku sekali untuk operasi berikutnya. Kegagalan tidak mengubah data terkonfirmasi.', 'type-label hd-secondary')), 'fail-h'),
        Section('Komposisi produk', h('div', { className: 'hd-stack' },
          h(HD.ChoiceGroup, { legend: 'Komposisi', value: ws.composition, onChange: function (v) { upd(function () { ws.composition = v; ws.revision++; }); }, options: [
            { value: 'full', label: D.COMPOSITIONS.full.label, description: 'Inti pengukuran ditambah biaya, jadwal dan metrik keluaran.' },
            { value: 'core', label: D.COMPOSITIONS.core.label, description: 'Hanya energi, cakupan, kualitas dan bukti. Aritmetika energi sama.' }] }),
          KV([['Rilis sumber', m.source_release], ['Komposisi', m.composition.id + ' v' + m.composition.version], ['Kemampuan aktif', m.capabilities.join(', ')],
            ['Adaptor', m.adapters.map(function (x) { return x.id + ': ' + x.status; }).join('; ')], ['Kebijakan', m.policies.baseline + ', ' + m.policies.change + ', ' + m.policies.stale], ['Perhitungan', m.calc]])), 'comp-h'),
        Section('Ruang kerja', h('div', { className: 'hd-stack hd-stack--tight' },
          ws.mode === 'demo' ? Btn('secondary', 'Buka ruang kerja lokal', function () { upd(function () { var lw = st.ws.local || D.emptyWorkspace('local'); if (!st.ws.local) { lw.nowMs = Date.now(); lw.initialPeriod = { preset: 'last7', start: D.addDays(D.localDate(lw.nowMs, lw.site.tz), -7), end: D.addDays(D.localDate(lw.nowMs, lw.site.tz), -1) }; } openWorkspace('local', lw); }); })
            : Btn('secondary', st.ws.demo ? 'Kembali ke demo' : 'Buka demo rumah tangga', function () { upd(function () { openWorkspace('demo', st.ws.demo || D.buildScenario('h-base')); }); }),
          ws.mode === 'demo' && Btn('destructive', 'Reset data demo', function () { upd(function () { st.sheet = 'reset'; }); }),
          P('Data impor di ruang kerja lokal tidak tersimpan setelah halaman ditutup; berkas perlu dipilih ulang.', 'type-label hd-secondary')), 'ws-h')),
        h(HD.SheetDialog, { open: st.sheet === 'reset', title: 'Reset data demo?', onClose: function () { upd(function () { st.sheet = null; }); },
          footer: h(Fragment, null, Btn('destructive', 'Reset demo', function () { upd(function () { st.sheet = null; var id = ws.scenarioId; openWorkspace('demo', D.buildScenario(id)); st.flash = { title: 'Data demo dikembalikan ke awal', body: 'Ruang kerja lokal dan impornya tidak berubah.' }; }); }, { fullWidth: true }),
            Btn('text', 'Batal', function () { upd(function () { st.sheet = null; }); }, { fullWidth: true })) },
          P('Hanya data demo skenario "' + ws.scenarioName + '" yang dikembalikan ke awal, termasuk impor, umpan balik dan pengaturan di dalam demo. Ruang kerja lokal tidak berubah.')));
    }

    /* ======================= S10 Import ======================= */
    function Import() {
      var dr = st.drafts.import || (st.drafts.import = { step: 'input', text: '', fileName: '', submitCount: 0 });
      var ex = EXAMPLES(ws.site.context);
      function setStep(s) { upd(function () { dr.step = s; }); }
      var stepBack = { input: null, mapping: 'input', preview: 'mapping', result: null }[dr.step];
      var screenBack = { label: 'Kembali', onClick: function () { if (stepBack) setStep(stepBack); else back(); } };
      var labels = { input: 'Langkah 1 dari 4 · Berkas', mapping: 'Langkah 2 dari 4 · Arti kolom dan pemetaan', preview: 'Langkah 3 dari 4 · Pratinjau', result: 'Langkah 4 dari 4 · Hasil' };
      var body;
      if (dr.step === 'input') {
        var o = opState(st, 'parse');
        body = h(Fragment, null,
          h(HD.ErrorSummary, { errors: dr.parseErrors || [], submitCount: dr.submitCount }),
          h(HD.Notice, { tone: 'info', title: 'Syarat berkas' }, 'CSV UTF-8 (BOM boleh), pemisah koma atau titik koma. Maksimal 10 MiB dan 150.000 baris data. Nama perangkat paling banyak 60 karakter. Energi angka 0 atau lebih; kosong tidak dianggap 0. Zona waktu dan panjang interval dikonfirmasi di langkah berikutnya.'),
          h('div', { className: 'hd-stack hd-stack--tight hd-file' },
            h('label', { htmlFor: 'csv-file', className: 'type-label-strong' }, 'Pilih berkas CSV'),
            h('input', { id: 'csv-file', type: 'file', accept: '.csv,text/csv,text/plain', onChange: function (e) {
              var f = e.target.files && e.target.files[0]; if (!f) return;
              if (f.size > D.LIMITS.bytes) { upd(function () { dr.fileName = f.name; dr.text = ''; dr.parseErrors = [{ targetId: 'csv-file', text: 'Ukuran ' + f.name + ' melebihi batas 10 MiB.' }]; dr.submitCount++; }); return; }
              var rd = new FileReader(); rd.onload = function () { upd(function () { dr.text = String(rd.result); dr.fileName = f.name; dr.parseErrors = []; }); }; rd.readAsText(f);
            } }),
            dr.fileName ? P('Berkas: ' + dr.fileName + '. Setelah peramban ditutup, berkas perlu dipilih ulang.', 'type-label') : null),
          h(HD.TextField, { id: 'csv-input', label: 'Atau tempel isi CSV', multiline: true, rows: 6, optional: true, value: dr.text, onChange: function (v) { upd(function () { dr.text = v; if (!dr.fileName || dr.pasted) { dr.fileName = 'tempelan.csv'; dr.pasted = true; } }); },
            error: (dr.parseErrors || []).length ? dr.parseErrors[0].text : null, draftNote: dr.text ? 'Isi tetap tersimpan bila Anda kembali.' : undefined }),
          h(HD.Disclosure, { summary: 'Contoh berkas yang dapat disalin' }, h('div', { className: 'hd-stack' }, ex.map(function (e) {
            return h('div', { key: e.id, className: 'hd-stack hd-stack--tight' }, P(e.label, 'type-body-strong'), h('pre', { tabIndex: 0, 'aria-label': 'Contoh ' + e.label }, e.text.replace(/^﻿/, '')),
              Btn('text', 'Gunakan contoh ini', function () { upd(function () { dr.text = e.text; dr.fileName = e.file; dr.pasted = false; dr.parseErrors = []; }); }));
          }))),
          Btn('primary', 'Periksa berkas', function () {
            upd(function () { st.ops.parse = { state: 'saving' }; });
            setTimeout(function () { upd(function () {
              var p = D.parseCsv(dr.text, dr.fileName || 'tempelan.csv'); st.ops.parse = { state: null };
              dr.submitCount++;
              if (!p.ok) { dr.parseErrors = p.errors.map(function (e) { return { targetId: 'csv-input', text: e.message }; }); return; }
              dr.parseErrors = []; dr.parsed = p;
              if (!dr.mapping || dr.mappingHash !== p.textHash) { dr.mapping = D.defaultMapping(ws, p); dr.mappingHash = p.textHash; }
              dr.step = 'mapping';
            }); }, 200);
          }, { loading: o.state === 'saving', loadingLabel: 'Memeriksa berkas…', fullWidth: true }));
      } else if (dr.step === 'mapping') {
        var p = dr.parsed, mp = dr.mapping, issues = D.buildPreview(ws, p, mp).mappingIssues;
        var shown = dr.mapTried ? issues : [];
        function errFor(id) { var e = shown.filter(function (x) { return x.id === id; })[0]; return e ? e.message : null; }
        function setM(patch) { upd(function () { Object.assign(mp, patch); }); }
        var assetOpts = [{ value: 'new', label: 'Buat perangkat baru' }].concat(ws.assets.filter(function (a) { return !a.archived; }).map(function (a) { return { value: a.id, label: a.name + ' · ' + D.KIND_LABEL[a.kind] + (a.location ? ' · ' + a.location : '') + ' · ID ' + a.id.slice(-6) }; }));
        body = h(Fragment, null,
          h(HD.ErrorSummary, { errors: shown.map(function (x) { return { targetId: x.id, text: x.message }; }), submitCount: dr.mapSubmit || 0 }),
          P(p.fileName + ' · ' + p.totalRows + ' baris data · pemisah ' + (p.delimiter === ';' ? 'titik koma' : 'koma') + ' · kolom: ' + p.headers.join(', '), 'type-label-strong'),
          p.valueKinds.length > 1 && h(HD.ChoiceGroup, { id: 'map-kind', legend: 'Jenis nilai yang dipakai', required: true, value: mp.valueKind, error: errFor('map-kind'), onChange: function (v) { setM({ valueKind: v }); },
            options: p.valueKinds.map(function (k) { return { value: k, label: { wh: 'Energi interval (Wh)', w: 'Daya rata-rata (W)', cum: 'Penghitung kumulatif (Wh)' }[k] + ' · kolom ' + p.headers[p.columns[k]] }; }), help: 'Energi dan daya yang setara tidak dijumlahkan.' }),
          mp.valueKind === 'w' && h(HD.ChoiceGroup, { id: 'map-power', legend: 'Arti kolom ' + p.headers[p.columns.w], required: true, value: mp.powerMeaning, error: errFor('map-power'), onChange: function (v) { setM({ powerMeaning: v }); },
            options: [{ value: 'average', label: 'Daya rata-rata selama interval', description: 'Diubah menjadi energi: W × durasi.' }, { value: 'instant', label: 'Daya sesaat (titik waktu)', description: 'Tidak dapat menjadi energi; impor diblokir.' }] }),
          mp.valueKind === 'cum' && h(HD.Notice, { tone: 'info', title: 'Penghitung kumulatif' }, 'Energi dihitung dari selisih dua pembacaan berurutan. Nilai yang turun dianggap reset: interval itu tidak diketahui, bukan negatif.'),
          p.naive && h('div', { className: 'hd-stack hd-stack--tight' },
            h(HD.ChoiceGroup, { type: 'select', legend: 'Zona waktu untuk waktu tanpa offset', value: mp.tz, onChange: function (v) { setM({ tz: v }); }, options: Object.keys(D.TZ).map(function (k) { return { value: k, label: D.TZ_LABEL[k] }; }) }),
            h(HD.ChoiceGroup, { id: 'map-tz', type: 'checkbox', legend: 'Konfirmasi zona waktu', required: true, value: mp.tzConfirmed ? ['ok'] : [], error: errFor('map-tz'), onChange: function (v) { setM({ tzConfirmed: v.length > 0 }); },
              options: [{ value: 'ok', label: 'Waktu dalam berkas adalah waktu lokal ' + mp.tz }] })),
          p.columns.ts != null && mp.valueKind !== 'cum' && h(HD.TextField, { id: 'map-interval', label: 'Panjang interval (menit)', optional: true, value: mp.intervalMinutes, error: errFor('map-interval'), onChange: function (v) { setM({ intervalMinutes: v.trim() }); },
            help: 'Timestamp dibaca sebagai awal interval. Disimpulkan: ' + Object.keys(p.cadence).map(function (k) { return k + ' = ' + (p.cadence[k] ? p.cadence[k] / 60000 + ' menit' : 'tidak dapat disimpulkan'); }).join('; ') + '. Isi untuk menimpa.' }),
          p.assetNames.map(function (nm, i) {
            return h(HD.ChoiceGroup, { key: nm, id: 'map-asset-' + i, type: 'select', legend: 'Perangkat untuk "' + nm + '"', value: mp.assetMap[nm], placeholder: 'Pilih perangkat', error: errFor('map-asset-' + i), onChange: function (v) { upd(function () { mp.assetMap[nm] = v; }); }, options: assetOpts });
          }),
          h(HD.ChoiceGroup, { id: 'map-scope', legend: 'Apakah beban perangkat dalam berkas ini terukur terpisah?', required: true, value: mp.scope, error: errFor('map-scope'), onChange: function (v) { setM({ scope: v }); },
            options: [{ value: 'disjoint', label: 'Ya, terpisah satu sama lain dan dari perangkat lain', description: 'Nilainya boleh dijumlahkan.' }, { value: 'unknown', label: 'Belum tahu', description: 'Nilai tampil per perangkat; total gabungan menunggu peninjauan di Cakupan & sumber.' }] }),
          Btn('primary', 'Lihat pratinjau', function () {
            upd(function () { dr.mapTried = true; dr.mapSubmit = (dr.mapSubmit || 0) + 1; });
            if (D.buildPreview(ws, p, mp).mappingIssues.length) return;
            upd(function () { dr.preview = D.buildPreview(ws, p, mp); dr.ack = false; dr.ackError = null; dr.step = 'preview'; });
          }, { fullWidth: true }),
          Btn('text', 'Ubah berkas', function () { setStep('input'); }, { fullWidth: true }));
      } else if (dr.step === 'preview') {
        var pv = dr.preview, so = opState(st, 'import:' + pv.opKey);
        function commit() {
          if (pv.needsAck && !dr.ack) { upd(function () { dr.ackError = 'Centang konfirmasi bahwa ' + pv.invalid + ' baris tidak valid tidak akan diimpor.'; dr.ackSubmit = (dr.ackSubmit || 0) + 1; }); return; }
          run('import:' + pv.opKey, D.api.commitImport(ws, pv), function (res) { dr.result = res; dr.step = 'result'; });
        }
        body = h(Fragment, null,
          h(HD.ErrorSummary, { errors: dr.ackError ? [{ targetId: 'imp-ack', text: dr.ackError }] : [], submitCount: dr.ackSubmit || 0 }),
          h(HD.ImportPreview, { fileName: pv.fileName, periodLabel: pv.periodStartIso ? D.fmtRange(pv.periodStartIso, pv.periodEndIso) : undefined, totalRows: pv.totalRows, invalidRows: pv.invalid, duplicateRows: pv.duplicates, conflictRows: pv.conflicts,
            mapping: pv.mapping, assumptions: pv.assumptions, errors: [], acknowledged: dr.ack, ackInputId: 'imp-ack', ackError: dr.ackError, onAcknowledge: function (v) { upd(function () { dr.ack = v; if (v) dr.ackError = null; }); },
            saveState: so.state, onConfirm: commit, checking: opState(st, 'check:' + pv.opKey).state === 'saving',
            onCheckStatus: function () { run('check:' + pv.opKey, D.api.checkOperation(ws, pv.opKey), function (res) { if (res.status === 'committed') { st.ops['import:' + pv.opKey] = { state: 'success' }; dr.result = Object.assign({ checked: true }, res); dr.step = 'result'; } else st.ops['import:' + pv.opKey] = { state: 'failure', message: 'Impor belum dikonfirmasi. Data tersimpan sebelumnya tetap tersedia. Anda dapat mencoba lagi.' }; }); },
            onCancel: function () { setStep('mapping'); } }),
          so.message && P(so.message, so.state === 'failure' ? 'hd-qualifier type-label-strong' : 'type-label'),
          pv.counterAnchors > 0 && P(pv.counterAnchors + ' baris adalah titik awal penghitung: valid, tetapi tidak menghasilkan energi.', 'type-label'),
          pv.blockReasons.filter(function (r) { return !/^Impor diblokir: \d+ dari/.test(r); }).length > 0 && h(HD.Notice, { tone: 'error', title: 'Impor diblokir' }, pv.blockReasons.filter(function (r) { return !/^Impor diblokir: \d+ dari/.test(r); }).join(' ')),
          pv.errors.length > 0 && h('section', { className: 'hd-stack hd-stack--tight', 'aria-labelledby': 'rowerr-h' },
            h('h2', { id: 'rowerr-h', className: 'type-body-strong' }, 'Baris yang tidak valid (' + pv.errors.length + ')'),
            P('Nomor baris data tidak menghitung header dan baris kosong; nomor baris file disebut bila berbeda dari baris data + 1.', 'type-label hd-secondary'),
            h('ul', { className: 'hd-errlist' }, pv.errors.slice(0, 50).map(function (e) { return h('li', { key: e.id, id: e.id, tabIndex: -1, className: 'type-body' }, e.message); })),
            pv.errors.length > 50 ? P((pv.errors.length - 50) + ' kesalahan lain tidak ditampilkan.', 'type-label') : null),
          P('Konfirmasi impor membuat satu operasi atomik (' + pv.opKey + '). Mencoba lagi memakai kunci yang sama sehingga data tidak terimpor dua kali.', 'type-caption hd-secondary'),
          Btn('text', 'Ubah pemetaan', function () { setStep('mapping'); }, { fullWidth: true }));
      } else {
        var r = dr.result;
        body = h(Fragment, null,
          h(HD.Notice, { tone: 'success', title: r.replayed || r.checked ? 'Impor sudah dikonfirmasi sebelumnya' : 'Impor dikonfirmasi', live: true },
            (r.replayed || r.checked ? 'Operasi yang sama ditemukan; tidak diimpor dua kali. ' : '') + r.acceptedRows + ' baris diterima, ' + r.added + ' interval energi ditambahkan, ' + r.skippedInvalid + ' baris tidak valid dilewati, ' + r.duplicates + ' duplikat dihitung sekali.'),
          KV([['Berkas', r.fileName], ['Periode data', r.periodStartIso ? D.fmtRange(r.periodStartIso, r.periodEndIso) : '—'], ['Perangkat baru', r.assetsCreated.join(', ') || 'Tidak ada'], ['Perangkat yang dipakai', r.assetsMapped.join(', ') || 'Tidak ada'], ['Asal data', 'Impor CSV · data historis'], ['Operasi', r.opKey]]),
          Btn('primary', 'Lihat periode data', function () {
            upd(function () {
              var end = r.periodEndIso > today() ? today() : r.periodEndIso, start = D.addDays(end, -6) < r.periodStartIso ? r.periodStartIso : D.addDays(end, -6);
              st.period = { preset: 'range', start: start, end: end }; st.drafts.import = null; st.route.tab = 'beranda'; st.route.stacks.beranda = [{ name: 'home' }];
              if (r.periodEndIso > today()) st.flash = { tone: 'info', title: 'Sebagian data setelah hari ini', body: 'Data setelah ' + D.fmtDate(today()) + ' belum ditampilkan; waktu perangkat tidak diubah.' };
            });
          }, { icon: 'calendar', fullWidth: true }),
          Btn('text', 'Impor berkas lain', function () { upd(function () { st.drafts.import = null; }); }, { fullWidth: true }));
      }
      return h(HD.Screen, { title: 'Impor data', subtitle: labels[dr.step], back: screenBack, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab }, body,
        dr.step !== 'result' && Btn('text', 'Tutup impor (draf tetap tersimpan)', back, { fullWidth: true }));
    }

    /* ======================= S11 Scope ======================= */
    function Scope(params) {
      var dr = st.drafts.scope;
      if (!dr) {
        dr = st.drafts.scope = { selection: ws.selection.slice(), disjoint: {}, alt: {} };
        if (params.preset) { if (dr.selection.indexOf(params.preset) < 0) dr.selection.push(params.preset); dr.selection = dr.selection.filter(function (x) { return x !== params.drop; }); }
      }
      var d = derived(), tz = ws.site.tz, o = opState(st, 'scope');
      var active = ws.assets.filter(function (a) { return !a.archived; });
      function val(id) { return D.assetSlice(proposed, D.assetById(proposed, id), d.q.startMs, d.q.endMs); }
      var relations = ws.relations.filter(function (r) { return !(r.type === 'unknown' && dr.disjoint[r.a + '|' + r.b]); });
      var assets = ws.assets.map(function (a) {
        if (!a.altPending || !dr.alt[a.id]) return a;
        var keep = dr.alt[a.id];
        return Object.assign({}, a, { altPending: null, bindings: a.bindings.filter(function (b) { return b.sourceId === keep; }) });
      });
      var proposed = Object.assign({}, ws, { relations: relations, assets: assets, revision: ws.revision + 0.5 });
      var issues = D.scopeIssues(proposed, dr.selection);
      var preview = issues.length ? null : D.summarize(proposed, { startMs: d.q.startMs, endMs: d.q.endMs, assetIds: dr.selection });
      var contains = ws.relations.filter(function (r) { return r.type === 'contains'; }).reduce(function (acc, r) { var g = acc.filter(function (x) { return x.a === r.a; })[0]; if (g) g.kids.push(r.b); else acc.push({ a: r.a, kids: [r.b] }); return acc; }, []), unknown = ws.relations.filter(function (r) { return r.type === 'unknown'; });
      var alts = ws.assets.filter(function (a) { return a.altPending && a.altPending.length > 1; });
      function toggle(id, on) { upd(function () { dr.selection = on ? dr.selection.concat([id]) : dr.selection.filter(function (x) { return x !== id; }); }); }
      function save() { run('scope', D.api.saveScope(ws, { selection: dr.selection, relations: relations, assets: assets }), function () { st.drafts.scope = null; st.flash = { title: 'Cakupan dikonfirmasi', body: 'Total gabungan memakai ' + dr.selection.length + ' perangkat yang tidak saling mencakup.' }; popRoute(); }); }
      return h(HD.Screen, { title: 'Cakupan & sumber', subtitle: periodLabel(), back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        P('Total gabungan hanya dihitung dari perangkat yang tidak saling mencakup dan dari satu sumber acuan per beban. Nilai masing-masing tetap terlihat.'),
        contains.map(function (r) {
          var A = D.assetById(ws, r.a), inSel = function (x) { return dr.selection.indexOf(x) >= 0; };
          var view = inSel(r.a) && !r.kids.some(inSel) ? 'parent' : !inSel(r.a) && r.kids.every(inSel) ? 'child' : undefined;
          var kids = r.kids, va = val(r.a), vk = kids.map(val), Bname = kids.map(function (k) { return D.assetById(ws, k).name; }).join(', ');
          if (va.conflict || vk.some(function (x) { return x.conflict; })) return h(HD.Notice, { key: r.a, tone: 'info', title: A.name + ' sudah mencakup ' + Bname }, 'Pilih sumber acuan di bawah terlebih dahulu; setelah itu pilih tampilan ' + A.name + ' atau ' + Bname + ' saja. Nilainya tidak pernah dijumlahkan.');
          var kidSum = vk.reduce(function (t, x) { return t + x.mWh; }, 0);
          return h('div', { key: r.a, className: 'hd-group' }, h(HD.ScopeSummary, { count: 1, overlap: 'parentChild', parent: { name: A.name, kwh: kwh(va.mWh) }, child: { name: Bname, kwh: kwh(kidSum), description: kids.length > 1 ? 'Hanya perangkat terukur di dalam ' + A.name + '; sisanya tidak diberi nama.' : undefined }, view: view,
            onViewChange: function (v) { upd(function () { if (v === 'parent') { dr.selection = dr.selection.filter(function (x) { return kids.indexOf(x) < 0; }); if (dr.selection.indexOf(r.a) < 0) dr.selection.push(r.a); } else { dr.selection = dr.selection.filter(function (x) { return x !== r.a; }); kids.forEach(function (k) { if (dr.selection.indexOf(k) < 0) dr.selection.push(k); }); } }); } }));
        }),
        unknown.map(function (r) {
          var A = D.assetById(ws, r.a), B = D.assetById(ws, r.b), k = r.a + '|' + r.b;
          if (!A || !B) return null;
          var vals = [[A, val(r.a)], [B, val(r.b)]].filter(function (x) { return x[1].mWh != null && x[1].covered.length; }).map(function (x) { return { name: x[0].name, kwh: kwh(x[1].mWh) }; });
          return h('div', { key: k, className: 'hd-group hd-stack' }, h(HD.ScopeSummary, { count: 2, overlap: 'unknown', values: vals }),
            h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Hubungan ' + A.name + ' dan ' + B.name, value: dr.disjoint[k] ? ['yes'] : [], onChange: function (v) { upd(function () { dr.disjoint[k] = v.length > 0; }); },
              options: [{ value: 'yes', label: 'Saya memastikan keduanya mengukur beban yang terpisah', description: 'Jangan centang bila ragu. Anda juga dapat mengeluarkan salah satunya dari cakupan.' }] }));
        }),
        alts.map(function (a) {
          var s = D.assetSlice(ws, a, d.q.startMs, d.q.endMs);
          return h('div', { key: 'alt' + a.id, className: 'hd-group hd-stack' },
            h(HD.Notice, { tone: 'attention', title: a.name + ': dua sumber untuk beban yang sama' }, 'Sumber pengganti tidak dijumlahkan. Pilih sumber acuan; sumber lain tetap tersimpan sebagai riwayat.'),
            h(HD.ChoiceGroup, { legend: 'Sumber acuan untuk ' + a.name, value: dr.alt[a.id] || null, onChange: function (v) { upd(function () { dr.alt[a.id] = v; }); },
              options: a.altPending.map(function (sid, i) { var src = D.sourceById(ws, sid); return { value: sid, label: src.label + ' · ' + (s.bySource[sid] == null ? 'belum ada data pada periode ini' : D.fmtKwh(s.bySource[sid])), description: i === 0 ? 'Sumber pertama' : 'Sumber baru; pilih yang pertama untuk melewati sumber baru' }; }),
              help: 'Berlaku untuk seluruh riwayat perangkat ini.' }));
        }),
        h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Perangkat dalam cakupan', value: dr.selection, onChange: function (v) { upd(function () { dr.selection = v; }); },
          options: active.map(function (a) { var s = val(a.id); return { value: a.id, label: a.name, description: D.KIND_LABEL[a.kind] + ' · ' + (s.conflict ? 'menunggu sumber acuan' : s.covered.length ? D.fmtKwh(s.mWh) : 'belum ada data') }; }) }),
        issues.length ? h(HD.Notice, { tone: 'attention', title: 'Pilihan belum valid' }, issues.map(function (i) { return i.text; }).join(' '))
          : preview && h(HD.Notice, { tone: 'info', title: 'Pratinjau cakupan' }, 'Termasuk: ' + preview.rows.map(function (r) { return r.asset.name; }).join(', ') + '. ' + (preview.excluded.length ? 'Tidak termasuk: ' + preview.excluded.map(function (x) { return x.name + ' (' + x.reason.toLowerCase() + ')'; }).join(', ') + '. ' : '') + 'Total gabungan: ' + (preview.totalMWh == null ? 'belum ada data' : D.fmtKwh(preview.totalMWh)) + '.'),
        o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Cakupan belum tersimpan', detail: o.message + ' Pilihan Anda tetap ada; cakupan terkonfirmasi sebelumnya masih dipakai.', onRetry: save }),
        Btn('primary', 'Konfirmasi cakupan', save, { fullWidth: true, loading: o.state === 'saving', loadingLabel: 'Menyimpan…',
          disabledReason: !dr.selection.length ? 'Pilih minimal satu perangkat.' : issues.length ? 'Cakupan masih tumpang tindih atau sumber acuan belum dipilih.' : null }),
        Btn('text', 'Batal', function () { upd(function () { st.drafts.scope = null; }); back(); }, { fullWidth: true }));
    }

    /* ======================= S12 Output metric ======================= */
    function Metric(params) {
      var dr = st.drafts.metric;
      if (!dr) { var m0 = ws.metric || {}; dr = st.drafts.metric = { name: m0.name || '', assetIds: (m0.assetIds || ws.selection).slice(), unit: m0.unit || 'unit', product: m0.product || '', method: m0.method || 'actual',
        quantityText: m0.quantity != null ? String(m0.quantity) : '', perDayText: m0.perDay != null ? String(m0.perDay) : '', periodStart: m0.periodStart || st.period.start, periodEnd: m0.periodEnd || st.period.end, uniform: false, winStart: '08:00', winEnd: '16:00', preview: null }; }
      var o = opState(st, 'metric');
      if (ws.composition === 'core') return h(HD.Screen, { title: 'Metrik energi per keluaran', back: { label: 'Kembali', onClick: back }, current: st.route.tab, onNavigate: goTab },
        h(HD.Notice, { tone: 'neutral', title: 'Modul metrik keluaran tidak aktif' }, 'Komposisi Inti saja. Pemantauan energi tetap lengkap.'));
      var qn = HD.format.parseDecimal(dr.quantityText || ''), pd = HD.format.parseDecimal(dr.perDayText || '');
      function def() {
        var b = D.periodBounds({ start: dr.periodStart, end: dr.periodEnd }, ws.site.tz), partial = ws.nowMs > b.start && ws.nowMs < b.end;
        return { name: dr.name.trim(), assetIds: dr.assetIds, unit: dr.unit.trim(), product: dr.product, method: dr.method, quantity: qn.empty ? null : qn.valid ? qn.value : NaN, perDay: pd.empty ? null : pd.valid ? pd.value : NaN,
          periodStart: dr.periodStart, periodEnd: dr.periodEnd, uniformConfirmed: partial && dr.uniform, outputWindows: partial && dr.uniform ? [{ days: [D.weekday(ws.nowMs, ws.site.tz)], start: dr.winStart, end: dr.winEnd }] : null };
      }
      var errs = [];
      if (dr.tried) {
        if (!dr.name.trim()) errs.push({ targetId: 'met-name', text: 'Isi nama metrik.' });
        if (!dr.unit.trim()) errs.push({ targetId: 'met-unit', text: 'Isi satuan keluaran, misalnya unit, batch atau kg.' });
        if (!dr.assetIds.length) errs.push({ targetId: 'met-assets', text: 'Pilih minimal satu perangkat pembilang.' });
        if (dr.preview && !dr.preview.ok) errs.push({ targetId: dr.preview.field === 'perDay' ? 'met-perday' : dr.preview.field === 'quantity' ? 'met-qty' : 'met-assets', text: dr.preview.reason });
      }
      var b = D.periodBounds({ start: dr.periodStart, end: dr.periodEnd }, ws.site.tz), partialDay = ws.nowMs > b.start && ws.nowMs < b.end;
      function doPreview() { upd(function () { dr.tried = true; dr.submitCount = (dr.submitCount || 0) + 1; dr.preview = !dr.name.trim() || !dr.unit.trim() ? { ok: false, reason: 'Lengkapi nama dan satuan.' } : D.computeMetric(ws, def()); }); }
      var pv = dr.preview && dr.preview.ok ? dr.preview : null;
      return h(HD.Screen, { title: 'Metrik energi per keluaran', subtitle: 'Opsional · tidak diperlukan untuk pemantauan', back: { label: 'Kembali', onClick: back }, provenance: provOf(ws), current: st.route.tab, onNavigate: goTab },
        h(HD.ErrorSummary, { errors: errs, submitCount: dr.submitCount || 0 }),
        h(HD.TextField, { id: 'met-name', label: 'Nama metrik', required: true, value: dr.name, error: errs.filter(function (e) { return e.targetId === 'met-name'; }).length ? 'Isi nama metrik.' : null, onChange: function (v) { upd(function () { dr.name = v; dr.preview = null; }); } }),
        h(HD.ChoiceGroup, { id: 'met-assets', type: 'checkbox', legend: 'Pembilang: perangkat yang dihitung', value: dr.assetIds, error: errs.filter(function (e) { return e.targetId === 'met-assets'; }).map(function (e) { return e.text; })[0] || null,
          onChange: function (v) { upd(function () { dr.assetIds = v; dr.preview = null; }); }, options: ws.assets.filter(function (a) { return !a.archived; }).map(function (a) { return { value: a.id, label: a.name, description: D.KIND_LABEL[a.kind] }; }), help: 'Perangkat tidak boleh saling mencakup.' }),
        h(HD.TextField, { id: 'met-unit', label: 'Satuan keluaran', required: true, value: dr.unit, error: errs.filter(function (e) { return e.targetId === 'met-unit'; }).length ? 'Isi satuan keluaran, misalnya unit, batch atau kg.' : null, onChange: function (v) { upd(function () { dr.unit = v; dr.preview = null; }); }, help: 'Satuan luas (m²) dan keluaran produksi tidak dicampur.' }),
        h(HD.TextField, { label: 'Produk atau arti keluaran', optional: true, value: dr.product, onChange: function (v) { upd(function () { dr.product = v; }); } }),
        P('Periode: ' + D.fmtRange(dr.periodStart, dr.periodEnd) + (partialDay ? ' (masih berjalan)' : ''), 'type-label-strong'),
        Btn('text', 'Pakai periode terpilih (' + D.fmtRange(st.period.start, st.period.end) + ')', function () { upd(function () { dr.periodStart = st.period.start; dr.periodEnd = st.period.end; dr.preview = null; }); }),
        h(HD.ChoiceGroup, { legend: 'Penyebut', value: dr.method, onChange: function (v) { upd(function () { dr.method = v; dr.preview = null; }); }, options: [{ value: 'actual', label: 'Aktual', description: 'Jumlah keluaran nyata untuk periode yang sama.' }, { value: 'estimated', label: 'Estimasi dari rata-rata', description: 'Rata-rata per hari produksi × hari produksi lengkap.' }] }),
        dr.method === 'actual' ? h(HD.NumericField, { id: 'met-qty', label: 'Jumlah keluaran aktual', unit: dr.unit || 'unit', value: dr.quantityText, showErrors: dr.tried, error: errs.filter(function (e) { return e.targetId === 'met-qty'; }).map(function (e) { return e.text; })[0] || null, onChange: function (t) { upd(function () { dr.quantityText = t; dr.preview = null; }); } })
          : h('div', { className: 'hd-stack' },
            h(HD.NumericField, { id: 'met-perday', label: 'Rata-rata keluaran per hari produksi', unit: dr.unit || 'unit', value: dr.perDayText, showErrors: dr.tried, error: errs.filter(function (e) { return e.targetId === 'met-perday'; }).map(function (e) { return e.text; })[0] || null, onChange: function (t) { upd(function () { dr.perDayText = t; dr.preview = null; }); }, note: 'Hari produksi: Senin–Sabtu.' }),
            partialDay && h(HD.ChoiceGroup, { type: 'checkbox', legend: 'Hari berjalan', value: dr.uniform ? ['u'] : [], onChange: function (v) { upd(function () { dr.uniform = v.length > 0; dr.preview = null; }); },
              options: [{ value: 'u', label: 'Keluaran merata selama jendela keluaran hari ini', description: 'Tanpa konfirmasi ini, hanya hari lengkap yang dihitung. Produksi batch tidak dianggap merata.' }] }),
            partialDay && dr.uniform && Row(h(HD.TextField, { label: 'Jendela keluaran mulai', type: 'time', value: dr.winStart, onChange: function (v) { upd(function () { dr.winStart = v; dr.preview = null; }); } }),
              h(HD.TextField, { label: 'Selesai', type: 'time', value: dr.winEnd, onChange: function (v) { upd(function () { dr.winEnd = v; dr.preview = null; }); } }))),
        Btn('secondary', 'Pratinjau metrik', doPreview, { fullWidth: true }),
        pv && h('div', { className: 'hd-group hd-stack' },
          h(HD.OutputMetricPreview, { enabled: true, energyKwh: kwh(pv.energyMWh), output: pv.output, unit: pv.unit, method: pv.method, periodLabel: pv.periodLabel }),
          KV([['Pembilang', dr.assetIds.map(function (id) { return D.assetById(ws, id).name; }).join(', ') + ' · ' + D.fmtKwh(pv.energyMWh)], ['Penyebut', (Math.round(pv.output * 100) / 100).toString().replace('.', ',') + ' ' + pv.unit + (dr.product ? ' (' + dr.product + ')' : '') + ' · ' + (pv.method === 'actual' ? 'aktual' : 'estimasi')],
            ['Periode', pv.periodLabel], ['Catatan', pv.notes.join(' ') || 'Periode lengkap; keluaran dan energi mencakup waktu yang sama.']]),
          P('Angka per keluaran yang lebih rendah adalah pengamatan, bukan bukti penghematan atau efisiensi peralatan.', 'type-label hd-secondary')),
        o.state === 'failure' && h(HD.ProgressStatus, { state: 'failure', label: 'Metrik belum tersimpan', detail: o.message + ' Metrik sebelumnya tidak berubah.' }),
        Btn('primary', 'Simpan metrik', function () { run('metric', D.api.saveMetric(ws, def()), function () { st.drafts.metric = null; st.flash = { title: 'Metrik disimpan', body: 'Ditampilkan di Beranda selama datanya valid.' }; popRoute(); }); },
          { fullWidth: true, loading: o.state === 'saving', loadingLabel: 'Menyimpan…', disabledReason: pv ? null : 'Buat pratinjau yang valid terlebih dahulu.' }),
        ws.metric && ws.metric.enabled && Btn('text', 'Nonaktifkan metrik', function () { run('metric-off', D.api.disableMetric(ws), function () { st.flash = { title: 'Metrik dinonaktifkan', body: 'Tampilan metrik dihapus. Pengukuran tidak berubah.' }; }); }, { fullWidth: true }),
        Btn('text', 'Batal', back, { fullWidth: true }));
    }

    /* ---------------- router ---------------- */
    var SCREENS = { home: Beranda, assets: Assets, saran: Saran, asset: Asset, source: Source, insight: Insight, hidden: Hidden, settings: Settings, demo: DemoInfo, import: Import, scope: Scope, metric: Metric };
    var content;
    if (!ws) content = Welcome();
    else { var t = top(); content = SCREENS[t.name](t.params); }
    return h('div', { className: 'hd-app hd-root', ref: scrollRef, lang: 'id', style: props && props.height ? { height: props.height } : undefined }, content,
      ws && ws.readings.length === 0 && top().name === 'home' ? null : null);
  }

  window.HematDayaApp = { App: App, version: '0.1.0' };
})();
