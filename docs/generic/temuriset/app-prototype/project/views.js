/* TemuRiset prototype views: routing, form state and view models over the one domain service.
   Markup stays in the .dc.html artboards. This file draws nothing except the slot adapter below. */
(function () {
  'use strict';
  var D = window.TemuRisetDomain, React = window.React;
  var STORE = 'temuriset-demo-v1';
  var svc = D.create();
  var ui, shellActive = false, listeners = [];

  var STAGES = { IDEA: 'Ide', PROTOTYPE: 'Prototipe', PILOT: 'Pilot', WORKING: 'Sudah berfungsi', MARKET: 'Siap pasar' };
  var STATUS = {
    PENDING_WORKSPACE_REVIEW: ['Menunggu tinjauan organisasi', 'neutral'], SUBMITTED: ['Terkirim', 'neutral'], UNDER_REVIEW: ['Sedang ditinjau', 'neutral'],
    REVISION_REQUESTED: ['Revisi diminta', 'warning'], APPROVED_FOR_DISCUSSION: ['Disetujui untuk diskusi', 'success'], REJECTED: ['Ditolak', 'danger'], WITHDRAWN: ['Ditarik', 'neutral'], CLOSED: ['Diskusi ditutup', 'neutral']
  };
  var READINESS = { READY_TO_SUBMIT: ['Siap dikirim', 'success'], NEEDS_INFORMATION: ['Perlu informasi', 'warning'], BLOCKED_FOR_THIS_TARGET: ['Terhalang untuk target ini', 'danger'] };
  var ELIGIBILITY_TONE = { ELIGIBLE: 'neutral', NEEDS_VERIFICATION: 'warning', INCOMPATIBLE: 'danger' };
  var ZONES = [{ value: 'Asia/Jakarta', label: 'WIB (Asia/Jakarta)' }, { value: 'Asia/Makassar', label: 'WITA (Asia/Makassar)' }, { value: 'Asia/Jayapura', label: 'WIT (Asia/Jayapura)' }];
  var SECTORS = ['Air dan sanitasi', 'Pertanian', 'Perangkat lunak', 'Material', 'Manufaktur', 'Energi'];
  var EN_ALIAS = { water: 'air', energy: 'energi', software: 'perangkat', agriculture: 'pertanian', farming: 'pertanian', packaging: 'kemasan', manufacturing: 'manufaktur' };
  var CONSENT_LABELS = { name: 'Nama pihak', type: 'Jenis kerja sama', scope: 'Cakupan', date: 'Tanggal', amount: 'Jumlah dana', percent: 'Persentase ekuitas' };

  function freshUi() {
    return { accountId: 'rani', partyId: 'p-rani', started: false, route: parse('#/start'), forms: {}, busy: {}, keys: {}, n: 0, filters: {}, notice: null, history: [], latency: 280, selected: {}, dialog: null, ai: {}, preflight: {} };
  }

  /* ---------- store plumbing ---------- */
  function render() { listeners.slice().forEach(function (l) { l(); }); }
  function persist() {
    if (!shellActive) return;
    try { localStorage.setItem(STORE, JSON.stringify({ domain: svc.state, accountId: ui.accountId, partyId: ui.partyId, started: ui.started })); } catch (e) { /* the demo still runs without storage */ }
  }
  function restore() {
    try {
      var raw = localStorage.getItem(STORE);
      if (!raw) return;
      var saved = JSON.parse(raw);
      if (saved.domain && saved.domain.schema === D.baseline().schema) { svc.replace(saved.domain); ui.accountId = saved.accountId; ui.partyId = saved.partyId; ui.started = saved.started; }
    } catch (e) { /* start from baseline */ }
  }
  function resetDemo() {
    try { localStorage.removeItem(STORE); } catch (e) { /* nothing stored */ }
    svc.replace(D.baseline());
    var started = false;
    ui = freshUi(); ui.started = started;
    setHash('#/start'); render();
  }
  function actor() { return { account: ui.accountId, party: ui.partyId }; }
  function acc() { return svc.state.accounts[ui.accountId]; }
  function persona() { return acc().persona; }
  function party(id) { return svc.state.parties[id] || { name: 'Pihak terbatas', kind: 'personal' }; }
  function ctx(key) { return { actor: actor(), key: key }; }
  function once(name) { if (!ui.keys[name]) { ui.n += 1; ui.keys[name] = name + '#' + ui.n; } return ui.keys[name]; }
  function spent(name) { delete ui.keys[name]; }
  function run(busyKey, call, done) {
    if (ui.busy[busyKey]) return;
    ui.busy[busyKey] = true; render();
    setTimeout(function () {
      var res = call();
      delete ui.busy[busyKey];
      if (done) done(res);
      persist(); render();
    }, shellActive ? ui.latency : 0);
  }
  function notice(text, tone) { ui.notice = { text: text, tone: tone || 'success' }; }

  /* ---------- routing ---------- */
  var ROUTES = [
    ['start', 'Start'], ['home', 'Home'], ['inventions/:id/edit', 'Editor'], ['inventions/:id', 'Invention'], ['inventions', 'Inventions'], ['discover', 'Discover'],
    ['support-requests/:id', 'Support'], ['support-requests', 'Support'], ['funding-requests/:id/edit', 'Funding'], ['funding-requests/:id', 'Funding'], ['partners/:id', 'Partner'],
    ['opportunities/:id/edit', 'Opportunity'], ['matches', 'Matches'], ['pitches/new', 'Preflight'], ['pitches/:id', 'Workspace'], ['pitches', 'Pitches'],
    ['partnerships/new', 'Partnership'], ['partnerships/:id', 'Partnership'], ['profiles/:id', 'Profile'], ['workspace/review-queue', 'ReviewQueue'], ['settings', 'Settings']
  ];
  function parse(hash) {
    var raw = String(hash || '').replace(/^#\/?/, ''), parts = raw.split('?'), path = parts[0], query = {};
    (parts[1] || '').split('&').filter(Boolean).forEach(function (kv) { var p = kv.split('='); query[decodeURIComponent(p[0])] = decodeURIComponent(p[1] || ''); });
    var segs = path.split('/').filter(Boolean);
    for (var r = 0; r < ROUTES.length; r++) {
      var pat = ROUTES[r][0].split('/'), params = {}, hit = pat.length === segs.length;
      for (var i = 0; hit && i < pat.length; i++) {
        if (pat[i].charAt(0) === ':') params[pat[i].slice(1)] = decodeURIComponent(segs[i]); else if (pat[i] !== segs[i]) hit = false;
      }
      if (hit) return { name: ROUTES[r][1], params: params, query: query, hash: '#/' + raw };
    }
    return { name: 'Home', params: {}, query: {}, hash: '#/home' };
  }
  function setHash(h) { try { if (shellActive && location.hash !== h) history.replaceState(null, '', h); } catch (e) { /* in-memory routing still works */ } }
  function focusMain(id) {
    setTimeout(function () {
      var el = (id && document.getElementById(id)) || document.getElementById('isi');
      if (el) el.focus();
      try { window.scrollTo(0, 0); } catch (e) { /* no scroll container */ }
    }, 40);
  }
  function go(path, opts) {
    var active = document.activeElement;
    ui.history.push({ hash: ui.route.hash, focusId: active && active.id });
    if (ui.history.length > 30) ui.history.shift();
    ui.route = parse(path);
    ui.notice = (opts && opts.keepNotice) ? ui.notice : null;
    setHash(ui.route.hash); enter(ui.route); render(); focusMain();
  }
  function back(fallback) {
    var prev = ui.history.pop();
    ui.route = parse(prev ? prev.hash : fallback);
    ui.notice = null;
    setHash(ui.route.hash); enter(ui.route); render(); focusMain(prev && prev.focusId);
  }
  function enter(route) {
    if (route.name === 'Editor') {
      var i = svc.state.inventions[route.params.id];
      if (i && svc.can(actor(), i.owner, 'edit')) svc.startDraft(ctx(), { id: i.id });
    }
    if (route.name === 'Matches' && shellActive) {
      ui.loading = route.hash;
      setTimeout(function () { ui.loading = null; render(); }, ui.latency);
    }
  }
  var NAV = {
    inovator: { beranda: '#/home', inovasi: '#/inventions', temukan: '#/discover', pitching: '#/pitches', profil: '#/settings' },
    mitra: { jelajahi: '#/discover', mandat: '#/partners/self', masuk: '#/pitches?box=masuk', diskusi: '#/pitches?box=diskusi', profil: '#/settings' }
  };
  function navigate(id) {
    var to = NAV[persona()][id];
    if (to.indexOf('self') >= 0) to = '#/partners/' + ui.partyId;
    go(to);
  }
  function setAccount(id, partyId) {
    ui.accountId = id;
    ui.partyId = partyId || svc.state.accounts[id].contexts[svc.state.accounts[id].contexts.length - 1];
    ui.forms = {}; ui.dialog = null; ui.selected = {}; ui.notice = null;
  }

  /* ---------- forms ---------- */
  function fid(key, name) { return (key + '-' + name).replace(/[^a-zA-Z0-9-]/g, '-'); }
  function form(key, init) {
    if (!ui.forms[key]) ui.forms[key] = { key: key, v: init(), err: {}, focusKey: 0, list: [], banner: null, dirty: false, save: 'saved' };
    return ui.forms[key];
  }
  function bind(f, name, extra) {
    return Object.assign({ id: fid(f.key, name), value: f.v[name], error: f.err[name] || null, onChange: function (x) {
      f.v[name] = x; f.dirty = true; f.save = 'local';
      if (f.err[name]) { delete f.err[name]; f.list = f.list.filter(function (e) { return e.fieldId !== fid(f.key, name); }); }
      render();
    } }, extra);
  }
  function fail(f, res) {
    f.err = res.fields || {};
    f.list = Object.keys(f.err).map(function (k) { return { fieldId: fid(f.key, k), message: f.err[k] }; });
    f.banner = f.list.length ? null : res.message;
    f.focusKey += 1;
  }
  function clearFail(f) { f.err = {}; f.list = []; f.banner = null; }
  function summary(f, retry) {
    if (!f.list.length && !f.banner) return { show: false };
    return { show: true, props: { id: fid(f.key, 'errors'), errors: f.list, focusKey: f.focusKey, title: f.list.length ? 'Masih ada yang perlu diperbaiki' : 'Belum berhasil', children: f.banner || undefined, retry: retry } };
  }

  /* ---------- formatting ---------- */
  function zone() { return acc().zone; }
  function clockLabel() { var t = svc.state.clock; return TR.format.longDate(t, 'UTC') + ', ' + TR.format.time(t, 'UTC') + ' UTC'; }
  function when(i) { return TR.format.date(i, zone()) + ', ' + TR.format.time(i, zone()) + ' ' + TR.format.zoneLabel(zone()); }
  function srFinancial(r) {
    if (r.noncash) return { subject: 'project', noncash: r.noncash };
    if (r.terms) return { subject: 'license', terms: r.terms };
    var b = r.budget;
    return { subject: 'project', currency: b.currency, min: b.min, max: b.max, period: b.period, scope: b.scope, estimateDate: b.estimateDate, assumptions: b.assumptions };
  }
  function oppFinancial(o) { return Object.assign({ compact: true }, o.financial); }
  function requestsOf(invId) { return Object.keys(svc.state.requests).map(function (k) { return svc.state.requests[k]; }).filter(function (r) { return r.inventionId === invId; }); }
  function fundingOf(invId) { return Object.keys(svc.state.fundings).map(function (k) { return svc.state.fundings[k]; }).filter(function (f) { return f.links.some(function (l) { return l.inventionId === invId; }); })[0] || null; }
  function cardProps(i) {
    var v = svc.pubV(i), rs = requestsOf(i.id).filter(function (r) { return r.status === 'ACTIVE'; }), r = rs[0], f = fundingOf(i.id);
    return { title: v.title, category: v.category, manager: 'Dikelola ' + party(i.owner).name + ' · ' + (party(i.owner).kind === 'personal' ? 'Pribadi' : 'Organisasi'), problem: v.problem, solution: v.solution, maturity: STAGES[v.stage],
      support: r ? r.outcome : f ? 'Mendukung Pendanaan Perusahaan ' + f.company : null, financial: r ? srFinancial(r) : null };
  }
  function fundingCard(f) {
    return { company: f.company, proposedEntity: f.subject === 'PROPOSED_ENTITY', stage: f.stage, form: f.form, purpose: f.purpose, currency: f.currency, target: f.target, desiredMin: f.desiredMin, desiredMax: f.desiredMax, partialAccepted: f.partial,
      inventions: f.links.map(function (l) { return svc.state.inventions[l.inventionId].versions[l.version - 1].title; }) };
  }
  function docProps(d, opts) {
    var v = opts && opts.version ? d.versions[opts.version - 1] : svc.last(d.versions), g = opts && opts.grant;
    return { title: d.title, version: v.n, file: v.file, extraction: v.extraction, review: v.review, grant: g ? { recipient: party(g.to).name, version: g.version, revoked: g.revoked } : null };
  }

  /* ---------- whose turn ---------- */
  function pitchTurn(p) {
    var mineIsRecipient = svc.isMember(actor(), p.recipient), other = party(mineIsRecipient ? p.requester : p.recipient).name;
    function you(title, text, tab, label) { return { who: 'you', title: title, text: text, tab: tab, label: label }; }
    function them(title, text, tab) { return { who: 'other', title: title, text: text, tab: tab }; }
    if (p.status === 'PENDING_WORKSPACE_REVIEW') return them('Menunggu tinjauan organisasi', 'Peninjau organisasi memeriksa versi yang tepat ini sebelum dikirim.', 'ringkasan');
    if (p.status === 'SUBMITTED' || p.status === 'UNDER_REVIEW') {
      return mineIsRecipient ? you('Putuskan pitching ini', 'Setujui untuk diskusi, minta revisi, atau tolak dengan alasan.', 'ringkasan', 'Tinjau pitching') : them('Pitching Anda sedang menunggu keputusan', other + ' dapat menyetujui, meminta revisi, atau menolak.', 'ringkasan');
    }
    if (p.status === 'REVISION_REQUESTED') {
      return mineIsRecipient ? them('Menunggu jawaban revisi', other + ' sedang menjawab permintaan Anda.', 'revisi') : you('Jawab permintaan revisi', 'Pertanyaan wajib perlu dijawab sebelum mengirim ulang.', 'revisi', 'Jawab revisi');
    }
    if (p.status !== 'APPROVED_FOR_DISCUSSION') return { who: null, title: STATUS[p.status][0], text: '', tab: 'ringkasan' };
    var rel = svc.partnershipOf(p.id), m = svc.activeMeeting(p.id), prop = svc.openProposal(p.id);
    if (rel) {
      var cur = svc.last(rel.versions);
      if (cur.status === 'CONFIRMED') return { who: null, title: 'Kerja Sama dikonfirmasi kedua pihak', text: 'Hanya data yang diizinkan kedua pihak yang tampil di publik.', tab: 'ringkasan', partnership: rel.id };
      return cur.confirmations[ui.partyId] ? Object.assign(them('Menunggu konfirmasi pihak lain', other + ' perlu mengonfirmasi ringkasan versi ' + cur.n + '.', 'ringkasan'), { partnership: rel.id })
        : Object.assign(you('Konfirmasi ringkasan Kerja Sama versi ' + cur.n, 'Periksa isi ringkasan dan data yang boleh tampil di publik.', 'ringkasan', 'Buka ringkasan'), { partnership: rel.id });
    }
    var done = Object.keys(svc.state.meetings).map(function (k) { return svc.state.meetings[k]; }).filter(function (x) { return x.pitchId === p.id && x.state === 'COMPLETED'; })[0];
    if (done) return Object.assign(you('Usulkan ringkasan Kerja Sama', 'Diskusi selesai. Kerja Sama hanya tercatat setelah kedua pihak mengonfirmasi versi yang sama.', 'jadwal', 'Usulkan ringkasan'), { propose: true });
    if (m) {
      var started = new Date(svc.state.clock).getTime() >= new Date(m.start).getTime();
      if (!started) return { who: null, title: 'Pertemuan sudah dikonfirmasi', text: when(m.start), tab: 'jadwal' };
      return m.outcomes[ui.partyId] ? them('Menunggu catatan pihak lain', 'Waktu yang berlalu tidak otomatis berarti pertemuan selesai.', 'jadwal') : you('Catat hasil pertemuan', 'Waktu yang berlalu tidak otomatis berarti pertemuan selesai.', 'jadwal', 'Catat hasil');
    }
    if (prop) return prop.by === ui.partyId ? them('Menunggu pihak lain memilih waktu', other + ' dapat memilih satu waktu atau mengusulkan waktu lain.', 'jadwal') : you('Pilih waktu pertemuan', 'Memilih belum memesan waktu. Konfirmasi agar pertemuan tercatat.', 'jadwal', 'Pilih waktu');
    return you('Usulkan waktu pertemuan', 'Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.', 'jadwal', 'Usulkan waktu');
  }
  function myPitches() {
    return Object.keys(svc.state.pitches).map(function (k) { return svc.state.pitches[k]; }).filter(function (p) { return svc.isMember(actor(), p.requester) || svc.isMember(actor(), p.recipient); });
  }
  function openPitch(p, tab) { go('#/pitches/' + p.id + (tab ? '?tab=' + tab : '')); }
  function turnAction(p, t) { return function () { if (t.partnership) go('#/partnerships/' + t.partnership); else if (t.propose) go('#/partnerships/new?pitch=' + p.id); else openPitch(p, t.tab); }; }

  /* ---------- base view ---------- */
  function base(title, subtitle, current) {
    var a = acc();
    return {
      shell: { persona: a.persona, current: current, onNavigate: navigate, title: title, subtitle: subtitle, provenance: 'Demo · Data fiktif' },
      ctx: { value: ui.partyId, readOnly: a.contexts.length === 1, options: a.contexts.map(function (id) { return { id: id, kind: party(id).kind, name: party(id).name }; }), onChange: function (id) { ui.partyId = id; ui.forms = {}; persist(); render(); } },
      ctxFinal: { value: ui.partyId, readOnly: true, options: a.contexts.map(function (id) { return { id: id, kind: party(id).kind, name: party(id).name }; }) },
      notice: ui.notice ? { label: ui.notice.text, tone: ui.notice.tone, live: true } : {}, hasNotice: !!ui.notice
    };
  }
  function nav(current) { return persona() === 'inovator' ? current[0] : current[1]; }
  var vm = {};

  /* ---------- S00 demo controls ---------- */
  function startJourney(fn) { svc.replace(D.baseline()); ui.forms = {}; ui.keys = {}; ui.dialog = null; ui.filters = {}; ui.selected = {}; ui.history = []; ui.notice = null; ui.started = true; fn(); setHash(ui.route.hash); enter(ui.route); persist(); render(); focusMain(); }
  var JOURNEYS = {
    J01: function () { svc.setVariant('gap', true); setAccount('rani'); ui.route = parse('#/home'); },
    J02: function () { setAccount('bima', 'p-dcm'); ui.route = parse('#/funding-requests/FRaise01'); },
    J03: function () { var id = D.seeds.submitted(svc); setAccount('mitraA'); ui.route = parse('#/pitches/' + id); },
    J04: function () { var id = D.seeds.approved(svc); setAccount('mitraA'); ui.route = parse('#/pitches/' + id + '?tab=jadwal'); },
    J05: function () { var id = D.seeds.meetingDone(svc); setAccount('rani'); ui.route = parse('#/partnerships/new?pitch=' + id); },
    DIRECT: function () { var id = D.seeds.submitted(svc); setAccount('mitraA'); svc.setVariant('direct', true); ui.route = parse('#/pitches/' + id); },
    SCHED72: function () { var id = D.seeds.approved(svc); svc.proposeSlots({ actor: D.actors.MITRA_A }, { pitchId: id, slots: ['2026-11-06T09:00:00Z', '2026-11-06T11:00:00Z', '2026-11-06T13:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'Membahas rencana validasi enam bulan' }); svc.setVariant('sched72', true); setAccount('rani'); ui.route = parse('#/pitches/' + id + '?tab=jadwal'); },
    DENIED: function () { var id = D.seeds.submitted(svc); svc.setVariant('denied', true); setAccount('lain'); ui.route = parse('#/pitches/' + id); },
    EMPTY: function () { setAccount('baru'); ui.route = parse('#/home'); }
  };
  vm.demo = function () {
    var s = svc.state, names = { gap: 'F01-GAP', scan: 'F01-SCAN', stale: 'F01-STALE', proposedEntity: 'Perusahaan belum didirikan', direct: 'DIRECT-APPROVAL', sched72: 'SCHED-72H', denied: 'F01-DENIED' };
    var active = Object.keys(s.variants).map(function (k) { return names[k] || k; });
    Object.keys(s.faults).forEach(function (k) { active.push(k === 'lostAfterCommit' ? 'F01-TIMEOUT' : 'Gagal sebelum simpan'); });
    var counterpart = null, open = ui.route.params.id && s.pitches[ui.route.params.id];
    if (open && (svc.isMember(actor(), open.requester) || svc.isMember(actor(), open.recipient))) counterpart = svc.isMember(actor(), open.requester) ? open.recipient : open.requester;
    if (ui.route.name === 'Partnership' && s.partnerships[ui.route.params.id]) { var rel = s.partnerships[ui.route.params.id]; counterpart = rel.parties[0] === ui.partyId ? rel.parties[1] : rel.parties[0]; }
    var accountFor = counterpart && Object.keys(s.accounts).filter(function (k) { return s.accounts[k].id !== 'stafA' && s.accounts[k].contexts.indexOf(counterpart) >= 0; })[0];
    function flagChoice(name, label, hint) { return { label: label, hint: hint, checked: !!s.flags[name], onChange: function (v) { var r = svc.setFlag(name, v); if (!r.ok) notice(r.message, 'warning'); persist(); render(); } }; }
    function variant(name, label, hint) { return { label: label, hint: hint, checked: !!s.variants[name], onChange: function (v) { svc.setVariant(name, v); persist(); render(); } }; }
    function fault(name, value, label, hint) { return { label: label, hint: hint, checked: s.faults[name] === value, onChange: function (v) { svc.setFault(name, v ? value : null); persist(); render(); } }; }
    return {
      summary: 'Kontrol demo · ' + acc().name + ' · ' + clockLabel() + ' (simulasi) · Varian: ' + (active.length ? active.join(', ') : 'tidak ada'),
      account: { label: 'Akun demo', hint: 'Mengganti akun tidak mengatur ulang kasus.', value: ui.accountId, emptyLabel: null, options: Object.keys(s.accounts).map(function (k) { var a = s.accounts[k]; return { value: k, label: a.name + ' · ' + (a.persona === 'mitra' ? 'Investor/Mitra' : 'Inovator') + ' · ' + a.fixture }; }), onChange: function (id) { setAccount(id); persist(); render(); } },
      hasCounterpart: !!accountFor, counterpartLabel: accountFor ? 'Beralih ke ' + s.accounts[accountFor].name : '', switchCounterpart: function () { setAccount(accountFor, counterpart); persist(); render(); focusMain(); },
      journeys: [['J01', 'J01 Pitching F01'], ['J02', 'J02 Satu raise'], ['J03', 'J03 Revisi'], ['J04', 'J04 Jadwal'], ['J05', 'J05 Kerja Sama'], ['DIRECT', 'DIRECT-APPROVAL'], ['SCHED72', 'SCHED-72H'], ['DENIED', 'F01-DENIED'], ['EMPTY', 'Akun kosong']].map(function (j) { return { label: j[1], run: function () { startJourney(JOURNEYS[j[0]]); } }; }),
      clockPresets: [['2026-11-02T08:00:00Z', 'Awal, 2 Nov 08.00'], ['2026-11-04T12:00:00Z', '4 Nov 12.00'], ['2026-11-04T13:00:00Z', '4 Nov 13.00'], ['2026-11-05T08:00:00Z', '5 Nov 08.00'], ['2026-11-07T08:00:00Z', '7 Nov 08.00']].map(function (c) { return { label: c[1], run: function () { svc.setClock(c[0]); persist(); render(); } }; }),
      variants: [variant('gap', 'F01-GAP', 'Kisaran biaya F01 kosong'), variant('scan', 'F01-SCAN', 'Pindaian: perlu diisi manual')],
      proposedEntity: { label: 'Perusahaan belum didirikan', hint: 'FRaise01 tanpa badan usaha', checked: !!s.variants.proposedEntity, onChange: function (v) { svc.setProposedEntity(v); persist(); render(); } },
      faults: [fault('lostAfterCommit', 'submitPitch', 'F01-TIMEOUT', 'Kiriman tersimpan, jawaban hilang'), fault('preCommit', 'saveDraft', 'Gagal simpan draf', 'Satu kali, sebelum tersimpan'), fault('preCommit', 'acceptSlot', 'Gagal konfirmasi waktu', 'Satu kali, sebelum tersimpan')],
      staleTarget: function () { svc.changeTargetVersion(); persist(); render(); },
      otherSession: function () { var i = s.inventions['inv-f01']; if (i.draft) { i.draftRev += 1; i.draft.summary = i.draft.summary + ' Diubah dari sesi lain.'; persist(); render(); } },
      flags: [flagChoice('orgReview', 'Tinjauan organisasi', 'Bawaan mati'), flagChoice('calendar', 'Adaptor kalender', 'Bawaan mati; slot internal dan ICS tetap jalan'), flagChoice('companyFunding', 'Pendanaan Perusahaan', 'Bawaan aktif')],
      ai: { label: 'Ringkasan otomatis', value: s.flags.ai, emptyLabel: null, options: [{ value: 'off', label: 'Mati (bawaan)' }, { value: 'on', label: 'Aktif' }, { value: 'down', label: 'Aktif, layanan gangguan' }], onChange: function (v) { svc.setFlag('ai', v); persist(); render(); } },
      reset: resetDemo
    };
  };

  /* ---------- S01 ---------- */
  vm.start = function () {
    var f = form('start', function () { return { persona: persona(), account: ui.accountId, zone: acc().zone }; });
    var accounts = Object.keys(svc.state.accounts).map(function (k) { return svc.state.accounts[k]; }).filter(function (a) { return a.persona === f.v.persona; });
    var chosen = svc.state.accounts[f.v.account];
    return Object.assign(base('Selamat datang di TemuRiset', 'Pertemukan inovasi dengan investor dan mitra yang tepat.', ''), {
      persona: bind(f, 'persona', { legend: 'Apa yang ingin Anda lakukan?', hint: 'Pilihan ini mengatur menu dan bahasa, bukan hak akses.', options: [{ value: 'inovator', label: 'Saya punya inovasi dan mencari dukungan', hint: 'Inovator' }, { value: 'mitra', label: 'Saya berinvestasi atau memberi dukungan', hint: 'Investor/Mitra' }], onChange: function (v) { f.v.persona = v; f.v.account = accounts.length && v === f.v.persona ? Object.keys(svc.state.accounts).filter(function (k) { return svc.state.accounts[k].persona === v; })[0] : ''; render(); } }),
      account: bind(f, 'account', { label: 'Akun demo', hint: 'Akun fiktif yang sudah ada. Demo ini tidak membuat akun baru.', emptyLabel: null, options: accounts.map(function (a) { return { value: a.id, label: a.name + ' · ' + a.fixture }; }) }),
      zone: bind(f, 'zone', { label: 'Zona waktu', emptyLabel: null, options: ZONES }),
      noOrg: 'Tanpa perusahaan atau institusi pun Anda dapat mulai. Konteks pribadi langsung tersedia.',
      enterLabel: 'Masuk sebagai ' + (chosen ? chosen.name : ''),
      enter: function () { setAccount(f.v.account); svc.setPrefs(ctx(), { zone: f.v.zone }); ui.started = true; persist(); go(persona() === 'mitra' ? '#/discover' : '#/home'); }
    });
  };

  /* ---------- S02 ---------- */
  function queue() {
    var items = [], s = svc.state;
    Object.keys(s.inventions).forEach(function (k) {
      var i = s.inventions[k];
      if (svc.isMember(actor(), i.owner) && i.draft) items.push({ who: 'you', title: 'Lanjutkan draf ' + (i.draft.title || 'inovasi baru'), text: 'Draf tersimpan. Versi terbit tidak berubah sampai Anda menerbitkan.', label: 'Lanjutkan draf', act: function () { go('#/inventions/' + i.id + '/edit?step=1'); } });
    });
    Object.keys(s.requests).forEach(function (k) {
      var r = s.requests[k];
      if (svc.isMember(actor(), r.owner) && r.status === 'ACTIVE' && !r.noncash && !r.terms && r.budget.min == null) items.push({ who: 'you', title: 'Lengkapi kisaran biaya pilot untuk kebutuhan ini', text: r.outcome + ' belum memiliki kisaran biaya. Mitra membandingkannya pada cakupan yang sama.', label: 'Lengkapi biaya', act: function () { go('#/support-requests/' + r.id); } });
    });
    myPitches().forEach(function (p) {
      var t = pitchTurn(p);
      if (t.who) items.push({ who: t.who, title: t.title + ' · ' + subjectTitle(p), text: t.text, label: t.who === 'you' ? t.label : 'Buka pitching', act: turnAction(p, t) });
    });
    Object.keys(s.reviews).forEach(function (k) {
      var r = s.reviews[k];
      if (r.state === 'QUEUED' && r.owner === ui.partyId) items.push({ who: 'you', title: 'Tinjau versi yang menunggu', text: r.kind === 'PUBLICATION' ? 'Penerbitan inovasi' : 'Pengiriman pitching', label: 'Buka antrean', act: function () { go('#/workspace/review-queue'); } });
    });
    return items.sort(function (a, b) { return (a.who === 'you' ? 0 : 1) - (b.who === 'you' ? 0 : 1); });
  }
  function subjectTitle(p) { return p.submissions[p.submissions.length - 1].sourceTitle; }
  vm.home = function () {
    var q = queue(), first = q[0], rest = q.slice(1), notes = svc.state.notifications.filter(function (n) { return n.party === ui.partyId; }).slice(-4).reverse();
    return Object.assign(base('Beranda', 'Halo, ' + acc().name + '. Inilah yang perlu diperhatikan.', 'beranda'), {
      hasFirst: !!first, empty: !first, first: first ? { who: first.who, title: first.title, body: first.text } : {}, firstLabel: first ? first.label : '', firstAct: first ? first.act : null,
      rest: rest.map(function (i) { return { title: i.title, text: i.text, label: i.label, act: i.act, status: { tone: i.who === 'you' ? 'action' : 'neutral', label: i.who === 'you' ? 'Menunggu Anda' : 'Menunggu pihak lain' } }; }), hasRest: rest.length > 0,
      notes: notes.map(function (n) { return { text: n.text, at: when(n.at) }; }), hasNotes: notes.length > 0, noNotes: notes.length === 0,
      addInvention: function () { var r = svc.createInvention(ctx()); persist(); go('#/inventions/' + r.id + '/edit?step=1'); },
      explore: function () { go('#/discover'); }
    });
  };

  /* ---------- inventions list and S04 ---------- */
  vm.inventions = function () {
    var all = Object.keys(svc.state.inventions).map(function (k) { return svc.state.inventions[k]; }).filter(function (i) { return svc.isMember(actor(), i.owner); });
    var published = all.filter(function (i) { return i.published; }), drafts = all.filter(function (i) { return !i.published; });
    return Object.assign(base('Inovasi Saya', 'Setiap inovasi dikelola oleh ' + party(ui.partyId).name + '.', 'inovasi'), {
      cards: published.map(function (i) { return { card: cardProps(i), open: function () { go('#/inventions/' + i.id); }, draftNote: i.draft ? 'Ada draf perubahan' : '', hasDraft: !!i.draft }; }),
      drafts: drafts.map(function (i) { return { title: i.draft.title || 'Inovasi tanpa judul', open: function () { go('#/inventions/' + i.id + '/edit?step=1'); } }; }), hasDrafts: drafts.length > 0,
      empty: all.length === 0,
      add: function () { var r = svc.createInvention(ctx()); persist(); go('#/inventions/' + r.id + '/edit?step=1'); }
    });
  };
  vm.invention = function () {
    var i = svc.state.inventions[ui.route.params.id], v = svc.pubV(i);
    if (!v || (i.archived && !svc.isMember(actor(), i.owner))) return Object.assign(base('Inovasi tidak tersedia', '', nav(['inovasi', 'jelajahi'])), { missing: true, found: false, leave: function () { back('#/home'); } });
    var owner = svc.isMember(actor(), i.owner), reqs = requestsOf(i.id), fund = fundingOf(i.id), docs = owner ? v.docs.map(function (d) { return svc.state.documents[d]; }) : [];
    var rels = svc.publicRelationships(i.owner).filter(function (r) { return r.inventionIds.indexOf(i.id) >= 0; });
    var first = reqs.filter(function (r) { return r.status === 'ACTIVE'; })[0];
    return Object.assign(base(v.title, v.category + ' · ' + STAGES[v.stage] + ' · Versi terbit ' + v.n, nav(['inovasi', 'jelajahi'])), {
      found: true, missing: false, v: v, owner: owner, notOwner: !owner, ownerName: party(i.owner).name,
      next: owner ? { who: 'you', title: first ? 'Temukan Investor/Mitra untuk ' + first.outcome : 'Tambahkan kebutuhan dukungan', body: first ? 'Lihat alasan kecocokan dan yang masih perlu dilengkapi.' : 'Dukungan yang dicari wajib dinyatakan sebelum menerima pitching.' } : { who: 'you', title: 'Tertarik membahas inovasi ini?', body: 'Simpan inovasi ini. Pihak pengelola mengirim pitching ke mandat Anda secara sengaja.' },
      primaryLabel: owner ? (first ? 'Lihat kecocokan' : 'Tambah kebutuhan') : (svc.state.saved[ui.partyId + ':' + i.id] ? 'Hapus dari simpanan' : 'Simpan inovasi'),
      primary: function () {
        if (owner) go(first ? '#/matches?source=' + first.id : '#/support-requests/new?invention=' + i.id);
        else { svc.toggleSaved(ctx(), { id: i.id }); persist(); }
      },
      edit: function () { go('#/inventions/' + i.id + '/edit?step=1'); },
      back: function () { back(owner ? '#/inventions' : '#/discover'); }, backLabel: owner ? 'Kembali ke Inovasi Saya' : 'Kembali ke hasil',
      facts: v.facts.map(function (x) { return { label: x.label, source: { value: x.value, timing: x.timing, provenance: x.provenance } }; }), hasFacts: v.facts.length > 0,
      people: v.people, reqs: reqs.map(function (r) { return { title: r.outcome, fin: srFinancial(r), status: { tone: r.status === 'ACTIVE' ? 'action' : 'neutral', icon: null, label: r.status === 'ACTIVE' ? 'Aktif' : 'Draf' }, open: function () { go('#/support-requests/' + r.id); } }; }), hasReqs: reqs.length > 0,
      funding: fund ? { card: fundingCard(fund), open: function () { go('#/funding-requests/' + fund.id); } } : null, hasFunding: !!fund,
      docs: docs.map(function (d) { return { props: docProps(d) }; }), hasDocs: docs.length > 0,
      rels: rels.map(function (r) { return { rows: Object.keys(r.fields).map(function (k) { return { label: CONSENT_LABELS[k], value: r.fields[k] }; }) }; }), hasRels: rels.length > 0,
      archive: function () { svc.archiveInvention(ctx(), { id: i.id }); persist(); notice('Inovasi diarsipkan. Diskusi yang berjalan tetap dapat dibuka.'); go('#/inventions', { keepNotice: true }); }
    });
  };

  /* ---------- S05 editor ---------- */
  function uploadSim(owner, f, list) {
    var r = svc.addDocument(ctx(), { owner: owner, kind: 'function', title: (f.v.title || 'Berkas') + ' · dokumen pendukung' }), id = r.id, rejected = !!ui.rejectNext;
    list.push(id); render();
    setTimeout(function () { svc.advanceDocument(ctx(), { id: id, state: { file: 'QUARANTINED' } }); }, 500);
    setTimeout(function () {
      if (rejected) { svc.advanceDocument(ctx(), { id: id, state: { file: 'REJECTED' } }); ui.rejectNext = false; return; }
      svc.advanceDocument(ctx(), { id: id, state: { file: 'AVAILABLE', extraction: 'RUNNING' } });
    }, 1100);
    setTimeout(function () {
      if (!rejected) svc.advanceDocument(ctx(), { id: id, state: { extraction: svc.state.variants.scan ? 'NEEDS_MANUAL_INPUT' : 'SUCCEEDED' } });
      persist();
    }, 1700);
  }
  vm.editor = function () {
    var id = ui.route.params.id, i = svc.state.inventions[id];
    if (!i || !i.draft) return Object.assign(base('Editor', '', 'inovasi'), { ready: false, notReady: true, leave: function () { back('#/inventions'); } });
    var step = Number(ui.route.query.step || 1), f = form('inv-' + id, function () { var x = D.clone(i.draft); x.__rev = i.draftRev; x.factLabel = ''; x.factValue = ''; x.factTiming = 'CURRENT'; return x; });
    var labels = [['1', 'Dasar'], ['2', 'Yang sudah ada dan bukti'], ['3', 'Dukungan dan keuangan'], ['4', 'Pratinjau publik']];
    function goStep(n) { go('#/inventions/' + id + '/edit?step=' + n); }
    function fields() { var x = {}; Object.keys(f.v).forEach(function (k) { if (k.indexOf('fact') !== 0 && k !== '__rev') x[k] = f.v[k]; }); x.facts = f.v.facts; return x; }
    function save(then) {
      f.save = 'saving'; clearFail(f); render();
      var name = 'draft-' + id + '-' + f.v.__rev;
      run('save', function () { return svc.saveDraft(ctx(once(name)), { id: id, rev: f.v.__rev, fields: fields() }); }, function (r) {
        if (r.ok) { spent(name); f.v.__rev = r.rev; f.dirty = false; f.save = 'saved'; f.savedAt = r.savedAt; if (then) then(); return; }
        if (r.code === 'STALE_VERSION') { spent(name); f.save = 'conflict'; f.conflict = r; return; }
        f.save = 'failed';
      });
    }
    var preview = { title: f.v.title || 'Judul inovasi', category: f.v.sector || 'Inovasi', manager: 'Dikelola ' + party(i.owner).name, problem: f.v.problem, solution: f.v.solution, maturity: STAGES[f.v.stage] };
    var docs = (f.v.docs || []).map(function (d) { return svc.state.documents[d]; }).filter(Boolean);
    return Object.assign(base(f.v.title || 'Inovasi baru', 'Draf ini belum terlihat oleh publik.', 'inovasi'), {
      ready: true, notReady: false, step1: step === 1, step2: step === 2, step3: step === 3, step4: step === 4,
      steps: { steps: labels.map(function (l) { return { id: l[0], label: l[1] }; }), current: String(step), onSelect: function (x) { save(function () { goStep(x); }); } },
      save: { state: f.save, location: 'demo', savedAt: f.savedAt, timeZone: zone(), onRetry: function () { save(); } }, summary: summary(f), showSummary: summary(f).show, summaryProps: summary(f).props,
      saving: !!ui.busy.save,
      conflict: f.save === 'conflict', conflictProps: { what: 'Draf ini berubah di sesi lain.', currentVersion: 'Revisi ' + i.draftRev, draft: f.v.summary, onRefresh: function () { f.v = Object.assign(D.clone(i.draft), { __rev: i.draftRev, factLabel: '', factValue: '', factTiming: 'CURRENT' }); f.save = 'saved'; render(); } },
      title: bind(f, 'title', { label: 'Judul inovasi', hint: '5 sampai 120 karakter.', required: true }),
      problem: bind(f, 'problem', { label: 'Masalah yang diselesaikan', hint: 'Jangan tuliskan rahasia teknis.', rows: 3, required: true }),
      users: bind(f, 'users', { label: 'Siapa penggunanya', required: true }),
      sector: bind(f, 'sector', { label: 'Sektor', options: SECTORS.map(function (s) { return { value: s, label: s }; }) }),
      summaryField: bind(f, 'summary', { label: 'Ringkasan yang aman untuk publik', hint: 'Tampil di kartu dan pencarian.', rows: 3, limit: 350, required: true }),
      solution: bind(f, 'solution', { label: 'Solusi yang sudah ada', rows: 3, required: true }),
      stage: bind(f, 'stage', { label: 'Tahap saat ini', required: true, options: Object.keys(STAGES).map(function (k) { return { value: k, label: STAGES[k] }; }) }),
      factList: (f.v.facts || []).map(function (x) { return { label: x.label, source: { value: x.value, timing: x.timing, provenance: x.provenance }, remove: function () { f.v.facts = f.v.facts.filter(function (y) { return y !== x; }); f.save = 'local'; render(); } }; }),
      factLabel: bind(f, 'factLabel', { label: 'Nama kemampuan' }), factValue: bind(f, 'factValue', { label: 'Nilai' }),
      factTiming: bind(f, 'factTiming', { label: 'Waktu', emptyLabel: null, options: [{ value: 'CURRENT', label: 'Saat ini' }, { value: 'PLANNED', label: 'Direncanakan' }] }),
      addFact: function () { if (!f.v.factLabel || !f.v.factValue) return; f.v.facts = (f.v.facts || []).concat([{ id: 'fct-' + Date.now(), label: f.v.factLabel, value: f.v.factValue, timing: f.v.factTiming, provenance: 'SELF_DECLARED', key: f.v.factLabel.toLowerCase() }]); f.v.factLabel = ''; f.v.factValue = ''; f.save = 'local'; render(); },
      docs: docs.map(function (d) { return { props: docProps(d) }; }), noDocs: docs.length === 0,
      upload: function () { f.v.docs = f.v.docs || []; uploadSim(i.owner, f, f.v.docs); f.save = 'local'; },
      rejectNext: { label: 'Simulasikan berkas ditolak', hint: 'Kontrol uji: unggahan berikutnya gagal pemeriksaan keamanan.', checked: !!ui.rejectNext, onChange: function (v) { ui.rejectNext = v; render(); } },
      reqs: requestsOf(id).map(function (r) { return { title: r.outcome, fin: srFinancial(r), open: function () { save(function () { go('#/support-requests/' + r.id + '?from=editor'); }); } }; }), hasReqs: requestsOf(id).length > 0,
      fund: fundingOf(id) ? { card: fundingCard(fundingOf(id)), open: function () { go('#/funding-requests/' + fundingOf(id).id); } } : null, hasFund: !!fundingOf(id),
      addReq: function () { save(function () { go('#/support-requests/new?invention=' + id); }); },
      preview: preview, visible: [['Terlihat publik', 'Judul, masalah, solusi, tahap, pengguna dan ringkasan'], ['Tetap privat', 'Semua berkas. Berkas dibagikan per versi dan per penerima saat pitching.'], ['Efek terbit', 'Versi baru menggantikan versi publik. Pitching yang sudah terkirim tidak berubah.']].map(function (r, n) { return { id: 'row' + n, label: r[0], value: r[1] }; }),
      nextVersion: i.versions.length + 1,
      publishLabel: svc.state.flags.orgReview && party(i.owner).kind === 'organization' ? 'Kirim ke tinjauan organisasi' : 'Terbitkan versi ' + (i.versions.length + 1),
      publishing: !!ui.busy.publish,
      publish: function () {
        save(function () {
          run('publish', function () { return svc.publishInvention(ctx(), { id: id }); }, function (r) {
            if (r.ok) { delete ui.forms[f.key]; notice(r.queued ? 'Versi ' + r.version + ' menunggu tinjauan organisasi. Versi publik tidak berubah.' : 'Versi ' + r.version + ' sudah terbit.'); go('#/inventions/' + id, { keepNotice: true }); return; }
            fail(f, r);
            var early = Object.keys(f.err).some(function (k) { return ['title', 'summary', 'problem', 'users'].indexOf(k) >= 0; });
            goStep(early ? 1 : 2); ui.forms[f.key] = f;
          });
        });
      },
      prevStep: function () { goStep(step - 1); }, hasPrev: step > 1,
      nextStep: function () { save(function () { goStep(step + 1); }); }, hasNext: step < 4,
      nextLabel: step === 3 ? 'Simpan dan lihat pratinjau' : 'Simpan dan lanjutkan',
      saveOnly: function () { save(); }
    });
  };

  /* ---------- S06 support ---------- */
  function supportForm(id, r, invId) {
    return form('sr-' + id, function () {
      var b = r ? r.budget : {};
      return { outcome: r ? r.outcome : '', relationship: r ? r.relationship : 'PROJECT', formType: r ? r.form : 'Pendanaan proyek', months: String(r ? r.months : 6), region: r ? r.region : 'Indonesia', partial: r ? r.partial : true, noncashOn: !!(r && r.noncash), noncash: r && r.noncash ? r.noncash : '', min: b.min || '', max: b.max || '', period: b.period || '6 bulan', scope: b.scope || 'biaya pilot enam bulan', assumptions: b.assumptions || '', invention: invId };
    });
  }
  vm.support = function () {
    var id = ui.route.params.id, q = ui.route.query;
    if (!id) {
      var list = Object.keys(svc.state.requests).map(function (k) { return svc.state.requests[k]; }).filter(function (r) { return svc.isMember(actor(), r.owner); });
      return Object.assign(base('Dukungan Proyek', 'Satu inovasi dapat memiliki beberapa kebutuhan untuk hasil yang berbeda.', 'inovasi'), {
        isList: true, isForm: false, denied: false, items: list.map(function (r) { return { title: r.outcome, inv: svc.pubV(svc.state.inventions[r.inventionId]).title, fin: srFinancial(r), open: function () { go('#/support-requests/' + r.id); } }; }), empty: list.length === 0, explore: function () { go('#/inventions'); }
      });
    }
    var isNew = id === 'new', r = isNew ? null : svc.state.requests[id];
    if ((!isNew && !r) || (r && !svc.isMember(actor(), r.owner))) return Object.assign(base('Akses dibatasi', '', 'inovasi'), { isList: false, isForm: false, denied: true });
    var invId = isNew ? q.invention : r.inventionId, f = supportForm(id, r, invId), returning = q.return;
    function afterSave(res) {
      if (returning) { notice('Kebutuhan tersimpan sebagai versi ' + res.version + '.'); go(decodeURIComponent(returning), { keepNotice: true }); return; }
      notice('Kebutuhan tersimpan sebagai versi ' + res.version + '.');
      if (isNew) { delete ui.forms[f.key]; go('#/support-requests/' + res.id, { keepNotice: true }); }
    }
    function save() {
      clearFail(f); f.save = 'saving';
      var name = 'sr-' + id + '-' + (r ? r.version : 0);
      run('saveSr', function () {
        return svc.saveSupportRequest(ctx(once(name)), { id: r ? r.id : undefined, inventionId: invId, expected: r ? r.version : undefined,
          fields: { outcome: f.v.outcome, relationship: f.v.relationship, form: f.v.formType, months: Number(f.v.months) || 6, region: f.v.region, partial: f.v.partial, noncash: f.v.noncashOn ? (f.v.noncash || 'Dukungan nonfinansial') : undefined },
          budget: { min: f.v.min, max: f.v.max, period: f.v.period, assumptions: f.v.assumptions } });
      }, function (res) {
        spent(name);
        if (res.ok) { f.save = 'saved'; f.dirty = false; afterSave(res); return; }
        f.save = 'failed'; fail(f, res);
      });
    }
    var v = r ? svc.pubV(svc.state.inventions[r.inventionId]) : (svc.state.inventions[invId] && svc.pubV(svc.state.inventions[invId]));
    var gap = r && !r.noncash && !r.terms && r.budget.min == null;
    return Object.assign(base(r ? r.outcome : 'Kebutuhan baru', (v ? v.title + ' · ' : '') + (r ? 'Versi ' + r.version : 'Belum tersimpan'), 'inovasi'), {
      isList: false, isForm: true, denied: false, showSummary: summary(f).show, summaryProps: summary(f).props, gap: !!gap,
      save: { state: ui.busy.saveSr ? 'saving' : f.save, location: 'demo' },
      outcome: bind(f, 'outcome', { label: 'Hasil yang ingin dicapai', required: true }),
      relationship: bind(f, 'relationship', { legend: 'Bentuk kerja sama yang diusulkan', options: [{ value: 'PROJECT', label: 'Proyek' }, { value: 'LICENSE', label: 'Lisensi' }] }),
      formType: bind(f, 'formType', { label: 'Bentuk dukungan' }), months: bind(f, 'months', { label: 'Lama kebutuhan (bulan)', type: 'decimal' }), region: bind(f, 'region', { label: 'Wilayah' }),
      partial: { label: 'Dukungan sebagian diterima', checked: f.v.partial, onChange: function (x) { f.v.partial = x; f.save = 'local'; render(); } },
      noncashOn: { label: 'Kebutuhan ini nonfinansial', hint: 'Misalnya fasilitas uji atau pendampingan.', checked: f.v.noncashOn, onChange: function (x) { f.v.noncashOn = x; f.save = 'local'; render(); } }, isNoncash: f.v.noncashOn, isCash: !f.v.noncashOn,
      noncash: bind(f, 'noncash', { label: 'Dukungan nonfinansial yang dicari' }),
      min: bind(f, 'min', { label: 'Batas bawah', type: 'decimal', prefix: 'USD', hint: 'Kosongkan jika belum ditentukan.' }), max: bind(f, 'max', { label: 'Batas atas', type: 'decimal', prefix: 'USD' }),
      period: bind(f, 'period', { label: 'Periode' }), scopeLabel: 'Cakupan biaya: ' + f.v.scope, assumptions: bind(f, 'assumptions', { label: 'Asumsi', rows: 2 }),
      saveLabel: returning ? 'Simpan dan kembali ke pemeriksaan' : 'Simpan kebutuhan', saveBusy: !!ui.busy.saveSr, doSave: save,
      canActivate: !!r && r.status === 'DRAFT', activate: function () { svc.setRequestStatus(ctx(), { id: r.id, status: 'ACTIVE' }); persist(); notice('Kebutuhan aktif.'); render(); },
      canMatch: !!r && r.status === 'ACTIVE', findMatch: function () { go('#/matches?source=' + r.id); },
      back: function () { back('#/support-requests'); }
    });
  };

  /* ---------- S07 funding ---------- */
  vm.funding = function () {
    var id = ui.route.params.id, x = svc.state.fundings[id], owner = x && svc.can(actor(), x.owner, 'edit'), editing = /\/edit/.test(ui.route.hash), on = svc.state.flags.companyFunding;
    if (!x) return Object.assign(base('Tidak ditemukan', '', 'inovasi'), { found: false });
    var f = form('fr-' + id + '-' + x.version, function () { return { target: x.target, desiredMin: x.desiredMin || '', desiredMax: x.desiredMax || '', purpose: x.purpose, stage: x.stage, timing: x.timing || '', partial: x.partial }; });
    var active = Object.keys(svc.state.pitches).map(function (k) { return svc.state.pitches[k]; }).filter(function (p) { return p.subject.id === id && svc.isMember(actor(), p.requester); });
    var linked = x.links.map(function (l) { var i = svc.state.inventions[l.inventionId], v = i.versions[l.version - 1]; return { title: v.title, version: 'Versi ' + l.version, stage: STAGES[v.stage], open: function () { go('#/inventions/' + i.id); }, prep: function () { go('#/pitches/new?source=' + id + '&target=B1&via=' + i.id); } }; });
    function save() {
      clearFail(f);
      var name = 'fr-' + id + '-' + x.version;
      run('saveFr', function () { return svc.saveFundingRequest(ctx(once(name)), { id: id, expected: x.version, fields: { target: f.v.target, desiredMin: f.v.desiredMin, desiredMax: f.v.desiredMax, purpose: f.v.purpose, stage: f.v.stage, timing: f.v.timing || null, partial: f.v.partial } }); }, function (r) {
        spent(name);
        if (r.ok) { notice('Permintaan pendanaan tersimpan sebagai versi ' + r.version + '. Pitching yang sudah terkirim tidak berubah.'); go('#/funding-requests/' + id, { keepNotice: true }); return; }
        fail(f, r);
      });
    }
    return Object.assign(base('Pendanaan Perusahaan', x.company + ' · Versi ' + x.version, 'inovasi'), {
      found: true, owner: !!owner, on: on, off: !on, editing: !!(editing && owner && on), reading: !(editing && owner && on), card: fundingCard(x), linked: linked,
      entityNote: x.subject === 'PROPOSED_ENTITY' ? 'Perusahaan belum didirikan. Diskusi hanya terbuka pada mandat yang menerimanya. Ekuitas terkonfirmasi tetap memerlukan badan usaha nyata.' : 'Satu permintaan pendanaan untuk ' + x.links.length + ' inovasi. Tahap pendanaan perusahaan terpisah dari kematangan tiap inovasi.',
      history: x.history.map(function (h) { return { text: 'Versi ' + h.version + ': Target Pendanaan ' + TR.format.money(x.currency, h.target) }; }), hasHistory: x.history.length > 0,
      hasPitch: active.length > 0, pitchLabel: 'Buka pitching aktif', openPitch: function () { go('#/pitches/' + active[0].id); },
      findInvestors: function () { go('#/matches?source=' + id); }, edit: function () { go('#/funding-requests/' + id + '/edit'); }, canEdit: !!owner && on,
      target: bind(f, 'target', { label: 'Target Pendanaan', type: 'decimal', prefix: 'USD', required: true, hint: 'Total untuk satu perusahaan.' }),
      desiredMin: bind(f, 'desiredMin', { label: 'Kisaran kontribusi per investor, batas bawah', type: 'decimal', prefix: 'USD' }), desiredMax: bind(f, 'desiredMax', { label: 'Kisaran kontribusi per investor, batas atas', type: 'decimal', prefix: 'USD' }),
      purpose: bind(f, 'purpose', { label: 'Penggunaan dana', rows: 2 }), stage: bind(f, 'stage', { label: 'Tahap pendanaan perusahaan' }), timing: bind(f, 'timing', { label: 'Waktu', hint: 'Kosongkan jika belum ditentukan.' }),
      partial: { label: 'Menerima pendanaan sebagian dan bersama investor lain', checked: f.v.partial, onChange: function (v) { f.v.partial = v; render(); } },
      showSummary: summary(f).show, summaryProps: summary(f).props, saving: !!ui.busy.saveFr, save: save, cancel: function () { go('#/funding-requests/' + id); }, saveLabel: 'Simpan versi ' + (x.version + 1)
    });
  };

  /* ---------- S08 / S09 ---------- */
  var INTAKE = { OPEN: ['Pitching dibuka', 'action'], CLOSED: ['Penerimaan ditutup', 'neutral'], UNCONFIRMED: ['Ketersediaan belum dikonfirmasi', 'warning'] };
  function oppCard(o) {
    return { title: o.title, version: 'Versi ' + o.version, statusLabel: { ACTIVE: 'Aktif', PAUSED: 'Dijeda', CLOSED: 'Ditutup', DRAFT: 'Draf', EXPIRED: 'Berakhir' }[o.status], outcome: o.outcome, support: o.support, fin: oppFinancial(o), timing: o.timing, reqs: o.requirements.map(function (r) { return { label: r.label, stage: r.appliesAt, mandatory: r.mandatory, mode: r.mode, result: 'NOT_APPLICABLE' }; }) };
  }
  vm.partner = function () {
    var id = ui.route.params.id, x = svc.state.partners[id], owner = svc.isMember(actor(), id);
    if (!x) return Object.assign(base('Profil belum tersedia', '', nav(['temukan', 'mandat'])), { found: false, nothing: true, leave: function () { back('#/home'); } });
    var opps = Object.keys(svc.state.opportunities).map(function (k) { return svc.state.opportunities[k]; }).filter(function (o) { return o.partner === id; });
    var intake = INTAKE[x.intake], src = x.source === 'OWNER_CONFIRMED' ? 'Dikonfirmasi pemilik profil' : 'Dilaporkan sumber';
    var incoming = owner ? myPitches().filter(function (p) { return p.recipient === id && pitchTurn(p).who === 'you'; }) : [];
    return Object.assign(base(party(id).name, x.subtype + ' · ' + (party(id).kind === 'personal' ? 'Individu' : 'Organisasi'), nav(['temukan', 'mandat'])), {
      found: true, nothing: false, x: x, owner: owner, notOwner: !owner, sectors: x.sectors.join(', '), source: src, intake: { tone: intake[1], label: intake[0], icon: x.intake === 'OPEN' ? 'check' : undefined },
      hasCheck: !!x.check, check: x.check ? { subject: 'investorCheck', currency: x.check.currency, min: x.check.min, max: x.check.max, compact: true } : null,
      external: x.route === 'EXTERNAL', externalUrl: x.externalUrl, internal: x.route === 'IN_APP',
      opps: opps.map(function (o) { return Object.assign(oppCard(o), { canEdit: owner, edit: function () { go('#/opportunities/' + o.id + '/edit'); }, toggle: function () { svc.setOpportunityStatus(ctx(), { id: o.id, status: o.status === 'ACTIVE' ? 'CLOSED' : 'ACTIVE' }); persist(); }, toggleLabel: o.status === 'ACTIVE' ? 'Tutup penerimaan' : 'Buka kembali' }); }), hasOpps: opps.length > 0,
      hasIncoming: incoming.length > 0, incomingNext: { who: 'you', title: incoming.length + ' pitching perlu keputusan Anda', body: 'Keputusan menyetujui diskusi, bukan pendanaan.' }, openIncoming: function () { go('#/pitches?box=masuk'); },
      back: function () { back(owner ? '#/discover' : '#/discover'); }, backLabel: 'Kembali ke pencarian'
    });
  };
  var RSTAGE = [{ value: 'SUBMISSION', label: 'Saat pengajuan' }, { value: 'DISCUSSION', label: 'Saat diskusi' }, { value: 'PILOT', label: 'Saat pilot' }, { value: 'COMMERCIALIZATION', label: 'Saat komersialisasi' }];
  var RMODE = [{ value: 'DECLARATION', label: 'Pernyataan' }, { value: 'DOCUMENT_PRESENT', label: 'Dokumen tersedia' }, { value: 'REVIEWER_CONFIRMED', label: 'Diperiksa peninjau' }];
  vm.opportunity = function () {
    var id = ui.route.params.id, o = svc.state.opportunities[id];
    if (!o || !svc.isMember(actor(), o.partner)) return Object.assign(base('Akses dibatasi', '', 'mandat'), { allowed: false, denied: true, leave: function () { back('#/discover'); } });
    var f = form('opp-' + id + '-' + o.version, function () { return { title: o.title, outcome: o.outcome, included: o.included, excluded: o.excluded, support: o.support, timing: o.timing, reqs: D.clone(o.requirements), newLabel: '', newStage: 'SUBMISSION', newMode: 'DECLARATION', review: false }; });
    function save() {
      clearFail(f);
      var name = 'opp-' + id + '-' + o.version;
      run('saveOpp', function () { return svc.saveOpportunity(ctx(once(name)), { id: id, expected: o.version, fields: { title: f.v.title, outcome: f.v.outcome, included: f.v.included, excluded: f.v.excluded, support: f.v.support, timing: f.v.timing, requirements: f.v.reqs } }); }, function (r) {
        spent(name);
        if (r.ok) { notice('Mandat aktif sebagai versi ' + r.version + '. Pitching yang sudah terkirim memakai versinya sendiri.'); go('#/partners/' + o.partner, { keepNotice: true }); return; }
        f.v.review = false; fail(f, r);
      });
    }
    return Object.assign(base('Ubah mandat', o.title + ' · Versi ' + o.version, 'mandat'), {
      allowed: true, denied: false, editing: !f.v.review, reviewing: f.v.review, showSummary: summary(f).show, summaryProps: summary(f).props,
      title: bind(f, 'title', { label: 'Judul mandat', required: true }), outcome: bind(f, 'outcome', { label: 'Hasil yang dicari', rows: 2 }), included: bind(f, 'included', { label: 'Termasuk', rows: 2 }), excluded: bind(f, 'excluded', { label: 'Tidak termasuk', rows: 2 }), support: bind(f, 'support', { label: 'Dukungan yang ditawarkan' }), timing: bind(f, 'timing', { label: 'Waktu' }),
      fin: oppFinancial(o),
      reqs: f.v.reqs.map(function (r, n) { return { row: { label: r.label, result: 'NOT_APPLICABLE', stage: r.appliesAt, mandatory: r.mandatory, mode: r.mode, reason: r.why }, stage: { label: 'Tahap berlaku: ' + r.label, emptyLabel: null, value: r.appliesAt, options: RSTAGE, id: 'req-stage-' + n, onChange: function (v) { r.appliesAt = v; render(); } }, remove: function () { f.v.reqs = f.v.reqs.filter(function (y) { return y !== r; }); render(); } }; }),
      newLabel: bind(f, 'newLabel', { label: 'Syarat baru', hint: 'Syarat naratif tanpa pemetaan ditinjau manual dan tidak menolak otomatis.' }), newStage: bind(f, 'newStage', { label: 'Tahap berlaku', emptyLabel: null, options: RSTAGE }), newMode: bind(f, 'newMode', { label: 'Cara pemeriksaan', emptyLabel: null, options: RMODE }),
      addReq: function () { if (!f.v.newLabel.trim()) return; f.v.reqs.push({ id: id + '-n' + f.v.reqs.length, label: f.v.newLabel, field: 'narrative', op: 'manual_review', value: null, mandatory: false, appliesAt: f.v.newStage, mode: f.v.newMode }); f.v.newLabel = ''; render(); },
      toReview: function () { f.v.review = true; render(); focusMain(); }, toEdit: function () { f.v.review = false; render(); },
      reviewRows: [['Judul', f.v.title], ['Hasil', f.v.outcome], ['Termasuk', f.v.included], ['Tidak termasuk', f.v.excluded], ['Dukungan', f.v.support], ['Waktu', f.v.timing]].map(function (r) { return { id: 'r-' + r[0], label: r[0], value: r[1] }; }),
      saving: !!ui.busy.saveOpp, save: save, saveLabel: 'Aktifkan versi ' + (o.version + 1), leave: function () { back('#/partners/' + o.partner); }
    });
  };

  /* ---------- S03 discovery ---------- */
  function matchesQuery(text, q) {
    if (!q) return true;
    var t = text.toLowerCase();
    return q.toLowerCase().split(/\s+/).filter(Boolean).every(function (w) { return t.indexOf(w) >= 0 || t.indexOf(EN_ALIAS[w] || '\u0000') >= 0; });
  }
  vm.discover = function () {
    var s = svc.state, isMitra = persona() === 'mitra', fl = ui.filters.discover || (ui.filters.discover = { q: '', sector: '', stage: '', intake: '', savedOnly: false });
    var type = ui.route.query.type || (isMitra ? 'inventions' : 'partners');
    function field(name, extra) { return Object.assign({ id: 'filter-' + name, value: fl[name], onChange: function (v) { fl[name] = v; render(); } }, extra); }
    var mine = s.partners[ui.partyId], isSaved = function (id) { return !!s.saved[ui.partyId + ':' + id]; }, isHidden = function (id) { return !!s.hidden[ui.partyId + ':' + id]; };
    var inventions = Object.keys(s.inventions).map(function (k) { return s.inventions[k]; }).filter(function (i) {
      var v = svc.pubV(i); if (!v || i.archived || i.owner === ui.partyId || isHidden(i.id)) return false;
      return matchesQuery([v.title, v.summary, v.problem, v.category, v.keywords.join(' ')].join(' '), fl.q) && (!fl.sector || v.sector === fl.sector) && (!fl.stage || v.stage === fl.stage) && (!fl.savedOnly || isSaved(i.id));
    });
    var fundings = Object.keys(s.fundings).map(function (k) { return s.fundings[k]; }).filter(function (f) {
      return s.flags.companyFunding && f.status === 'ACTIVE' && !isHidden(f.id) && matchesQuery([f.company, f.purpose, f.stage].join(' '), fl.q) && (!fl.savedOnly || isSaved(f.id));
    });
    var partners = Object.keys(s.partners).map(function (k) { return s.partners[k]; }).filter(function (x) {
      return x.id !== ui.partyId && !isHidden(x.id) && matchesQuery([party(x.id).name, x.subtype, x.thesis, x.forms, x.sectors.join(' ')].join(' '), fl.q) && (!fl.sector || x.sectors.indexOf(fl.sector) >= 0) && (!fl.intake || x.intake === fl.intake) && (!fl.savedOnly || isSaved(x.id));
    });
    function invRow(i) {
      var v = svc.pubV(i), rel = mine && mine.sectors.indexOf(v.sector) >= 0, card = cardProps(i);
      card.reasons = (rel ? ['Sesuai sektor pada profil Anda: ' + v.sector] : []).concat(v.curated ? ['Pilihan kurator demo, bukan peringkat'] : []);
      return { card: card, open: function () { go('#/inventions/' + i.id); }, save: function () { svc.toggleSaved(ctx(), { id: i.id }); persist(); }, saveLabel: isSaved(i.id) ? 'Tersimpan' : 'Simpan', hide: function () { svc.lessRelevant(ctx(), { id: i.id }); persist(); }, relevant: rel, title: v.title };
    }
    var rows = inventions.map(invRow), relevant = rows.filter(function (r) { return r.relevant; }), others = rows.filter(function (r) { return !r.relevant; });
    var count = type === 'funding' ? fundings.length : type === 'partners' ? partners.length : rows.length;
    var q = queue();
    var req = isMitra ? null : Object.keys(s.requests).map(function (k) { return s.requests[k]; }).filter(function (r) { return svc.isMember(actor(), r.owner) && r.status === 'ACTIVE'; })[0];
    var fr = isMitra ? null : Object.keys(s.fundings).map(function (k) { return s.fundings[k]; }).filter(function (f) { return svc.isMember(actor(), f.owner); })[0];
    var src = req ? req.id : fr ? fr.id : null;
    return Object.assign(base(isMitra ? 'Jelajahi' : 'Temukan Investor/Mitra', isMitra ? 'Inovasi dan pendanaan perusahaan yang sedang mencari dukungan.' : 'Investor dan mitra dengan mandat yang dinyatakan.', isMitra ? 'jelajahi' : 'temukan'), {
      isMitra: isMitra, isInovator: !isMitra, showInventions: type === 'inventions', showFunding: type === 'funding', showPartners: type === 'partners',
      queueTop: q.length && q[0].who === 'you' ? { who: 'you', title: q[0].title, body: q[0].text } : null, hasQueue: !!(q.length && q[0].who === 'you' && isMitra), queueLabel: q.length ? q[0].label : '', queueAct: q.length ? q[0].act : null,
      hasSource: !!src, sourceNext: { who: 'you', title: 'Lihat kecocokan untuk kebutuhan Anda', body: 'Kecocokan menilai satu kebutuhan terhadap satu mandat, lengkap dengan alasan dan kekurangannya.' }, seeMatches: function () { go('#/matches?source=' + src); },
      typeTabs: isMitra ? { legend: 'Jenis hasil', value: type, options: [{ value: 'inventions', label: 'Inovasi' }, { value: 'funding', label: 'Pendanaan Perusahaan', disabledReason: s.flags.companyFunding ? undefined : 'Tidak aktif pada komposisi ini' }], onChange: function (t) { go('#/discover?type=' + t); } } : null,
      q: field('q', { label: 'Cari', hint: 'Bahasa Indonesia atau Inggris.' }), sector: field('sector', { label: 'Sektor', emptyLabel: 'Semua sektor', options: SECTORS.map(function (x) { return { value: x, label: x }; }) }),
      stage: field('stage', { label: 'Tahap', emptyLabel: 'Semua tahap', options: Object.keys(STAGES).map(function (k) { return { value: k, label: STAGES[k] }; }) }), intake: field('intake', { label: 'Penerimaan', emptyLabel: 'Semua', options: [{ value: 'OPEN', label: 'Dibuka' }, { value: 'UNCONFIRMED', label: 'Belum dikonfirmasi' }] }),
      savedOnly: { label: 'Hanya yang disimpan', checked: fl.savedOnly, onChange: function (v) { fl.savedOnly = v; render(); } },
      resultCount: count + ' hasil', relevant: relevant, others: others, hasRelevant: relevant.length > 0, hasOthers: others.length > 0, none: count === 0,
      clear: function () { ui.filters.discover = { q: '', sector: '', stage: '', intake: '', savedOnly: false }; render(); },
      fundings: fundings.map(function (f) { return { card: fundingCard(f), open: function () { go('#/funding-requests/' + f.id); }, save: function () { svc.toggleSaved(ctx(), { id: f.id }); persist(); }, saveLabel: isSaved(f.id) ? 'Tersimpan' : 'Simpan' }; }),
      partners: partners.map(function (x) {
        var intake = INTAKE[x.intake];
        return { name: party(x.id).name, subtype: x.subtype + ' · ' + (party(x.id).kind === 'personal' ? 'Individu' : 'Organisasi'), thesis: x.thesis, forms: x.forms, sectors: x.sectors.join(', '), source: x.source === 'OWNER_CONFIRMED' ? 'Dikonfirmasi pemilik profil' : 'Dilaporkan sumber', status: { tone: intake[1], label: intake[0], icon: x.intake === 'OPEN' ? 'check' : undefined }, hasCheck: !!x.check, check: x.check ? { subject: 'investorCheck', currency: x.check.currency, min: x.check.min, max: x.check.max, compact: true } : null, open: function () { go('#/partners/' + x.id); }, save: function () { svc.toggleSaved(ctx(), { id: x.id }); persist(); }, saveLabel: isSaved(x.id) ? 'Tersimpan' : 'Simpan', hide: function () { svc.lessRelevant(ctx(), { id: x.id }); persist(); } };
      })
    });
  };

  /* ---------- S10 matches ---------- */
  function sourceRef(id) { return svc.state.fundings[id] ? { type: 'FUNDING_REQUEST', id: id } : { type: 'SUPPORT_REQUEST', id: id }; }
  function mySources() {
    var s = svc.state, out = [];
    Object.keys(s.requests).forEach(function (k) { var r = s.requests[k]; if (svc.isMember(actor(), r.owner) && r.status === 'ACTIVE') out.push({ value: r.id, label: svc.pubV(s.inventions[r.inventionId]).title + ': ' + r.outcome }); });
    Object.keys(s.fundings).forEach(function (k) { var f = s.fundings[k]; if (svc.isMember(actor(), f.owner)) out.push({ value: f.id, label: f.company + ': Pendanaan Perusahaan' }); });
    return out;
  }
  vm.matches = function () {
    var sources = mySources(), id = ui.route.query.source || (sources[0] && sources[0].value), allowed = sources.some(function (x) { return x.value === id; });
    if (!allowed) return Object.assign(base('Kecocokan', 'Pilih kebutuhan untuk melihat investor dan mitra yang sesuai.', 'temukan'), { empty: true, hasResults: false, addNeed: function () { go('#/inventions'); } });
    var ref = sourceRef(id), results = svc.activeTargets(ref);
    function row(r) {
      var opp = svc.state.opportunities[r.opportunity.id], partner = svc.state.partners[opp.partner], ready = READINESS[r.readiness], dup = svc.preflight(ctx(), { source: ref, opportunityId: opp.id }).duplicate;
      var gapAction = r.gap && r.gap.action === 'complete-budget';
      return {
        title: opp.title, partner: party(opp.partner).name + ' · ' + partner.subtype + ' · Versi mandat ' + opp.version, fin: oppFinancial(opp), label: { tone: r.relevant ? ELIGIBILITY_TONE[r.eligibility] : 'neutral', icon: r.eligibility === 'ELIGIBLE' && r.relevant ? 'check' : undefined, label: r.label }, ready: { tone: ready[1], label: ready[0], icon: null },
        reasons: r.reasons, hasReasons: r.reasons.length > 0, hasGap: !!r.gap, gapTitle: r.gap ? r.gap.label : 'Relevansi', gapText: r.gap ? r.gap.reason : 'Topik kebutuhan ini tidak beririsan dengan mandat, walau syaratnya terpenuhi.', gapTone: r.gap && r.gap.result === 'FAIL' ? 'danger' : 'warning', gapStatus: r.gap ? { tone: r.gap.result === 'FAIL' ? 'danger' : 'warning', label: r.gap.result === 'FAIL' ? 'Tidak terpenuhi' : 'Belum diketahui' } : { tone: 'neutral', icon: 'minus', label: 'Topik berbeda' },
        canPitch: r.readiness === 'READY_TO_SUBMIT' && !dup, hasDup: !!dup, openDup: function () { go('#/pitches/' + dup); },
        pitch: function () { go('#/pitches/new?source=' + id + '&target=' + opp.id); },
        canComplete: !!gapAction, complete: function () { go('#/support-requests/' + id + '?return=' + encodeURIComponent('#/matches?source=' + id)); },
        needsInfo: r.readiness === 'NEEDS_INFORMATION' && !gapAction, blocked: r.readiness === 'BLOCKED_FOR_THIS_TARGET', profile: function () { go('#/partners/' + opp.partner); },
        rows: r.rows.map(function (x) { return { label: x.label, result: x.result, stage: x.appliesAt, mandatory: x.mandatory, mode: x.mode, reason: x.reason }; }),
        scoreNote: 'Indeks kecocokan ' + r.fit.lower + '–' + r.fit.upper + ', cakupan informasi ' + Math.round(r.fit.coverage * 100) + '%. Rentang ini menggambarkan informasi yang belum ada, bukan peluang pendanaan.',
        evidence: r.evidence.provided + ' disediakan dan ' + r.evidence.reviewed + ' diperiksa dari ' + r.evidence.applicable + ' syarat.',
        detailKey: 'match-' + id + '-' + opp.id, detailLabel: 'Lihat rincian syarat · ' + opp.title
      };
    }
    var ready = results.filter(function (r) { return r.eligibility !== 'INCOMPATIBLE' && r.relevant; }).map(row), excluded = results.filter(function (r) { return r.eligibility === 'INCOMPATIBLE' || !r.relevant; }).map(row);
    var external = Object.keys(svc.state.partners).map(function (k) { return svc.state.partners[k]; }).filter(function (x) { return x.route === 'EXTERNAL'; }).map(function (x) { return { name: party(x.id).name, url: x.externalUrl, source: 'Dilaporkan sumber. Membuka formulir di luar TemuRiset bukan pitching yang terkirim.' }; });
    return Object.assign(base('Kecocokan', 'Satu kebutuhan dinilai terhadap setiap mandat secara terpisah.', 'temukan'), {
      empty: false, loading: ui.loading === ui.route.hash, hasResults: ui.loading !== ui.route.hash, source: { label: 'Kebutuhan yang dipakai', emptyLabel: null, value: id, options: sources, id: 'match-source', onChange: function (v) { go('#/matches?source=' + v); } },
      ready: ready, excluded: excluded, hasReady: ready.length > 0, noReady: ready.length === 0, hasExcluded: excluded.length > 0, excludedLabel: excluded.length + ' mandat tidak direkomendasikan untuk kebutuhan ini', external: external, hasExternal: external.length > 0
    });
  };

  /* ---------- S11 preflight ---------- */
  vm.preflight = function () {
    var q = ui.route.query, ref = sourceRef(q.source), src = svc.sourceOf(ref), opp = svc.state.opportunities[q.target];
    if (!src || !opp || !svc.can(actor(), src.owner, 'view')) return Object.assign(base('Akses dibatasi', '', 'pitching'), { allowed: false, denied: true });
    var key = 'pre-' + q.source + '-' + q.target, pre = svc.preflight(ctx(), { source: ref, opportunityId: q.target }), r = pre.result;
    var docs = Object.keys(svc.state.documents).map(function (k) { return svc.state.documents[k]; }).filter(function (d) { return d.owner === src.owner; });
    var f = form(key, function () { return { brief: svc.templateBrief({ source: ref, opportunityId: q.target }), token: pre.token, files: {} }; });
    var stale = f.v.token.opportunityVersion !== opp.version || f.v.token.sourceVersion !== src.version, ready = READINESS[r.readiness];
    var mustPickFile = opp.requirements.some(function (x) { return x.mode === 'DOCUMENT_PRESENT' && x.appliesAt === 'SUBMISSION'; });
    var chosen = docs.filter(function (d) { return f.v.files[d.id]; }).map(function (d) { return { docId: d.id, version: svc.last(d.versions).n }; });
    var intent = 'submit-' + key;
    function send() {
      clearFail(f); f.lost = false;
      if (mustPickFile && !chosen.length) { fail(f, { fields: { files: 'Pilih berkas yang ingin dibagikan kepada penerima ini.' } }); render(); return; }
      if (f.v.brief.trim().length < 20) { fail(f, { fields: { brief: 'Brief terlalu pendek. Ceritakan masalah dan dukungan yang diminta.' } }); render(); return; }
      run('send', function () { return svc.submitPitch(ctx(once(intent)), { source: ref, opportunityId: q.target, token: f.v.token, brief: f.v.brief, files: chosen }); }, function (res) {
        if (res.ok) { spent(intent); delete ui.forms[key]; notice(res.replayed ? 'Pitching Anda sudah tercatat sebelumnya. Tidak ada kiriman ganda.' : 'Pitching terkirim kepada ' + party(opp.partner).name + '.'); go('#/pitches/' + res.pitchId, { keepNotice: true }); return; }
        if (res.code === 'LOST_RESPONSE') { f.lost = true; return; }
        spent(intent);
        if (res.code === 'STALE_VERSION') { f.staleHit = true; return; }
        if (res.code === 'DUPLICATE') { f.dup = res.pitchId; return; }
        fail(f, res);
      });
    }
    var ai = svc.state.flags.ai;
    return Object.assign(base('Periksa sebelum mengirim', 'Tidak ada yang terkirim sampai Anda menekan tombol kirim.', 'pitching'), {
      allowed: true, denied: false, ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Mengirim sebagai' }),
      ready: { tone: ready[1], label: ready[0] }, isReady: r.readiness === 'READY_TO_SUBMIT' && !stale, notReady: r.readiness !== 'READY_TO_SUBMIT',
      rows: [['Penerima', party(opp.partner).name + ' · ' + opp.title], ['Versi mandat', 'Versi ' + opp.version], ['Yang diajukan', (src.funding ? 'Pendanaan Perusahaan ' + src.funding.company : src.request.outcome) + ' · Versi ' + src.version], ['Inovasi', src.inventions.map(function (l) { var i = svc.state.inventions[l.inventionId]; return i.versions[l.version - 1].title + ' versi ' + l.version; }).join(', ')], ['Tujuan', { PROJECT: 'Dukungan Proyek', LICENSE: 'Lisensi', EQUITY: 'Pendanaan Perusahaan (ekuitas)' }[src.relationship]]].map(function (x, n) { return { id: 'pf' + n, label: x[0], value: x[1] }; }),
      isFunding: !!src.funding, isProject: !!src.request, fundingCard: src.funding ? fundingCard(src.funding) : null, fin: src.request ? srFinancial(src.request) : null, oppFin: oppFinancial(opp),
      reqRows: r.rows.map(function (x) { return { label: x.label, result: x.result, stage: x.appliesAt, mandatory: x.mandatory, mode: x.mode, reason: x.reason }; }),
      files: docs.map(function (d) { var v = svc.last(d.versions); return { check: { id: fid(key, d.id), label: 'Bagikan ' + d.title + ' versi ' + v.n, hint: 'Hanya versi ini, hanya kepada ' + party(opp.partner).name + '.', checked: !!f.v.files[d.id], onChange: function (x) { f.v.files[d.id] = x; delete f.err.files; f.list = []; render(); } }, doc: docProps(d) }; }), hasFiles: docs.length > 0, noFiles: docs.length === 0,
      fileError: f.err.files || null, hasFileError: !!f.err.files, fileAnchor: fid(key, 'files'),
      brief: bind(f, 'brief', { label: 'Brief pitching', hint: 'Dibuat dari fakta yang ada. Anda dapat mengubahnya.', rows: 9 }),
      aiOn: ai === 'on' || ai === 'down', aiDown: !!f.aiFail, aiBusy: !!ui.busy.ai,
      summarize: function () {
        f.aiFail = false;
        run('ai', function () { return ai === 'on'; }, function (ok) {
          if (!ok) { f.aiFail = true; return; }
          f.v.brief = f.v.brief.split('\n').slice(0, 4).join('\n');
        });
      },
      showSummary: summary(f).show, summaryProps: summary(f).props, lost: !!f.lost,
      lostProps: { id: fid(key, 'lost'), title: 'Status pengiriman belum diketahui', focusKey: 1, children: 'Jawaban layanan tidak kami terima. Pitching mungkin sudah tercatat. Kirim ulang aman: isi dan kunci yang sama tidak membuat kiriman ganda.', retry: { label: 'Coba kirim lagi', onClick: send } },
      stale: stale, staleProps: { what: 'Mandat atau kebutuhan berubah setelah pemeriksaan ini dibuat.', currentVersion: 'Versi mandat ' + opp.version + ', versi kebutuhan ' + src.version, draft: f.v.brief, refreshLabel: 'Periksa ulang', onRefresh: function () { f.v.token = pre.token; f.staleHit = false; render(); } },
      hasDup: !!(pre.duplicate || f.dup), openDup: function () { go('#/pitches/' + (pre.duplicate || f.dup)); }, closed: opp.status !== 'ACTIVE',
      sending: !!ui.busy.send, send: send, canSend: r.readiness === 'READY_TO_SUBMIT' && !stale && !pre.duplicate && opp.status === 'ACTIVE',
      effect: 'Pitching dikirim kepada ' + party(opp.partner).name + ' sebagai ' + party(src.owner).name + '. Versi di atas dibekukan dan berkas terpilih dibagikan kepada penerima ini saja.',
      back: function () { back('#/matches?source=' + q.source); },
      print: function () { try { window.print(); } catch (e) { /* print blocked by host */ } }
    });
  };

  /* ---------- S12 pitch lists ---------- */
  vm.pitches = function () {
    var box = ui.route.query.box, isMitra = persona() === 'mitra', fl = ui.filters.pitches || (ui.filters.pitches = { status: '', turn: '' });
    var all = myPitches(), rows = all.filter(function (p) {
      if (box === 'masuk' && !(svc.isMember(actor(), p.recipient) && p.status !== 'APPROVED_FOR_DISCUSSION')) return false;
      if (box === 'diskusi' && p.status !== 'APPROVED_FOR_DISCUSSION') return false;
      var t = pitchTurn(p);
      return (!fl.status || p.status === fl.status) && (!fl.turn || t.who === fl.turn);
    }).map(function (p) {
      var t = pitchTurn(p), st = STATUS[p.status], outgoing = svc.isMember(actor(), p.requester), last = p.timeline[p.timeline.length - 1];
      return { title: subjectTitle(p), peer: (outgoing ? 'Kepada ' + party(p.recipient).name : 'Dari ' + party(p.requester).name) + ' · ' + p.opportunity.title, purpose: { PROJECT: 'Dukungan Proyek', LICENSE: 'Lisensi', EQUITY: 'Pendanaan Perusahaan' }[p.purpose], status: { tone: st[1], label: st[0], icon: null }, turn: t.who ? { tone: t.who === 'you' ? 'action' : 'neutral', label: t.who === 'you' ? 'Menunggu Anda' : 'Menunggu pihak lain' } : { tone: 'neutral', icon: null, label: 'Tidak ada tindakan' }, updated: 'Diperbarui ' + when(last.at), inventions: p.inventions.length > 1 ? p.inventions.length + ' inovasi terkait, satu permintaan pendanaan' : '', hasInventions: p.inventions.length > 1, open: function () { openPitch(p); } };
    });
    var titles = { masuk: 'Pitching Masuk', diskusi: 'Diskusi dan Jadwal' };
    function field(name, extra) { return Object.assign({ id: 'pf-' + name, value: fl[name], onChange: function (v) { fl[name] = v; render(); } }, extra); }
    return Object.assign(base(titles[box] || 'Pitching dan Diskusi', 'Filter tetap tersimpan saat Anda kembali dari sebuah kasus.', isMitra ? (box === 'diskusi' ? 'diskusi' : 'masuk') : 'pitching'), {
      rows: rows, hasRows: rows.length > 0, noneFiltered: rows.length === 0 && !!(fl.status || fl.turn), noneAtAll: rows.length === 0 && !(fl.status || fl.turn), isInovator: !isMitra,
      status: field('status', { label: 'Status', emptyLabel: 'Semua status', options: Object.keys(STATUS).map(function (k) { return { value: k, label: STATUS[k][0] }; }) }), turn: field('turn', { label: 'Giliran', emptyLabel: 'Semua', options: [{ value: 'you', label: 'Menunggu Anda' }, { value: 'other', label: 'Menunggu pihak lain' }] }),
      clear: function () { ui.filters.pitches = { status: '', turn: '' }; render(); }, explore: function () { go('#/discover'); }
    });
  };

  /* ---------- S13 workspace ---------- */
  function deniedView() { return Object.assign(base('Anda belum memiliki akses', '', nav(['pitching', 'masuk'])), { allowed: false, denied: true, leave: function () { back('#/home'); } }); }
  vm.workspace = function () {
    var id = ui.route.params.id, p = svc.pitchFor(actor(), id);
    if (!p) return deniedView();
    var isRecipient = svc.isMember(actor(), p.recipient), t = pitchTurn(p), st = STATUS[p.status], sub = p.submissions[p.submissions.length - 1], tab = ui.route.query.tab || t.tab || 'ringkasan';
    var decidable = isRecipient && ['SUBMITTED', 'UNDER_REVIEW'].indexOf(p.status) >= 0, canDecide = svc.can(actor(), p.recipient, 'decide');
    var f = form('pit-' + id, function () { return { reason: '', msg: '', task: '' }; }), dlg = ui.dialog && ui.dialog.pitch === id ? ui.dialog.kind : null;
    var snap = sub.funding, req = sub.request;
    function decide(decision) {
      clearFail(f);
      var name = 'decide-' + id + '-' + p.version, reason = f.v.reason;
      run('decide', function () { return svc.decide(ctx(once(name)), { pitchId: id, decision: decision, reason: reason, expected: p.version }); }, function (r) {
        spent(name);
        if (r.ok) { ui.dialog = null; f.v.reason = ''; notice(decision === 'APPROVE' ? 'Disetujui untuk diskusi. Ini belum merupakan pendanaan atau kerja sama.' : 'Pitching ditolak. Alasan hanya terlihat oleh pengirim.'); return; }
        if (!r.fields) ui.dialog = null;
        fail(f, r);
      });
    }
    var rejectReason = p.decisions.filter(function (d) { return d.decision === 'REJECT'; })[0];
    var tabs = [{ id: 'ringkasan', label: 'Ringkasan' }, { id: 'revisi', label: 'Revisi' + (p.rounds.length ? ' (' + p.rounds.length + ')' : '') }, { id: 'dokumen', label: 'Dokumen' }, { id: 'diskusi', label: 'Diskusi' }];
    if (p.status === 'APPROVED_FOR_DISCUSSION') tabs.push({ id: 'jadwal', label: 'Jadwal' });
    tabs.push({ id: 'riwayat', label: 'Riwayat' });
    var rel = svc.partnershipOf(id), grants = Object.keys(svc.state.grants).map(function (k) { return svc.state.grants[k]; }).filter(function (g) { return g.pitchId === id; });
    var parties = [p.requester, p.recipient];
    return Object.assign(base(subjectTitle(p), (isRecipient ? 'Dari ' + party(p.requester).name : 'Kepada ' + party(p.recipient).name) + ' · ' + p.opportunity.title + ' · Versi mandat ' + p.opportunity.version, nav(['pitching', p.status === 'APPROVED_FOR_DISCUSSION' ? 'diskusi' : 'masuk'])), {
      allowed: true, denied: false, status: { tone: st[1], label: st[0], icon: null }, turn: t, hasTurn: !!t.who, noTurn: !t.who, next: { who: t.who, title: t.title, body: t.text || undefined }, hasNextAction: t.who === 'you' && (tab !== t.tab || t.partnership || t.propose), nextLabel: t.label, nextAct: turnAction(p, t),
      noTurnNote: { tone: st[1], label: t.title }, noTurnText: t.text || 'Tidak ada tindakan yang menunggu.', backLabel: isRecipient ? 'Kembali ke Pitching Masuk' : 'Kembali ke Pitching dan Diskusi', back: function () { back(isRecipient ? '#/pitches?box=masuk' : '#/pitches'); },
      ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Bertindak sebagai' }),
      tabsProps: { label: 'Bagian ruang pitching', tabs: tabs.map(function (x) { return { id: x.id, label: x.label, content: null }; }), value: tab, onChange: function (x) { ui.route = parse('#/pitches/' + id + '?tab=' + x); ui.notice = null; setHash(ui.route.hash); render(); } },
      /* summary */
      submissionLabel: 'Submisi ' + p.submissions.length + ' · dikirim ' + when(sub.at), brief: sub.brief, isFunding: !!snap, isProject: !!req, fundingSnap: snap ? fundingCard(snap) : null, fin: req ? srFinancial(req) : null,
      facts: (sub.inventions[0].facts || []).map(function (x) { return { label: x.label, source: { value: x.value, timing: x.timing, provenance: x.provenance } }; }), hasFacts: (sub.inventions[0].facts || []).length > 0,
      invList: sub.inventions.map(function (x) { return { text: x.title + ' · versi ' + x.version + ' · ' + STAGES[x.stage], open: function () { go('#/inventions/' + x.id); } }; }),
      reqRows: sub.requirements.map(function (x) { return { label: x.label, result: x.result, stage: x.appliesAt, mandatory: x.mandatory, mode: x.mode, reason: x.reason }; }),
      decidable: decidable && canDecide, viewOnly: decidable && !canDecide, showBegin: isRecipient && p.status === 'SUBMITTED' && canDecide,
      beginBusy: !!ui.busy.begin, begin: function () { run('begin', function () { return svc.beginReview(ctx(), { pitchId: id }); }); },
      openApprove: function () { ui.dialog = { pitch: id, kind: 'approve' }; render(); }, openReject: function () { ui.dialog = { pitch: id, kind: 'reject' }; render(); }, openRevision: function () { ui.route = parse('#/pitches/' + id + '?tab=revisi'); setHash(ui.route.hash); render(); },
      approveDlg: { open: dlg === 'approve', title: 'Setujui untuk diskusi?', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Setujui untuk diskusi', busy: !!ui.busy.decide, busyLabel: 'Menyimpan keputusan…', onClick: function () { decide('APPROVE'); } } },
      rejectDlg: { open: dlg === 'reject', title: 'Tolak pitching ini?', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Tolak pitching', intent: 'danger', busy: !!ui.busy.decide, busyLabel: 'Menyimpan keputusan…', onClick: function () { decide('REJECT'); } }, initialFocusId: fid(f.key, 'reason') },
      reason: bind(f, 'reason', { label: 'Alasan singkat', hint: 'Hanya terlihat oleh pengirim pitching. Tidak memengaruhi reputasi publik.', required: true, rows: 3 }),
      showSummary: summary(f).show, summaryProps: summary(f).props, wasRejected: !!rejectReason, rejectText: rejectReason ? 'Alasan: ' + rejectReason.reason : '',
      canWithdraw: !isRecipient && ['SUBMITTED', 'UNDER_REVIEW', 'REVISION_REQUESTED'].indexOf(p.status) >= 0,
      withdrawDlg: { open: dlg === 'withdraw', title: 'Tarik pitching ini?', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Tarik pitching', intent: 'danger', busy: !!ui.busy.withdraw, onClick: function () { run('withdraw', function () { return svc.withdraw(ctx(), { pitchId: id }); }, function () { ui.dialog = null; notice('Pitching ditarik. Penerima tidak dapat lagi memutuskan kiriman ini.'); }); } } },
      openWithdraw: function () { ui.dialog = { pitch: id, kind: 'withdraw' }; render(); },
      closable: p.status === 'APPROVED_FOR_DISCUSSION' && !rel, openClose: function () { ui.dialog = { pitch: id, kind: 'close' }; render(); },
      closeDlg: { open: dlg === 'close', title: 'Tutup diskusi ini?', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Tutup diskusi', intent: 'danger', onClick: function () { var r = svc.closeDiscussion(ctx(), { pitchId: id, reason: f.v.reason }); if (r.ok) { ui.dialog = null; f.v.reason = ''; persist(); render(); } else { fail(f, r); render(); } } } },
      hasRel: !!rel, openRel: function () { go('#/partnerships/' + rel.id); },
      /* documents */
      docs: sub.files.map(function (x) {
        var g = grants.filter(function (y) { return y.docId === x.docId && y.version === x.version; })[0], d = svc.state.documents[x.docId], mine = svc.isMember(actor(), d.owner), probe = svc.state.grants && g;
        var deniedDoc = !mine && (!g || g.revoked);
        return { denied: deniedDoc, ok: !deniedDoc, props: deniedDoc ? { denied: true } : docProps(d, { version: x.version, grant: g }), mine: mine && !!g && !g.revoked, revoke: function () { ui.dialog = { pitch: id, kind: 'revoke', grant: g.id }; render(); },
          download: function () { var res = svc.fetchDocument(ctx(), { docId: x.docId, version: x.version }); notice(res.ok ? 'Unduhan demo disiapkan: ' + res.title + ' versi ' + x.version + '.' : 'Akses ke dokumen ini sudah tidak tersedia.', res.ok ? 'success' : 'warning'); persist(); render(); }, canDownload: !deniedDoc && !!probe };
      }), hasDocs: sub.files.length > 0, noDocs: sub.files.length === 0,
      revokeDlg: { open: dlg === 'revoke', title: 'Cabut akses dokumen?', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Cabut akses', intent: 'danger', onClick: function () { svc.revokeGrant(ctx(), { id: ui.dialog.grant }); ui.dialog = null; persist(); notice('Akses dicabut. Unduhan baru diblokir, tetapi salinan yang sudah diunduh tidak dapat ditarik.'); render(); } } },
      /* discussion */
      messages: p.messages.map(function (m) { return { who: party(m.by).name, at: when(m.at), text: m.text }; }), hasMessages: p.messages.length > 0, noMessages: p.messages.length === 0,
      msg: bind(f, 'msg', { label: 'Tulis pesan', rows: 3 }), msgBusy: !!ui.busy.msg, send: function () { var text = f.v.msg; run('msg', function () { return svc.sendMessage(ctx(), { pitchId: id, text: text }); }, function (r) { if (r.ok) { f.v.msg = ''; clearFail(f); } else fail(f, r); }); },
      tasks: p.tasks.map(function (x) { return { title: x.title, owner: 'Penanggung jawab: ' + party(x.owner).name, done: x.status === 'DONE', open: x.status !== 'DONE', status: { tone: x.status === 'DONE' ? 'success' : 'neutral', label: x.status === 'DONE' ? 'Selesai' : 'Terbuka' }, finish: function () { svc.completeTask(ctx(), { pitchId: id, taskId: x.id }); persist(); } }; }), hasTasks: p.tasks.length > 0,
      task: bind(f, 'task', { label: 'Tugas baru', hint: 'Klarifikasi setelah persetujuan dicatat sebagai tugas.' }), taskOwner: { label: 'Penanggung jawab', emptyLabel: null, value: f.v.taskOwner || parties[0], options: parties.map(function (x) { return { value: x, label: party(x).name }; }), onChange: function (v) { f.v.taskOwner = v; render(); } },
      addTask: function () { var r = svc.addTask(ctx(), { pitchId: id, title: f.v.task, owner: f.v.taskOwner || parties[0] }); if (r.ok) { f.v.task = ''; clearFail(f); persist(); render(); } else { fail(f, r); render(); } },
      /* history */
      timeline: p.timeline.slice().reverse().map(function (x) { return { text: x.text, who: party(x.by).name, at: when(x.at) }; }),
      submissions: p.submissions.map(function (x, n) { return { label: 'Submisi ' + (n + 1) + ' · ' + when(x.at) + ' · mandat versi ' + x.opportunityVersion + ' · kebutuhan versi ' + x.sourceVersion, brief: x.brief }; }),
      report: function () { go('#/settings?report=' + id); }
    });
  };

  /* ---------- revision panel ---------- */
  vm.revisions = function () {
    var id = ui.route.params.id, p = svc.pitchFor(actor(), id);
    if (!p) return { allowed: false };
    var isRecipient = svc.isMember(actor(), p.recipient), canAsk = isRecipient && ['SUBMITTED', 'UNDER_REVIEW'].indexOf(p.status) >= 0 && svc.can(actor(), p.recipient, 'decide'), round = p.rounds.length ? p.rounds[p.rounds.length - 1] : null, answering = !isRecipient && p.status === 'REVISION_REQUESTED';
    var compose = form('rev-new-' + id + '-' + p.rounds.length, function () { return { items: D.clone(D.revisionItems) }; });
    function send() {
      clearFail(compose);
      var name = 'rev-' + id + '-' + p.version;
      run('revise', function () { return svc.requestRevision(ctx(once(name)), { pitchId: id, expected: p.version, items: compose.v.items }); }, function (r) {
        spent(name);
        if (r.ok) notice('Revisi putaran ' + r.round + ' dikirim. Menunggu jawaban pihak lain.'); else fail(compose, r);
      });
    }
    var ans = form('rev-ans-' + id + '-' + p.rounds.length, function () { var v = {}; if (round) round.items.forEach(function (i) { v[i.id] = i.answer ? { response: i.answer.response, text: i.answer.text } : {}; }); return { answers: v, files: {} }; });
    var docs = Object.keys(svc.state.documents).map(function (k) { return svc.state.documents[k]; }).filter(function (d) { return d.owner === p.requester; });
    function saveAll(then) {
      ans.save = 'saving'; render();
      run('saveAns', function () {
        var res = { ok: true };
        round.items.forEach(function (i) { var r = svc.saveAnswer(ctx(), { pitchId: id, itemId: i.id, value: ans.v.answers[i.id] }); if (!r.ok) res = r; });
        return res;
      }, function (r) { ans.save = r.ok ? 'saved' : 'failed'; if (r.ok && then) then(); });
    }
    function resubmit() {
      clearFail(ans);
      var missing = round.items.filter(function (i) { return i.required && !(ans.v.answers[i.id] || {}).response; });
      if (missing.length) {
        ans.err = {}; missing.forEach(function (i) { ans.err[i.id] = 'Pilih tanggapan untuk pertanyaan wajib ini.'; });
        ans.list = missing.map(function (i) { return { fieldId: fid(ans.key, i.id), message: 'Jawab: ' + i.question }; }); ans.focusKey += 1; render(); return;
      }
      saveAll(function () {
        var chosen = docs.filter(function (d) { return ans.v.files[d.id]; }).map(function (d) { return { docId: d.id, version: svc.last(d.versions).n }; }), name = 'resub-' + id + '-' + p.version;
        run('resubmit', function () { return svc.resubmit(ctx(once(name)), { pitchId: id, expected: p.version, files: chosen.length ? chosen : p.submissions[p.submissions.length - 1].files }); }, function (r) {
          spent(name);
          if (r.ok) { notice('Dikirim ulang sebagai submisi ' + r.submission + '. Submisi sebelumnya tetap tersimpan.'); ui.route = parse('#/pitches/' + id + '?tab=ringkasan'); setHash(ui.route.hash); return; }
          if (r.code === 'STALE_VERSION') ans.staleHit = r.message; else fail(ans, r);
        });
      });
    }
    var hist = p.rounds.slice().reverse().map(function (r) {
      return { label: 'Putaran ' + r.n, isCurrent: r === round && answering, items: r.items.map(function (i, n) {
        var a = i.answer, labels = { CAN: 'Dapat dipenuhi', DISCUSS: 'Perlu diskusi', CANNOT: 'Belum dapat dipenuhi' };
        return { index: n + 1, question: i.question, reason: 'Alasan: ' + i.reason, expect: i.expect ? 'Yang diharapkan: ' + i.expect : '', required: { tone: i.required ? 'action' : 'neutral', icon: null, label: i.required ? 'Wajib dijawab' : 'Opsional' },
          answered: !!(a && a.response), notAnswered: !(a && a.response), answerLabel: a && a.response ? labels[a.response] : 'Belum dijawab', answerText: a ? a.text || '' : '', review: i.review === 'ACCEPTED' ? 'Diterima' : i.review === 'NEEDS_DETAIL' ? 'Perlu detail: ' + (i.reviewNote || '') : '', hasReview: !!i.review,
          canReview: isRecipient && !!(a && a.response) && !i.review && svc.can(actor(), p.recipient, 'decide'), accept: function () { svc.reviewItem(ctx(), { pitchId: id, itemId: i.id, result: 'ACCEPTED' }); persist(); }, askDetail: function () { svc.reviewItem(ctx(), { pitchId: id, itemId: i.id, result: 'NEEDS_DETAIL', note: 'Mohon rincian tambahan melalui putaran revisi berikutnya.' }); persist(); } };
      }) };
    });
    return {
      allowed: true, canAsk: canAsk, answering: answering, none: !p.rounds.length && !canAsk, hasHistory: hist.length > 0, history: hist.filter(function (h) { return !h.isCurrent; }), hasPast: hist.filter(function (h) { return !h.isCurrent; }).length > 0,
      roundLabel: 'Revisi putaran ' + (p.rounds.length + 1),
      composeItems: compose.v.items.map(function (i, n) {
        function set(k) { return function (v) { i[k] = v; render(); }; }
        return { n: n + 1, question: { id: 'q' + n, label: 'Pertanyaan ' + (n + 1), value: i.question, rows: 2, onChange: set('question') }, reason: { id: 'w' + n, label: 'Alasan', value: i.reason, onChange: set('reason') }, expect: { id: 'e' + n, label: 'Yang diharapkan', value: i.expect, onChange: set('expect') }, required: { id: 'r' + n, label: 'Wajib dijawab', checked: i.required, onChange: set('required') }, remove: function () { compose.v.items = compose.v.items.filter(function (y) { return y !== i; }); render(); } };
      }),
      addItem: function () { compose.v.items.push({ category: 'Lainnya', question: '', reason: '', required: false, due: null, expect: '' }); render(); },
      composeSummary: summary(compose).props, composeShow: summary(compose).show, sendBusy: !!ui.busy.revise, send: send,
      answerItems: round && answering ? round.items.map(function (i, n) { return { props: { id: fid(ans.key, i.id), round: round.n, index: n + 1, question: i.question, reason: i.reason, required: i.required, due: i.due ? i.due + 'T00:00:00Z' : undefined, value: ans.v.answers[i.id], error: ans.err[i.id] || null, onChange: function (v) { ans.v.answers[i.id] = v; ans.save = 'local'; delete ans.err[i.id]; render(); } }, expect: i.expect ? 'Yang diharapkan: ' + i.expect : '' }; }) : [],
      files: docs.map(function (d) { var v = svc.last(d.versions); return { id: d.id, check: { label: d.title + ' · versi ' + v.n, hint: 'Hanya versi ini yang dibagikan kepada penerima.', checked: !!ans.v.files[d.id], onChange: function (x) { ans.v.files[d.id] = x; render(); } } }; }),
      newVersion: function () { var d = docs[0]; if (ui.failUpload) { ans.uploadErr = 'Berkas gagal diunggah. Jawaban Anda tidak berubah.'; ui.failUpload = false; render(); return; } ans.uploadErr = null; svc.newDocumentVersion(ctx(), { id: d.id }); persist(); }, hasDoc: docs.length > 0,
      failUpload: { label: 'Simulasikan unggahan gagal', hint: 'Kontrol uji, satu kali.', checked: !!ui.failUpload, onChange: function (v) { ui.failUpload = v; render(); } }, uploadErr: ans.uploadErr || '', hasUploadErr: !!ans.uploadErr,
      save: { state: ui.busy.saveAns ? 'saving' : (ans.save === 'saved' ? 'saved' : ans.dirty || ans.save === 'local' ? 'local' : 'saved'), location: 'demo' }, saveDraft: function () { saveAll(); }, answerShow: summary(ans).show, answerSummary: summary(ans).props,
      resubmit: resubmit, resubmitBusy: !!ui.busy.resubmit || !!ui.busy.saveAns, staleMsg: ans.staleHit || '', hasStale: !!ans.staleHit, staleProps: { what: ans.staleHit, onRefresh: function () { ans.staleHit = null; render(); }, refreshLabel: 'Muat versi terbaru' },
      effect: 'Mengirim ulang membuat submisi baru. Submisi dan putaran sebelumnya tetap tersimpan. Jawaban bukan persetujuan.',
      ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Menjawab sebagai' })
    };
  };

  /* ---------- S14 schedule ---------- */
  function slotOptions(z) {
    var out = [];
    ['2026-11-04', '2026-11-05', '2026-11-06'].forEach(function (d) {
      for (var h = 7; h <= 14; h++) ['00', '30'].forEach(function (m) {
        var t = d + 'T' + String(h).padStart(2, '0') + ':' + m + ':00.000Z';
        out.push({ value: t, label: TR.format.longDate(t, z) + ' · ' + TR.format.time(t, z) + ' ' + TR.format.zoneLabel(z) });
      });
    });
    return out;
  }
  vm.schedule = function () {
    var id = ui.route.params.id, p = svc.pitchFor(actor(), id);
    if (!p || p.status !== 'APPROVED_FOR_DISCUSSION') return { allowed: false, notOpen: true };
    var open = svc.openProposal(id), latest = svc.latestProposal(id), meeting = svc.activeMeeting(id), otherParty = p.requester === ui.partyId ? p.recipient : p.requester;
    var otherAcc = Object.keys(svc.state.accounts).map(function (k) { return svc.state.accounts[k]; }).filter(function (a) { return a.contexts.indexOf(otherParty) >= 0 && a.id !== 'stafA'; })[0], z = zone();
    var seedSlots = open || !latest ? (p.requester === ui.partyId ? ['2026-11-04T09:30:00.000Z', '2026-11-04T10:00:00.000Z'] : D.defaultSlots.map(function (x) { return new Date(x).toISOString(); })) : latest.slots.map(function (x) { return x.start; });
    var f = form('sch-' + id + '-' + ui.partyId, function () { return { composing: false, rescheduling: false, slots: seedSlots, minutes: '60', zone: z, agenda: latest ? latest.agenda : 'Membahas rencana validasi enam bulan', link: '', selected: null, outcome: 'COMPLETED', note: '' }; });
    var finished = Object.keys(svc.state.meetings).map(function (k) { return svc.state.meetings[k]; }).filter(function (x) { return x.pitchId === id && (x.state === 'COMPLETED' || x.state === 'NO_SHOW_REPORTED'); }).pop();
    var composing = !!(f.v.rescheduling || f.v.composing || (!meeting && !open && !finished));
    var shown = open || latest, closedState = latest && !open && !meeting && !finished ? latest.state : null;
    var options = slotOptions(z);
    function propose() {
      clearFail(f);
      var name = 'prop-' + id + '-' + (open ? open.id : 'new') + '-' + (meeting ? meeting.id : '');
      var args = { pitchId: id, slots: f.v.slots, minutes: Number(f.v.minutes), zone: f.v.zone, agenda: f.v.agenda, link: f.v.link, replaces: f.v.rescheduling && meeting ? meeting.id : undefined };
      run('propose', function () { return svc.proposeSlots(ctx(once(name)), args); }, function (r) {
        spent(name);
        if (r.ok) { f.v.composing = false; f.v.rescheduling = false; notice(args.replaces ? 'Jadwal pengganti diusulkan. Pertemuan yang ada tetap berlaku sampai pengganti dikonfirmasi.' : 'Usulan waktu dikirim. Menunggu pihak lain.'); return; }
        fail(f, r);
      });
    }
    var intent = open ? 'accept-' + open.id + '-' + f.v.selected : '';
    function confirm() {
      clearFail(f); f.conflict = null;
      run('accept', function () { return svc.acceptSlot(ctx(once(intent)), { proposalId: open.id, slotId: f.v.selected }); }, function (r) {
        spent(intent);
        if (r.ok) { f.v.selected = null; notice('Waktu pertemuan dikonfirmasi.'); return; }
        if (r.code === 'BOOKING_CONFLICT') { f.conflict = r.message; f.v.selected = null; return; }
        f.conflict = r.message;
      });
    }
    var m = meeting;
    var calendarNote = svc.state.flags.calendar ? 'Adaptor kalender aktif dalam simulasi. Ketersediaan luar belum diperiksa sungguhan pada demo ini.' : 'Kalender luar tidak terhubung, jadi ketersediaan di luar TemuRiset belum diketahui. Bentrok dicek pada jadwal internal.';
    var started = m && new Date(svc.state.clock).getTime() >= new Date(m.start).getTime();
    return {
      allowed: true, notOpen: false, composing: composing, choosing: !composing && !!open && open.by !== ui.partyId, waiting: !composing && !!open && open.by === ui.partyId, hasMeeting: !!m, showMeeting: !!m && !f.v.rescheduling, calendarNote: calendarNote,
      isDone: !composing && !m && !open && !!finished, doneLabel: finished ? (finished.state === 'COMPLETED' ? 'Pertemuan selesai' : 'Pertemuan dilaporkan tidak terjadi') : '', doneText: finished ? TR.format.longDate(finished.start, z) + ' · ' + TR.format.slotTime(finished.start, finished.minutes, z) + ' · Agenda: ' + finished.agenda : '', doneTone: finished && finished.state === 'COMPLETED' ? 'success' : 'neutral',
      composeAnother: function () { f.v.composing = true; f.v.slots = ['2026-11-05T09:00:00.000Z', '2026-11-05T11:00:00.000Z']; render(); },
      closedNote: closedState === 'EXPIRED' ? (latest.expiredBy === 'AGE' ? 'Usulan sebelumnya kedaluwarsa setelah 72 jam. Pitching tetap disetujui untuk diskusi.' : 'Semua waktu pada usulan sebelumnya sudah lewat. Pitching tetap disetujui untuk diskusi.') : closedState === 'CANCELLED' ? 'Usulan sebelumnya dibatalkan.' : '', hasClosedNote: closedState === 'EXPIRED' || closedState === 'CANCELLED',
      composeTitle: f.v.rescheduling ? 'Usulkan jadwal pengganti' : open ? 'Usulkan waktu lain' : 'Usulkan waktu pertemuan', isReschedule: !!f.v.rescheduling, keepNote: 'Pertemuan yang sudah dikonfirmasi tetap berlaku sampai pengganti dikonfirmasi.',
      slotRows: f.v.slots.map(function (x, n) { return { field: { id: fid(f.key, 'slot' + n), label: 'Waktu ' + (n + 1), emptyLabel: null, value: x, options: options, onChange: function (v) { f.v.slots[n] = v; render(); } }, remove: function () { f.v.slots = f.v.slots.filter(function (y, i) { return i !== n; }); render(); }, canRemove: f.v.slots.length > 2 }; }),
      addSlot: function () { f.v.slots.push(options[6].value); render(); }, canAddSlot: f.v.slots.length < 5, slotsError: f.err.slots || '', hasSlotsError: !!f.err.slots,
      minutes: bind(f, 'minutes', { legend: 'Durasi', options: [{ value: '30', label: '30 menit' }, { value: '60', label: '60 menit' }] }), zoneField: bind(f, 'zone', { label: 'Zona waktu usulan', emptyLabel: null, options: ZONES }),
      agenda: bind(f, 'agenda', { label: 'Agenda', rows: 2, required: true }), link: bind(f, 'link', { label: 'Tautan pertemuan (opsional)', hint: 'Harus memakai https.' }),
      showSummary: summary(f).show, summaryProps: summary(f).props, proposeBusy: !!ui.busy.propose, propose: propose, cancelCompose: function () { f.v.composing = false; f.v.rescheduling = false; render(); }, canCancelCompose: !!(f.v.composing || f.v.rescheduling),
      list: shown ? { slots: shown.slots.map(function (x) { return { id: x.id, start: x.start, minutes: shown.minutes, conflict: x.conflict }; }), zone: z, otherZone: otherAcc ? otherAcc.zone : undefined, selectedId: f.v.selected, onSelect: function (v) { f.v.selected = v; f.conflict = null; render(); }, onConfirm: confirm, onPropose: function () { f.v.composing = true; f.v.slots = seedSlots.slice(); render(); }, busy: !!ui.busy.accept, agenda: shown.agenda } : null,
      hasConflict: !!f.conflict, conflictText: f.conflict, conflictStatus: { tone: 'warning', icon: 'alert', label: 'Belum dikonfirmasi' }, selectionNote: f.v.selected ? 'Waktu ini baru dipilih. Belum ada pertemuan sampai Anda mengonfirmasi.' : '', hasSelection: !!f.v.selected,
      ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Mengonfirmasi sebagai' }),
      waitList: open ? open.slots.map(function (x) { return { day: TR.format.longDate(x.start, z), time: TR.format.slotTime(x.start, open.minutes, z), conflict: !!x.conflict }; }) : [], waitAgenda: open ? open.agenda : '', proposalAt: open ? 'Diusulkan ' + when(open.at) + ' · berakhir paling lambat 72 jam' : '', cancelProposal: function () { svc.cancelProposal(ctx(), { proposalId: open.id }); persist(); },
      replacementOpen: !!(m && open), replacementNote: 'Ada usulan jadwal pengganti. Pertemuan di bawah tetap berlaku sampai pengganti dikonfirmasi.',
      meeting: m ? { day: TR.format.longDate(m.start, z), time: TR.format.slotTime(m.start, m.minutes, z), other: otherAcc ? TR.format.slotTime(m.start, m.minutes, otherAcc.zone) : '', utc: TR.format.time(m.start, 'UTC') + '–' + TR.format.time(m.end, 'UTC') + ' UTC', agenda: m.agenda, link: m.link || '', hasLink: !!m.link } : {},
      meetingStatus: { tone: 'success', label: 'Pertemuan dikonfirmasi' }, ics: m ? svc.ics(m) : '', icsDownload: function () {
        try { var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([svc.ics(m)], { type: 'text/calendar' })); a.download = 'temuriset-demo.ics'; a.click(); notice('Berkas ICS disiapkan.'); } catch (e) { notice('Unduhan tidak tersedia di sini. Salin isi ICS di bawah.', 'warning'); }
        render();
      },
      reschedule: function () { f.v.rescheduling = true; f.v.slots = ['2026-11-05T09:00:00.000Z', '2026-11-05T11:00:00.000Z']; render(); }, cancelMeeting: function () { svc.cancelMeeting(ctx(), { id: m.id }); persist(); notice('Pertemuan dibatalkan. Pitching tetap disetujui untuk diskusi.'); render(); },
      canOutcome: !!(m && started && !m.outcomes[ui.partyId]), outcomeWait: !!(m && !started), outcomeRecorded: !!(m && m.outcomes[ui.partyId]), disputed: !!(m && m.disputed), recordedText: m && m.outcomes[ui.partyId] ? 'Anda sudah mencatat hasil. Menunggu catatan pihak lain.' : '',
      outcome: bind(f, 'outcome', { legend: 'Hasil pertemuan', options: [{ value: 'COMPLETED', label: 'Pertemuan selesai' }, { value: 'NO_SHOW', label: 'Pertemuan tidak terjadi' }] }), note: bind(f, 'note', { label: 'Langkah berikutnya', rows: 2 }),
      record: function () { var r = svc.recordOutcome(ctx(), { id: m.id, result: f.v.outcome, note: f.v.note }); if (!r.ok) fail(f, r); persist(); render(); }
    };
  };

  /* ---------- S15 relationship ---------- */
  var RELTYPE = { PROJECT: 'Proyek', LICENSE: 'Lisensi', EQUITY: 'Ekuitas' };
  vm.partnership = function () {
    var isNew = ui.route.params.id === undefined, pitchId = ui.route.query.pitch, title = 'Kerja Sama';
    if (isNew) {
      var p = svc.pitchFor(actor(), pitchId);
      if (!p) return Object.assign(base('Anda belum memiliki akses', '', nav(['pitching', 'diskusi'])), { allowed: false, denied: true, leave: function () { back('#/home'); } });
      var f = form('ks-new-' + pitchId, function () { var v = p.submissions[0]; return { type: p.purpose, name: v.sourceTitle + ' dan ' + party(p.recipient).name, scope: 'Validasi prototipe dua belas bulan', date: '1 Desember 2026', amount: 'USD 25.000', evidence: 'Catatan pertemuan 4 November 2026', percent: '', percentDate: '', ceiling: { name: true, type: true, scope: true, date: true, amount: true }, }; });
      function propose() {
        clearFail(f);
        var ceiling = Object.keys(f.v.ceiling).filter(function (k) { return f.v.ceiling[k]; }), name = 'ks-' + pitchId;
        run('ks', function () { return svc.proposePartnership(ctx(once(name)), { pitchId: pitchId, type: f.v.type, values: { name: f.v.name, type: RELTYPE[f.v.type], scope: f.v.scope, date: f.v.date, amount: f.v.amount, evidence: f.v.evidence, percent: f.v.percent, percentDate: f.v.percentDate }, ceiling: ceiling, subset: ceiling }); }, function (r) {
          spent(name);
          if (r.ok) { delete ui.forms[f.key]; notice('Ringkasan versi 1 dikirim. Menunggu konfirmasi pihak lain.'); go('#/partnerships/' + r.id, { keepNotice: true }); return; }
          fail(f, r);
        });
      }
      return Object.assign(base('Usulkan ringkasan Kerja Sama', subjectTitle(p), nav(['pitching', 'diskusi'])), {
        allowed: true, denied: false, composing: true, viewing: false, showSummary: summary(f).show, summaryProps: summary(f).props,
        type: bind(f, 'type', { legend: 'Jenis Kerja Sama', options: [{ value: 'PROJECT', label: 'Proyek', hint: 'Dukungan, validasi, atau pengembangan bersama.' }, { value: 'LICENSE', label: 'Lisensi', hint: 'Hak yang dinyatakan. Bukan pengalihan hak.' }, { value: 'EQUITY', label: 'Ekuitas', hint: 'Memerlukan badan usaha nyata.' }] }),
        name: bind(f, 'name', { label: 'Nama pihak yang ditampilkan' }), scope: bind(f, 'scope', { label: 'Cakupan', rows: 2, required: true }), date: bind(f, 'date', { label: 'Tanggal mulai', required: true }), amount: bind(f, 'amount', { label: 'Jumlah dana', hint: 'Jumlah proyek tidak menciptakan saham atau kepemilikan.' }), evidence: bind(f, 'evidence', { label: 'Rujukan bukti (privat)' }),
        isEquity: f.v.type === 'EQUITY', percent: bind(f, 'percent', { label: 'Persentase ekuitas (opsional)' }), percentDate: bind(f, 'percentDate', { label: 'Tanggal berlaku persentase' }),
        ceilingFields: Object.keys(f.v.ceiling).map(function (k) { return { label: CONSENT_LABELS[k], hint: 'Batas atas yang boleh dipilih kedua pihak.', checked: f.v.ceiling[k], onChange: function (v) { f.v.ceiling[k] = v; render(); } }; }),
        busy: !!ui.busy.ks, propose: propose, back: function () { back('#/pitches/' + pitchId); }, backLabel: 'Kembali ke ruang pitching', ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Mengusulkan sebagai' })
      });
    }
    var id = ui.route.params.id, r = svc.state.partnerships[id];
    if (!r || r.parties.indexOf(ui.partyId) < 0 || !svc.isMember(actor(), ui.partyId)) return Object.assign(base('Anda belum memiliki akses', '', nav(['pitching', 'diskusi'])), { allowed: false, denied: true, leave: function () { back('#/home'); } });
    var cur = svc.last(r.versions), otherId = r.parties[0] === ui.partyId ? r.parties[1] : r.parties[0], eff = svc.effectiveFields(r), g = form('ks-' + id + '-v' + cur.n + '-' + ui.partyId, function () { var sel = {}; (cur.confirmations[ui.partyId] ? cur.confirmations[ui.partyId].subset : cur.ceiling).forEach(function (k) { sel[k] = true; }); return { sel: sel, scope: cur.values.scope, note: '' }; });
    var mine = cur.confirmations[ui.partyId], theirs = cur.confirmations[otherId], dlg = ui.dialog && ui.dialog.ks === id;
    var consent = {
      version: cur.n, type: RELTYPE[r.type] + ' · ' + cur.values.name, fields: cur.ceiling.map(function (k) { return { id: k, label: CONSENT_LABELS[k], value: cur.values[k] }; }),
      mine: { name: party(ui.partyId).name, selected: Object.keys(g.v.sel).filter(function (k) { return g.v.sel[k]; }), confirmedVersion: mine ? cur.n : null },
      other: { name: party(otherId).name, selected: theirs ? theirs.subset : [], confirmedVersion: theirs ? cur.n : null },
      restricted: r.restrictions.map(function (x) { return x.field; }), busy: !!ui.busy.conf,
      onToggle: function (k, v) { g.v.sel[k] = v; render(); },
      onConfirm: function () { var name = 'conf-' + id + '-' + cur.n; run('conf', function () { return svc.confirmPartnership(ctx(once(name)), { id: id, version: cur.n, subset: Object.keys(g.v.sel).filter(function (k) { return g.v.sel[k]; }) }); }, function (res) { spent(name); if (res.ok) notice(res.status === 'CONFIRMED' ? 'Kedua pihak mengonfirmasi versi ' + cur.n + '.' : 'Konfirmasi Anda tercatat. Menunggu pihak lain.'); else fail(g, res); }); },
      onRequestChange: function () { ui.dialog = { ks: id }; render(); }, onRestrict: cur.status === 'CONFIRMED' ? function (k) { svc.restrictField(ctx(), { id: id, field: k }); persist(); notice(CONSENT_LABELS[k] + ' disembunyikan dari tampilan publik.'); render(); } : undefined,
      readOnly: cur.status === 'CONFIRMED' || cur.status === 'DECLINED'
    };
    var pub = eff.fields.map(function (k) { return { label: CONSENT_LABELS[k], value: r.versions[eff.version - 1].values[k] }; });
    var older = r.versions.slice(0, -1).map(function (v) { return { label: 'Versi ' + v.n + ' · ' + ({ CHANGES_REQUESTED: 'Perubahan diminta', CONFIRMED: 'Dikonfirmasi', DECLINED: 'Ditolak', PENDING_COUNTERPARTY: 'Menunggu' })[v.status], text: 'Cakupan: ' + v.values.scope + (v.note ? ' · Catatan: ' + v.note : '') }; });
    return Object.assign(base('Kerja Sama', cur.values.name, nav(['pitching', 'diskusi'])), {
      allowed: true, denied: false, composing: false, viewing: true, consent: consent, showSummary: summary(g).show, summaryProps: summary(g).props, scopeText: 'Cakupan: ' + cur.values.scope,
      next: cur.status === 'CONFIRMED' ? null : mine ? { who: 'other', title: 'Menunggu ' + party(otherId).name + ' mengonfirmasi versi ' + cur.n, body: 'Satu konfirmasi belum menjadi Kerja Sama bersama.' } : { who: 'you', title: 'Periksa dan konfirmasi versi ' + cur.n, body: 'Konfirmasi hanya berlaku untuk versi ini.' }, hasNext: cur.status !== 'CONFIRMED',
      confirmedNote: 'Dikonfirmasi kedua pihak pada versi ' + cur.n + '. Ini mencatat ringkasan, bukan pelaksanaan hukum atau pengalihan hak.', isConfirmed: cur.status === 'CONFIRMED', confirmedStatus: { tone: 'success', label: 'Dikonfirmasi kedua pihak' },
      pub: pub, hasPub: pub.length > 0, noPub: pub.length === 0, older: older, hasOlder: older.length > 0, ctxFinal: Object.assign(base('', '', '').ctxFinal, { actionLabel: 'Mengonfirmasi sebagai' }),
      changeDlg: { open: !!dlg, title: 'Minta perubahan ringkasan', onClose: function () { ui.dialog = null; render(); }, primary: { label: 'Buat versi ' + (cur.n + 1), busy: !!ui.busy.corr, onClick: function () { var name = 'corr-' + id + '-' + cur.n; run('corr', function () { return svc.requestCorrection(ctx(once(name)), { id: id, version: cur.n, note: g.v.note, values: { scope: g.v.scope } }); }, function (res) { spent(name); if (res.ok) { ui.dialog = null; notice('Versi ' + res.version + ' dibuat. Konfirmasi lama tidak berlaku lagi.'); } else fail(g, res); }); } } },
      changeNote: 'Versi baru tidak mewarisi konfirmasi apa pun. Kedua pihak perlu mengonfirmasi lagi.', correctScope: bind(g, 'scope', { label: 'Cakupan yang benar', rows: 2 }), correctNote: bind(g, 'note', { label: 'Catatan koreksi', rows: 2 }),
      back: function () { back('#/pitches/' + r.pitchId); }, backLabel: 'Kembali ke ruang pitching', viewProfile: function () { go('#/profiles/' + ui.partyId); },
      canDecline: cur.status !== 'CONFIRMED' && cur.status !== 'DECLINED' && !mine, decline: function () { svc.declinePartnership(ctx(), { id: id }); persist(); render(); },
      contest: function () { svc.requestRelationshipReview(ctx(), { id: id }); persist(); notice('Klaim publik disembunyikan selama ditinjau. Riwayat privat tetap ada.'); render(); }, canContest: cur.status === 'CONFIRMED' && !r.contested
    });
  };

  /* ---------- S16 public profile ---------- */
  vm.profile = function () {
    var id = ui.route.params.id, x = svc.state.parties[id];
    if (!x) return Object.assign(base('Profil tidak tersedia', '', 'profil'), { found: false, missing: true, leave: function () { back('#/home'); } });
    var inv = Object.keys(svc.state.inventions).map(function (k) { return svc.state.inventions[k]; }).filter(function (i) { return i.owner === id && i.published && !i.archived; });
    var rels = svc.publicRelationships(id);
    return Object.assign(base(x.name, x.kind === 'personal' ? 'Pribadi' : 'Organisasi', 'profil'), {
      found: true, missing: false, bio: x.bio || 'Belum menulis profil.', cards: inv.map(function (i) { return { card: cardProps(i), open: function () { go('#/inventions/' + i.id); } }; }), hasCards: inv.length > 0,
      rels: rels.map(function (r) { return { rows: Object.keys(r.fields).map(function (k) { return { id: k, label: CONSENT_LABELS[k], value: r.fields[k] }; }), note: 'Dikonfirmasi kedua pihak · versi ' + r.version + ' · ' + TR.format.date(svc.state.clock, zone()) }; }), hasRels: rels.length > 0, noRels: rels.length === 0,
      back: function () { back('#/home'); }, status: { tone: 'success', label: 'Dikonfirmasi kedua pihak' }
    });
  };

  /* ---------- S17 review ---------- */
  vm.review = function () {
    var on = svc.state.flags.orgReview, allowed = ui.accountId === 'bima' && ui.partyId === 'p-dcm';
    if (!on || !allowed) return Object.assign(base('Antrean tinjauan', '', 'profil'), { available: false, unavailable: true, leave: function () { back('#/home'); }, reasonText: on ? 'Antrean ini hanya terlihat oleh peninjau organisasi.' : 'Tinjauan organisasi tidak aktif pada komposisi ini.' });
    var f = form('rq', function () { return { reason: '' }; });
    var items = Object.keys(svc.state.reviews).map(function (k) { return svc.state.reviews[k]; }).map(function (r) {
      var isPub = r.kind === 'PUBLICATION', i = isPub ? svc.state.inventions[r.ref] : null, p = isPub ? null : svc.state.pitches[r.ref];
      return { title: isPub ? 'Penerbitan ' + i.versions[r.version - 1].title + ' versi ' + r.version : 'Pengiriman pitching ' + subjectTitle(p) + ' kepada ' + party(p.recipient).name, queued: r.state === 'QUEUED', state: { tone: r.state === 'APPROVED' ? 'success' : r.state === 'RETURNED' ? 'warning' : 'neutral', label: { QUEUED: 'Menunggu tinjauan', APPROVED: 'Disetujui', RETURNED: 'Dikembalikan' }[r.state] }, scope: 'Tinjauan terbatas pada versi ini dan daftar periksa organisasi. Bukan keputusan mitra.',
        approve: function () { var res = svc.decideReview(ctx(), { id: r.id, approve: true }); if (res.ok) { notice('Versi ini disetujui.'); } persist(); render(); }, ret: function () { if (!f.v.reason.trim()) { fail(f, { fields: { reason: 'Tuliskan alasan pengembalian.' } }); render(); return; } svc.decideReview(ctx(), { id: r.id, approve: false, reason: f.v.reason }); f.v.reason = ''; persist(); render(); } };
    });
    return Object.assign(base('Antrean tinjauan', 'Kemampuan tinjauan untuk ' + party(ui.partyId).name + '.', 'profil'), { available: true, unavailable: false, items: items, hasItems: items.length > 0, none: items.length === 0, reason: bind(f, 'reason', { label: 'Alasan jika dikembalikan', rows: 2 }), showSummary: summary(f).show, summaryProps: summary(f).props });
  };

  /* ---------- S18 settings ---------- */
  vm.settings = function () {
    var a = acc(), rpt = ui.route.query.report, f = form('set-' + ui.accountId, function () { return { zone: a.zone, notify: a.notify || 'in-app', reason: '', object: rpt ? 'Ruang pitching ' + rpt : 'Profil atau konten publik' }; });
    var reports = svc.state.reports.filter(function (r) { return r.by === ui.partyId; }), privacy = svc.state.privacy.filter(function (r) { return r.by === ui.partyId; });
    return Object.assign(base('Profil dan privasi', a.name + ' · ' + party(ui.partyId).name, 'profil'), {
      zone: bind(f, 'zone', { label: 'Zona waktu', emptyLabel: null, options: ZONES }), locale: { label: 'Bahasa', emptyLabel: null, value: 'id', options: [{ value: 'id', label: 'Bahasa Indonesia' }] },
      notify: bind(f, 'notify', { legend: 'Pemberitahuan', options: [{ value: 'in-app', label: 'Di dalam aplikasi', hint: 'Email belum terhubung pada demo ini.' }] }),
      savePrefs: function () { svc.setPrefs(ctx(), { zone: f.v.zone, notify: f.v.notify }); persist(); notice('Preferensi tersimpan di demo ini.'); render(); },
      openProfile: function () { go('#/profiles/' + ui.partyId); },
      object: bind(f, 'object', { label: 'Yang dilaporkan' }), reason: bind(f, 'reason', { label: 'Alasan laporan', hint: 'Laporan bersifat privat.', rows: 3, required: true }), showSummary: summary(f).show, summaryProps: summary(f).props,
      sendReport: function () { clearFail(f); var r = svc.report(ctx(), { object: f.v.object, reason: f.v.reason }); if (r.ok) { f.v.reason = ''; notice('Laporan diterima. Nomor kasus ' + r.id + '.'); } else fail(f, r); persist(); render(); },
      reports: reports.map(function (r) { return { text: r.object + ' · ' + r.id, status: { tone: 'neutral', label: 'Diterima, menunggu penanganan' } }; }), hasReports: reports.length > 0,
      requestExport: function () { svc.privacyRequest(ctx(), { kind: 'Ekspor data' }); persist(); notice('Permintaan ekspor diterima.'); render(); }, requestDelete: function () { svc.privacyRequest(ctx(), { kind: 'Penghapusan data' }); persist(); notice('Permintaan penghapusan diterima.'); render(); },
      privacy: privacy.map(function (r) { return { text: r.kind + ' · ' + r.id, status: { tone: 'neutral', label: 'Diterima' } }; }), hasPrivacy: privacy.length > 0,
      canReview: svc.state.flags.orgReview && ui.accountId === 'bima' && ui.partyId === 'p-dcm', openReview: function () { go('#/workspace/review-queue'); }
    });
  };

  /* ---------- shell ---------- */
  vm.router = function () {
    var r = {}; ROUTES.forEach(function (x) { r[x[1]] = false; });
    r[ui.route.name] = true;
    return { r: r };
  };

  /* Adapter: TR components take node props, and x-dc markup only supplies children.
     Direct children marked data-slot="prop" become that prop; data-slot="tab:id" fills a TR.Tabs panel. It draws nothing itself. */
  function collect(children, slots, rest) {
    React.Children.forEach(children, function (c) {
      if (c == null || c === false) return;
      if (typeof c === 'string' && !c.trim()) return;
      if (c.type === React.Fragment) { collect(c.props.children, slots, rest); return; }
      var name = c.props && c.props['data-slot'];
      if (name) { var inner = []; collect(c.props.children, {}, inner); if (inner.length) slots[name] = inner; } else rest.push(c);
    });
  }
  function Slotted(p) {
    var C = p.of.split('.').reduce(function (o, k) { return o[k]; }, window), props = {}, slots = {}, rest = [];
    Object.keys(p).forEach(function (k) { if (k !== 'of' && k !== 'children' && k !== 'body') props[k] = p[k]; });
    collect(p.children, slots, rest);
    if (p.body) rest.unshift(p.body);
    Object.keys(slots).forEach(function (k) { if (k.indexOf('tab:') !== 0) props[k] = slots[k]; });
    if (props.tabs) props.tabs = props.tabs.map(function (t) { return Object.assign({}, t, { content: slots['tab:' + t.id] }); });
    return rest.length ? React.createElement(C, props, rest) : React.createElement(C, props);
  }

  var PREVIEW = {
    Start: {}, Home: { seed: 'revision' }, Discover: { account: 'mitraA' }, Inventions: {}, Invention: { hash: '#/inventions/inv-f01' }, Editor: { hash: '#/inventions/inv-f01/edit?step=2' },
    Support: { hash: '#/support-requests/sr-f01' }, Funding: { account: 'bima', party: 'p-dcm', hash: '#/funding-requests/FRaise01' }, Partner: { hash: '#/partners/p-a' }, Opportunity: { account: 'mitraA', hash: '#/opportunities/A1/edit' },
    Matches: { hash: '#/matches?source=sr-f01' }, Preflight: { hash: '#/pitches/new?source=sr-f01&target=A1' }, Pitches: { seed: 'revision' }, Workspace: { seed: 'submitted', account: 'mitraA', pitch: true }, Revisions: { seed: 'revision', pitch: true }, Schedule: { seed: 'proposal', pitch: true },
    Partnership: { seed: 'partnership', partnership: true }, Profile: { hash: '#/profiles/p-rani' }, ReviewQueue: { account: 'bima', party: 'p-dcm', review: true }, Settings: {}, DemoControls: {}
  };
  function preview(name) {
    var p = PREVIEW[name] || {}, id = p.seed ? D.seeds[p.seed](svc) : null;
    if (p.account) setAccount(p.account, p.party);
    if (p.review) svc.setFlag('orgReview', true);
    if (p.hash) ui.route = parse(p.hash);
    if (p.pitch) ui.route = parse('#/pitches/' + id);
    if (p.partnership) ui.route = parse('#/partnerships/' + id);
    if (!p.hash && !p.pitch && !p.partnership) ui.route = Object.assign(parse('#/home'), { name: name });
    enter(ui.route);
  }

  ui = freshUi();
  svc.subscribe(render);
  window.TemuRisetApp = {
    Slotted: Slotted, vm: vm, svc: svc, get ui() { return ui; },
    // Main owns the shared case. An artboard opened alone builds its own preview state.
    boot: function () {
      if (shellActive) return;
      shellActive = true;
      restore();
      var h = ''; try { h = location.hash; } catch (e) { /* no location */ }
      if (h && h.length > 2) { ui.route = parse(h); ui.started = true; }
      else if (ui.started) ui.route = parse(persona() === 'mitra' ? '#/discover' : '#/home');
      enter(ui.route);
      try { window.addEventListener('hashchange', function () { if (location.hash !== ui.route.hash) { ui.route = parse(location.hash); enter(ui.route); render(); } }); } catch (e) { /* hash routing unavailable */ }
    },
    attach: function (component, name) {
      if (!shellActive && !window.__trPreviewed) { window.__trPreviewed = true; preview(name); }
      var fn = function () { component.forceUpdate(); };
      listeners.push(fn);
      return function () { listeners = listeners.filter(function (l) { return l !== fn; }); };
    }
  };
})();
