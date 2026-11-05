// Rendered-UI journey walker. Paste into the console of Main.dc.html (or the Browser pane) and await window.walk().
// It clicks real buttons and types into real fields. It proves UI behavior in this fictional demo only.
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const app = () => window.TemuRisetApp;
  const page = () => document.body.innerText.replace(/\u00a0/g, ' ');
  const log = [];
  function all() { return [...document.querySelectorAll('button, a, summary, [role=tab]')]; }
  function find(label) {
    const hit = all().filter((b) => b.innerText.trim() === label);
    return hit[hit.length - 1] || all().find((b) => b.innerText.trim().startsWith(label));
  }
  async function click(label, first) {
    const b = first ? all().find((x) => x.innerText.trim() === label) : find(label);
    if (!b) throw new Error('Tidak ada kontrol: ' + label);
    b.click();
    await sleep(720);
  }
  function field(label) {
    const l = [...document.querySelectorAll('label')].find((x) => x.innerText.trim().replace(/\s*\(wajib\)$/, '').startsWith(label));
    if (!l) throw new Error('Tidak ada field: ' + label);
    return document.getElementById(l.htmlFor);
  }
  function type(label, value) {
    const el = field(label), proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
    el.dispatchEvent(new Event(el.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
    return sleep(40);
  }
  async function choose(label, scope) {
    const l = [...document.querySelectorAll((scope ? scope + ' ' : '') + 'label')].find((x) => x.innerText.includes(label));
    if (!l) throw new Error('Tidak ada pilihan: ' + label);
    l.querySelector('input').click();
    await sleep(60);
  }
  async function start(name) { await click(name); await sleep(150); }
  async function asAccount(id, party) {
    const sel = [...document.querySelectorAll('select')].find((s) => [...s.options].some((o) => o.value === 'mitraA'));
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(sel, id);
    sel.dispatchEvent(new Event('change', { bubbles: true }));
    await sleep(120);
    if (party) { app().ui.partyId = party; app().svc.setVariant('__touch', false); await sleep(120); }
  }
  function has(id, snippet) { log.push([page().includes(snippet) ? 'PASS' : 'FAIL', id, snippet]); }
  function hasNot(id, snippet) { log.push([!page().includes(snippet) ? 'PASS' : 'FAIL', id, 'tidak ada: ' + snippet]); }
  function eq(id, a, b) { log.push([a === b ? 'PASS' : 'FAIL', id, String(a) + ' = ' + String(b)]); }
  function openDemo() { const d = document.querySelector('.tr-controls details'); if (d && !d.open) d.querySelector('summary').click(); return sleep(60); }
  const st = () => app().svc.state;

  async function j01() {
    await start('J01 Pitching F01');
    has('J01 home gap first', 'Lengkapi kisaran biaya pilot');
    await click('Temukan Investor/Mitra');
    await click('Lihat kecocokan');
    has('J01 three reasons area', 'Perlu konfirmasi');
    has('J01 gap visible', 'Kisaran biaya pilot untuk kebutuhan ini belum diisi');
    await click('Lengkapi kisaran biaya');
    await type('Batas bawah', '-1'); await click('Simpan dan kembali ke pemeriksaan');
    has('J01 AC16 error summary', 'Masih ada yang perlu diperbaiki');
    eq('J01 error focus', document.activeElement.className.includes('tr-error-summary'), true);
    await type('Batas bawah', '20000'); await type('Batas atas', '30000');
    await click('Simpan dan kembali ke pemeriksaan');
    has('J01 returned to matches', 'Kecocokan kuat');
    await click('Siapkan pitching', true);
    has('J01 preflight ready', 'Siap dikirim');
    has('J01 provided not reviewed', 'Disediakan, belum diperiksa');
    has('J01 later work', 'Untuk tahap berikutnya');
    await click('Kirim pitching');
    has('J01 file must be chosen', 'Pilih berkas yang ingin dibagikan');
    await choose('Bagikan Laporan uji fungsi'); await sleep(30);
    await openDemo();
    await click('F01-STALE: ubah versi mandat');
    has('J01 stale conflict', 'Versi sudah berubah');
    has('J01 stale retains brief', 'Draf Anda masih aman');
    await click('Periksa ulang');
    hasNot('J01 stale cleared', 'Draf Anda masih aman');
    await choose('F01-TIMEOUT');
    await click('Kirim pitching');
    has('J01 lost response', 'Status pengiriman belum diketahui');
    eq('J01 committed once', Object.keys(st().pitches).length, 1);
    await click('Coba kirim lagi');
    has('J01 replay notice', 'sudah tercatat sebelumnya');
    eq('J01 still one pitch', Object.keys(st().pitches).length, 1);
    has('J01 inventor waits', 'Menunggu pihak lain');
    await asAccount('mitraA');
    has('J01 same case as recipient', 'Menunggu Anda');
    await click('Mulai tinjau');
    has('J01 under review', 'Sedang ditinjau');
    await asAccount('stafA');
    has('AC04 view only', 'Akun Anda hanya dapat melihat');
    await asAccount('lain');
    has('AC48 denied', 'Anda belum memiliki akses');
    hasNot('AC48 no title leak', 'ClearSpring');
  }
  async function j03() {
    await asAccount('mitraA');
    await click('Minta revisi');
    await click('Kirim permintaan revisi');
    has('J03 waits for inventor', 'Menunggu jawaban revisi');
    await asAccount('rani');
    has('J03 inventor turn', 'Jawab permintaan revisi');
    await click('Kirim ulang pitching');
    has('J03 required blocks', 'Masih ada yang perlu diperbaiki');
    const radios = [...document.querySelectorAll('.tr-revision')];
    radios[0].querySelectorAll('input[type=radio]')[2].click(); await sleep(50);
    const ta = radios[0].querySelector('textarea');
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, 'Biaya baru mencakup satu lokasi.');
    ta.dispatchEvent(new Event('input', { bubbles: true })); await sleep(40);
    has('J03 unsaved', 'Belum tersimpan');
    await click('Simulasikan unggahan gagal').catch(() => {});
    await choose('Simulasikan unggahan gagal');
    await click('Unggah versi baru');
    has('J03 failed upload keeps answers', 'Jawaban Anda tidak berubah');
    eq('J03 answer retained', document.querySelector('.tr-revision textarea').value, 'Biaya baru mencakup satu lokasi.');
    await click('Unggah versi baru');
    await choose('Laporan uji fungsi ClearSpring · versi 2');
    await click('Kirim ulang pitching'); await sleep(450);
    has('J03 second submission', 'submisi 2');
    const id = Object.keys(st().pitches)[0], p = st().pitches[id];
    eq('J03 two submissions', p.submissions.length, 2);
    eq('J03 new file version', p.submissions[1].files[0].version, 2);
    eq('J03 first snapshot version kept', p.submissions[0].files[0].version, 1);
    await asAccount('mitraA');
    await click('Revisi (1)');
    await click('Terima jawaban');
    has('J03 item accepted', 'Diterima');
    await click('Ringkasan');
    await click('Setujui untuk diskusi');
    has('J03 approval copy', 'Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.');
    const dlg = document.querySelector('dialog[open]');
    [...dlg.querySelectorAll('button')].find((b) => b.innerText.includes('Setujui')).click(); await sleep(500);
    has('J03 approved', 'Disetujui untuk diskusi');
    eq('J03 no relationship', Object.keys(st().partnerships).length, 0);
  }
  async function j04() {
    await click('Jadwal');
    has('J04 compose', 'Usulkan waktu pertemuan');
    await click('Kirim usulan waktu');
    has('J04 pending other', 'Menunggu pihak lain memilih waktu');
    await asAccount('rani');
    has('J04 local time Jakarta', '16.00');
    has('J04 other zone Makassar', '17.00');
    document.querySelectorAll('.tr-slots input[type=radio]')[0].click(); await sleep(60);
    has('J04 selection not booked', 'Dipilih, belum dikonfirmasi');
    eq('J04 no meeting yet', Object.keys(st().meetings).length, 0);
    await click('Konfirmasi waktu'); await sleep(350);
    has('J04 conflict recoverable', 'bentrok');
    has('J04 agenda kept', 'Membahas rencana validasi enam bulan');
    await click('Usulkan waktu lain');
    has('J04 alternatives prefill', 'Usulkan waktu lain');
    await click('Kirim usulan waktu');
    await asAccount('mitraA');
    document.querySelectorAll('.tr-slots input[type=radio]')[1].click(); await sleep(60);
    await click('Konfirmasi waktu'); await sleep(350);
    has('J04 confirmed', 'Pertemuan dikonfirmasi');
    eq('J04 one meeting', Object.values(st().meetings).filter((m) => m.state === 'CONFIRMED').length, 1);
    log.push([document.body.textContent.includes('DTSTART:20261104T100000Z') ? 'PASS' : 'FAIL', 'J04 ics utc', 'DTSTART:20261104T100000Z']);
    await click('Usulkan jadwal pengganti');
    await click('Kirim usulan waktu');
    has('J04 old meeting stays', 'Pertemuan dikonfirmasi');
    eq('J04 meeting still confirmed', Object.values(st().meetings).filter((m) => m.state === 'CONFIRMED').length, 1);
    const pr = Object.values(st().proposals).find((x) => x.state === 'OPEN');
    app().svc.cancelProposal({ actor: { account: 'mitraA', party: 'p-a' } }, { proposalId: pr.id }); await sleep(100);
  }
  async function j05() {
    await openDemo();
    await click('4 Nov 12.00');
    has('J04 attendance not auto', 'Catat hasil pertemuan');
    await click('Catat hasil pertemuan');
    await asAccount('rani');
    await click('Catat hasil pertemuan');
    has('J05 meeting done panel', 'Pertemuan selesai');
    hasNot('J05 no compose after done', 'Kirim usulan waktu');
    has('J05 next propose', 'Usulkan ringkasan Kerja Sama');
    await click('Usulkan ringkasan');
    await click('Kirim ringkasan versi 1');
    has('J05 pending', 'Menunggu Mitra A mengonfirmasi versi 1');
    hasNot('J05 no mutual badge', 'Dikonfirmasi kedua pihak');
    await asAccount('mitraA');
    await click('Minta perubahan');
    await type('Cakupan yang benar', 'Validasi prototipe enam bulan');
    const dlg = document.querySelector('dialog[open]');
    [...dlg.querySelectorAll('button')].find((b) => b.innerText.includes('Buat versi 2')).click(); await sleep(500);
    has('J05 v2 no inherited', 'Konfirmasi lama tidak berlaku lagi');
    await choose('Jumlah dana', 'main');
    await click('Konfirmasi versi 2');
    await asAccount('rani');
    has('J05 v2 pending for inventor', 'Periksa dan konfirmasi versi 2');
    await click('Konfirmasi versi 2');
    has('J05 mutual', 'Dikonfirmasi kedua pihak');
  }

  async function j05b() {
    await click('Lihat profil publik');
    has('J05 public scope', 'Validasi prototipe enam bulan');
    hasNot('J05 amount private', 'USD 25.000');
    await asAccount('lain');
    has('J05 public visible to stranger', 'Validasi prototipe enam bulan');
    hasNot('J05 stranger no amount', 'USD 25.000');
    await asAccount('rani');
    await click('Kembali');
    await click('Sembunyikan', true);
    has('J05 narrowing notice', 'disembunyikan dari tampilan publik');
    has('J05 restricted row', 'Disembunyikan');
  }
  async function j02() {
    await start('J02 Satu raise');
    has('J02 one card', 'Demo Circular Materials Ltd');
    has('J02 two links', '2 inovasi terkait');
    has('J02 target', 'USD 500.000');
    has('J02 contribution', 'USD 50.000–100.000');
    await click('Temukan investor');
    has('J02 overlap reason', 'bukan dengan seluruh target');
    await click('Siapkan pitching', true);
    has('J02 preflight', 'Siap dikirim');
    await click('Kirim pitching'); await sleep(450);
    const id = Object.keys(st().pitches)[0];
    has('J02 sent', 'Pitching terkirim');
    await asAccount('investorB');
    await click('Jelajahi');
    has('J02 queue on discover', 'Putuskan pitching ini');
    await choose('Pendanaan Perusahaan', 'main');
    await sleep(150);
    eq('J02 funding result once', [...document.querySelectorAll('article.tr-card')].length, 1);
    await asAccount('bima', 'p-dcm');
    window.location.hash = '#/funding-requests/FRaise01'; await sleep(200);
    await click('Siapkan pitching');
    has('J02 duplicate via second link', 'Pitching untuk permintaan dan mandat ini sudah ada');
    await click('Buka pitching yang ada');
    eq('J02 same pitch', location.hash.includes(id), true);
    window.location.hash = '#/funding-requests/FRaise01/edit'; await sleep(200);
    await type('Target Pendanaan', '600000');
    await click('Simpan versi 2');
    has('J02 new version', 'Versi 2');
    eq('J02 snapshot keeps target', st().pitches[id].submissions[0].funding.target, '500000');
    await start('J02 Satu raise');
    await openDemo(); await choose('Perusahaan belum didirikan');
    has('J02 proposed entity', 'Perusahaan belum didirikan');
    await click('Temukan investor');
    has('J02 B1 blocked hidden in excluded', 'tidak direkomendasikan');
    has('J02 B2 accepts', 'Diskusi tim pra-pendirian');
  }
  async function variants() {
    await start('DIRECT-APPROVAL');
    await click('Setujui untuk diskusi', true); await sleep(60);
    [...document.querySelector('dialog[open]').querySelectorAll('button')].find((b) => b.innerText.includes('Setujui')).click(); await sleep(500);
    has('DIRECT approved', 'Disetujui untuk diskusi');
    await click('Revisi (0)').catch(() => click('Revisi'));
    hasNot('DIRECT no revision after approval', 'Kirim permintaan revisi');
    await start('SCHED-72H');
    has('SCHED72 open', 'Pilih waktu pertemuan');
    await click('5 Nov 08.00');
    has('SCHED72 age expiry', 'kedaluwarsa setelah 72 jam');
    has('SCHED72 pitch still approved', 'Disetujui untuk diskusi');
    await start('J04 Jadwal');
    await click('Kirim usulan waktu');
    await click('4 Nov 13.00');
    has('Past expiry', 'Semua waktu pada usulan sebelumnya sudah lewat');
    await start('F01-DENIED');
    has('DENIED copy', 'Anda belum memiliki akses');
    hasNot('DENIED no title', 'ClearSpring');
    await start('Akun kosong');
    has('EMPTY start actions', 'Belum ada yang perlu dikerjakan');
    await click('Inovasi Saya');
    has('EMPTY list', 'Belum ada inovasi yang terbit');
    await click('Tambah inovasi', true);
    await click('Simpan dan lanjutkan');
    await click('Simpan dan lanjutkan');
    await click('Simpan dan lihat pratinjau');
    await click('Terbitkan versi 1'); await sleep(450);
    has('EDITOR publish validation', 'Masih ada yang perlu diperbaiki');
    await type('Judul inovasi', 'Inovasi Uji');
    await choose('F01-GAP').catch(() => {});
  }
  async function editor() {
    await start('J01 Pitching F01');
    await click('Inovasi Saya');
    await click('Buka inovasi');
    await click('Ubah inovasi');
    await openDemo(); await choose('Gagal simpan draf');
    await type('Judul inovasi', 'ClearSpring Baru');
    await click('Simpan dan lanjutkan');
    has('EDITOR failed save', 'Gagal menyimpan');
    eq('EDITOR retained', field('Judul inovasi').value, 'ClearSpring Baru');
    await click('Coba lagi');
    has('EDITOR saved', 'Tersimpan di demo ini');
    await click('Simpan dan lanjutkan');
    has('EDITOR step2 current planned', 'Direncanakan');
    const seen = []; const offDocs = app().svc.subscribe(() => { Object.values(st().documents).forEach((d) => { const f = d.versions[d.versions.length - 1].file; if (seen[seen.length - 1] !== f) seen.push(f); }); });
    await click('Unggah berkas contoh'); await sleep(2400); offDocs();
    eq('EDITOR upload order', ['UPLOADING', 'QUARANTINED', 'AVAILABLE'].every((x) => seen.includes(x)), true);
    has('EDITOR available', 'Aman dan tersedia');
    await click('Ubah draf dari sesi lain');
    await click('Simpan draf');
    has('EDITOR conflict', 'Versi sudah berubah');
    await click('Muat versi terbaru');
    await click('Simpan dan lanjutkan');
    await click('Simpan dan lihat pratinjau');
    has('EDITOR public preview', 'Tampilan publik');
    await click('Terbitkan versi 2'); await sleep(450);
    has('EDITOR published', 'Versi 2 sudah terbit');
  }
  async function comps() {
    await start('J02 Satu raise');
    await openDemo(); await choose('Pendanaan Perusahaan', '.tr-controls');
    has('COMP funding off', 'tidak aktif pada komposisi ini');
    hasNot('COMP no edit', 'Ubah permintaan');
    await start('J01 Pitching F01');
    await openDemo(); await choose('Tinjauan organisasi');
    await asAccount('bima', 'p-dcm');
    await click('Profil');
    await click('Antrean tinjauan');
    has('COMP review empty', 'Antrean kosong');
    await start('J02 Satu raise');
    await openDemo(); await choose('Tinjauan organisasi');
    await click('Temukan investor');
    await click('Siapkan pitching', true);
    await click('Kirim pitching'); await sleep(450);
    has('COMP gated', 'Menunggu tinjauan organisasi');
    await openDemo(); await choose('Tinjauan organisasi');
    has('COMP cannot disable pending', 'Selesaikan 1 item');
    await click('Beranda').catch(() => click('Profil'));
    window.location.hash = '#/workspace/review-queue'; await sleep(200);
    await click('Setujui versi ini');
    has('COMP approved', 'Versi ini disetujui');
    await start('J01 Pitching F01');
    await openDemo();
    await type('Ringkasan otomatis', 'down'); await sleep(60);
  }

  // Reports horizontal overflow on every reachable route at the current viewport width.
  async function audit() {
    const id = Object.keys(st().pitches)[0], rel = Object.keys(st().partnerships)[0], out = [];
    const hashes = ['home', 'inventions', 'inventions/inv-f01', 'inventions/inv-f01/edit?step=1', 'inventions/inv-f01/edit?step=2', 'inventions/inv-f01/edit?step=3', 'inventions/inv-f01/edit?step=4', 'discover', 'support-requests', 'support-requests/sr-f01', 'funding-requests/FRaise01', 'partners/p-a', 'partners/p-e', 'matches?source=sr-f01', 'pitches/new?source=sr-f01&target=A1', 'pitches', 'profiles/p-rani', 'settings'];
    if (id) ['ringkasan', 'revisi', 'dokumen', 'diskusi', 'jadwal', 'riwayat'].forEach((t) => hashes.push('pitches/' + id + '?tab=' + t));
    if (rel) hashes.push('partnerships/' + rel);
    for (const h of hashes) {
      window.location.hash = '#/' + h; await sleep(140);
      const w = document.documentElement.clientWidth, bad = [...document.querySelectorAll('body *')].filter((el) => {
        if (el.closest('.tr-sr') || el.classList.contains('tr-sr') || el.tagName === 'OPTION') return false;
        const r = el.getBoundingClientRect(); return r.width > 0 && r.right > w + 1;
      });
      if (document.documentElement.scrollWidth > w + 1 || bad.length) out.push([h, document.documentElement.scrollWidth, bad.slice(0, 2).map((e) => e.tagName + '.' + String(e.className).slice(0, 40))]);
    }
    return { width: document.documentElement.clientWidth, font: getComputedStyle(document.documentElement).fontSize, routes: hashes.length, overflow: out };
  }

  // Rendered checks: names, duplicate ids, one h1, text contrast against the nearest opaque background, target size.
  function rgb(c) { const m = c.match(/[\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2], a: m[3] === undefined ? 1 : m[3] }; }
  function lum(c) { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); }
  function ratio(a, b) { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function bgOf(el) { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.a >= 1) return c; } return { r: 255, g: 255, b: 255, a: 1 }; }
  function scan() {
    const out = { unnamed: [], unlabelled: [], dupIds: [], h1: document.querySelectorAll('h1').length, lowContrast: [], smallTargets: [], under44: 0 };
    document.querySelectorAll('button, a[href], summary').forEach((b) => {
      if (!b.offsetParent || b.closest('details:not([open]) > .tr-disclosure__body')) return;
      if (!(b.innerText.trim() || b.getAttribute('aria-label'))) out.unnamed.push(b.outerHTML.slice(0, 70));
      const r = b.getBoundingClientRect(), inline = b.tagName === 'A' && getComputedStyle(b).display === 'inline';
      if (!inline && (r.height < 24 || r.width < 24)) out.smallTargets.push(b.innerText.slice(0, 24));
      if (b.tagName === 'BUTTON' && r.height < 44 && !b.closest('.tr-tabs__list')) out.under44 += 1;
    });
    document.querySelectorAll('input, select, textarea').forEach((f) => { if (f.type !== 'hidden' && !(f.labels && f.labels.length) && !f.getAttribute('aria-label')) out.unlabelled.push(f.id); });
    const ids = {}; document.querySelectorAll('[id]').forEach((e) => { ids[e.id] = (ids[e.id] || 0) + 1; }); out.dupIds = Object.keys(ids).filter((k) => ids[k] > 1);
    document.querySelectorAll('main *, .tr-bar *, .tr-tabbar *').forEach((el) => {
      if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) || !el.offsetParent || el.closest('.tr-sr')) return;
      const cs = getComputedStyle(el), fg = rgb(cs.color), v = ratio(fg, bgOf(el)), size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 700;
      if (v < ((size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5)) out.lowContrast.push(el.tagName + ' ' + el.textContent.trim().slice(0, 24) + ' ' + v.toFixed(2));
    });
    return out;
  }
  async function a11y() {
    const id = Object.keys(st().pitches)[0], rel = Object.keys(st().partnerships)[0], merged = {}, h1 = {};
    const hashes = ['home', 'inventions', 'inventions/inv-f01', 'inventions/inv-f01/edit?step=1', 'inventions/inv-f01/edit?step=2', 'inventions/inv-f01/edit?step=4', 'discover', 'support-requests/sr-f01', 'funding-requests/FRaise01', 'partners/p-a', 'matches?source=sr-f01', 'pitches/new?source=sr-f01&target=A1', 'pitches', 'profiles/p-rani', 'settings'];
    if (id) ['ringkasan', 'revisi', 'dokumen', 'diskusi', 'jadwal', 'riwayat'].forEach((t) => hashes.push('pitches/' + id + '?tab=' + t));
    if (rel) hashes.push('partnerships/' + rel);
    for (const h of hashes) {
      window.location.hash = '#/' + h; await sleep(130);
      const r = scan();
      if (r.h1 !== 1) h1[h] = r.h1;
      ['unnamed', 'unlabelled', 'dupIds', 'lowContrast', 'smallTargets'].forEach((k) => { if (r[k].length) (merged[k] = merged[k] || {})[h] = r[k].slice(0, 3); });
      merged.under44 = (merged.under44 || 0) + r.under44;
    }
    return { routes: hashes.length, h1, merged };
  }

  async function more() {
    // S01 persona switch, S18 settings, S08/S09 mandates, other fixtures, reject, revoke, tasks, AI states.
    await start('Akun kosong');
    window.location.hash = '#/start'; await sleep(200);
    await choose('Saya berinvestasi', 'main'); await sleep(100);
    has('S01 labelled demo account', 'Akun fiktif yang sudah ada');
    has('S01 enter label partner', 'Masuk sebagai Peserta P');
    await click('Masuk sebagai Peserta P');
    has('S01 partner lands on Jelajahi', 'Jelajahi');
    has('AC02 partner no fake org needed copy', 'Mitra A');
    await click('Kebutuhan/Mandat');
    has('S08 own mandates', 'Validasi prototipe enam bulan');
    await click('Ubah mandat', true);
    await type('Syarat baru', 'Kesiapan lokasi uji'); await click('Tambah syarat');
    has('AC27 narrative row', 'Kesiapan lokasi uji');
    await click('Tinjau mandat');
    has('S09 review before activate', 'Aktifkan versi 2');
    await click('Aktifkan versi 2'); await sleep(450);
    has('S09 activated new version', 'Mandat aktif sebagai versi 2');
    eq('AC27 narrative unknown', app().svc.evaluate({ type: 'SUPPORT_REQUEST', id: 'sr-f01' }, 'A1').rows.find((r) => r.field === 'narrative').result, 'UNKNOWN');
    await asAccount('dewi');
    window.location.hash = '#/matches?source=sr-f02'; await sleep(500);
    has('F02 needs confirmation', 'Perlu konfirmasi');
    has('F02 authority unknown copy', 'Ini bukan berarti wewenang tidak ada');
    hasNot('F02 no invented money', 'USD 20.000');
    await asAccount('galih');
    window.location.hash = '#/matches?source=sr-f03'; await sleep(500);
    has('F03 not positive', 'tidak direkomendasikan');
    await click('1 mandat tidak direkomendasikan').catch(() => {});
    log.push([document.body.textContent.includes('Fitur baru direncanakan') ? 'PASS' : 'FAIL', 'F03 planned not current', 'Fitur baru direncanakan']);
    await asAccount('sinta');
    window.location.hash = '#/matches?source=sr-f06'; await sleep(500);
    has('F06 mentoring route', 'Pendampingan ide tahap awal');
    await asAccount('rani');
    window.location.hash = '#/partners/p-e'; await sleep(200);
    has('AC22 source reported', 'Dilaporkan sumber');
    has('AC24 external not a pitch', 'bukan pitching yang terkirim');
    await asAccount('mitraA');
    await click('Jelajahi');
    has('S03 curated label', 'Pilihan kurator demo');
    await type('Cari', 'water'); await sleep(100);
    has('FR10 English search', 'ClearSpring');
    await type('Cari', 'tidakadahasil'); await sleep(100);
    has('AC29 empty explains', 'Syarat wajib tidak kami longgarkan');
    await click('Hapus semua filter');
    await start('J03 Revisi');
    await click('Tolak'); await sleep(50);
    const dlg = document.querySelector('dialog[open]');
    [...dlg.querySelectorAll('button')].find((b) => b.innerText.trim() === 'Tolak pitching').click(); await sleep(500);
    has('FR14 reject needs reason', 'Alasan wajib diisi');
    eq('FR14 reject stays in dialog', !!document.querySelector('dialog[open]'), true);
    await type('Alasan singkat', 'Di luar cakupan'); await sleep(40);
    [...document.querySelector('dialog[open]').querySelectorAll('button')].find((b) => b.innerText.trim() === 'Tolak pitching').click(); await sleep(500);
    has('FR14 rejected', 'Ditolak');
    await asAccount('rani');
    has('FR14 private reason for sender', 'Di luar cakupan');
    await start('J04 Jadwal');
    await click('Dokumen');
    await click('Unduh versi ini');
    has('Doc download recipient', 'Unduhan demo disiapkan');
    await asAccount('rani');
    await click('Dokumen');
    await click('Cabut akses'); await sleep(50);
    [...document.querySelector('dialog[open]').querySelectorAll('button')].find((b) => b.innerText.trim() === 'Cabut akses').click(); await sleep(150);
    has('AC65 recall limit stated', 'salinan yang sudah diunduh tidak dapat ditarik');
    await asAccount('mitraA');
    await click('Dokumen');
    has('Doc denied after revoke', 'Dokumen terbatas');
    hasNot('Doc title hidden', 'Laporan uji fungsi ClearSpring');
    [...document.querySelectorAll('[role=tab]')].find((b) => b.innerText.trim() === 'Diskusi').click(); await sleep(150);
    await click('Kirim pesan');
    has('Message validation', 'Pesan belum diisi');
    await type('Tulis pesan', 'Selamat pagi'); await click('Kirim pesan');
    has('Message sent', 'Selamat pagi');
    await type('Tugas baru', 'Kirim rincian biaya'); await click('Tambah tugas');
    has('Post-approval clarification as task', 'Kirim rincian biaya');
    await click('Tandai selesai');
    has('Task done', 'Selesai');
    await start('J01 Pitching F01');
    await openDemo(); await choose('F01-GAP');
    await type('Ringkasan otomatis', 'down');
    window.location.hash = '#/pitches/new?source=sr-f01&target=A1'; await sleep(250);
    await click('Ringkas brief dari fakta yang ada'); await sleep(300);
    has('AI down keeps template', 'Ringkasan otomatis tidak tersedia');
    eq('AI down brief kept', field('Brief pitching').value.includes('Masalah:'), true);
    await type('Ringkasan otomatis', 'off'); await sleep(80);
    hasNot('AI off manual only', 'Ringkas brief dari fakta yang ada');
    await click('Atur ulang demo');
    has('Reset to start', 'Selamat datang di TemuRiset');
    eq('Reset clears case', Object.keys(st().pitches).length, 0);
  }
  // Each artboard opened alone must render from its own preview state.
  async function boards() {
    const names = ['DemoControls', 'Start', 'Home', 'Discover', 'Inventions', 'Invention', 'Editor', 'Support', 'Funding', 'Partner', 'Opportunity', 'Matches', 'Preflight', 'Pitches', 'Workspace', 'Revisions', 'Schedule', 'Partnership', 'Profile', 'ReviewQueue', 'Settings'], out = {};
    for (const n of names) {
      const f = document.createElement('iframe'); f.style.cssText = 'width:1280px;height:900px;position:absolute;left:-2000px'; f.src = n + '.dc.html'; document.body.appendChild(f);
      const errors = []; await new Promise((r) => { f.onload = r; });
      f.contentWindow.addEventListener('error', (e) => errors.push(e.message));
      await sleep(900);
      const t = (f.contentDocument.body.innerText || '').trim().replace(/\s+/g, ' ');
      out[n] = { chars: t.length, head: t.slice(0, 46), errors };
      f.remove();
    }
    return out;
  }

  async function more2() {
    await start('J01 Pitching F01');
    await openDemo(); await choose('F01-GAP'); await choose('F01-SCAN'); await sleep(100);
    window.location.hash = '#/pitches/new?source=sr-f01&target=A1'; await sleep(300);
    has('F01-SCAN manual input', 'Perlu diisi manual');
    has('F01-SCAN file still available', 'Aman dan tersedia');
    has('F01-SCAN present passes', 'Terpenuhi');
    window.location.hash = '#/inventions/inv-f01/edit?step=2'; await sleep(300);
    await choose('Simulasikan berkas ditolak');
    await click('Unggah berkas contoh'); await sleep(2200);
    has('Upload rejected state', 'Ditolak saat pemeriksaan keamanan');
    await start('J04 Jadwal');
    await click('Kirim usulan waktu');
    await asAccount('rani');
    document.querySelectorAll('.tr-slots input[type=radio]')[1].click(); await sleep(80);
    await click('Konfirmasi waktu'); await sleep(300);
    const first = Object.values(st().meetings).find((m) => m.state === 'CONFIRMED');
    await click('Usulkan jadwal pengganti');
    await click('Kirim usulan waktu');
    eq('Replacement keeps old meeting', st().meetings[first.id].state, 'CONFIRMED');
    await asAccount('mitraA');
    has('Replacement visible with meeting', 'Ada usulan pengganti');
    document.querySelectorAll('.tr-slots input[type=radio]')[0].click(); await sleep(80);
    await click('Konfirmasi waktu'); await sleep(300);
    eq('Replacement cancels old atomically', st().meetings[first.id].state, 'CANCELLED');
    eq('One active meeting', Object.values(st().meetings).filter((m) => m.state === 'CONFIRMED').length, 1);
    await openDemo(); await choose('Adaptor kalender'); await sleep(100);
    has('Calendar on note', 'Adaptor kalender aktif dalam simulasi');
    await choose('Adaptor kalender'); await sleep(100);
    has('Calendar off fallback', 'Kalender luar tidak terhubung');
  }
  window.walk = async function (parts) {
    log.length = 0;
    await openDemo();
    for (const p of parts || ['j01', 'j03', 'j04', 'j05', 'j05b', 'j02', 'variants', 'editor', 'comps', 'more', 'more2']) {
      try { await ({ j01, j03, j04, j05, j05b, j02, variants, editor, comps, more, more2 })[p](); } catch (e) { log.push(['FAIL', p + ' berhenti', e.message]); break; }
    }
    return log.filter((x) => x[0] === 'FAIL').concat([['SUM', log.filter((x) => x[0] === 'PASS').length + ' pass', log.filter((x) => x[0] === 'FAIL').length + ' fail']]);
  };
  window.walkHelpers = { boards, a11y, audit, click, type, choose, has, hasNot, eq, asAccount, start, openDemo, log, sleep };
})();
