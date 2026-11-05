/* TemuRiset prototype domain: the one local service and state authority.
   Every value is a fictional DEMO fixture. This simulates intended behavior and proves no server guarantee. */
(function (root) {
  'use strict';
  var T0 = '2026-11-02T08:00:00.000Z';
  var HOUR = 3600000;
  var WEIGHTS = {
    A: { problem: 0.45, stage: 0.15, sector: 0.15, financial: 0.15, timing: 0.10 },
    B: { support: 0.40, form: 0.30, geo: 0.15, availability: 0.15 }
  };

  function clone(x) { return JSON.parse(JSON.stringify(x)); }
  function ms(i) { return new Date(i).getTime(); }
  function iso(t) { return new Date(t).toISOString(); }
  function ok(extra) { return Object.assign({ ok: true }, extra); }
  function err(code, message, extra) { return Object.assign({ ok: false, code: code, message: message }, extra); }
  function last(a) { return a[a.length - 1]; }

  /* ---------- decimals: strings, never floats ---------- */
  function cmpDec(a, b) {
    var pa = String(a).split('.'), pb = String(b).split('.');
    var ia = BigInt(pa[0]), ib = BigInt(pb[0]);
    if (ia !== ib) return ia < ib ? -1 : 1;
    var fa = (pa[1] || '').padEnd(8, '0'), fb = (pb[1] || '').padEnd(8, '0');
    return fa < fb ? -1 : fa > fb ? 1 : 0;
  }
  // Accepts 20000, 20.000 (Indonesian grouping) and 20000,50. Returns null when it is not a nonnegative decimal.
  function parseAmount(text) {
    var t = String(text == null ? '' : text).trim();
    if (!t) return '';
    if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(t)) t = t.replace(/\./g, '');
    t = t.replace(',', '.');
    return /^\d+(\.\d+)?$/.test(t) ? t : null;
  }

  /* ---------- half-open intervals ---------- */
  function overlaps(aStart, aEnd, bStart, bEnd) { return ms(aStart) < ms(bEnd) && ms(bStart) < ms(aEnd); }
  function addMin(i, m) { return iso(ms(i) + m * 60000); }

  /* ---------- conservative fit bounds (PRD section 10) ---------- */
  function harmonic(a, b) { return a + b === 0 ? 0 : 2 * a * b / (a + b); }
  function side(features, weights) {
    var low = 0, unknown = 0;
    Object.keys(weights).forEach(function (k) {
      if (features[k] == null) unknown += weights[k]; else low += weights[k] * features[k];
    });
    return { low: low, high: low + unknown, known: 1 - unknown };
  }
  function fitBounds(a, b) {
    return {
      lower: Math.round(10000 * harmonic(a.low, b.low)) / 100,
      upper: Math.round(10000 * harmonic(a.high, b.high)) / 100,
      coverage: Math.round(((a.known + b.known) / 2) * 100) / 100
    };
  }

  /* ---------- fixtures ---------- */
  function accounts() {
    return {
      rani: { id: 'rani', name: 'Rani', persona: 'inovator', fixture: 'F01', zone: 'Asia/Jakarta', contexts: ['p-rani'] },
      bima: { id: 'bima', name: 'Bima', persona: 'inovator', fixture: 'F04/F05', zone: 'Asia/Jakarta', contexts: ['p-bima', 'p-dcm'] },
      dewi: { id: 'dewi', name: 'Dewi', persona: 'inovator', fixture: 'F02', zone: 'Asia/Jakarta', contexts: ['p-field'] },
      galih: { id: 'galih', name: 'Galih', persona: 'inovator', fixture: 'F03', zone: 'Asia/Jakarta', contexts: ['p-queue'] },
      sinta: { id: 'sinta', name: 'Sinta', persona: 'inovator', fixture: 'F06', zone: 'Asia/Makassar', contexts: ['p-grid'] },
      mitraA: { id: 'mitraA', name: 'Peserta P', persona: 'mitra', fixture: 'Recipient A', zone: 'Asia/Makassar', contexts: ['p-a'] },
      stafA: { id: 'stafA', name: 'Staf Mitra A', persona: 'mitra', fixture: 'Recipient A, tanpa wewenang memutuskan', zone: 'Asia/Jakarta', contexts: ['p-a'] },
      investorB: { id: 'investorB', name: 'Investor B', persona: 'mitra', fixture: 'Recipient B', zone: 'Asia/Jakarta', contexts: ['p-b'] },
      mitraC: { id: 'mitraC', name: 'Perwakilan Distributor C', persona: 'mitra', fixture: 'Recipient C', zone: 'Asia/Jakarta', contexts: ['p-c'] },
      mitraD: { id: 'mitraD', name: 'Perwakilan Mitra Lisensi D', persona: 'mitra', fixture: 'Recipient D', zone: 'Asia/Jakarta', contexts: ['p-d'] },
      lain: { id: 'lain', name: 'Pengguna Lain', persona: 'inovator', fixture: 'F01-DENIED', zone: 'Asia/Jakarta', contexts: ['p-x'] },
      baru: { id: 'baru', name: 'Pengguna Baru', persona: 'inovator', fixture: 'Akun kosong', zone: 'Asia/Jakarta', contexts: ['p-new'] }
    };
  }
  function parties() {
    function p(id, kind, name, extra) { return Object.assign({ id: id, kind: kind, name: name }, extra); }
    return {
      'p-rani': p('p-rani', 'personal', 'Rani', { bio: 'Inovator independen di bidang air bersih.', published: true }),
      'p-bima': p('p-bima', 'personal', 'Bima'),
      'p-dcm': p('p-dcm', 'organization', 'Demo Circular Materials Ltd', { bio: 'Perusahaan fiktif untuk demo material sirkular.', entity: 'IDENTIFIED', published: true }),
      'p-field': p('p-field', 'organization', 'Komunitas FieldDry Demo'),
      'p-queue': p('p-queue', 'organization', 'Tim QueueNest Demo'),
      'p-grid': p('p-grid', 'organization', 'Tim GridShare Demo', { entity: 'UNCONFIRMED' }),
      'p-a': p('p-a', 'organization', 'Mitra A', { bio: 'Mitra validasi prototipe (fiktif).', published: true }),
      'p-b': p('p-b', 'personal', 'Investor B', { bio: 'Investor individu (fiktif).', published: true }),
      'p-c': p('p-c', 'organization', 'Distributor C'),
      'p-d': p('p-d', 'organization', 'Mitra Lisensi D'),
      'p-e': p('p-e', 'organization', 'Dana Riset E'),
      'p-x': p('p-x', 'personal', 'Pengguna Lain'),
      'p-new': p('p-new', 'personal', 'Pengguna Baru')
    };
  }
  function capsFor(account) {
    if (account === 'stafA') return ['view'];
    return ['view', 'edit', 'submit', 'decide', 'confirm', 'schedule'];
  }
  function invention(id, owner, v) {
    return { id: id, owner: owner, status: 'PUBLISHED', archived: false, published: 1, versions: [Object.assign({ n: 1, at: T0 }, v)], draft: null, draftRev: 0, savedAt: null, reviewPending: false };
  }
  function inventions() {
    return {
      'inv-f01': invention('inv-f01', 'p-rani', {
        fixture: 'F01', title: 'ClearSpring', category: 'Air bersih', sector: 'Air dan sanitasi',
        summary: 'Filter air sederhana yang mudah dirawat untuk keluarga tanpa akses air bersih.',
        problem: 'Keluarga tanpa akses air bersih perlu cara menyaring air yang mudah dirawat.',
        solution: 'Prototipe filter air yang sudah berfungsi.', users: 'Keluarga dan komunitas kecil tanpa jaringan air bersih',
        stage: 'PROTOTYPE', keywords: ['air', 'filter', 'prototipe', 'validasi'],
        facts: [
          { id: 'fct-cap', label: 'Kapasitas saring', value: '10 L/jam', timing: 'CURRENT', provenance: 'PROVIDED', key: 'capacity' },
          { id: 'fct-plan', label: 'Kapasitas saring', value: '20 L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED', key: 'capacity' }
        ],
        people: [{ role: 'Pembuat', name: 'Rani' }, { role: 'Pengelola', name: 'Rani' }, { role: 'Pemegang hak yang dinyatakan', name: 'Rani · belum didaftarkan' }],
        authority: 'SELF_DECLARED', entity: 'NONE_NEEDED', docs: ['doc-f01']
      }),
      'inv-f02': invention('inv-f02', 'p-field', {
        fixture: 'F02', title: 'FieldDry', category: 'Pertanian', sector: 'Pertanian',
        summary: 'Proses pengeringan hasil panen yang tidak bergantung pada cuaca.',
        problem: 'Hasil panen perlu dikeringkan tanpa bergantung pada cuaca.', solution: 'Proses pengeringan pada tahap pilot.', users: 'Kelompok tani',
        stage: 'PILOT', keywords: ['pertanian', 'pengeringan', 'uji', 'fasilitas'], facts: [],
        people: [{ role: 'Pengelola', name: 'Komunitas FieldDry Demo' }, { role: 'Wewenang', name: 'Belum dikonfirmasi' }],
        authority: 'UNCONFIRMED', entity: 'UNCONFIRMED', docs: []
      }),
      'inv-f03': invention('inv-f03', 'p-queue', {
        fixture: 'F03', title: 'QueueNest', category: 'Perangkat lunak', sector: 'Perangkat lunak',
        summary: 'Aplikasi penjadwalan untuk tim layanan dengan koneksi tidak stabil.',
        problem: 'Tim layanan perlu mengatur antrean walau koneksi tidak stabil.', solution: 'Aplikasi penjadwalan dengan ekspor luring.', users: 'Tim layanan',
        stage: 'WORKING', keywords: ['perangkat', 'lunak', 'lisensi', 'penjadwalan', 'aplikasi'],
        facts: [
          { id: 'fct-exp', label: 'Ekspor luring', value: 'Ekspor luring', timing: 'CURRENT', provenance: 'SELF_DECLARED', key: 'offline_export' },
          { id: 'fct-sso', label: 'SSO', value: 'SSO', timing: 'PLANNED', provenance: 'SELF_DECLARED', key: 'sso' }
        ],
        people: [{ role: 'Pengelola', name: 'Tim QueueNest Demo' }], authority: 'SELF_DECLARED', entity: 'UNCONFIRMED', docs: []
      }),
      'inv-f04': invention('inv-f04', 'p-dcm', {
        fixture: 'F04', title: 'LoopMaterial', category: 'Material', sector: 'Material',
        summary: 'Material kemasan sirkular pada tahap prototipe.',
        problem: 'Kemasan sekali pakai sulit didaur ulang.', solution: 'Prototipe material kemasan.', users: 'Produsen kemasan',
        stage: 'PROTOTYPE', keywords: ['material', 'kemasan', 'sirkular'], facts: [],
        people: [{ role: 'Pengelola', name: 'Demo Circular Materials Ltd' }], authority: 'SELF_DECLARED', entity: 'IDENTIFIED', docs: ['doc-f04']
      }),
      'inv-f05': invention('inv-f05', 'p-dcm', {
        fixture: 'F05', title: 'ReFormPress', category: 'Manufaktur', sector: 'Manufaktur',
        summary: 'Proses manufaktur untuk membentuk ulang material daur ulang.',
        problem: 'Material daur ulang sulit dibentuk ulang secara konsisten.', solution: 'Prototipe mesin pembentuk.', users: 'Produsen kemasan',
        stage: 'PROTOTYPE', keywords: ['manufaktur', 'material', 'sirkular'], facts: [],
        people: [{ role: 'Pengelola', name: 'Demo Circular Materials Ltd' }], authority: 'SELF_DECLARED', entity: 'IDENTIFIED', docs: []
      }),
      'inv-f06': invention('inv-f06', 'p-grid', {
        fixture: 'F06', curated: true, title: 'GridShare', category: 'Energi', sector: 'Energi',
        summary: 'Konsep pemantauan energi bersama untuk komunitas.',
        problem: 'Komunitas perlu memantau pemakaian energi bersama.', solution: 'Konsep pemantauan energi komunitas.', users: 'Komunitas energi',
        stage: 'IDEA', keywords: ['energi', 'komunitas', 'pendampingan'], facts: [],
        people: [{ role: 'Pengelola', name: 'Tim GridShare Demo' }, { role: 'Status badan hukum', name: 'Belum dikonfirmasi' }],
        authority: 'SELF_DECLARED', entity: 'UNCONFIRMED', docs: []
      })
    };
  }
  function supportRequests() {
    function sr(id, inv, owner, r) { return Object.assign({ id: id, inventionId: inv, owner: owner, status: 'ACTIVE', version: 1, region: 'Indonesia', months: 6, partial: true }, r); }
    return {
      'sr-f01': sr('sr-f01', 'inv-f01', 'p-rani', { outcome: 'Validasi prototipe enam bulan', form: 'Pendanaan proyek', relationship: 'PROJECT',
        budget: { min: '20000', max: '30000', currency: 'USD', period: '6 bulan', scope: 'biaya pilot enam bulan', estimateDate: '2026-10-30', assumptions: 'Uji lapangan di dua lokasi' } }),
      'sr-f02': sr('sr-f02', 'inv-f02', 'p-field', { outcome: 'Uji proses pengeringan', form: 'Fasilitas uji', relationship: 'PROJECT', noncash: 'Tanpa dana tunai: fasilitas uji', budget: { min: null, max: null, currency: 'USD', period: null, scope: 'fasilitas uji' } }),
      'sr-f03': sr('sr-f03', 'inv-f03', 'p-queue', { outcome: 'Diskusi lisensi', form: 'Lisensi', relationship: 'LICENSE', terms: 'Belum ditentukan', budget: { min: null, max: null, currency: 'USD', period: null, scope: 'lisensi' } }),
      'sr-f06': sr('sr-f06', 'inv-f06', 'p-grid', { outcome: 'Pendampingan ide tahap awal', form: 'Pendampingan', relationship: 'PROJECT', noncash: 'Pendampingan, kebutuhan dana belum diketahui', budget: { min: null, max: null, currency: 'USD', period: null, scope: 'pendampingan' } })
    };
  }
  function fundingRequests() {
    return {
      FRaise01: { id: 'FRaise01', fixture: 'F04/F05', owner: 'p-dcm', subject: 'EXISTING_ENTITY', company: 'Demo Circular Materials Ltd', stage: 'Pre-seed', form: 'Ekuitas', purpose: 'Mengembangkan dua inovasi perusahaan', relationship: 'EQUITY',
        currency: 'USD', target: '500000', desiredMin: '50000', desiredMax: '100000', partial: true, status: 'ACTIVE', version: 1, timing: null,
        links: [{ inventionId: 'inv-f04', version: 1 }, { inventionId: 'inv-f05', version: 1 }], history: [] }
    };
  }
  function partners() {
    function pr(id, x) { return Object.assign({ id: id, source: 'OWNER_CONFIRMED', route: 'IN_APP', intake: 'OPEN', general: false }, x); }
    return {
      'p-a': pr('p-a', { fixture: 'Recipient A', subtype: 'Mitra validasi prototipe', thesis: 'Membantu prototipe menjadi siap uji lapangan.', sectors: ['Air dan sanitasi', 'Pertanian', 'Energi'], stages: 'Ide, prototipe, pilot', regions: 'Indonesia', forms: 'Pendanaan proyek, fasilitas uji, pendampingan' }),
      'p-b': pr('p-b', { fixture: 'Recipient B', subtype: 'Investor individu', thesis: 'Investasi ekuitas pada perusahaan tahap awal.', sectors: ['Material', 'Manufaktur'], stages: 'Pre-seed dengan prototipe', regions: 'Indonesia', forms: 'Ekuitas', check: { min: '50000', max: '150000', currency: 'USD' } }),
      'p-c': pr('p-c', { fixture: 'Recipient C', subtype: 'Distributor', thesis: 'Mendistribusikan produk yang sudah siap pasar.', sectors: ['Air dan sanitasi', 'Material'], stages: 'Siap pasar', regions: 'Indonesia', forms: 'Distribusi' }),
      'p-d': pr('p-d', { fixture: 'Recipient D', subtype: 'Mitra lisensi perangkat lunak', thesis: 'Melisensikan perangkat lunak untuk pelanggan korporasi.', sectors: ['Perangkat lunak'], stages: 'Sudah berfungsi', regions: 'Indonesia', forms: 'Lisensi' }),
      'p-e': pr('p-e', { fixture: 'Tambahan demo (AC22, AC24)', subtype: 'Direktori pendanaan', thesis: 'Pendanaan riset terapan.', sectors: ['Air dan sanitasi'], stages: 'Belum diketahui', regions: 'Belum diketahui', forms: 'Hibah', source: 'SOURCE_REPORTED', route: 'EXTERNAL', intake: 'UNCONFIRMED', externalUrl: 'https://example.org/formulir-demo' })
    };
  }
  function req(id, label, field, op, value, appliesAt, mode, extra) {
    return Object.assign({ id: id, label: label, field: field, op: op, value: value, mandatory: true, appliesAt: appliesAt, mode: mode }, extra);
  }
  function opportunities() {
    function opp(id, partner, x) { return Object.assign({ id: id, partner: partner, version: 1, status: 'ACTIVE', history: [] }, x); }
    return {
      A1: opp('A1', 'p-a', { title: 'Validasi prototipe enam bulan', outcome: 'Prototipe teruji di lapangan dalam enam bulan.', included: 'Uji fungsi dan uji lapangan terbatas', excluded: 'Sertifikasi dan produksi massal', support: 'Pendanaan proyek dan pendampingan uji', stages: ['PROTOTYPE', 'PILOT'], relationship: 'PROJECT', sectors: ['Air dan sanitasi', 'Pertanian', 'Energi'], keywords: ['prototipe', 'validasi', 'uji', 'air'], timing: 'Dibuka sampai 31 Desember 2026',
        financial: { subject: 'partner', min: '15000', max: '40000', currency: 'USD', period: '6 bulan', scope: 'biaya pilot enam bulan' },
        requirements: [
          req('A1-stage', 'Tahap inovasi', 'stage', 'in_set', ['PROTOTYPE', 'PILOT'], 'SUBMISSION', 'DECLARATION', { why: 'Mitra ini hanya menguji inovasi yang sudah memiliki prototipe.' }),
          req('A1-file', 'Berkas uji fungsi', 'doc:function', 'exists', true, 'SUBMISSION', 'DOCUMENT_PRESENT', { why: 'Mitra perlu melihat bukti fungsi sebelum menyiapkan uji.' }),
          req('A1-budget', 'Kisaran biaya pilot', 'budget', 'range_overlap', null, 'SUBMISSION', 'DECLARATION', { why: 'Biaya dibandingkan dengan dukungan mitra pada cakupan dan periode yang sama.' }),
          req('A1-cert', 'Sertifikat komersialisasi', 'doc:certificate', 'exists', true, 'COMMERCIALIZATION', 'REVIEWER_CONFIRMED', { why: 'Diperlukan nanti sebelum dijual, bukan untuk uji prototipe.' })
        ] }),
      A2: opp('A2', 'p-a', { title: 'Fasilitas uji pascapanen', outcome: 'Akses fasilitas uji untuk proses pascapanen.', included: 'Pemakaian fasilitas uji', excluded: 'Dana tunai', support: 'Fasilitas uji', stages: ['PILOT'], relationship: 'PROJECT', sectors: ['Pertanian'], keywords: ['pertanian', 'pengeringan', 'fasilitas', 'uji'], timing: 'Dibuka sampai 31 Desember 2026',
        financial: { subject: 'partner', noncash: 'Tanpa dana tunai: fasilitas uji' },
        requirements: [
          req('A2-stage', 'Tahap inovasi', 'stage', 'in_set', ['PILOT'], 'SUBMISSION', 'DECLARATION'),
          req('A2-auth', 'Wewenang atas inovasi', 'authority', 'equals', 'REVIEWED', 'SUBMISSION', 'REVIEWER_CONFIRMED', { why: 'Fasilitas hanya dibuka bagi pihak yang wewenangnya sudah diperiksa.' })
        ] }),
      A3: opp('A3', 'p-a', { title: 'Pendampingan ide tahap awal', outcome: 'Ide tahap awal mendapat pendampingan.', included: 'Sesi pendampingan', excluded: 'Dana tunai', support: 'Pendampingan', stages: ['IDEA', 'PROTOTYPE'], relationship: 'PROJECT', sectors: ['Energi', 'Air dan sanitasi'], keywords: ['pendampingan', 'komunitas', 'energi'], timing: 'Dibuka sampai 31 Desember 2026',
        financial: { subject: 'partner', noncash: 'Pendampingan tanpa dana tunai' },
        requirements: [req('A3-stage', 'Tahap inovasi', 'stage', 'in_set', ['IDEA', 'PROTOTYPE'], 'SUBMISSION', 'DECLARATION')] }),
      B1: opp('B1', 'p-b', { title: 'Investasi ekuitas pre-seed', outcome: 'Investasi pada perusahaan pre-seed dengan prototipe.', included: 'Ekuitas pada badan usaha yang sudah ada', excluded: 'Pendanaan proyek', support: 'Investasi ekuitas', stages: ['PROTOTYPE'], relationship: 'EQUITY', sectors: ['Material', 'Manufaktur'], keywords: ['material', 'sirkular', 'manufaktur'], timing: 'Dibuka sampai 31 Maret 2027',
        financial: { subject: 'investorCheck', min: '50000', max: '150000', currency: 'USD' },
        requirements: [
          req('B1-form', 'Bentuk pendanaan', 'relationship', 'equals', 'EQUITY', 'SUBMISSION', 'DECLARATION', { why: 'Mandat ini hanya untuk ekuitas.' }),
          req('B1-entity', 'Badan usaha yang sudah berdiri', 'entity', 'equals', 'IDENTIFIED', 'SUBMISSION', 'DECLARATION', { why: 'Ekuitas memerlukan subjek hukum yang nyata.' }),
          req('B1-check', 'Kisaran kontribusi', 'contribution', 'range_overlap', null, 'SUBMISSION', 'DECLARATION', { why: 'Dibandingkan dengan kontribusi yang diinginkan, bukan seluruh target.' })
        ] }),
      B2: opp('B2', 'p-b', { title: 'Diskusi tim pra-pendirian', outcome: 'Diskusi awal dengan tim yang belum mendirikan perusahaan.', included: 'Diskusi', excluded: 'Konfirmasi ekuitas sebelum badan usaha ada', support: 'Diskusi investasi', stages: ['PROTOTYPE'], relationship: 'EQUITY', sectors: ['Material', 'Manufaktur'], keywords: ['material', 'sirkular'], timing: 'Dibuka sampai 31 Maret 2027',
        financial: { subject: 'investorCheck', min: '50000', max: '150000', currency: 'USD' },
        requirements: [
          req('B2-form', 'Bentuk pendanaan', 'relationship', 'equals', 'EQUITY', 'SUBMISSION', 'DECLARATION'),
          req('B2-check', 'Kisaran kontribusi', 'contribution', 'range_overlap', null, 'SUBMISSION', 'DECLARATION')
        ] }),
      C1: opp('C1', 'p-c', { title: 'Distribusi produk siap pasar', outcome: 'Produk bersertifikat masuk jaringan distribusi.', included: 'Distribusi', excluded: 'Pengembangan prototipe', support: 'Distribusi', stages: ['MARKET'], relationship: 'PROJECT', sectors: ['Air dan sanitasi', 'Material'], keywords: ['distribusi', 'pasar', 'sertifikat', 'air'], timing: 'Dibuka sampai 31 Desember 2026',
        financial: { subject: 'partner', noncash: 'Jaringan distribusi' },
        requirements: [
          req('C1-stage', 'Tahap inovasi', 'stage', 'in_set', ['MARKET'], 'SUBMISSION', 'DECLARATION', { why: 'Mitra ini hanya menerima produk siap pasar.' }),
          req('C1-cert', 'Sertifikat yang berlaku', 'doc:certificate', 'exists', true, 'SUBMISSION', 'REVIEWER_CONFIRMED', { why: 'Distribusi memerlukan sertifikat saat pengajuan.' })
        ] }),
      D1: opp('D1', 'p-d', { title: 'Lisensi perangkat lunak korporasi', outcome: 'Lisensi perangkat lunak untuk pelanggan korporasi.', included: 'Diskusi lisensi', excluded: 'Pendanaan', support: 'Lisensi', stages: ['WORKING'], relationship: 'LICENSE', sectors: ['Perangkat lunak'], keywords: ['perangkat', 'lunak', 'lisensi', 'penjadwalan'], timing: 'Dibuka sampai 31 Desember 2026',
        financial: { subject: 'license', terms: 'Belum ditentukan' },
        requirements: [
          req('D1-sso', 'SSO yang sudah berjalan', 'feature:sso', 'current', true, 'SUBMISSION', 'DECLARATION', { why: 'Pelanggan korporasi memerlukan SSO saat ini, bukan rencana.' }),
          req('D1-form', 'Bentuk kerja sama', 'relationship', 'equals', 'LICENSE', 'SUBMISSION', 'DECLARATION')
        ] })
    };
  }
  function documents() {
    return {
      'doc-f01': { id: 'doc-f01', owner: 'p-rani', kind: 'function', title: 'Laporan uji fungsi ClearSpring', versions: [{ n: 1, file: 'AVAILABLE', extraction: 'SUCCEEDED', review: 'PROVIDED_UNREVIEWED', at: T0 }] },
      'doc-f04': { id: 'doc-f04', owner: 'p-dcm', kind: 'deck', title: 'Ringkasan perusahaan Demo Circular Materials', versions: [{ n: 1, file: 'AVAILABLE', extraction: 'NOT_REQUESTED', review: 'PROVIDED_UNREVIEWED', at: T0 }] }
    };
  }
  function baseline() {
    var accs = accounts();
    return {
      schema: 1, clock: T0, seq: 1,
      flags: { ai: 'off', calendar: false, companyFunding: true, orgReview: false },
      variants: {}, faults: {},
      accounts: accs, parties: parties(), inventions: inventions(), requests: supportRequests(), fundings: fundingRequests(),
      partners: partners(), opportunities: opportunities(), documents: documents(), grants: {},
      saved: {}, hidden: {}, pitches: {}, proposals: {}, meetings: {},
      bookings: [{ id: 'bk-p', party: 'p-a', start: '2026-11-04T09:00:00.000Z', end: '2026-11-04T10:00:00.000Z', title: 'Agenda lain Peserta P' }],
      partnerships: {}, reviews: {}, reports: [], privacy: [], notifications: [], audit: [], idem: {}
    };
  }

  /* ---------- service ---------- */
  function create(initial) {
    var s = initial || baseline();
    var listeners = [];

    function emit() { listeners.forEach(function (l) { l(); }); }
    function nextId(prefix) { s.seq += 1; return prefix + '-' + s.seq; }
    function now() { return s.clock; }
    function audit(actor, what, ref) { s.audit.push({ at: now(), actor: actor.party, what: what, ref: ref }); }
    function notify(party, text, ref) { s.notifications.push({ id: nextId('n'), party: party, text: text, ref: ref, at: now() }); }
    function isMember(actor, party) { var a = s.accounts[actor.account]; return !!a && a.contexts.indexOf(party) >= 0 && actor.party === party; }
    function can(actor, party, cap) { return isMember(actor, party) && capsFor(actor.account).indexOf(cap) >= 0; }
    function denied() { return err('NOT_FOUND', 'Halaman ini hanya dapat dibuka oleh pihak yang diberi izin.'); }

    // Every consequential mutation: acting party, expected version, idempotency key, injected faults.
    function mutate(name, ctx, args, body) {
      var key = ctx.key, digest = JSON.stringify([name, ctx.actor.party, args]);
      if (key && s.idem[key]) {
        if (s.idem[key].digest !== digest) return err('IDEMPOTENCY_CONFLICT', 'Permintaan ini sudah dipakai untuk isi yang berbeda. Muat ulang lalu kirim sebagai permintaan baru.');
        return Object.assign({}, clone(s.idem[key].result), { replayed: true });
      }
      if (s.faults.preCommit === name) { delete s.faults.preCommit; emit(); return err('NETWORK', 'Tidak dapat menghubungi layanan. Belum ada perubahan yang disimpan.', { retryable: true }); }
      var res = body();
      if (res.ok && key) s.idem[key] = { digest: digest, result: clone(res) };
      if (res.ok && s.faults.lostAfterCommit === name) { delete s.faults.lostAfterCommit; emit(); return err('LOST_RESPONSE', 'Jawaban layanan tidak diterima, jadi hasilnya belum diketahui.', { retryable: true, unknown: true }); }
      emit();
      return res;
    }

    /* ----- projections ----- */
    function inv(id) { return s.inventions[id]; }
    function pubV(i) { return i && i.published ? i.versions[i.published - 1] : null; }
    function sourceOf(ref) {
      if (ref.type === 'FUNDING_REQUEST') {
        var f = s.fundings[ref.id];
        if (!f) return null;
        var first = f.links.length ? pubV(inv(f.links[0].inventionId)) : null;
        return { ref: ref, version: f.version, owner: f.owner, title: f.company, relationship: f.relationship, funding: f, invention: first, stage: first ? first.stage : null, sector: first ? first.sector : null, keywords: f.links.reduce(function (acc, l) { return acc.concat(pubV(inv(l.inventionId)).keywords); }, []), entity: f.subject === 'PROPOSED_ENTITY' ? 'PROPOSED' : 'IDENTIFIED', inventions: f.links };
      }
      var r = s.requests[ref.id];
      if (!r) return null;
      var v = pubV(inv(r.inventionId));
      return { ref: ref, version: r.version, owner: r.owner, title: v ? v.title : '', relationship: r.relationship, request: r, invention: v, stage: v && v.stage, sector: v && v.sector, keywords: v ? v.keywords : [], entity: v ? v.entity : null, authority: v ? v.authority : null, inventions: [{ inventionId: r.inventionId, version: v ? v.n : 0 }] };
    }
    function docsOf(src, kind) {
      var ids = [];
      src.inventions.forEach(function (l) { var i = inv(l.inventionId); if (i) ids = ids.concat(i.versions[l.version - 1] ? i.versions[l.version - 1].docs : []); });
      return ids.map(function (id) { return s.documents[id]; }).filter(function (d) { return d && (!kind || d.kind === kind); });
    }
    function compareBudget(src, opp) {
      var f = opp.financial, b = src.request && src.request.budget;
      if (!b || b.min == null || b.max == null) return { result: 'UNKNOWN', reason: 'Kisaran biaya pilot untuk kebutuhan ini belum diisi.', action: 'complete-budget', feature: null };
      if (f.min == null) return { result: 'UNKNOWN', reason: 'Mitra tidak menyatakan kisaran yang sebanding.', feature: null };
      if (b.currency !== f.currency) return { result: 'UNKNOWN', reason: 'Mata uang berbeda dan tidak ada dasar konversi yang disetujui.', feature: null };
      if (b.period !== f.period || b.scope !== f.scope) return { result: 'UNKNOWN', reason: 'Periode atau cakupan berbeda, jadi jumlahnya belum sebanding.', feature: null };
      if (cmpDec(b.min, f.max) <= 0 && cmpDec(f.min, b.max) <= 0) return { result: 'PASS', reason: 'Kisaran biaya beririsan pada cakupan dan periode yang sama.', feature: 1 };
      if (src.request.partial) return { result: 'PASS', reason: 'Kisaran tidak beririsan, tetapi dukungan sebagian diterima.', feature: 0.5 };
      return { result: 'FAIL', reason: 'Kisaran biaya tidak beririsan dan dukungan penuh diwajibkan.', feature: 0 };
    }
    function compareContribution(src, opp) {
      var f = src.funding, c = opp.financial;
      if (!f) return { result: 'UNKNOWN', reason: 'Dasar kontribusi belum jelas.', feature: null };
      if (f.desiredMin == null || f.desiredMax == null) return { result: 'UNKNOWN', reason: 'Kisaran kontribusi per investor belum diisi.', feature: null };
      if (f.currency !== c.currency) return { result: 'UNKNOWN', reason: 'Mata uang berbeda dan tidak ada dasar konversi yang disetujui.', feature: null };
      if (cmpDec(f.desiredMin, c.max) <= 0 && cmpDec(c.min, f.desiredMax) <= 0) return { result: 'PASS', reason: 'Kisaran investasi beririsan dengan kontribusi yang diinginkan, bukan dengan seluruh target.', feature: 1 };
      return f.partial ? { result: 'PASS', reason: 'Tidak beririsan, tetapi pendanaan sebagian diterima.', feature: 0.5 } : { result: 'FAIL', reason: 'Kisaran tidak beririsan dan pendanaan penuh diwajibkan.', feature: 0 };
    }
    function evalReq(r, src, opp) {
      var f = r.field;
      if (f === 'stage') return r.value.indexOf(src.stage) >= 0 ? { result: 'PASS', reason: 'Tahap inovasi diterima mandat ini.' } : { result: 'FAIL', reason: r.why || 'Tahap inovasi tidak diterima mandat ini.' };
      if (f === 'relationship') return src.relationship === r.value ? { result: 'PASS', reason: 'Bentuk kerja sama sesuai.' } : { result: 'FAIL', reason: r.why || 'Bentuk kerja sama tidak sesuai dengan mandat ini.' };
      if (f === 'budget') return compareBudget(src, opp);
      if (f === 'contribution') return compareContribution(src, opp);
      if (f === 'authority') return src.authority === 'REVIEWED' ? { result: 'PASS', reason: 'Wewenang sudah diperiksa.' } : { result: 'UNKNOWN', reason: 'Wewenang atas inovasi belum dikonfirmasi. Ini bukan berarti wewenang tidak ada.', action: 'clarify-authority' };
      if (f === 'entity') {
        if (src.entity === 'IDENTIFIED') return { result: 'PASS', reason: 'Badan usaha sudah disebutkan.' };
        if (src.entity === 'PROPOSED') return { result: 'FAIL', reason: 'Perusahaan belum didirikan, sedangkan mandat ini memerlukan badan usaha.' };
        return { result: 'UNKNOWN', reason: 'Status badan hukum belum dikonfirmasi.' };
      }
      if (f.indexOf('feature:') === 0) {
        var key = f.slice(8), facts = (src.invention ? src.invention.facts : []).filter(function (x) { return x.key === key; });
        if (facts.some(function (x) { return x.timing === 'CURRENT'; })) return { result: 'PASS', reason: 'Fitur sudah ada saat ini.' };
        if (facts.length) return { result: 'FAIL', reason: 'Fitur baru direncanakan, sedangkan mandat ini memerlukan fitur yang sudah berjalan.' };
        return { result: 'UNKNOWN', reason: 'Belum ada informasi tentang fitur ini.' };
      }
      if (f.indexOf('doc:') === 0) {
        var docs = docsOf(src, f.slice(4)), cur = docs.map(function (d) { return last(d.versions); });
        if (r.mode === 'DOCUMENT_PRESENT') {
          if (cur.some(function (v) { return v.file === 'AVAILABLE'; })) return { result: 'PASS', reason: 'Berkas tersedia. Isinya belum diperiksa.' };
          return { result: 'UNKNOWN', reason: docs.length ? 'Berkas belum lolos pemeriksaan keamanan.' : 'Berkas belum disediakan.' };
        }
        if (cur.some(function (v) { return v.review === 'REVIEWED_SUPPORTED'; })) return { result: 'PASS', reason: 'Sudah diperiksa untuk kriteria ini.' };
        return { result: 'UNKNOWN', reason: 'Belum ada dokumen yang diperiksa untuk kriteria ini.' };
      }
      return { result: 'UNKNOWN', reason: 'Perlu ditinjau secara manual.' };
    }
    function evaluate(ref, oppId) {
      var src = sourceOf(ref), opp = s.opportunities[oppId];
      var rows = opp.requirements.map(function (r) { return Object.assign({}, r, evalReq(r, src, opp)); });
      var entry = rows.filter(function (r) { return r.appliesAt === 'SUBMISSION' && r.mandatory; });
      var failed = entry.filter(function (r) { return r.result === 'FAIL'; }), unknown = entry.filter(function (r) { return r.result === 'UNKNOWN'; });
      var eligibility = failed.length ? 'INCOMPATIBLE' : unknown.length ? 'NEEDS_VERIFICATION' : 'ELIGIBLE';
      var readiness = failed.length ? 'BLOCKED_FOR_THIS_TARGET' : unknown.length ? 'NEEDS_INFORMATION' : 'READY_TO_SUBMIT';
      var money = rows.filter(function (r) { return r.field === 'budget' || r.field === 'contribution'; })[0];
      var overlap = opp.keywords.filter(function (k) { return src.keywords.indexOf(k) >= 0; }).length / opp.keywords.length;
      var a = side({ problem: Math.round(overlap * 100) / 100, stage: opp.stages.indexOf(src.stage) >= 0 ? 1 : 0, sector: opp.sectors.indexOf(src.sector) >= 0 ? 1 : 0, financial: money ? (money.feature == null ? null : money.feature) : null, timing: null }, WEIGHTS.A);
      var b = side({ support: 1, form: src.relationship === opp.relationship ? 1 : 0, geo: 1, availability: opp.status === 'ACTIVE' ? 1 : 0 }, WEIGHTS.B);
      var fit = fitBounds(a, b);
      // No relevance signal means abstaining: compatible geography or stage alone never recommends a target.
      var relevant = overlap > 0;
      var label = eligibility === 'INCOMPATIBLE' ? 'Tidak cocok untuk target ini'
        : !relevant ? 'Belum ada sinyal relevansi'
        : eligibility === 'NEEDS_VERIFICATION' ? 'Perlu konfirmasi'
        : fit.coverage < 0.4 ? 'Informasi belum cukup'
        : fit.lower >= 70 && fit.coverage >= 0.7 ? 'Kecocokan kuat'
        : fit.lower >= 50 && fit.coverage >= 0.5 ? 'Kecocokan potensial' : 'Kecocokan lemah';
      var reasons = rows.filter(function (r) { return r.result === 'PASS' && r.appliesAt === 'SUBMISSION'; }).map(function (r) { return r.reason; }).slice(0, 3);
      var gap = failed[0] || unknown[0] || null;
      var later = rows.filter(function (r) { return r.appliesAt !== 'SUBMISSION'; });
      return { source: { type: ref.type, id: ref.id, version: src.version }, opportunity: { id: oppId, version: opp.version }, rows: rows, eligibility: eligibility, readiness: readiness, relevant: relevant, label: label, reasons: reasons, gap: gap, later: later, fit: fit,
        evidence: { provided: rows.filter(function (r) { return r.mode !== 'REVIEWER_CONFIRMED' && r.result === 'PASS'; }).length, reviewed: rows.filter(function (r) { return r.mode === 'REVIEWER_CONFIRMED' && r.result === 'PASS'; }).length, applicable: rows.length } };
    }
    function activeTargets(ref) {
      var order = { ELIGIBLE: 0, NEEDS_VERIFICATION: 1, INCOMPATIBLE: 2 };
      return Object.keys(s.opportunities).filter(function (id) { return s.opportunities[id].status === 'ACTIVE'; }).map(function (id) { return evaluate(ref, id); })
        .sort(function (x, y) { return order[x.eligibility] - order[y.eligibility] || y.fit.lower - x.fit.lower || (x.opportunity.id < y.opportunity.id ? -1 : 1); });
    }
    function freeze(src, opp, brief, files, actor) {
      return { at: now(), by: actor.party, brief: brief, files: files, opportunityVersion: opp.version, sourceVersion: src.version, sourceTitle: src.title,
        request: src.request ? clone(src.request) : null, funding: src.funding ? clone(src.funding) : null,
        inventions: src.inventions.map(function (l) { var v = inv(l.inventionId).versions[l.version - 1]; return { id: l.inventionId, version: l.version, title: v.title, stage: v.stage, facts: clone(v.facts) }; }), requirements: evaluate(src.ref, opp.id).rows };
    }
    function pitchFor(actor, id) {
      var p = s.pitches[id];
      if (!p) return null;
      return isMember(actor, p.requester) || isMember(actor, p.recipient) ? p : null;
    }
    function reviewerOf(actor) { return actor.account === 'bima' && actor.party === 'p-dcm'; }
    function activePitch(ref, oppId) {
      return Object.keys(s.pitches).map(function (k) { return s.pitches[k]; }).filter(function (p) {
        return p.subject.id === ref.id && p.subject.type === ref.type && p.opportunity.id === oppId && ['REJECTED', 'WITHDRAWN', 'CLOSED'].indexOf(p.status) < 0;
      })[0];
    }
    function openProposal(pitchId) {
      Object.keys(s.proposals).forEach(function (k) { expireIfDue(s.proposals[k]); });
      return Object.keys(s.proposals).map(function (k) { return s.proposals[k]; }).filter(function (x) { return x.pitchId === pitchId && x.state === 'OPEN'; })[0] || null;
    }
    function latestProposal(pitchId) { return Object.keys(s.proposals).map(function (k) { return s.proposals[k]; }).filter(function (x) { return x.pitchId === pitchId; }).pop() || null; }
    function activeMeeting(pitchId) { return Object.keys(s.meetings).map(function (k) { return s.meetings[k]; }).filter(function (m) { return m.pitchId === pitchId && m.state === 'CONFIRMED'; })[0] || null; }
    function expireIfDue(p) {
      if (p.state !== 'OPEN') return;
      var t = ms(now());
      if (t - ms(p.at) >= 72 * HOUR) { p.state = 'EXPIRED'; p.expiredBy = 'AGE'; } else if (p.slots.every(function (x) { return ms(x.start) <= t; })) { p.state = 'EXPIRED'; p.expiredBy = 'ALL_PAST'; }
    }
    function partnershipOf(pitchId) { return Object.keys(s.partnerships).map(function (k) { return s.partnerships[k]; }).filter(function (x) { return x.pitchId === pitchId; })[0] || null; }
    function effectiveFields(rel) {
      var conf = rel.versions.filter(function (v) { return v.status === 'CONFIRMED'; }).pop();
      if (!conf) return { version: null, fields: [] };
      var cut = rel.restrictions.map(function (r) { return r.field; }), parties = rel.parties;
      return { version: conf.n, fields: conf.ceiling.filter(function (f) {
        return parties.every(function (p) { return conf.confirmations[p] && conf.confirmations[p].subset.indexOf(f) >= 0; }) && cut.indexOf(f) < 0;
      }) };
    }
    function publicRelationships(partyId) {
      return Object.keys(s.partnerships).map(function (k) { return s.partnerships[k]; }).filter(function (r) { return r.parties.indexOf(partyId) >= 0 && !r.contested; }).map(function (r) {
        var e = effectiveFields(r); if (!e.version) return null;
        var v = r.versions[e.version - 1], m = {};
        e.fields.forEach(function (f) { m[f] = v.values[f]; });
        return { id: r.id, version: e.version, fields: m, parties: r.parties, inventionIds: r.inventionIds };
      }).filter(Boolean);
    }
    function ics(m) {
      function stamp(i) { return i.replace(/[-:]/g, '').replace('.000', ''); }
      return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//TemuRiset Demo//ID', 'BEGIN:VEVENT', 'UID:' + m.id + '@temuriset.demo', 'DTSTAMP:' + stamp(now()), 'DTSTART:' + stamp(m.start), 'DTEND:' + stamp(m.end), 'SUMMARY:Diskusi pitching (data demo)', 'DESCRIPTION:' + m.agenda, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
    }

    /* ----- operations ----- */
    var op = {
      /* portfolio */
      createInvention: function (ctx) {
        return mutate('createInvention', ctx, {}, function () {
          var id = nextId('inv');
          s.inventions[id] = { id: id, owner: ctx.actor.party, status: 'DRAFT', archived: false, published: 0, versions: [], draftRev: 1, savedAt: now(), draft: { title: '', summary: '', problem: '', solution: '', users: '', sector: '', stage: '', facts: [], docs: [], people: [] } };
          audit(ctx.actor, 'Membuat draf inovasi', id);
          return ok({ id: id });
        });
      },
      startDraft: function (ctx, a) {
        var i = inv(a.id);
        if (!i || !can(ctx.actor, i.owner, 'edit')) return denied();
        if (!i.draft) { i.draft = clone(i.versions[i.published - 1]); delete i.draft.n; i.draftRev = 1; i.savedAt = null; emit(); }
        return ok({ draft: clone(i.draft), rev: i.draftRev });
      },
      saveDraft: function (ctx, a) {
        return mutate('saveDraft', ctx, a, function () {
          var i = inv(a.id);
          if (!i || !can(ctx.actor, i.owner, 'edit')) return denied();
          if (a.rev !== i.draftRev) return err('STALE_VERSION', 'Draf ini sudah berubah di sesi lain.', { current: clone(i.draft), rev: i.draftRev });
          i.draft = Object.assign({}, i.draft, a.fields); i.draftRev += 1; i.savedAt = now();
          return ok({ rev: i.draftRev, savedAt: i.savedAt });
        });
      },
      publishInvention: function (ctx, a) {
        return mutate('publishInvention', ctx, a, function () {
          var i = inv(a.id), d = i && i.draft;
          if (!i || !can(ctx.actor, i.owner, 'edit')) return denied();
          if (!d) return err('NO_DRAFT', 'Tidak ada perubahan untuk diterbitkan.');
          var errors = {};
          if ((d.title || '').trim().length < 5 || d.title.length > 120) errors.title = 'Judul harus 5 sampai 120 karakter.';
          if (!(d.summary || '').trim() || d.summary.length > 350) errors.summary = 'Ringkasan wajib diisi, paling banyak 350 karakter.';
          if (!(d.problem || '').trim()) errors.problem = 'Tuliskan masalah yang diselesaikan.';
          if (!(d.solution || '').trim()) errors.solution = 'Tuliskan solusi yang sudah ada.';
          if (!(d.users || '').trim()) errors.users = 'Tuliskan siapa penggunanya.';
          if (!d.stage) errors.stage = 'Pilih tahap saat ini.';
          if (Object.keys(errors).length) return err('VALIDATION', 'Periksa kembali isian Anda.', { fields: errors });
          var n = i.versions.length + 1, v = Object.assign(clone(d), { n: n, at: now(), keywords: d.keywords || [], facts: d.facts || [], people: d.people || [], docs: d.docs || [], category: d.category || d.sector || 'Inovasi', authority: d.authority || 'SELF_DECLARED', entity: d.entity || 'UNCONFIRMED' });
          i.versions.push(v);
          if (s.flags.orgReview && s.parties[i.owner].kind === 'organization') {
            var rid = nextId('rev');
            s.reviews[rid] = { id: rid, kind: 'PUBLICATION', ref: i.id, version: n, owner: i.owner, state: 'QUEUED', at: now() };
            i.reviewPending = true; i.draft = null;
            audit(ctx.actor, 'Mengirim inovasi ke tinjauan organisasi', i.id);
            return ok({ queued: true, version: n });
          }
          i.published = n; i.status = 'PUBLISHED'; i.draft = null;
          audit(ctx.actor, 'Menerbitkan inovasi versi ' + n, i.id);
          return ok({ version: n });
        });
      },
      archiveInvention: function (ctx, a) {
        return mutate('archiveInvention', ctx, a, function () {
          var i = inv(a.id);
          if (!i || !can(ctx.actor, i.owner, 'edit')) return denied();
          i.archived = true; i.status = 'ARCHIVED';
          return ok();
        });
      },
      /* documents and grants */
      addDocument: function (ctx, a) {
        return mutate('addDocument', ctx, a, function () {
          if (!isMember(ctx.actor, a.owner)) return denied();
          var id = nextId('doc');
          s.documents[id] = { id: id, owner: a.owner, kind: a.kind || 'function', title: a.title, versions: [{ n: 1, file: 'UPLOADING', extraction: 'NOT_REQUESTED', review: 'PROVIDED_UNREVIEWED', at: now() }] };
          return ok({ id: id });
        });
      },
      advanceDocument: function (ctx, a) {
        var d = s.documents[a.id], v = d && last(d.versions);
        if (!v) return denied();
        Object.assign(v, a.state); emit();
        return ok({ version: v.n });
      },
      newDocumentVersion: function (ctx, a) {
        return mutate('newDocumentVersion', ctx, a, function () {
          var d = s.documents[a.id];
          if (!d || !isMember(ctx.actor, d.owner)) return denied();
          var prev = last(d.versions);
          prev.review = 'SUPERSEDED';
          d.versions.push({ n: prev.n + 1, file: 'AVAILABLE', extraction: 'SUCCEEDED', review: 'PROVIDED_UNREVIEWED', at: now() });
          return ok({ version: prev.n + 1 });
        });
      },
      revokeGrant: function (ctx, a) {
        return mutate('revokeGrant', ctx, a, function () {
          var g = s.grants[a.id];
          if (!g || !isMember(ctx.actor, s.documents[g.docId].owner)) return denied();
          g.revoked = true; g.revokedAt = now();
          audit(ctx.actor, 'Mencabut akses dokumen', g.docId);
          return ok();
        });
      },
      fetchDocument: function (ctx, a) {
        var d = s.documents[a.docId];
        if (!d) return denied();
        if (isMember(ctx.actor, d.owner)) return ok({ title: d.title, version: a.version, bytes: 'Isi berkas demo' });
        var grant = Object.keys(s.grants).map(function (k) { return s.grants[k]; }).filter(function (g) { return g.docId === a.docId && g.version === a.version && g.to === ctx.actor.party && !g.revoked; })[0];
        if (!grant) return denied();
        grant.downloads = (grant.downloads || 0) + 1; emit();
        return ok({ title: d.title, version: a.version, bytes: 'Isi berkas demo' });
      },
      /* support and funding */
      saveSupportRequest: function (ctx, a) {
        return mutate('saveSupportRequest', ctx, a, function () {
          var r = a.id ? s.requests[a.id] : null;
          if (a.id && !r) return denied();
          var owner = r ? r.owner : inv(a.inventionId).owner;
          if (!can(ctx.actor, owner, 'edit')) return denied();
          if (r && a.expected != null && a.expected !== r.version) return err('STALE_VERSION', 'Kebutuhan ini sudah berubah. Muat versi terbaru.');
          var errors = {}, b = a.budget || {}, min = parseAmount(b.min), max = parseAmount(b.max), nonfinancial = !!a.fields.noncash;
          if (min === null) errors.min = 'Isi angka nol atau lebih, tanpa tanda minus.';
          if (max === null) errors.max = 'Isi angka nol atau lebih, tanpa tanda minus.';
          if (min && max && cmpDec(max, min) < 0) errors.max = 'Batas atas tidak boleh lebih kecil dari batas bawah.';
          if (!nonfinancial && (min === '0' || max === '0')) errors.min = 'Nol hanya dipakai untuk kebutuhan nonfinansial. Kosongkan jika belum ditentukan.';
          if (Object.keys(errors).length) return err('VALIDATION', 'Periksa kembali kisaran biaya.', { fields: errors });
          var budget = Object.assign({}, r ? r.budget : { currency: 'USD', period: '6 bulan', scope: 'biaya pilot enam bulan' }, { min: min || null, max: max || null, currency: b.currency || 'USD', period: b.period || (r && r.budget.period) || null, assumptions: b.assumptions != null ? b.assumptions : (r && r.budget.assumptions) });
          if (!r) {
            var id = nextId('sr');
            r = s.requests[id] = Object.assign({ id: id, inventionId: a.inventionId, owner: owner, status: 'DRAFT', version: 1, region: 'Indonesia', months: 6, partial: true, relationship: 'PROJECT', budget: budget }, a.fields);
          } else { Object.assign(r, a.fields, { budget: budget }); r.version += 1; }
          delete s.variants.gap;
          audit(ctx.actor, 'Menyimpan kebutuhan versi ' + r.version, r.id);
          return ok({ id: r.id, version: r.version });
        });
      },
      setRequestStatus: function (ctx, a) {
        return mutate('setRequestStatus', ctx, a, function () {
          var r = s.requests[a.id];
          if (!r || !can(ctx.actor, r.owner, 'edit')) return denied();
          r.status = a.status;
          return ok();
        });
      },
      saveFundingRequest: function (ctx, a) {
        return mutate('saveFundingRequest', ctx, a, function () {
          if (!s.flags.companyFunding) return err('CAPABILITY_UNAVAILABLE', 'Pendanaan Perusahaan tidak aktif pada komposisi ini. Riwayat yang ada tetap dapat dibaca.');
          var f = s.fundings[a.id];
          if (!f || !can(ctx.actor, f.owner, 'edit')) return denied();
          if (a.expected != null && a.expected !== f.version) return err('STALE_VERSION', 'Permintaan pendanaan ini sudah berubah. Muat versi terbaru.');
          var errors = {}, target = parseAmount(a.fields.target), lo = parseAmount(a.fields.desiredMin), hi = parseAmount(a.fields.desiredMax);
          if (target === null || target === '') errors.target = 'Isi target pendanaan dengan angka.';
          if (lo === null) errors.desiredMin = 'Isi angka tanpa tanda minus.';
          if (hi === null) errors.desiredMax = 'Isi angka tanpa tanda minus.';
          if (lo && hi && cmpDec(hi, lo) < 0) errors.desiredMax = 'Batas atas tidak boleh lebih kecil dari batas bawah.';
          if (Object.keys(errors).length) return err('VALIDATION', 'Periksa kembali isian pendanaan.', { fields: errors });
          f.history.push({ version: f.version, target: f.target, at: now() });
          Object.assign(f, a.fields, { target: target, desiredMin: lo || null, desiredMax: hi || null });
          f.version += 1;
          audit(ctx.actor, 'Menyimpan permintaan pendanaan versi ' + f.version, f.id);
          return ok({ version: f.version });
        });
      },
      setProposedEntity: function (on) {
        var f = s.fundings.FRaise01;
        f.subject = on ? 'PROPOSED_ENTITY' : 'EXISTING_ENTITY';
        if (on) s.variants.proposedEntity = true; else delete s.variants.proposedEntity;
        emit();
      },
      /* partner intake */
      saveOpportunity: function (ctx, a) {
        return mutate('saveOpportunity', ctx, a, function () {
          var o = s.opportunities[a.id];
          if (!o || !can(ctx.actor, o.partner, 'edit')) return denied();
          if (a.expected != null && a.expected !== o.version) return err('STALE_VERSION', 'Mandat ini sudah berubah. Muat versi terbaru.');
          if (!(a.fields.title || '').trim()) return err('VALIDATION', 'Periksa kembali isian mandat.', { fields: { title: 'Judul mandat wajib diisi.' } });
          o.history.push({ version: o.version, title: o.title, at: now() });
          Object.assign(o, a.fields); o.version += 1;
          return ok({ version: o.version });
        });
      },
      setOpportunityStatus: function (ctx, a) {
        return mutate('setOpportunityStatus', ctx, a, function () {
          var o = s.opportunities[a.id];
          if (!o || !can(ctx.actor, o.partner, 'edit')) return denied();
          o.status = a.status;
          return ok();
        });
      },
      changeTargetVersion: function () {
        var o = s.opportunities.A1;
        o.history.push({ version: o.version, title: o.title, at: now() });
        o.version += 1; o.timing = 'Dibuka sampai 15 Desember 2026'; s.variants.stale = true; emit();
      },
      /* discovery */
      toggleSaved: function (ctx, a) { var k = ctx.actor.party + ':' + a.id; if (s.saved[k]) delete s.saved[k]; else s.saved[k] = true; emit(); return ok(); },
      lessRelevant: function (ctx, a) { s.hidden[ctx.actor.party + ':' + a.id] = true; emit(); return ok(); },
      /* preflight and pitch */
      preflight: function (ctx, a) {
        var src = sourceOf(a.source), opp = s.opportunities[a.opportunityId];
        if (!src || !opp || !can(ctx.actor, src.owner, 'view')) return denied();
        var r = evaluate(a.source, a.opportunityId), dup = activePitch(a.source, a.opportunityId);
        return ok({ token: { sourceVersion: src.version, opportunityVersion: opp.version, at: now(), actor: ctx.actor.party }, result: r, duplicate: dup ? dup.id : null, intake: opp.status });
      },
      templateBrief: function (a) {
        var src = sourceOf(a.source), opp = s.opportunities[a.opportunityId], f = src.funding, v = src.invention, r = src.request;
        var money = f ? 'Target Pendanaan USD ' + f.target + ' untuk satu perusahaan; kontribusi yang diinginkan USD ' + f.desiredMin + '–' + f.desiredMax + '.' : r && r.budget.min ? 'Kebutuhan USD ' + r.budget.min + '–' + r.budget.max + ' untuk ' + r.budget.scope + '.' : 'Kebutuhan dana belum ditentukan.';
        var current = v ? v.facts.filter(function (x) { return x.timing === 'CURRENT'; }).map(function (x) { return x.label + ' saat ini ' + x.value; }).join('; ') : '';
        var planned = v ? v.facts.filter(function (x) { return x.timing === 'PLANNED'; }).map(function (x) { return x.label + ' direncanakan ' + x.value; }).join('; ') : '';
        return [v ? 'Masalah: ' + v.problem : '', v ? 'Solusi saat ini: ' + v.solution : '', current, planned, 'Dukungan yang diminta: ' + (f ? f.purpose : r.outcome) + '.', money, 'Relevansi: ' + opp.title + '.'].filter(Boolean).join('\n');
      },
      submitPitch: function (ctx, a) {
        return mutate('submitPitch', ctx, { source: a.source, opportunityId: a.opportunityId, brief: a.brief, files: a.files }, function () {
          var src = sourceOf(a.source), opp = s.opportunities[a.opportunityId];
          if (!src || !opp || !can(ctx.actor, src.owner, 'submit')) return denied();
          if (opp.status !== 'ACTIVE') return err('TARGET_CLOSED', 'Penerimaan pada mandat ini sudah ditutup. Pitching baru tidak dapat dikirim.');
          if (a.token.opportunityVersion !== opp.version || a.token.sourceVersion !== src.version) return err('STALE_VERSION', 'Versi mandat atau kebutuhan berubah setelah pemeriksaan. Periksa ulang sebelum mengirim.', { retryable: false });
          var dup = activePitch(a.source, a.opportunityId);
          if (dup) return err('DUPLICATE', 'Pitching untuk permintaan dan mandat ini sudah ada.', { pitchId: dup.id });
          var r = evaluate(a.source, a.opportunityId);
          if (r.readiness !== 'READY_TO_SUBMIT') return err('NOT_READY', 'Masih ada syarat pengajuan yang belum selesai.');
          var id = nextId('pit');
          var files = (a.files || []).map(function (f) { return { docId: f.docId, version: f.version }; });
          var gated = s.flags.orgReview && s.parties[src.owner].kind === 'organization';
          var p = s.pitches[id] = { id: id, version: 1, subject: a.source, inventions: clone(src.inventions), requester: src.owner, recipient: opp.partner, opportunity: { id: opp.id, version: opp.version, title: opp.title }, purpose: src.relationship, status: gated ? 'PENDING_WORKSPACE_REVIEW' : 'SUBMITTED', submissions: [freeze(src, opp, a.brief, files, ctx.actor)], rounds: [], decisions: [], messages: [], tasks: [], timeline: [] };
          files.forEach(function (f) { var gid = nextId('gr'); s.grants[gid] = { id: gid, docId: f.docId, version: f.version, to: opp.partner, pitchId: id, revoked: false, at: now() }; });
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Pitching dikirim' });
          if (gated) { var rid = nextId('rev'); s.reviews[rid] = { id: rid, kind: 'SUBMISSION', ref: id, version: 1, owner: src.owner, state: 'QUEUED', at: now() }; }
          else notify(opp.partner, 'Pitching baru: ' + src.title, id);
          audit(ctx.actor, 'Mengirim pitching', id);
          return ok({ pitchId: id });
        });
      },
      beginReview: function (ctx, a) {
        return mutate('beginReview', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !can(ctx.actor, p.recipient, 'view')) return denied();
          if (p.status !== 'SUBMITTED') return err('INVALID_STATE', 'Pitching ini tidak dalam status terkirim.');
          p.status = 'UNDER_REVIEW'; p.version += 1;
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Mulai ditinjau' });
          return ok({ version: p.version });
        });
      },
      decide: function (ctx, a) {
        return mutate('decide', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !isMember(ctx.actor, p.recipient)) return denied();
          if (!can(ctx.actor, p.recipient, 'decide')) return err('FORBIDDEN', 'Akun Anda dapat melihat pitching ini, tetapi tidak berwenang memutuskan.');
          if (a.expected !== p.version) return err('STALE_VERSION', 'Pitching ini baru saja berubah. Muat versi terbaru sebelum memutuskan.');
          if (['SUBMITTED', 'UNDER_REVIEW'].indexOf(p.status) < 0) return err('INVALID_STATE', 'Keputusan tidak dapat dibuat pada status ini.');
          if (a.decision === 'REJECT' && !(a.reason || '').trim()) return err('VALIDATION', 'Tuliskan alasan singkat.', { fields: { reason: 'Alasan wajib diisi dan hanya terlihat oleh pengirim pitching.' } });
          p.status = a.decision === 'APPROVE' ? 'APPROVED_FOR_DISCUSSION' : 'REJECTED';
          p.version += 1;
          p.decisions.push({ decision: a.decision, reason: a.reason || null, at: now(), by: ctx.actor.party, submission: p.submissions.length });
          p.timeline.push({ at: now(), by: ctx.actor.party, text: a.decision === 'APPROVE' ? 'Disetujui untuk diskusi' : 'Ditolak' });
          notify(p.requester, a.decision === 'APPROVE' ? 'Pitching disetujui untuk diskusi' : 'Pitching ditolak', p.id);
          audit(ctx.actor, 'Keputusan ' + a.decision, p.id);
          return ok({ version: p.version });
        });
      },
      withdraw: function (ctx, a) {
        return mutate('withdraw', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !can(ctx.actor, p.requester, 'submit')) return denied();
          if (['SUBMITTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', 'PENDING_WORKSPACE_REVIEW'].indexOf(p.status) < 0) return err('INVALID_STATE', 'Pitching ini tidak dapat ditarik lagi.');
          p.status = 'WITHDRAWN'; p.version += 1;
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Ditarik pengirim' });
          return ok();
        });
      },
      closeDiscussion: function (ctx, a) {
        return mutate('closeDiscussion', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          if (p.status !== 'APPROVED_FOR_DISCUSSION') return err('INVALID_STATE', 'Diskusi tidak sedang terbuka.');
          if (!(a.reason || '').trim()) return err('VALIDATION', 'Tuliskan alasan penutupan.', { fields: { reason: 'Alasan wajib diisi.' } });
          p.status = 'CLOSED'; p.version += 1; p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Diskusi ditutup: ' + a.reason });
          return ok();
        });
      },
      requestRevision: function (ctx, a) {
        return mutate('requestRevision', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !isMember(ctx.actor, p.recipient)) return denied();
          if (!can(ctx.actor, p.recipient, 'decide')) return err('FORBIDDEN', 'Akun Anda tidak berwenang meminta revisi.');
          if (a.expected !== p.version) return err('STALE_VERSION', 'Pitching ini baru saja berubah. Muat versi terbaru.');
          if (['SUBMITTED', 'UNDER_REVIEW'].indexOf(p.status) < 0) return err('INVALID_STATE', 'Revisi tidak dapat diminta setelah keputusan dibuat. Gunakan tugas diskusi.');
          if (!a.items.length || a.items.some(function (i) { return !(i.question || '').trim() || !(i.reason || '').trim(); })) return err('VALIDATION', 'Setiap permintaan perlu pertanyaan dan alasan.', { fields: { items: 'Lengkapi pertanyaan dan alasan.' } });
          var n = p.rounds.length + 1;
          p.rounds.push({ n: n, at: now(), by: ctx.actor.party, items: a.items.map(function (i, x) { return Object.assign({ id: 'r' + n + 'i' + (x + 1), answer: null, attachments: [], review: null, reviewNote: null }, i); }) });
          p.status = 'REVISION_REQUESTED'; p.version += 1;
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Revisi putaran ' + n + ' diminta' });
          notify(p.requester, 'Revisi putaran ' + n + ' diminta', p.id);
          return ok({ round: n, version: p.version });
        });
      },
      saveAnswer: function (ctx, a) {
        return mutate('saveAnswer', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !can(ctx.actor, p.requester, 'submit')) return denied();
          var item = last(p.rounds).items.filter(function (x) { return x.id === a.itemId; })[0];
          if (!item) return err('NOT_FOUND', 'Pertanyaan tidak ditemukan.');
          item.answer = Object.assign({}, item.answer, a.value, { savedAt: now() });
          if (a.attachment) item.attachments.push(a.attachment);
          return ok();
        });
      },
      resubmit: function (ctx, a) {
        return mutate('resubmit', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !can(ctx.actor, p.requester, 'submit')) return denied();
          if (a.expected !== p.version) return err('STALE_VERSION', 'Pitching ini baru saja berubah. Jawaban Anda tetap ada.');
          if (p.status !== 'REVISION_REQUESTED') return err('INVALID_STATE', 'Pitching ini tidak sedang menunggu revisi.');
          var missing = last(p.rounds).items.filter(function (i) { return i.required && !(i.answer && i.answer.response); });
          if (missing.length) return err('VALIDATION', 'Jawab semua pertanyaan wajib sebelum mengirim ulang.', { missing: missing.map(function (i) { return i.id; }) });
          var src = sourceOf(p.subject), opp = s.opportunities[p.opportunity.id], files = (a.files || []).map(function (f) { return { docId: f.docId, version: f.version }; });
          p.submissions.push(freeze(src, opp, a.brief || last(p.submissions).brief, files, ctx.actor));
          files.forEach(function (f) {
            var has = Object.keys(s.grants).some(function (k) { var g = s.grants[k]; return g.docId === f.docId && g.version === f.version && g.to === p.recipient && !g.revoked; });
            if (!has) { var gid = nextId('gr'); s.grants[gid] = { id: gid, docId: f.docId, version: f.version, to: p.recipient, pitchId: p.id, revoked: false, at: now() }; }
          });
          p.status = 'SUBMITTED'; p.version += 1;
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Dikirim ulang, submisi ' + p.submissions.length });
          notify(p.recipient, 'Pitching dikirim ulang', p.id);
          return ok({ submission: p.submissions.length, version: p.version });
        });
      },
      reviewItem: function (ctx, a) {
        return mutate('reviewItem', ctx, a, function () {
          var p = s.pitches[a.pitchId];
          if (!p || !can(ctx.actor, p.recipient, 'decide')) return denied();
          var item = null;
          p.rounds.forEach(function (r) { r.items.forEach(function (i) { if (i.id === a.itemId) item = i; }); });
          if (!item) return err('NOT_FOUND', 'Pertanyaan tidak ditemukan.');
          item.review = a.result; item.reviewNote = a.note || null;
          return ok();
        });
      },
      /* discussion */
      sendMessage: function (ctx, a) {
        return mutate('sendMessage', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          if (!(a.text || '').trim()) return err('VALIDATION', 'Tulis pesan terlebih dahulu.', { fields: { text: 'Pesan belum diisi.' } });
          p.messages.push({ id: nextId('m'), by: ctx.actor.party, text: a.text, at: now() });
          return ok();
        });
      },
      addTask: function (ctx, a) {
        return mutate('addTask', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          if (!(a.title || '').trim()) return err('VALIDATION', 'Tuliskan tugasnya.', { fields: { title: 'Tugas belum diisi.' } });
          p.tasks.push({ id: nextId('t'), title: a.title, owner: a.owner, status: 'OPEN', at: now() });
          return ok();
        });
      },
      completeTask: function (ctx, a) {
        return mutate('completeTask', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          p.tasks.forEach(function (t) { if (t.id === a.taskId) t.status = 'DONE'; });
          return ok();
        });
      },
      /* scheduling */
      proposeSlots: function (ctx, a) {
        return mutate('proposeSlots', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          if (!can(ctx.actor, ctx.actor.party, 'schedule')) return err('FORBIDDEN', 'Akun Anda tidak berwenang mengatur jadwal.');
          if (p.status !== 'APPROVED_FOR_DISCUSSION') return err('INVALID_STATE', 'Jadwal hanya dapat diatur setelah pitching disetujui untuk diskusi.');
          var errors = {}, slots = a.slots || [];
          if (slots.length < 2 || slots.length > 5) errors.slots = 'Usulkan 2 sampai 5 waktu.';
          if ([30, 60].indexOf(a.minutes) < 0) errors.minutes = 'Pilih durasi 30 atau 60 menit.';
          if (!(a.agenda || '').trim()) errors.agenda = 'Tuliskan agenda singkat.';
          if (a.link && !/^https:\/\//.test(a.link)) errors.link = 'Tautan pertemuan harus memakai https.';
          if (slots.some(function (x) { return ms(x) <= ms(now()); })) errors.slots = 'Waktu yang diusulkan harus setelah jam saat ini.';
          if (Object.keys(errors).length) return err('VALIDATION', 'Periksa kembali usulan waktu.', { fields: errors });
          var open = openProposal(p.id);
          if (open) open.state = 'SUPERSEDED';
          var id = nextId('sp');
          s.proposals[id] = { id: id, pitchId: p.id, by: ctx.actor.party, at: now(), minutes: a.minutes, zone: a.zone, agenda: a.agenda, link: a.link || null, state: 'OPEN', replaces: a.replaces || null,
            slots: slots.map(function (x, n) { return { id: 'slot' + (n + 1), start: iso(ms(x)) }; }) };
          p.timeline.push({ at: now(), by: ctx.actor.party, text: (a.replaces ? 'Mengusulkan jadwal pengganti' : open ? 'Mengusulkan waktu lain' : 'Mengusulkan waktu pertemuan') });
          notify(p.requester === ctx.actor.party ? p.recipient : p.requester, 'Usulan waktu pertemuan baru', p.id);
          return ok({ id: id });
        });
      },
      acceptSlot: function (ctx, a) {
        return mutate('acceptSlot', ctx, a, function () {
          var pr = s.proposals[a.proposalId], p = pr && pitchFor(ctx.actor, pr.pitchId);
          if (!p) return denied();
          expireIfDue(pr);
          if (pr.state !== 'OPEN') return err('PROPOSAL_CLOSED', pr.state === 'EXPIRED' ? 'Usulan ini sudah kedaluwarsa. Pitching tetap disetujui untuk diskusi.' : 'Usulan ini sudah diganti.');
          if (pr.by === ctx.actor.party) return err('FORBIDDEN', 'Pihak lain yang perlu menerima usulan Anda.');
          var slot = pr.slots.filter(function (x) { return x.id === a.slotId; })[0];
          if (!slot) return err('NOT_FOUND', 'Waktu ini tidak ada dalam usulan.');
          var start = slot.start, end = addMin(start, pr.minutes), required = [p.requester, p.recipient];
          var clash = s.bookings.filter(function (b) { return required.indexOf(b.party) >= 0 && b.meetingId !== pr.replaces && overlaps(start, end, b.start, b.end); });
          if (clash.length) { slot.conflict = true; emit(); return err('BOOKING_CONFLICT', 'Waktu ini bentrok dengan jadwal peserta. Pilih waktu lain atau usulkan waktu baru.', { slotId: slot.id }); }
          if (pr.replaces) {
            s.meetings[pr.replaces].state = 'CANCELLED'; s.meetings[pr.replaces].replacedBy = pr.id;
            s.bookings = s.bookings.filter(function (b) { return b.meetingId !== pr.replaces; });
          }
          var id = nextId('mt');
          s.meetings[id] = { id: id, pitchId: p.id, start: start, end: end, minutes: pr.minutes, zone: pr.zone, agenda: pr.agenda, link: pr.link, state: 'CONFIRMED', outcomes: {} };
          required.forEach(function (party) { s.bookings.push({ id: nextId('bk'), party: party, start: start, end: end, meetingId: id }); });
          pr.state = 'ACCEPTED'; pr.slotId = slot.id;
          p.timeline.push({ at: now(), by: ctx.actor.party, text: pr.replaces ? 'Jadwal pengganti dikonfirmasi' : 'Waktu pertemuan dikonfirmasi' });
          notify(pr.by, 'Waktu pertemuan dikonfirmasi', p.id);
          return ok({ meetingId: id });
        });
      },
      cancelProposal: function (ctx, a) {
        return mutate('cancelProposal', ctx, a, function () {
          var pr = s.proposals[a.proposalId], p = pr && pitchFor(ctx.actor, pr.pitchId);
          if (!p) return denied();
          pr.state = 'CANCELLED';
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Usulan waktu dibatalkan' });
          return ok();
        });
      },
      cancelMeeting: function (ctx, a) {
        return mutate('cancelMeeting', ctx, a, function () {
          var m = s.meetings[a.id], p = m && pitchFor(ctx.actor, m.pitchId);
          if (!p) return denied();
          m.state = 'CANCELLED';
          s.bookings = s.bookings.filter(function (b) { return b.meetingId !== m.id; });
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Pertemuan dibatalkan' });
          return ok();
        });
      },
      recordOutcome: function (ctx, a) {
        return mutate('recordOutcome', ctx, a, function () {
          var m = s.meetings[a.id], p = m && pitchFor(ctx.actor, m.pitchId);
          if (!p) return denied();
          if (ms(now()) < ms(m.start)) return err('TOO_EARLY', 'Hasil pertemuan dicatat setelah pertemuan dimulai.');
          m.outcomes[ctx.actor.party] = { result: a.result, note: a.note || '', at: now() };
          var vals = [p.requester, p.recipient].map(function (x) { return m.outcomes[x] && m.outcomes[x].result; });
          if (vals[0] && vals[1]) {
            if (vals[0] === vals[1]) m.state = vals[0] === 'COMPLETED' ? 'COMPLETED' : 'NO_SHOW_REPORTED'; else m.disputed = true;
          }
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Mencatat hasil pertemuan' });
          return ok();
        });
      },
      /* relationship */
      proposePartnership: function (ctx, a) {
        return mutate('proposePartnership', ctx, a, function () {
          var p = pitchFor(ctx.actor, a.pitchId);
          if (!p) return denied();
          if (!can(ctx.actor, ctx.actor.party, 'confirm')) return err('FORBIDDEN', 'Akun Anda tidak berwenang mengusulkan Kerja Sama.');
          if (partnershipOf(p.id)) return err('DUPLICATE', 'Ringkasan Kerja Sama untuk pitching ini sudah ada.');
          var m = Object.keys(s.meetings).map(function (k) { return s.meetings[k]; }).filter(function (x) { return x.pitchId === p.id && x.state === 'COMPLETED'; })[0];
          if (!m) return err('NO_COMPLETED_MEETING', 'Ringkasan Kerja Sama diusulkan setelah kedua pihak mencatat pertemuan selesai.');
          var errors = {};
          if (!(a.values.scope || '').trim()) errors.scope = 'Tuliskan cakupan kerja sama.';
          if (!(a.values.date || '').trim()) errors.date = 'Tuliskan tanggal mulai.';
          if (a.type === 'EQUITY') {
            var entity = sourceOf(p.subject).entity;
            if (entity !== 'IDENTIFIED') errors.type = 'Ekuitas memerlukan badan usaha yang sudah ada. Perusahaan belum didirikan.';
          }
          if (a.values.percent && a.type !== 'EQUITY') errors.percent = 'Persentase hanya berlaku untuk ekuitas.';
          if (a.values.percent && !a.values.percentDate) errors.percentDate = 'Persentase memerlukan tanggal berlaku.';
          if (Object.keys(errors).length) return err('VALIDATION', 'Periksa kembali ringkasan.', { fields: errors });
          var id = nextId('ks'), ceiling = a.ceiling, subset = a.subset.filter(function (f) { return ceiling.indexOf(f) >= 0; });
          var v = { n: 1, values: a.values, ceiling: ceiling, status: 'PENDING_COUNTERPARTY', proposedBy: ctx.actor.party, at: now(), confirmations: {} };
          v.confirmations[ctx.actor.party] = { subset: subset, at: now() };
          s.partnerships[id] = { id: id, pitchId: p.id, type: a.type, parties: [p.requester, p.recipient], inventionIds: p.inventions.map(function (l) { return l.inventionId; }), versions: [v], restrictions: [], contested: false };
          p.timeline.push({ at: now(), by: ctx.actor.party, text: 'Mengusulkan ringkasan Kerja Sama versi 1' });
          notify(p.requester === ctx.actor.party ? p.recipient : p.requester, 'Ringkasan Kerja Sama perlu konfirmasi', id);
          return ok({ id: id });
        });
      },
      requestCorrection: function (ctx, a) {
        return mutate('requestCorrection', ctx, a, function () {
          var r = s.partnerships[a.id];
          if (!r || r.parties.indexOf(ctx.actor.party) < 0 || !isMember(ctx.actor, ctx.actor.party)) return denied();
          var cur = last(r.versions);
          if (a.version !== cur.n) return err('STALE_VERSION', 'Versi ringkasan sudah berubah.');
          if (!(a.values.scope || '').trim()) return err('VALIDATION', 'Periksa kembali koreksi.', { fields: { scope: 'Tuliskan cakupan yang benar.' } });
          cur.status = 'CHANGES_REQUESTED'; cur.note = a.note || '';
          r.versions.push({ n: cur.n + 1, values: Object.assign({}, cur.values, a.values), ceiling: a.ceiling || cur.ceiling, status: 'PENDING_COUNTERPARTY', proposedBy: ctx.actor.party, at: now(), confirmations: {} });
          s.pitches[r.pitchId].timeline.push({ at: now(), by: ctx.actor.party, text: 'Koreksi menghasilkan ringkasan versi ' + (cur.n + 1) });
          return ok({ version: cur.n + 1 });
        });
      },
      confirmPartnership: function (ctx, a) {
        return mutate('confirmPartnership', ctx, a, function () {
          var r = s.partnerships[a.id];
          if (!r || r.parties.indexOf(ctx.actor.party) < 0 || !isMember(ctx.actor, ctx.actor.party)) return denied();
          if (!can(ctx.actor, ctx.actor.party, 'confirm')) return err('FORBIDDEN', 'Akun Anda tidak berwenang mengonfirmasi Kerja Sama.');
          var cur = last(r.versions);
          if (a.version !== cur.n) return err('STALE_VERSION', 'Versi ringkasan sudah berubah. Konfirmasi versi lama tidak berlaku.');
          cur.confirmations[ctx.actor.party] = { subset: a.subset.filter(function (f) { return cur.ceiling.indexOf(f) >= 0; }), at: now() };
          if (r.parties.every(function (p) { return cur.confirmations[p]; })) cur.status = 'CONFIRMED';
          s.pitches[r.pitchId].timeline.push({ at: now(), by: ctx.actor.party, text: 'Mengonfirmasi ringkasan versi ' + cur.n });
          return ok({ status: cur.status });
        });
      },
      declinePartnership: function (ctx, a) {
        return mutate('declinePartnership', ctx, a, function () {
          var r = s.partnerships[a.id];
          if (!r || r.parties.indexOf(ctx.actor.party) < 0) return denied();
          last(r.versions).status = 'DECLINED';
          return ok();
        });
      },
      restrictField: function (ctx, a) {
        return mutate('restrictField', ctx, a, function () {
          var r = s.partnerships[a.id];
          if (!r || r.parties.indexOf(ctx.actor.party) < 0) return denied();
          r.restrictions.push({ field: a.field, by: ctx.actor.party, at: now() });
          return ok();
        });
      },
      requestRelationshipReview: function (ctx, a) {
        return mutate('requestRelationshipReview', ctx, a, function () {
          var r = s.partnerships[a.id];
          if (!r || r.parties.indexOf(ctx.actor.party) < 0) return denied();
          r.contested = true;
          return ok();
        });
      },
      /* organization review */
      decideReview: function (ctx, a) {
        return mutate('decideReview', ctx, a, function () {
          var r = s.reviews[a.id];
          if (!r || !reviewerOf(ctx.actor)) return denied();
          if (r.state !== 'QUEUED') return err('INVALID_STATE', 'Item ini sudah diputuskan.');
          r.state = a.approve ? 'APPROVED' : 'RETURNED'; r.reason = a.reason || null;
          if (r.kind === 'PUBLICATION') {
            var i = inv(r.ref);
            i.reviewPending = false;
            if (a.approve) { i.published = r.version; i.status = 'PUBLISHED'; }
          } else {
            var p = s.pitches[r.ref];
            p.status = a.approve ? 'SUBMITTED' : 'WITHDRAWN'; p.version += 1;
            p.timeline.push({ at: now(), by: ctx.actor.party, text: a.approve ? 'Lolos tinjauan organisasi' : 'Dikembalikan tinjauan organisasi' });
            if (a.approve) notify(p.recipient, 'Pitching baru', p.id);
          }
          return ok();
        });
      },
      setFlag: function (name, value) {
        if (name === 'orgReview' && !value) {
          var pending = Object.keys(s.reviews).filter(function (k) { return s.reviews[k].state === 'QUEUED'; });
          if (pending.length) return err('PENDING_REVIEW_ITEMS', 'Selesaikan ' + pending.length + ' item tinjauan sebelum mematikan kemampuan ini.');
        }
        s.flags[name] = value; emit();
        return ok();
      },
      /* privacy and reports */
      report: function (ctx, a) {
        return mutate('report', ctx, a, function () {
          if (!(a.reason || '').trim()) return err('VALIDATION', 'Tuliskan alasan laporan.', { fields: { reason: 'Alasan wajib diisi.' } });
          var id = nextId('rp');
          s.reports.push({ id: id, by: ctx.actor.party, object: a.object, reason: a.reason, state: 'DITERIMA', at: now() });
          return ok({ id: id });
        });
      },
      privacyRequest: function (ctx, a) {
        return mutate('privacyRequest', ctx, a, function () {
          var id = nextId('pv');
          s.privacy.push({ id: id, by: ctx.actor.party, kind: a.kind, state: 'DITERIMA', at: now() });
          return ok({ id: id });
        });
      },
      setPrefs: function (ctx, a) {
        var acc = s.accounts[ctx.actor.account];
        Object.assign(acc, a); emit();
        return ok();
      },
      /* demo clock and fault switches */
      setClock: function (t) {
        s.clock = iso(ms(t));
        Object.keys(s.proposals).forEach(function (k) { expireIfDue(s.proposals[k]); });
        emit();
      },
      setVariant: function (name, on) {
        if (on) s.variants[name] = true; else delete s.variants[name];
        if (name === 'gap') { s.requests['sr-f01'].budget.min = on ? null : '20000'; s.requests['sr-f01'].budget.max = on ? null : '30000'; }
        if (name === 'scan') last(s.documents['doc-f01'].versions).extraction = on ? 'NEEDS_MANUAL_INPUT' : 'SUCCEEDED';
        emit();
      },
      setFault: function (name, value) { if (value) s.faults[name] = value; else delete s.faults[name]; emit(); }
    };

    Object.defineProperty(op, 'state', { get: function () { return s; } });
    return Object.assign(op, {
      replace: function (next) { s = next; emit(); },
      subscribe: function (fn) { listeners.push(fn); return function () { listeners = listeners.filter(function (l) { return l !== fn; }); }; },
      evaluate: evaluate, activeTargets: activeTargets, sourceOf: sourceOf, pubV: pubV, pitchFor: pitchFor, openProposal: openProposal, latestProposal: latestProposal,
      activeMeeting: activeMeeting, partnershipOf: partnershipOf, effectiveFields: effectiveFields, publicRelationships: publicRelationships, ics: ics, isMember: isMember, can: can, last: last
    });
  }

  /* ---------- repeatable scripted states: presets, previews and journey checks ---------- */
  var RANI = { account: 'rani', party: 'p-rani' }, MITRA_A = { account: 'mitraA', party: 'p-a' }, BIMA = { account: 'bima', party: 'p-dcm' }, INVESTOR_B = { account: 'investorB', party: 'p-b' };
  function submitF01(svc) {
    var source = { type: 'SUPPORT_REQUEST', id: 'sr-f01' };
    var pre = svc.preflight({ actor: RANI }, { source: source, opportunityId: 'A1' });
    return svc.submitPitch({ actor: RANI, key: 'seed-f01' }, { source: source, opportunityId: 'A1', token: pre.token, brief: svc.templateBrief({ source: source, opportunityId: 'A1' }), files: [{ docId: 'doc-f01', version: 1 }] }).pitchId;
  }
  function pitchVersion(svc, id) { return svc.state.pitches[id].version; }
  var revisionItems = [
    { category: 'Anggaran', question: 'Apakah biaya pilot sudah mencakup pengujian di dua lokasi?', reason: 'Kami perlu memastikan cakupan biaya sebelum menyiapkan uji.', required: true, due: '2026-11-09', expect: 'Rincian biaya per lokasi' },
    { category: 'Fitur', question: 'Kapan kapasitas 20 L/jam direncanakan tersedia?', reason: 'Membantu kami menyusun tahap uji berikutnya.', required: false, due: null, expect: 'Perkiraan waktu' }
  ];
  function seedSubmitted(svc) { var id = submitF01(svc); svc.beginReview({ actor: MITRA_A }, { pitchId: id }); return id; }
  function seedRevision(svc) {
    var id = seedSubmitted(svc);
    svc.requestRevision({ actor: MITRA_A }, { pitchId: id, expected: pitchVersion(svc, id), items: revisionItems });
    return id;
  }
  function seedApproved(svc) {
    var id = seedSubmitted(svc);
    svc.decide({ actor: MITRA_A }, { pitchId: id, decision: 'APPROVE', expected: pitchVersion(svc, id) });
    return id;
  }
  var defaultSlots = ['2026-11-04T09:00:00Z', '2026-11-04T11:00:00Z', '2026-11-04T13:00:00Z'];
  function seedProposal(svc) {
    var id = seedApproved(svc);
    svc.proposeSlots({ actor: MITRA_A }, { pitchId: id, slots: defaultSlots, minutes: 60, zone: 'Asia/Jakarta', agenda: 'Membahas rencana validasi enam bulan' });
    return id;
  }
  function seedMeetingDone(svc) {
    var id = seedApproved(svc);
    svc.proposeSlots({ actor: MITRA_A }, { pitchId: id, slots: ['2026-11-04T10:00:00Z', '2026-11-04T11:00:00Z'], minutes: 60, zone: 'Asia/Jakarta', agenda: 'Membahas rencana validasi enam bulan' });
    var pr = svc.openProposal(id), acc = svc.acceptSlot({ actor: RANI }, { proposalId: pr.id, slotId: 'slot1' });
    svc.setClock('2026-11-04T12:00:00Z');
    svc.recordOutcome({ actor: RANI }, { id: acc.meetingId, result: 'COMPLETED', note: 'Sepakat melanjutkan' });
    svc.recordOutcome({ actor: MITRA_A }, { id: acc.meetingId, result: 'COMPLETED', note: 'Sepakat melanjutkan' });
    return id;
  }
  function seedPartnership(svc) {
    var id = seedMeetingDone(svc);
    return svc.proposePartnership({ actor: RANI }, { pitchId: id, type: 'PROJECT', values: { name: 'ClearSpring dan Mitra A', type: 'Kerja sama proyek', scope: 'Validasi prototipe dua belas bulan', date: '1 Desember 2026', amount: 'USD 25.000' }, ceiling: ['name', 'type', 'scope', 'date', 'amount'], subset: ['name', 'type', 'scope', 'date', 'amount'] }).id;
  }
  function seedFunding(svc) {
    var source = { type: 'FUNDING_REQUEST', id: 'FRaise01' }, pre = svc.preflight({ actor: BIMA }, { source: source, opportunityId: 'B1' });
    return svc.submitPitch({ actor: BIMA, key: 'seed-fraise' }, { source: source, opportunityId: 'B1', token: pre.token, brief: svc.templateBrief({ source: source, opportunityId: 'B1' }), files: [{ docId: 'doc-f04', version: 1 }] }).pitchId;
  }
  var seeds = { submitted: seedSubmitted, revision: seedRevision, approved: seedApproved, proposal: seedProposal, meetingDone: seedMeetingDone, partnership: seedPartnership, funding: seedFunding };

  var api = { create: create, baseline: baseline, clone: clone, parseAmount: parseAmount, cmpDec: cmpDec, overlaps: overlaps, side: side, fitBounds: fitBounds, seeds: seeds, revisionItems: revisionItems, defaultSlots: defaultSlots, T0: T0, actors: { RANI: RANI, MITRA_A: MITRA_A, BIMA: BIMA, INVESTOR_B: INVESTOR_B } };
  root.TemuRisetDomain = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
