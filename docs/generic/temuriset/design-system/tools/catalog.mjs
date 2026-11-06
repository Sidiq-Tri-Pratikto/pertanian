// Component contracts and live demos. build.mjs writes each entry to
// project/components/<name>/README.md and preview.html, so one record stays the single source.
// Demo code runs in the preview frame with h, TR, F (format), X (fixtures), useState and S(label, child).

export const components = [
  {
    name: 'Button', group: 'Actions', height: 330,
    summary: 'One action, named by its effect; at most one primary per task region.',
    anatomy: 'Control (44 px comfortable minimum), optional icon or spinner, label, reason line when disabled.',
    provides: '`children`, `intent` primary | secondary | danger, `onClick`, `type`, `icon`, `busy` + `busyLabel`, `disabledReason`, `fullWidth`, `id`, `form`, `describedBy`.',
    states: 'Default, hover, pressed, focus, busy (repeat clicks ignored, `aria-busy`), disabled-with-reason (dashed boundary, readable label, reason beside it).',
    a11y: 'Native `<button>`, name from the visible label; Enter and Space work. Disabled uses `aria-disabled`, so it stays focusable and the reason is read through `aria-describedby`.',
    tokens: '`tr-comp-button-primary-*`, `tr-sys-color-action-*`, `tr-sys-color-disabled-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`, `tr-sys-motion-feedback`.',
    responsive: 'Labels wrap. Use `fullWidth` in narrow footers.',
    do: 'Say the effect: "Kirim pitching", "Setujui untuk diskusi", "Konfirmasi waktu".',
    dont: 'Do not write "OK" or "Lanjutkan" for a consequential action. Do not dim a disabled button with opacity or hide why it is disabled.',
    demo: `
  var busy = useState(false);
  function send() { busy[1](true); setTimeout(function () { busy[1](false); }, 1500); }
  return h(React.Fragment, null,
    S('Intent', h('div', { className: 'tr-row' },
      h(TR.Button, { intent: 'primary' }, 'Kirim pitching'),
      h(TR.Button, { intent: 'secondary' }, 'Lihat bukti'),
      h(TR.Button, { intent: 'danger' }, 'Tarik pitching'))),
    S('Busy (click it; repeat clicks are ignored)', h(TR.Button, { intent: 'primary', busy: busy[0], busyLabel: 'Mengirim\\u2026', onClick: send }, 'Kirim pitching')),
    S('Disabled with reason', h(TR.Button, { intent: 'primary', disabledReason: 'Jawab semua pertanyaan wajib terlebih dahulu.' }, 'Kirim ulang pitching')));`
  },
  {
    name: 'Link', group: 'Actions', height: 150,
    summary: 'Navigation by descriptive text, including contextual change links.',
    anatomy: 'Underlined text, optional hidden context, external-route icon with hidden note.',
    provides: '`href`, `children`, `external`, `context` (hidden text naming the field), `onClick` (in-page handling).',
    states: 'Default, hover, focus.',
    a11y: 'Native `<a>`. `context` makes "Ubah" read as "Ubah judul inovasi". External links announce "(membuka situs lain)".',
    tokens: '`tr-sys-color-link`.',
    responsive: 'Wraps inside running text.',
    do: 'Label an external route as an external route.',
    dont: 'Do not imply that opening an external application submitted an in-app pitch.',
    demo: `
  return h(React.Fragment, null,
    S('Ordinary', h(TR.Link, { href: '#bukti' }, 'Lihat bukti pendukung')),
    S('Contextual change link', h(TR.Link, { href: '#judul', context: 'judul inovasi' }, 'Ubah')),
    S('External route', h(TR.Link, { href: '#luar', external: true }, 'Formulir mitra di situs mereka')));`
  },
  {
    name: 'TextField', group: 'Inputs', height: 400,
    summary: 'Labelled single-line input for text, email and decimal values.',
    anatomy: 'Visible label, requiredness, hint, inline error, input, optional unit.',
    provides: '`label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `type` text | email | decimal, `prefix`, `suffix`, `id`, `name`, `autoComplete`.',
    states: 'Default, focus, invalid (2 px boundary plus text), filled.',
    a11y: '`<label for>`, `aria-describedby` joins hint and error, `aria-invalid` on error. Decimal uses `inputMode="decimal"` and stays text, so an empty value is never turned into zero.',
    tokens: '`tr-comp-field-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`.',
    responsive: 'Full width of its container; the unit stays beside the value.',
    do: 'Keep nonsecret input on error and show the unit next to the number.',
    dont: 'Do not use placeholder text as the label.',
    demo: `
  var a = useState('ClearSpring'), b = useState('20000'), c = useState('-1');
  return h(React.Fragment, null,
    h(TR.TextField, { label: 'Judul inovasi', hint: 'Antara 5 sampai 120 karakter.', required: true, value: a[0], onChange: a[1] }),
    h(TR.TextField, { label: 'Biaya minimum', type: 'decimal', prefix: 'USD', value: b[0], onChange: b[1] }),
    h(TR.TextField, { label: 'Biaya maksimum', type: 'decimal', prefix: 'USD', value: c[0], onChange: c[1], error: 'Biaya tidak boleh kurang dari 0.' }));`
  },
  {
    name: 'TextArea', group: 'Inputs', height: 340,
    summary: 'Labelled multiline answer that keeps its text through errors and retries.',
    anatomy: 'Label, hint, error, resizable area, optional character count.',
    provides: '`label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `rows`, `limit`, `id`.',
    states: 'Default, focus, invalid, over limit (text and colour).',
    a11y: 'Count is linked by `aria-describedby` and is not a live region, so typing is not announced key by key.',
    tokens: '`tr-comp-field-*`, `tr-sys-color-danger-text`.',
    responsive: 'Full width; the person can resize it vertically.',
    do: 'Size it to the expected answer. State the limit in the hint or count.',
    dont: 'Do not cut text at the limit; let the person edit it down.',
    demo: `
  var a = useState('Prototipe sudah berfungsi dengan kapasitas 10 L/jam.');
  return h(React.Fragment, null,
    h(TR.TextArea, { label: 'Ringkasan singkat', hint: 'Jangan masukkan informasi rahasia.', limit: 80, value: a[0], onChange: a[1] }),
    h(TR.TextArea, { label: 'Penjelasan', value: '', rows: 2, error: 'Tulis penjelasan singkat.' }));`
  },
  {
    name: 'Select', group: 'Inputs', height: 240,
    summary: 'Native selection with a visible empty choice.',
    anatomy: 'Label, hint, error, browser select.',
    provides: '`label`, `value`, `onChange(value)`, `options` [{value, label, disabledReason}], `emptyLabel` (null removes it), `hint`, `required`, `error`.',
    states: 'Default, focus, invalid, disabled option with its reason in the text.',
    a11y: 'Native keyboard and screen-reader behaviour.',
    tokens: '`tr-comp-field-*`.',
    responsive: 'Full width; the platform picker opens on phones.',
    do: 'Start empty when no choice has been made.',
    dont: 'Do not silently pick a sector, currency or company.',
    demo: `
  var a = useState('');
  return h(TR.Select, { label: 'Sektor', hint: 'Dipakai untuk pencarian.', value: a[0], onChange: a[1], options: [
    { value: 'air', label: 'Air bersih' }, { value: 'pertanian', label: 'Pertanian' }, { value: 'energi', label: 'Energi' },
    { value: 'lain', label: 'Sektor lain', disabledReason: 'Belum tersedia di marketplace ini' }] });`
  },
  {
    name: 'ChoiceGroup', group: 'Inputs', height: 380,
    summary: 'Mutually exclusive radio choices with whole-row targets.',
    anatomy: 'Fieldset, legend, hint, error, rows with label, hint and optional disabled reason.',
    provides: '`legend`, `options` [{value, label, hint, disabledReason}], `value`, `onChange(value)`, `hint`, `required`, `error`, `id` (first radio), `name`.',
    states: 'Default, hover, focus, selected (2 px boundary plus filled radio), disabled with reason, invalid.',
    a11y: 'Native radios: Tab enters the group, arrows move within it. The row is the `<label>`.',
    tokens: '`tr-sys-color-selected-*`, `tr-sys-color-border-control`, `tr-sys-size-borderSelected`.',
    responsive: 'One column at every width, so long labels stay readable.',
    do: 'Use for support type, relationship type and current or planned status.',
    dont: 'Do not delete unrelated saved drafts when the purpose changes.',
    demo: `
  var a = useState('project');
  return h(TR.ChoiceGroup, { legend: 'Apa yang Anda cari?', required: true, value: a[0], onChange: a[1], options: [
    { value: 'project', label: 'Dukungan Proyek', hint: 'Untuk satu inovasi dan cakupan kerja tertentu.' },
    { value: 'company', label: 'Pendanaan Perusahaan', hint: 'Untuk perusahaan; dapat terkait beberapa inovasi.' },
    { value: 'license', label: 'Diskusi lisensi', disabledReason: 'Tidak diaktifkan di marketplace demo ini.' }] });`
  },
  {
    name: 'Checkbox', group: 'Inputs', height: 300,
    summary: 'Independent yes or no choice; consent stays unchecked until really given.',
    anatomy: 'Row label, checkbox, hint, reason. `Checkbox.Group` adds fieldset and legend.',
    provides: '`label`, `checked`, `onChange(checked)`, `hint`, `disabledReason`, `error`, `id`. Group: `legend`, `hint`, `children`.',
    states: 'Unchecked, checked, focus, disabled with reason, invalid.',
    a11y: 'Native checkbox; Space toggles. The row is the `<label>`.',
    tokens: '`tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.',
    responsive: 'One column.',
    do: 'Ask for one named permission at a time.',
    dont: 'Do not precheck a blanket permission for private files or publication.',
    demo: `
  var a = useState(false), b = useState(true);
  return h(TR.Checkbox.Group, { legend: 'Data yang boleh tampil di publik', hint: 'Anda dapat mengubahnya sebelum mengirim.' },
    h(TR.Checkbox, { label: 'Nama mitra', checked: b[0], onChange: b[1] }),
    h(TR.Checkbox, { label: 'Nilai dukungan', hint: 'Default privat.', checked: a[0], onChange: a[1] }),
    h(TR.Checkbox, { label: 'Persentase saham', disabledReason: 'Hanya untuk hubungan ekuitas dengan badan usaha yang disebutkan.' }));`
  },
  {
    name: 'FieldError', group: 'Inputs', height: 120,
    summary: 'Plain correction message tied to one field.',
    anatomy: 'Icon, hidden "Kesalahan:" prefix, message.',
    provides: '`id`, `children`, `code` (stable error code stored as `data-code`).',
    states: 'Single state; shown only when the field is invalid.',
    a11y: 'Linked from the field through `aria-describedby`. The same words appear in `TR.ErrorSummary`.',
    tokens: '`tr-sys-color-danger-text`.',
    responsive: 'Wraps.',
    do: 'Say what to fix: "Biaya maksimum tidak boleh lebih kecil dari biaya minimum."',
    dont: 'Do not show stack traces, HTTP codes or another party\'s data. Do not erase the value.',
    demo: `
  return h(TR.FieldError, { code: 'BUDGET_RANGE' }, 'Biaya maksimum tidak boleh lebih kecil dari biaya minimum.');`
  },
  {
    name: 'ErrorSummary', group: 'Inputs', height: 330,
    summary: 'Focused list of what stopped a submission, linking to each field.',
    anatomy: 'Focusable region, heading, linked list, optional retry.',
    provides: '`errors` [{fieldId, message}], `focusKey` (change it on each failed attempt), `title`, `children`, `retry` {label, onClick}, `id`.',
    states: 'Field errors; global retry without a field target.',
    a11y: 'Focus moves to the region only when `focusKey` changes, so a background save never steals focus. Each link focuses its field.',
    tokens: '`tr-sys-color-danger-*`, `tr-sys-size-borderSelected`.',
    responsive: 'Full width at the top of the task.',
    do: 'Repeat the words of the inline errors.',
    dont: 'Do not replace it with a disappearing toast.',
    demo: `
  var k = useState(0), v = useState('');
  var errors = v[0] ? [] : [{ fieldId: 'demo-budget', message: 'Isi anggaran pilot' }];
  return h(React.Fragment, null,
    k[0] > 0 && errors.length ? h(TR.ErrorSummary, { errors: errors, focusKey: k[0] }) : null,
    h(TR.TextField, { id: 'demo-budget', label: 'Anggaran pilot', type: 'decimal', prefix: 'USD', value: v[0], onChange: v[1], error: k[0] > 0 && !v[0] ? 'Isi anggaran pilot' : null }),
    h('div', { className: 'tr-row' }, h(TR.Button, { intent: 'primary', onClick: function () { k[1](k[0] + 1); } }, 'Kirim jawaban')),
    S('Global retry, no field target', h(TR.ErrorSummary, { title: 'Pitching belum terkirim', retry: { label: 'Coba kirim lagi', onClick: function () {} } }, 'Koneksi terputus. Isian Anda masih ada.')));`
  },
  {
    name: 'Dialog', group: 'Overlays', height: 190,
    summary: 'Modal for one short decision, with safe focus handling.',
    anatomy: 'Title, close button, body, primary and secondary effect.',
    provides: '`open`, `onClose`, `title`, `children`, `primary` {label, onClick, busy, busyLabel, intent, disabledReason}, `secondary` {label, onClick}, `initialFocusId`, `returnFocusId`.',
    states: 'Closed, open, busy, recoverable error shown inside the body.',
    a11y: 'Native modal `<dialog>`, labelled by its title. Initial focus lands on the title unless `initialFocusId` is set. Tab and Shift+Tab stay inside. Escape closes without committing. Focus returns to the opener.',
    tokens: '`tr-sys-radius-dialog`, `tr-sys-shadow-dialog`, `tr-sys-color-overlay`.',
    responsive: 'Width caps at 40 rem; the body scrolls and the footer stays reachable.',
    do: 'Use for a short confirmation, such as sharing one document version.',
    dont: 'Do not put multi-step work in a dialog. Prefer an ordinary page. It owns focus, not authorization.',
    demo: `
  var o = useState(false), err = useState(false);
  return h(React.Fragment, null,
    h('div', { className: 'tr-row' }, h(TR.Button, { intent: 'primary', id: 'open-dialog', onClick: function () { o[1](true); } }, 'Bagikan dokumen')),
    h(TR.Dialog, { open: o[0], onClose: function () { o[1](false); err[1](false); }, title: 'Bagikan dokumen ini?',
      primary: { label: 'Bagikan versi ini', onClick: function () { err[1](true); } }, secondary: { label: 'Kembali memeriksa' } },
      h('p', null, 'Mitra Demo A dapat membuka laporan uji fungsi versi 2. Versi berikutnya tidak ikut dibagikan.'),
      err[0] ? h(TR.Status, { tone: 'danger', label: 'Gagal membagikan', live: true }, 'Koneksi terputus. Pilihan Anda tidak hilang.') : null));`
  },
  {
    name: 'Disclosure', group: 'Overlays', height: 200,
    summary: 'Keeps supporting detail one click away.',
    anatomy: 'Summary toggle with chevron, region.',
    provides: '`label`, `children`, `defaultOpen`, `storageKey` (keeps the state when returning within the session).',
    states: 'Collapsed, expanded, focus.',
    a11y: 'Native `<details>`; Enter and Space toggle and the expanded state is exposed.',
    tokens: '`tr-sys-color-action-secondary-foreground`, `tr-sys-color-border-decorative`.',
    responsive: 'Full width.',
    do: 'Use for score detail, provenance and calculation notes.',
    dont: 'Never hide a blocking gap inside it.',
    demo: `
  return h(TR.Disclosure, { label: 'Detail teknis peringkat', storageKey: 'tr-demo-disclosure' },
    h('p', null, 'Indeks prioritas peninjauan 71,72\\u201380,00.'),
    h('p', { className: 'tr-muted tr-sys-type-support' }, 'Rentang ini menunjukkan informasi yang belum lengkap. Ini bukan peluang pendanaan.'));`
  },
  {
    name: 'Tabs', group: 'Overlays', height: 230,
    summary: 'Related views inside one pitch workspace.',
    anatomy: 'Tab list, tabs, one panel.',
    provides: '`label`, `tabs` [{id, label, content}], `value`, `onChange(id)`.',
    states: 'Default, hover, focus, selected (2 px bar, weight and surface).',
    a11y: 'ARIA tabs with automatic activation. Arrow keys, Home and End move between tabs; Tab moves to the panel.',
    tokens: '`tr-sys-color-selected-*`, `tr-sys-color-border-control`.',
    responsive: 'Tabs wrap to more rows, so every tab stays reachable without hidden scrolling.',
    do: 'Keep a logical heading in each panel.',
    dont: 'Do not use tabs for ordered steps; use `TR.Steps`.',
    demo: `
  return h(TR.Tabs, { label: 'Ruang pitching', tabs: [
    { id: 'ringkasan', label: 'Ringkasan', content: h('p', null, 'Ringkasan pitching ClearSpring.') },
    { id: 'revisi', label: 'Revisi (1)', content: h('p', null, 'Satu pertanyaan menunggu jawaban Anda.') },
    { id: 'jadwal', label: 'Jadwal', content: h('p', null, 'Belum ada usulan waktu.') }] });`
  },
  {
    name: 'Status', group: 'Feedback', height: 360,
    summary: 'A domain result in words, supported by icon and colour.',
    anatomy: 'Label with icon; with `children` it becomes a notice with an explanation.',
    provides: '`label`, `tone` neutral | success | danger | warning | action, `icon` (null removes it), `children`, `live` true | alert.',
    states: 'Five tones. Pending work stays neutral; UNKNOWN is warning with a question mark; FAIL is danger with a cross.',
    a11y: 'Meaning is always in the text. `live` adds `role="status"` or `alert` without moving focus.',
    tokens: '`tr-sys-color-success-*`, `tr-sys-color-danger-*`, `tr-sys-color-warning-*`, `tr-sys-color-selected-*`, `tr-sys-color-surface-subtle`.',
    responsive: 'Wraps.',
    do: 'Pass the real result from the domain and add one sentence on what it means.',
    dont: 'Do not derive PASS or approval from colour. Do not paint pending work as success.',
    demo: `
  return h(React.Fragment, null,
    S('Labels', h('div', { className: 'tr-row' },
      h(TR.Status, { tone: 'success', label: 'Terpenuhi' }),
      h(TR.Status, { tone: 'danger', label: 'Tidak terpenuhi' }),
      h(TR.Status, { tone: 'warning', label: 'Belum diketahui' }),
      h(TR.Status, { tone: 'neutral', label: 'Menunggu konfirmasi' }),
      h(TR.Status, { tone: 'action', label: 'Menunggu Anda' }))),
    S('With explanation', h(TR.Status, { tone: 'warning', label: 'Perlu konfirmasi' }, 'Kewenangan hak belum diperiksa. Ini bukan penolakan.')),
    S('Approval is not funding', h(TR.Status, { tone: 'success', label: 'Disetujui untuk diskusi' }, 'Mitra bersedia berdiskusi. Ini belum berarti pendanaan atau kerja sama.')));`
  },
  {
    name: 'EmptyState', group: 'Feedback', height: 300,
    summary: 'Explains why nothing is here and what to do next.',
    anatomy: 'Icon, heading, reason, action.',
    provides: '`kind` noInventions | noMatches | closedIntake | denied, or `title` + `children`; `action`.',
    states: 'Four distinct reasons.',
    a11y: 'Heading plus text; the action is an ordinary control.',
    tokens: '`tr-sys-color-surface`, `tr-sys-color-border-decorative`.',
    responsive: 'Centered, one column.',
    do: 'Offer a way forward, such as relaxing a filter on purpose.',
    dont: 'Do not fill the space with zero amounts, invented trends or recommendations. A denied state never names a protected title.',
    demo: `
  var a = TR.demo.useAxes({ kind: 'noMatches' });
  var actions = { noInventions: 'Buat inovasi', noMatches: 'Longgarkan filter', closedIntake: 'Cari mitra lain', denied: 'Minta akses' };
  return h(React.Fragment, null,
    h(TR.demo.Controls, { state: a, axes: [{ id: 'kind', label: 'Reason', options: Object.keys(actions) }] }),
    h(TR.EmptyState, { kind: a.value.kind, action: h(TR.Button, { intent: 'primary' }, actions[a.value.kind]) }));`
  },
  {
    name: 'SaveState', group: 'Feedback', height: 300,
    summary: 'Says truthfully whether work is saved, and where.',
    anatomy: 'Icon or spinner, label, recovery note and retry when failed.',
    provides: '`state` local | saving | saved | failed | conflict, `location` demo | server, `savedAt`, `timeZone`, `onRetry`.',
    states: 'Belum tersimpan, Menyimpan, Tersimpan di demo ini, Gagal menyimpan, Versi sudah berubah.',
    a11y: 'The label is `role="status"`, announced once per state and never per keystroke; focus does not move.',
    tokens: '`tr-sys-color-success-text`, `tr-sys-color-danger-text`, `tr-sys-color-warning-text`.',
    responsive: 'Wraps; keep it beside the page heading.',
    do: 'State the location. A demo says "Tersimpan di demo ini".',
    dont: 'Do not draw a check before the save is acknowledged, or while offline.',
    demo: `
  var a = TR.demo.useAxes({ state: 'saved' });
  return h(React.Fragment, null,
    h(TR.demo.Controls, { state: a, axes: [{ id: 'state', label: 'Draft saving', options: ['local', 'saving', 'saved', 'failed', 'conflict'] }] }),
    h(TR.SaveState, { state: a.value.state, savedAt: '2026-10-31T07:32:00Z', onRetry: function () { a.set('state', 'saving'); } }));`
  },
  {
    name: 'ContextSwitcher', group: 'Navigation', height: 240,
    summary: 'Shows and changes the personal or organization context a person acts in.',
    anatomy: 'Labelled select; read-only line before consequential actions.',
    provides: '`value`, `onChange(id)`, `options` [{id, kind personal | organization, name, disabledReason}], `readOnly`, `actionLabel`, `label`, `hint`.',
    states: 'Personal, organization, unavailable with a safe reason, read-only.',
    a11y: 'Native select. Read-only form is plain text.',
    tokens: '`tr-comp-field-*`.',
    responsive: 'Sits in the top bar; full width on phones.',
    do: 'Show the read-only line before send, decide and confirm.',
    dont: 'Do not treat a selection as authority: the server checks membership. Do not force a person to create an organization.',
    demo: `
  var a = useState('pribadi');
  return h(React.Fragment, null,
    h(TR.ContextSwitcher, { value: a[0], onChange: a[1], options: X.contexts }),
    S('Before a consequential action', h(TR.ContextSwitcher, { readOnly: true, value: a[0], options: X.contexts, actionLabel: 'Akan dikirim sebagai' })));`
  },
  {
    name: 'NextStep', group: 'Navigation', height: 340,
    summary: 'Tells a person whose turn it is and the one thing to do now.',
    anatomy: 'Responsibility label, heading, reason, optional due date, one action.',
    provides: '`who` you | other, `title`, `children`, `due`, `action`.',
    states: 'Menunggu Anda (selected surface, 2 px boundary), Menunggu pihak lain (plain surface, no action needed).',
    a11y: 'Section labelled by its heading. Responsibility is in words.',
    tokens: '`tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.',
    responsive: 'Full width at the top of the task, before supporting detail.',
    do: 'Open every workspace with it. Write one sentence and one effect-named action.',
    dont: 'Do not stack several next steps. When it waits on someone else, say so and ask for nothing.',
    demo: `
  return h(React.Fragment, null,
    h(TR.NextStep, { title: 'Jawab satu pertanyaan revisi', due: '2026-11-10', action: h(TR.Button, { intent: 'primary' }, 'Jawab revisi') }, 'Mitra Demo A meminta anggaran pilot sebelum memutuskan.'),
    h(TR.NextStep, { who: 'other', title: 'Mitra Demo A sedang meninjau' }, 'Anda tidak perlu melakukan apa pun sekarang. Kami memberi tahu Anda saat ada jawaban.'));`
  },
  {
    name: 'Steps', group: 'Navigation', height: 200,
    summary: 'Progress through a fixed-order editor.',
    anatomy: 'Current step sentence, ordered list with marks.',
    provides: '`steps` [{id, label, done}], `current`, `onSelect(id)`, `label`.',
    states: 'Done (check plus hidden text), current (filled mark, `aria-current="step"`), to do.',
    a11y: 'Navigation landmark with an ordered list. Other steps are buttons when `onSelect` is given.',
    tokens: '`tr-sys-color-action-primary-*`, `tr-sys-color-selected-*`.',
    responsive: 'Grid wraps to one column on narrow screens; the sentence always names the current step.',
    do: 'Allow jumping back without losing input.',
    dont: 'Do not use it for resumable unordered work; that is a task list.',
    demo: `
  var a = useState('uang');
  return h(TR.Steps, { current: a[0], onSelect: a[1], steps: [{ id: 'dasar', label: 'Dasar' }, { id: 'bukti', label: 'Yang sudah ada dan bukti' }, { id: 'uang', label: 'Dukungan dan biaya' }, { id: 'publik', label: 'Pratinjau publik' }] });`
  },
  {
    name: 'SummaryList', group: 'Navigation', height: 260,
    summary: 'Check-your-answers list with a contextual change link per row.',
    anatomy: 'Term, value, change link.',
    provides: '`rows` [{id, label, value, onChange}].',
    states: 'Read-only row; row with change link.',
    a11y: '`<dl>`. Each link reads "Ubah <field>".',
    tokens: '`tr-sys-color-border-decorative`, `tr-sys-color-link`.',
    responsive: 'Stacks below 48 rem; three columns above.',
    do: 'Use before every send, publication and confirmation.',
    dont: 'Do not put private evidence in a public preview.',
    demo: `
  function noop() {}
  return h(TR.SummaryList, { rows: [
    { id: 'penerima', label: 'Penerima', value: 'Mitra Demo A \\u00b7 Validasi prototipe', onChange: noop },
    { id: 'biaya', label: 'Biaya proyek', value: 'USD 20.000\\u201330.000 selama 6 bulan', onChange: noop },
    { id: 'peran', label: 'Dikirim sebagai', value: 'Rani \\u00b7 Pribadi' }] });`
  },
  {
    name: 'InventionCard', group: 'Domain', height: 620,
    summary: 'One invention, led by problem, current solution and what it needs.',
    anatomy: 'Category band or image, title, manager, facts, scoped money, reasons, gap, one action.',
    provides: '`title`, `category`, `image` {src, alt}, `manager`, `problem`, `solution`, `maturity`, `support`, `financial` (FinancialScope props), `facts`, `reasons`, `gap`, `action`. Pass an authorized projection only.',
    states: 'With or without image, with or without gap, noncash.',
    a11y: '`<article>` with a heading. The fallback band is labelled text; a missing image is not a problem state.',
    tokens: '`tr-sys-color-surface`, `tr-sys-color-selected-surface`, `tr-sys-radius-surface`.',
    responsive: 'Fits a 18 rem column; content stacks.',
    do: 'Keep a short reason and one action. Label planned functionality.',
    dont: 'Do not add ratings, follower counts, funding progress or invented photos.',
    demo: `
  var f = X.F01;
  return h('div', { style: { maxWidth: '26rem' } }, h(TR.InventionCard, Object.assign({}, f, {
    facts: h('div', { className: 'tr-stack' },
      h(TR.FactSource, { value: '10 L/jam', timing: 'CURRENT', provenance: 'PROVIDED' }),
      h(TR.FactSource, { value: '20 L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED' })),
    reasons: ['Mitra menerima tahap prototipe.'],
    action: h(TR.Button, { intent: 'primary' }, 'Siapkan pitching') })));`
  },
  {
    name: 'FundingRequestCard', group: 'Domain', height: 640,
    summary: 'One company raise, even when several inventions support it.',
    anatomy: 'Band, company, entity label, facts, target, contribution, linked inventions, one action.',
    provides: '`company`, `proposedEntity`, `stage`, `form`, `purpose`, `currency`, `target`, `desiredMin`, `desiredMax`, `partialAccepted`, `inventions` [titles], `reasons`, `gap`, `action`.',
    states: 'Existing or named entity, company not yet formed, with or without contribution range.',
    a11y: '`<article>` with a heading; the linked count is text.',
    tokens: 'As `TR.InventionCard`.',
    responsive: 'Fits a 18 rem column.',
    do: 'Show the target and contribution as separate labelled amounts.',
    dont: 'Do not repeat the raise per invention, assume a formed company or derive shares or valuation.',
    demo: `
  return h('div', { style: { maxWidth: '26rem' } }, h(TR.FundingRequestCard, Object.assign({}, X.FRaise01, {
    reasons: ['Kontribusi cocok dengan kisaran investor USD 50.000\\u2013150.000.'],
    action: h(TR.Button, { intent: 'primary' }, 'Siapkan pitching') })));`
  },
  {
    name: 'FinancialScope', group: 'Domain', height: 400,
    summary: 'An amount that always says what it is an amount of.',
    anatomy: 'Subject, amount with unit, period, scope, estimate date, assumptions, optional fields.',
    provides: '`subject` project | companyTarget | contribution | investorCheck | partner | license, `currency`, `min`, `max` (decimal strings; null means unknown), `period`, `scope`, `estimateDate`, `assumptions`, `noncash`, `terms`, `compact`, `edit`, `label`.',
    states: 'Range, single value, unknown ("Belum ditentukan"), noncash.',
    a11y: 'Text only. Amount and unit never split across lines.',
    tokens: '`tr-sys-type-amount`, `tr-sys-color-surface-subtle`.',
    responsive: 'Amount stays together; the period wraps to the next line.',
    do: 'Keep duration beside the range. Compare only like with like.',
    dont: 'Do not convert currency, show funding progress or percentages, or render unknown as zero.',
    demo: `
  return h(React.Fragment, null,
    h(TR.FinancialScope, X.F01.financial),
    h(TR.FinancialScope, { subject: 'companyTarget', currency: 'USD', min: '500000', max: '500000' }),
    h(TR.FinancialScope, { subject: 'contribution', currency: 'USD', min: '50000', max: '100000' }),
    h(TR.FinancialScope, { subject: 'project', currency: 'USD', min: null, max: null, scope: 'Validasi prototipe' }),
    h(TR.FinancialScope, X.F02.financial));`
  },
  {
    name: 'RequirementRow', group: 'Domain', height: 620,
    summary: 'One requirement, its result in words and what to do about it.',
    anatomy: 'Label, result, stage, mandatory flag, verification mode, reason, source, action.',
    provides: '`label`, `result` PASS | FAIL | UNKNOWN | NOT_APPLICABLE, `stage` SUBMISSION | DISCUSSION | PILOT | COMMERCIALIZATION, `mandatory`, `mode` DECLARATION | DOCUMENT_PRESENT | REVIEWER_CONFIRMED, `reason`, `source`, `action`. Render inside `<ul class="tr-reqs">`.',
    states: 'Four results, plus later-stage work drawn neutral with "Tidak menghalangi pengajuan".',
    a11y: 'List item with a heading; results are text.',
    tokens: 'Status tones, `tr-sys-color-border-decorative`.',
    responsive: 'Result wraps under the label.',
    do: 'Show gaps first and say the next action.',
    dont: 'Do not turn UNKNOWN into FAIL, or a planned capability into PASS.',
    demo: `
  return h('ul', { className: 'tr-reqs' },
    h(TR.RequirementRow, { label: 'Laporan uji fungsi tersedia', result: 'PASS', stage: 'SUBMISSION', mode: 'DOCUMENT_PRESENT', reason: 'Laporan uji fungsi versi 2 tersedia.' }),
    h(TR.RequirementRow, { label: 'SSO sudah berfungsi', result: 'FAIL', stage: 'SUBMISSION', mode: 'DECLARATION', reason: 'SSO masih direncanakan, sedangkan mitra meminta SSO yang sudah ada.', action: h(TR.Button, {}, 'Cari mitra lain') }),
    h(TR.RequirementRow, { label: 'Kewenangan hak diperiksa', result: 'UNKNOWN', stage: 'SUBMISSION', mode: 'REVIEWER_CONFIRMED', reason: 'Kewenangan belum diperiksa. Ini bukan penolakan.', action: h(TR.Button, {}, 'Lengkapi informasi') }),
    h(TR.RequirementRow, { label: 'Sertifikasi produk', result: 'UNKNOWN', stage: 'COMMERCIALIZATION', mode: 'DOCUMENT_PRESENT' }),
    h(TR.RequirementRow, { label: 'Persyaratan ekuitas', result: 'NOT_APPLICABLE', stage: 'SUBMISSION', mandatory: false, reason: 'Permintaan ini berupa dukungan proyek.' }));`
  },
  {
    name: 'FactSource', group: 'Domain', height: 240,
    summary: 'Whether a fact exists now, and how far it has been checked.',
    anatomy: 'Value, timing tag, provenance tag, review scope, source link.',
    provides: '`value`, `timing` CURRENT | PLANNED | REQUESTED, `provenance` SOURCE_REPORTED | SELF_DECLARED | PROVIDED | REVIEWED | UNKNOWN, `reviewScope`, `sourceHref`, `sourceLabel`.',
    states: 'Planned and requested tags use a dashed boundary. Only REVIEWED gets a success check.',
    a11y: 'Text labels; the source link carries hidden context.',
    tokens: '`tr-sys-color-border-control`, `tr-sys-color-success-*`.',
    responsive: 'Wraps.',
    do: 'Put it next to the claim it qualifies.',
    dont: 'Do not let a source link reveal a protected title. An upload is not a review.',
    demo: `
  return h(React.Fragment, null,
    h(TR.FactSource, { value: '10 L/jam', timing: 'CURRENT', provenance: 'PROVIDED', sourceHref: '#laporan' }),
    h(TR.FactSource, { value: '20 L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED' }),
    h(TR.FactSource, { value: 'Ekspor luring', timing: 'CURRENT', provenance: 'REVIEWED', reviewScope: 'Kriteria fungsi, versi 2' }),
    h(TR.FactSource, { value: 'SSO', timing: 'REQUESTED', provenance: 'SOURCE_REPORTED' }));`
  },
  {
    name: 'DocumentItem', group: 'Domain', height: 560,
    summary: 'A document with file safety, text reading, evidence review and sharing kept apart.',
    anatomy: 'Title, version, three independent status axes, sharing sentence, action.',
    provides: '`title`, `version`, `file`, `extraction`, `review`, `grant` {recipient, version, revoked}, `denied`, `action`.',
    states: 'Every combination of the three axes; denied (no title shown); revoked with its truthful limit.',
    a11y: '`<dl>` of axis names and results. Each result is text.',
    tokens: 'Status tones, `tr-sys-color-border-decorative`.',
    responsive: 'Axes form one column on phones.',
    do: 'Say the sharing limit: one named recipient, one version.',
    dont: 'Do not let an upload imply review, or a quarantined file open. Never show a protected title to someone without access.',
    demo: `
  var a = TR.demo.useAxes({ file: 'AVAILABLE', extraction: 'NEEDS_MANUAL_INPUT', review: 'PROVIDED_UNREVIEWED', grant: 'none' });
  return h(React.Fragment, null,
    h(TR.demo.Controls, { state: a, axes: [
      { id: 'file', label: 'File availability', options: ['CREATED', 'UPLOADING', 'QUARANTINED', 'AVAILABLE', 'REJECTED'] },
      { id: 'extraction', label: 'Extraction', options: ['NOT_REQUESTED', 'PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'NEEDS_MANUAL_INPUT'] },
      { id: 'review', label: 'Review', options: ['PROVIDED_UNREVIEWED', 'REVIEWED_SUPPORTED', 'REVIEWED_UNSUPPORTED', 'NEEDS_CLARIFICATION', 'EXPIRED', 'SUPERSEDED'] },
      { id: 'grant', label: 'Grant', options: ['none', 'granted', 'revoked', 'denied viewer'] }] }),
    h(TR.DocumentItem, { title: 'Laporan uji fungsi', version: 2, file: a.value.file, extraction: a.value.extraction, review: a.value.review, denied: a.value.grant === 'denied viewer',
      grant: a.value.grant === 'granted' ? { recipient: 'Mitra Demo A' } : a.value.grant === 'revoked' ? { recipient: 'Mitra Demo A', revoked: true } : null,
      action: h(TR.Button, {}, a.value.grant === 'denied viewer' ? 'Minta akses' : 'Isi data manual') }));`
  },
  {
    name: 'RevisionItem', group: 'Domain', height: 660,
    summary: 'One revision question, its reason, and an answer that may honestly be no.',
    anatomy: 'Round and item heading, required flag, question, reason, due date, response, explanation, attachments, review result.',
    provides: '`round`, `index`, `question`, `reason`, `required`, `due`, `value` {response, text}, `onChange(value)`, `attachments`, `review`, `error`, `id`.',
    states: 'Required, optional, answered, invalid, reviewed.',
    a11y: 'Uses `TR.ChoiceGroup` and `TR.TextArea`.',
    tokens: 'As its parts.',
    responsive: 'One column.',
    do: 'Keep each answer in place when one upload fails.',
    dont: 'Do not treat "Perlu diskusi" or "Belum dapat dipenuhi" as approval or as an error.',
    demo: `
  var v = useState({ response: 'DISCUSS', text: 'Anggaran pilot masih dihitung bersama pemasok.' });
  return h(TR.RevisionItem, { round: 1, index: 1, required: true, due: '2026-11-10', question: 'Berapa anggaran pilot yang Anda perlukan?', reason: 'Kami perlu menilai cakupan pilot.', value: v[0], onChange: v[1] });`
  },
  {
    name: 'ScheduleSlotList', group: 'Domain', height: 620,
    summary: 'Proposed times in a person\'s own zone; a selection is not a booking.',
    anatomy: 'Agenda, slot radios with date, time, zone and duration, the other party\'s time, actions.',
    provides: '`slots` [{id, start (UTC ISO), minutes, conflict}], `zone`, `otherZone`, `selectedId`, `onSelect(id)`, `confirmedId`, `state` open | expired | superseded | cancelled, `onConfirm`, `onPropose`, `busy`, `agenda`, `error`.',
    states: 'Open, selected (not confirmed), confirmed, conflict, expired, superseded, cancelled.',
    a11y: 'Native radios. Each slot reads full date, time and zone.',
    tokens: '`tr-sys-color-selected-*`, Status tones.',
    responsive: 'One column; long dates wrap.',
    do: 'Show the IANA-derived zone label and both parties\' times.',
    dont: 'Do not say booked until acceptance succeeds on the server.',
    demo: `
  var sel = useState(null), done = useState(null), slots = X.slots.map(function (s) {
    return Object.assign({}, s, { conflict: F.overlaps(s.start, s.minutes, X.booked.start, X.booked.minutes) });
  });
  return h(TR.ScheduleSlotList, { slots: slots, zone: 'Asia/Jakarta', otherZone: 'Asia/Makassar', agenda: 'Membahas cakupan validasi prototipe.', selectedId: sel[0], onSelect: sel[1], confirmedId: done[0], onConfirm: function () { done[1](sel[0]); sel[1](null); }, onPropose: function () {} });`
  },
  {
    name: 'PartnershipConsent', group: 'Domain', height: 760,
    summary: 'Both parties confirm one exact version; only what both allow can go public.',
    anatomy: 'Version heading, state, summary, field rows with each party\'s choice and result, actions.',
    provides: '`version`, `type`, `summary`, `fields` [{id, label, value}], `mine` {name, selected, confirmedVersion}, `other` {name, selected, confirmedVersion}, `restricted` [ids], `onToggle(id, checked)`, `onConfirm`, `onRequestChange`, `onRestrict(id)`, `busy`, `readOnly`, `error`.',
    states: 'Draf, Menunggu konfirmasi, Dikonfirmasi kedua pihak, field private, field public, field hidden by a live restriction.',
    a11y: 'Checkboxes before you confirm; plain text after. Results are text with icons.',
    tokens: 'Status tones, `tr-sys-color-border-decorative`.',
    responsive: 'One column per field.',
    do: 'Say that hiding a field cannot recall a download.',
    dont: 'One confirmation is never mutual. A new version inherits no confirmation. Amounts stay private by default.',
    demo: `
  var ids = ['nama', 'jenis', 'cakupan', 'nilai'];
  var labels = { nama: 'Nama mitra', jenis: 'Jenis hubungan', cakupan: 'Cakupan', nilai: 'Nilai dukungan' };
  return h(TR.PartnershipConsent, { version: 2, type: 'Kerja Sama proyek', fields: ids.map(function (i) { return { id: i, label: labels[i] }; }),
    mine: { name: 'Rani', selected: ids, confirmedVersion: 2 },
    other: { name: 'Mitra Demo A', selected: ['nama', 'jenis', 'cakupan'], confirmedVersion: 2 },
    onRestrict: function () {} });`
  },
  {
    name: 'VersionConflict', group: 'Domain', height: 330,
    summary: 'Something changed underneath; the person\'s draft is safe.',
    anatomy: 'Warning, what changed, current version, retained draft, recovery actions.',
    provides: '`what`, `currentVersion`, `draft`, `onRefresh`, `refreshLabel`, `onCopy`, `onCompare`.',
    states: 'Single state with optional actions.',
    a11y: 'Labelled group. Place focus on it or announce it after the failed action.',
    tokens: '`tr-sys-color-warning-*`, `tr-sys-color-surface-subtle`.',
    responsive: 'Actions wrap.',
    do: 'Offer one clear recovery and keep the text.',
    dont: 'Do not merge consequential changes silently or reveal protected actor or source details.',
    demo: `
  return h(TR.VersionConflict, { what: 'Persyaratan Mitra Demo A diperbarui sejak Anda memeriksanya.', currentVersion: 'Versi 3', draft: 'Kami ingin memvalidasi prototipe selama 6 bulan.', onRefresh: function () {}, refreshLabel: 'Periksa ulang', onCopy: function () {} });`
  },
  {
    name: 'Screen', group: 'Layout', height: 460, width: 1000,
    summary: 'The app frame: acting context, navigation, title, next step, task and support.',
    anatomy: 'Skip link, top bar with wordmark, provenance and context, heading, main column, supporting column, phone tab bar.',
    provides: '`persona` inovator | mitra, `current`, `onNavigate(id)`, `title`, `subtitle`, `back`, `save`, `next`, `aside`, `context`, `provenance`, `children`.',
    states: 'Inovator or Investor/Mitra navigation; phone bar with Lainnya; static bar when large text would make it cover content.',
    a11y: 'Skip link, `<main>`, labelled navigation, `aria-current="page"`.',
    tokens: '`tr-sys-layout-*`, `tr-sys-color-selected-*`.',
    responsive: 'Below 48 rem a bar shows four destinations plus Lainnya and support stacks after the task. Above it, five top links and a 20 rem aside.',
    do: 'Put the active task before the timeline and context in reading order.',
    dont: 'Do not add a third persona or top-level pages for states.',
    demo: `
  var c = useState('inovasi'), ctx = useState('pribadi');
  return h(TR.Screen, { current: c[0], onNavigate: c[1], title: 'Inovasi Saya', subtitle: 'Satu inovasi sedang disiapkan.', provenance: X.provenance,
    context: h(TR.ContextSwitcher, { value: ctx[0], onChange: ctx[1], options: X.contexts }),
    next: h(TR.NextStep, { title: 'Lengkapi biaya ClearSpring', action: h(TR.Button, { intent: 'primary' }, 'Lanjutkan pengisian') }, 'Tinggal satu langkah sebelum pratinjau publik.'),
    aside: h('div', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Riwayat'), h('p', null, 'Draf disimpan di demo ini.')) },
    h(TR.EmptyState, { kind: 'noInventions' }));`, root: ''
  },
  {
    name: 'Icon', group: 'Layout', height: 180,
    summary: 'Small own stroke set; always beside text unless the control has a name.',
    anatomy: 'Inline SVG, 24 grid, `currentColor`, hidden from assistive technology.',
    provides: '`name`, `size` small.',
    states: 'None.',
    a11y: '`aria-hidden`. Meaning comes from the neighbouring text.',
    tokens: '`tr-sys-size-icon`, `tr-sys-size-iconSmall`.',
    responsive: 'Sized in rem.',
    do: 'Support a word.',
    dont: 'Do not use an icon as the only signal of a status.',
    demo: `
  var names = ['check', 'cross', 'question', 'minus', 'alert', 'clock', 'lock', 'shield', 'file', 'upload', 'external', 'down', 'right', 'left', 'arrow', 'close', 'user', 'building', 'search', 'home', 'bulb', 'chat', 'inbox', 'calendar', 'more', 'refresh', 'edit', 'eye', 'eyeOff', 'partner'];
  return h('div', { className: 'tr-row' }, names.map(function (n) { return h('span', { key: n, title: n }, h(TR.Icon, { name: n })); }));`
  }
];

// Page previews: compositions, not bundle exports.
export const pages = [
  {
    name: 'Foundations', group: 'Foundations', height: 900,
    demo: `
  var roles = ['canvas', 'surface', 'surface-subtle', 'text-primary', 'text-secondary', 'action-primary-background', 'action-primary-hover', 'action-secondary-foreground', 'selected-surface', 'border-decorative', 'border-control', 'focus', 'danger-text', 'danger-surface', 'success-text', 'success-surface', 'warning-text', 'warning-surface'];
  var type = ['heading-lg', 'heading-md', 'heading-sm', 'body', 'body-strong', 'label', 'support', 'amount'];
  return h(React.Fragment, null,
    h('h2', { className: 'tr-sys-type-heading-md' }, 'Colour roles'),
    h('div', { className: 'tr-grid' }, roles.map(function (r) {
      return h('p', { key: r, className: 'tr-swatch tr-sys-type-support' }, h('i', { style: { background: 'var(--tr-sys-color-' + r + ')' } }), 'tr-sys-color-' + r);
    })),
    h('h2', { className: 'tr-sys-type-heading-md' }, 'Type'),
    type.map(function (t) { return h('p', { key: t, className: 'tr-sys-type-' + t }, t + ' \\u00b7 Periksa sebelum mengirim'); }),
    h('h2', { className: 'tr-sys-type-heading-md' }, 'Focus and targets'),
    h('p', null, 'Tab through these: a white gap, then a blue ring, on each surface.'),
    ['surface', 'surface-subtle', 'selected-surface', 'danger-surface', 'warning-surface', 'success-surface'].map(function (s) {
      return h('div', { key: s, className: 'tr-row', style: { background: 'var(--tr-sys-color-' + s + ')', padding: 'var(--tr-ref-space-12)' } },
        h(TR.Button, { intent: 'primary' }, 'Kirim pitching'), h(TR.Button, {}, 'Lihat bukti'), h(TR.Link, { href: '#x' }, s));
    }));`
  },
  {
    name: 'StateAxes', group: 'Foundations', height: 980,
    demo: `
  var a = TR.demo.useAxes({ save: 'saved', file: 'AVAILABLE', extraction: 'NEEDS_MANUAL_INPUT', review: 'PROVIDED_UNREVIEWED', requirement: 'UNKNOWN', pitch: 'Dikirim', schedule: 'Usulan terbuka', relationship: 'Menunggu konfirmasi', disclosure: 'Nilai dukungan privat' });
  var combos = [
    ['Saved answer, quarantined file', { save: 'saved', file: 'QUARANTINED', extraction: 'NOT_REQUESTED', review: 'PROVIDED_UNREVIEWED' }],
    ['Available scan, manual extraction', { file: 'AVAILABLE', extraction: 'NEEDS_MANUAL_INPUT', review: 'PROVIDED_UNREVIEWED' }],
    ['Saved draft, unknown requirement', { save: 'saved', requirement: 'UNKNOWN' }],
    ['Stale preflight, retained message', { save: 'conflict' }],
    ['Confirmed relationship, private amount', { relationship: 'Dikonfirmasi kedua pihak', disclosure: 'Nilai dukungan privat' }]];
  var v = a.value;
  return h(React.Fragment, null,
    h(TR.demo.Controls, { state: a, axes: [
      { id: 'save', label: 'Draft saving', options: ['local', 'saving', 'saved', 'failed', 'conflict'] },
      { id: 'file', label: 'File availability', options: ['CREATED', 'UPLOADING', 'QUARANTINED', 'AVAILABLE', 'REJECTED'] },
      { id: 'extraction', label: 'Extraction', options: ['NOT_REQUESTED', 'PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'NEEDS_MANUAL_INPUT'] },
      { id: 'review', label: 'Review', options: ['PROVIDED_UNREVIEWED', 'REVIEWED_SUPPORTED', 'REVIEWED_UNSUPPORTED', 'NEEDS_CLARIFICATION', 'EXPIRED', 'SUPERSEDED'] },
      { id: 'requirement', label: 'Requirement', options: ['PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE'] },
      { id: 'pitch', label: 'Pitch', options: ['Dikirim', 'Sedang ditinjau', 'Revisi diminta', 'Disetujui untuk diskusi', 'Ditolak', 'Ditarik', 'Ditutup'] },
      { id: 'schedule', label: 'Scheduling', options: ['Usulan terbuka', 'Dipilih, belum dikonfirmasi', 'Waktu dikonfirmasi', 'Kedaluwarsa', 'Diganti', 'Dibatalkan'] },
      { id: 'relationship', label: 'Relationship', options: ['Draf', 'Menunggu konfirmasi', 'Perubahan diminta', 'Ditolak', 'Dikonfirmasi kedua pihak'] },
      { id: 'disclosure', label: 'Disclosure', options: ['Nilai dukungan privat', 'Disembunyikan oleh pembatasan'] }] },
      combos.map(function (c) { return h(TR.Button, { key: c[0], onClick: function () { Object.keys(c[1]).forEach(function (k) { a.set(k, c[1][k]); }); } }, c[0]); })),
    h(TR.SaveState, { state: v.save, savedAt: '2026-10-31T07:32:00Z' }),
    v.save === 'conflict' ? h(TR.VersionConflict, { what: 'Persyaratan berubah sejak pemeriksaan terakhir.', draft: 'Kami ingin memvalidasi prototipe selama 6 bulan.', onRefresh: function () {}, refreshLabel: 'Periksa ulang' }) : null,
    h(TR.DocumentItem, { title: 'Laporan uji fungsi', version: 2, file: v.file, extraction: v.extraction, review: v.review }),
    h('ul', { className: 'tr-reqs' }, h(TR.RequirementRow, { label: 'Hasil uji diperiksa peninjau', result: v.requirement, stage: 'SUBMISSION', mode: 'REVIEWER_CONFIRMED' })),
    h('div', { className: 'tr-row' },
      h(TR.Status, { tone: 'neutral', icon: 'chat', label: 'Pitching: ' + v.pitch }),
      h(TR.Status, { tone: 'neutral', icon: 'calendar', label: 'Jadwal: ' + v.schedule }),
      h(TR.Status, { tone: v.relationship === 'Dikonfirmasi kedua pihak' ? 'success' : 'neutral', label: 'Kerja Sama: ' + v.relationship }),
      h(TR.Status, { tone: 'neutral', icon: 'eyeOff', label: v.disclosure })));`
  },
  {
    name: 'PatternDiscovery', group: 'Patterns', height: 1100, root: '',
    demo: `
  var view = useState('list'), stale = useState(false), sent = useState(false), busy = useState(false), conflict = useState(false);
  var brief = useState('ClearSpring adalah prototipe filter air yang sudah berfungsi. Kami mencari mitra untuk validasi selama 6 bulan.');
  var ctx = useState('pribadi'), nav = useState('temukan');
  function send() {
    busy[1](true);
    setTimeout(function () {
      busy[1](false);
      if (stale[0]) conflict[1](true); else sent[1](true);
    }, 700);
  }
  function reset() { view[1]('list'); stale[1](false); sent[1](false); conflict[1](false); }
  var controls = h(TR.demo.Controls, { state: { reset: reset } },
    h(TR.Checkbox, { label: 'Persyaratan berubah sebelum kirim', hint: 'Mensimulasikan pemeriksaan yang sudah basi.', checked: stale[0], onChange: stale[1] }));
  var shell = { current: nav[0], onNavigate: nav[1], provenance: X.provenance, context: h(TR.ContextSwitcher, { value: ctx[0], onChange: ctx[1], options: X.contexts }) };
  if (view[0] === 'preflight') {
    var checks = h('ul', { className: 'tr-reqs' },
      h(TR.RequirementRow, { label: 'Tahap prototipe diterima', result: 'PASS', stage: 'SUBMISSION', mode: 'DECLARATION', reason: 'ClearSpring berada pada tahap prototipe.' }),
      h(TR.RequirementRow, { label: 'Laporan uji fungsi tersedia', result: 'PASS', stage: 'SUBMISSION', mode: 'DOCUMENT_PRESENT', reason: 'Berkas tersedia. Isinya belum diperiksa.' }),
      h(TR.RequirementRow, { label: 'Biaya dalam cakupan yang sama', result: 'PASS', stage: 'SUBMISSION', mode: 'DECLARATION', reason: 'USD 20.000\\u201330.000 berada dalam kisaran mitra USD 15.000\\u201340.000 selama 6 bulan.' }));
    var sum = h(TR.SummaryList, { rows: [
      { id: 'penerima', label: 'Penerima', value: 'Mitra Demo A \\u00b7 Validasi prototipe', onChange: function () { view[1]('list'); } },
      { id: 'inovasi', label: 'Inovasi', value: 'ClearSpring versi 1' },
      { id: 'tujuan', label: 'Tujuan', value: 'Dukungan Proyek: validasi prototipe' },
      { id: 'biaya', label: 'Biaya', value: h(TR.FinancialScope, X.F01.financial) },
      { id: 'berkas', label: 'Berkas dibagikan', value: 'Laporan uji fungsi versi 2, hanya untuk Mitra Demo A' }] });
    return h(TR.Screen, Object.assign({ title: 'Periksa sebelum mengirim', subtitle: 'ClearSpring ke Mitra Demo A',
      back: h(TR.Link, { href: '#hasil', onClick: function () { view[1]('list'); } }, 'Kembali ke hasil'),
      next: sent[0]
        ? h(TR.NextStep, { who: 'other', title: 'Mitra Demo A menerima pitching Anda' }, 'Mereka akan menyetujui diskusi, meminta revisi atau menolak. Terkirim belum berarti pendanaan.')
        : h(TR.NextStep, { title: 'Siap dikirim', action: h(TR.Button, { intent: 'primary', busy: busy[0], busyLabel: 'Mengirim\\u2026', onClick: send }, 'Kirim pitching') }, 'Semua syarat pengajuan terpenuhi. Periksa ringkasan lalu kirim.'),
      aside: h('div', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Syarat berikutnya'),
        h('ul', { className: 'tr-reqs' },
          h(TR.RequirementRow, { label: 'Hasil uji diperiksa peninjau', result: 'UNKNOWN', stage: 'DISCUSSION', mode: 'REVIEWER_CONFIRMED' }),
          h(TR.RequirementRow, { label: 'Sertifikasi produk', result: 'UNKNOWN', stage: 'COMMERCIALIZATION', mode: 'DOCUMENT_PRESENT' }))) }, shell),
      conflict[0] ? h(TR.VersionConflict, { what: 'Persyaratan Mitra Demo A berubah sejak Anda memeriksanya. Pitching belum terkirim.', currentVersion: 'Versi 2', draft: brief[0], refreshLabel: 'Periksa ulang', onRefresh: function () { stale[1](false); conflict[1](false); } }) : null,
      h(TR.ContextSwitcher, { readOnly: true, value: ctx[0], options: X.contexts, actionLabel: 'Akan dikirim sebagai' }),
      h('section', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Ringkasan'), sum),
      h('section', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Syarat pengajuan'), checks),
      h(TR.TextArea, { label: 'Ringkasan untuk mitra', hint: 'Anda dapat mengubahnya. Ringkasan hanya memuat fakta yang Anda sediakan.', value: brief[0], onChange: brief[1], limit: 350 }),
      controls);
  }
  var f1 = X.F01, f2 = X.F02, f3 = X.F03;
  var project = h('div', { className: 'tr-grid' },
    h(TR.InventionCard, Object.assign({}, f1, {
      facts: h('div', { className: 'tr-stack' }, h(TR.FactSource, { value: '10 L/jam', timing: 'CURRENT', provenance: 'PROVIDED' }), h(TR.FactSource, { value: '20 L/jam', timing: 'PLANNED', provenance: 'SELF_DECLARED' })),
      reasons: ['Mitra Demo A menerima tahap prototipe.', 'Kisaran mitra USD 15.000\\u201340.000 untuk cakupan dan masa yang sama.'],
      gap: h(TR.Status, { tone: 'success', label: 'Siap dikirim' }),
      action: h(TR.Button, { intent: 'primary', onClick: function () { view[1]('preflight'); } }, 'Siapkan pitching') })),
    h(TR.InventionCard, Object.assign({}, f2, {
      gap: h(TR.Status, { tone: 'warning', label: 'Perlu konfirmasi' }, 'Kewenangan hak belum diperiksa, sedangkan Mitra Demo B memintanya sebelum pengajuan. Ini bukan penolakan.'),
      action: h(TR.Button, {}, 'Lengkapi informasi') })),
    h(TR.InventionCard, Object.assign({}, f3, {
      facts: h('div', { className: 'tr-stack' }, h(TR.FactSource, { value: 'Ekspor luring', timing: 'CURRENT', provenance: 'SELF_DECLARED' }), h(TR.FactSource, { value: 'SSO', timing: 'PLANNED', provenance: 'SELF_DECLARED' })),
      gap: h(TR.Status, { tone: 'danger', label: 'Tidak cocok untuk mitra ini' }, 'Mitra Demo D meminta SSO yang sudah ada saat pengajuan. SSO QueueNest masih direncanakan.'),
      action: h(TR.Button, {}, 'Cari mitra lain') })));
  var funding = h('div', { className: 'tr-stack', style: { maxWidth: '30rem' } },
    h(TR.FundingRequestCard, Object.assign({}, X.FRaise01, {
      reasons: ['Kontribusi yang diinginkan cocok dengan kisaran investor USD 50.000\\u2013150.000.'],
      gap: h(TR.Status, { tone: 'success', label: 'Siap dikirim' }),
      action: h(TR.Button, { intent: 'primary' }, 'Siapkan pitching') })),
    h(TR.Disclosure, { label: 'Detail teknis peringkat' },
      h('p', null, 'Indeks prioritas peninjauan 71,72\\u201380,00.'),
      h('p', { className: 'tr-muted tr-sys-type-support' }, 'Rentang ini hanya untuk mengurutkan peninjauan. Ini bukan peluang pendanaan.')));
  return h(TR.Screen, Object.assign({ title: 'Temukan Investor/Mitra', subtitle: 'Hasil dikelompokkan menurut jenis permintaan.',
    next: h(TR.NextStep, { title: 'ClearSpring siap untuk Mitra Demo A', action: h(TR.Button, { intent: 'primary', onClick: function () { view[1]('preflight'); } }, 'Siapkan pitching') }, 'Periksa syarat dan ringkasan sebelum mengirim. Tidak ada yang terkirim sampai Anda menekan Kirim pitching.') }, shell),
    h(TR.Tabs, { label: 'Jenis permintaan', tabs: [
      { id: 'proyek', label: 'Dukungan Proyek', content: project },
      { id: 'perusahaan', label: 'Pendanaan Perusahaan', content: funding }] }));`
  },
  {
    name: 'PatternPortfolio', group: 'Patterns', height: 1100, root: '',
    demo: `
  var STEPS = [{ id: 'dasar', label: 'Dasar' }, { id: 'bukti', label: 'Yang sudah ada dan bukti' }, { id: 'uang', label: 'Dukungan dan biaya' }, { id: 'publik', label: 'Pratinjau publik' }];
  var FIRST = { title: 'ClearSpring', problem: 'Keluarga tanpa akses air bersih perlu cara menyaring air yang mudah dirawat.', solution: 'Prototipe filter air yang sudah berfungsi.', current: '10 L/jam', planned: '20 L/jam', min: '20000', max: '30000', period: '6 bulan' };
  var step = useState('dasar'), data = useState(FIRST), save = useState('saved'), failNext = useState(false), noBudget = useState(false);
  var attempt = useState(0), confirm = useState(false), share = useState(false), done = useState(false), timer = React.useRef(null);
  var d = data[0];
  var nav = useState('inovasi'), ctx = useState('pribadi');
  function persist() {
    save[1]('saving');
    clearTimeout(timer.current);
    timer.current = setTimeout(function () { save[1](failNext[0] ? 'failed' : 'saved'); }, 700);
  }
  function set(k) { return function (v) { var n = Object.assign({}, data[0]); n[k] = v; data[1](n); save[1]('local'); clearTimeout(timer.current); timer.current = setTimeout(persist, 900); }; }
  function toggleBudget(v) { noBudget[1](v); var n = Object.assign({}, data[0]); n.min = v ? '' : FIRST.min; n.max = v ? '' : FIRST.max; data[1](n); }
  var errors = [];
  if (d.min !== '' && Number(d.min) < 0) errors.push({ fieldId: 'f-min', message: 'Biaya minimum tidak boleh kurang dari 0.' });
  if (d.min !== '' && d.max !== '' && Number(d.max) < Number(d.min)) errors.push({ fieldId: 'f-max', message: 'Biaya maksimum tidak boleh lebih kecil dari biaya minimum.' });
  function err(id) { var e = attempt[0] > 0 && errors.filter(function (x) { return x.fieldId === id; })[0]; return e ? e.message : null; }
  var i = STEPS.map(function (s) { return s.id; }).indexOf(step[0]);
  function next() { if (step[0] === 'uang' && errors.length) { attempt[1](attempt[0] + 1); return; } attempt[1](0); step[1](STEPS[i + 1].id); }
  var hasBudget = d.min !== '' && d.max !== '';
  var fin = { subject: 'project', currency: 'USD', min: d.min === '' ? null : d.min, max: d.max === '' ? null : d.max, period: d.period, scope: 'Validasi prototipe' };
  var body = {
    dasar: h('div', { className: 'tr-stack' },
      h(TR.TextField, { label: 'Judul inovasi', required: true, hint: 'Antara 5 sampai 120 karakter.', value: d.title, onChange: set('title') }),
      h(TR.TextArea, { label: 'Masalah yang diselesaikan', hint: 'Tulis tanpa informasi rahasia.', rows: 3, value: d.problem, onChange: set('problem') })),
    bukti: h('div', { className: 'tr-stack' },
      h(TR.TextArea, { label: 'Yang sudah ada saat ini', rows: 3, value: d.solution, onChange: set('solution') }),
      h(TR.TextField, { label: 'Kapasitas saat ini', hint: 'Yang benar-benar berfungsi sekarang.', value: d.current, onChange: set('current') }),
      h(TR.TextField, { label: 'Kapasitas yang direncanakan', hint: 'Rencana tidak memenuhi syarat untuk hal yang harus sudah ada.', value: d.planned, onChange: set('planned') }),
      h(TR.DocumentItem, { title: 'Laporan uji fungsi', version: 2, file: 'AVAILABLE', extraction: 'NEEDS_MANUAL_INPUT', review: 'PROVIDED_UNREVIEWED', action: h(TR.Button, {}, 'Isi data manual') })),
    uang: h('div', { className: 'tr-stack' },
      attempt[0] > 0 && errors.length ? h(TR.ErrorSummary, { errors: errors, focusKey: attempt[0] }) : null,
      h('p', null, 'Anda dapat melewati bagian ini saat menyimpan draf. Biaya diperlukan sebelum mengirim.'),
      h(TR.TextField, { id: 'f-min', label: 'Biaya minimum', type: 'decimal', prefix: 'USD', value: d.min, onChange: set('min'), error: err('f-min') }),
      h(TR.TextField, { id: 'f-max', label: 'Biaya maksimum', type: 'decimal', prefix: 'USD', value: d.max, onChange: set('max'), error: err('f-max') }),
      h(TR.TextField, { label: 'Lama proyek', value: d.period, onChange: set('period') })),
    publik: h('div', { className: 'tr-stack' },
      h('p', null, 'Inilah yang dilihat investor dan mitra. Berkas tidak ikut tampil.'),
      h(TR.InventionCard, { title: d.title, category: 'Air bersih', manager: 'Dikelola Rani \\u00b7 Pribadi', problem: d.problem, solution: d.solution, maturity: 'Prototipe', support: 'Validasi prototipe', financial: fin }),
      h(TR.Checkbox, { label: 'Bagikan laporan uji fungsi versi 2 kepada Mitra Demo A', hint: 'Hanya versi ini dan hanya penerima ini.', checked: share[0], onChange: share[1] }),
      h(TR.ContextSwitcher, { readOnly: true, value: ctx[0], options: X.contexts, actionLabel: 'Akan dikirim sebagai' }),
      done[0] ? h(TR.Status, { tone: 'success', label: 'Terkirim ke Mitra Demo A', live: true }, 'Data publik dan satu versi berkas telah dibagikan. Ini bukan persetujuan dari mitra.') : null)
  }[step[0]];
  var last = step[0] === 'publik';
  var actions = h('div', { className: 'tr-row' },
    last
      ? h(TR.Button, { intent: 'primary', id: 'send-open', disabledReason: !hasBudget ? 'Isi kisaran biaya di langkah 3 terlebih dahulu.' : null, onClick: function () { confirm[1](true); } }, 'Tinjau dan kirim')
      : h(TR.Button, { intent: 'primary', onClick: next }, 'Lanjut'),
    i > 0 ? h(TR.Button, { onClick: function () { step[1](STEPS[i - 1].id); } }, 'Kembali') : null);
  return h(TR.Screen, { current: nav[0], onNavigate: nav[1], provenance: X.provenance, title: 'Siapkan ClearSpring', subtitle: 'Isi bertahap. Draf tersimpan otomatis.',
    context: h(TR.ContextSwitcher, { value: ctx[0], onChange: ctx[1], options: X.contexts }),
    save: h(TR.SaveState, { state: save[0], savedAt: '2026-10-31T07:32:00Z', onRetry: persist }),
    aside: !hasBudget ? h(TR.Status, { tone: 'warning', label: 'Biaya belum ditentukan' }, 'Draf tetap tersimpan. Isi biaya sebelum mengirim.') : undefined },
    h(TR.Steps, { steps: STEPS, current: step[0], onSelect: function (s) { attempt[1](0); step[1](s); } }),
    h('section', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-md' }, STEPS[i].label), body, actions),
    h(TR.demo.Controls, { state: { reset: function () { data[1](FIRST); step[1]('dasar'); save[1]('saved'); failNext[1](false); noBudget[1](false); share[1](false); done[1](false); attempt[1](0); } } },
      h(TR.Checkbox, { label: 'Penyimpanan berikutnya gagal', checked: failNext[0], onChange: failNext[1] }),
      h(TR.Checkbox, { label: 'Tanpa anggaran', checked: noBudget[0], onChange: toggleBudget })),
    h(TR.Dialog, { open: confirm[0], onClose: function () { confirm[1](false); }, returnFocusId: 'send-open', title: 'Kirim ke Mitra Demo A?',
      primary: { label: 'Kirim sekarang', onClick: function () { confirm[1](false); done[1](true); } }, secondary: { label: 'Periksa lagi' } },
      h(TR.SummaryList, { rows: [{ id: 'd1', label: 'Penerima', value: 'Mitra Demo A' }, { id: 'd2', label: 'Data publik', value: 'Judul, masalah, solusi, tahap dan biaya' }, { id: 'd3', label: 'Berkas', value: share[0] ? 'Laporan uji fungsi versi 2' : 'Tidak ada berkas' }] })));`
  },
  {
    name: 'PatternRevisionSchedule', group: 'Patterns', height: 1100, root: '',
    demo: `
  var tab = useState('revisi'), a1 = useState({}), a2 = useState({ response: 'CANNOT', text: 'Kapasitas 20 L/jam masih direncanakan.' });
  var attempt = useState(0), phase = useState('revision'), sel = useState(null), meeting = useState(null), failReplace = useState(false), failure = useState(false), busy = useState(false), replacing = useState(false);
  var nav = useState('pitching'), ctx = useState('pribadi');
  var missing = !a1[0].response;
  var errors = missing ? [{ fieldId: 'q1', message: 'Pilih tanggapan untuk pertanyaan anggaran pilot.' }] : [];
  function resubmit() { if (missing) { attempt[1](attempt[0] + 1); return; } attempt[1](0); phase[1]('waiting'); }
  var slots = X.slots.map(function (s) { return Object.assign({}, s, { conflict: F.overlaps(s.start, s.minutes, X.booked.start, X.booked.minutes) }); });
  function confirmSlot() {
    busy[1](true);
    setTimeout(function () {
      busy[1](false);
      if (replacing[0] && failReplace[0]) { failure[1](true); return; }
      failure[1](false); meeting[1](sel[0]); sel[1](null); replacing[1](false);
    }, 600);
  }
  function reset() { phase[1]('revision'); a1[1]({}); sel[1](null); meeting[1](null); failReplace[1](false); failure[1](false); replacing[1](false); attempt[1](0); tab[1]('revisi'); }
  var next = phase[0] === 'revision'
    ? h(TR.NextStep, { title: 'Jawab pertanyaan revisi', due: '2026-11-10', action: h(TR.Button, { intent: 'primary', onClick: function () { tab[1]('revisi'); } }, 'Jawab revisi') }, 'Mitra Demo A menunggu satu jawaban wajib sebelum memutuskan.')
    : phase[0] === 'waiting'
      ? h(TR.NextStep, { who: 'other', title: 'Mitra Demo A sedang meninjau jawaban Anda' }, 'Anda tidak perlu melakukan apa pun sekarang.')
      : meeting[0]
        ? h(TR.NextStep, { who: 'other', title: 'Pertemuan sudah dikonfirmasi' }, 'Catat hasil pertemuan setelah selesai. Waktu yang berlalu saja tidak berarti diskusi selesai.')
        : h(TR.NextStep, { title: 'Pilih waktu diskusi', action: h(TR.Button, { intent: 'primary', onClick: function () { tab[1]('jadwal'); } }, 'Pilih waktu') }, 'Mitra menyetujui diskusi. Ini belum berarti pendanaan atau kerja sama.');
  var revision = phase[0] === 'revision'
    ? h('div', { className: 'tr-stack' },
        attempt[0] > 0 && errors.length ? h(TR.ErrorSummary, { errors: errors, focusKey: attempt[0] }) : null,
        h(TR.RevisionItem, { id: 'q1', round: 1, index: 1, required: true, due: '2026-11-10', question: 'Berapa anggaran pilot yang Anda perlukan?', reason: 'Kami perlu menilai cakupan pilot.', value: a1[0], onChange: a1[1], error: attempt[0] > 0 && missing ? 'Pilih tanggapan untuk pertanyaan anggaran pilot.' : null }),
        h(TR.RevisionItem, { round: 1, index: 2, question: 'Apakah kapasitas 20 L/jam dapat ikut diuji?', reason: 'Kapasitas itu masih direncanakan.', value: a2[0], onChange: a2[1] }),
        h('div', { className: 'tr-row' }, h(TR.Button, { intent: 'primary', onClick: resubmit }, 'Kirim ulang pitching')))
    : h(TR.Status, { tone: 'neutral', label: 'Jawaban terkirim' }, 'Putaran 1 tersimpan di riwayat. Rencana 20 L/jam tetap berstatus direncanakan.');
  var schedule = phase[0] !== 'approved'
    ? h(TR.EmptyState, { icon: 'calendar', title: 'Belum ada usulan waktu' }, 'Jadwal dibuka setelah mitra menyetujui diskusi.')
    : h('div', { className: 'tr-stack' },
        meeting[0] ? h(TR.Status, { tone: 'success', label: 'Pertemuan berlaku' }, F.longDate(slots.filter(function (s) { return s.id === meeting[0]; })[0].start, 'Asia/Jakarta') + ', ' + F.slotTime(slots.filter(function (s) { return s.id === meeting[0]; })[0].start, 60, 'Asia/Jakarta')) : null,
        meeting[0] && !replacing[0] ? h('div', { className: 'tr-row' }, h(TR.Button, { onClick: function () { replacing[1](true); } }, 'Usulkan penggantian')) : null,
        !meeting[0] || replacing[0] ? h(TR.ScheduleSlotList, { slots: slots.map(function (s) { return Object.assign({}, s, { conflict: s.conflict || s.id === meeting[0] }); }), zone: 'Asia/Jakarta', otherZone: 'Asia/Makassar', agenda: 'Membahas cakupan validasi prototipe.', selectedId: sel[0], onSelect: sel[1], busy: busy[0], onConfirm: confirmSlot, onPropose: function () {},
          error: failure[0] ? h(TR.Status, { tone: 'danger', label: 'Penggantian gagal', live: 'alert' }, 'Jadwal semula tetap berlaku. Pilihan Anda belum hilang, silakan coba lagi.') : null }) : null);
  return h(TR.Screen, { current: nav[0], onNavigate: nav[1], provenance: X.provenance, title: 'ClearSpring dan Mitra Demo A', subtitle: 'Dukungan Proyek: validasi prototipe',
    context: h(TR.ContextSwitcher, { value: ctx[0], onChange: ctx[1], options: X.contexts }), next: next,
    aside: h('div', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Status saat ini'),
      h(TR.Status, { tone: 'neutral', icon: 'chat', label: phase[0] === 'revision' ? 'Revisi diminta' : phase[0] === 'waiting' ? 'Sedang ditinjau' : 'Disetujui untuk diskusi' }),
      h(TR.FinancialScope, Object.assign({ compact: true }, X.F01.financial))) },
    h(TR.Tabs, { label: 'Ruang pitching', value: tab[0], onChange: tab[1], tabs: [
      { id: 'revisi', label: 'Revisi', content: revision },
      { id: 'jadwal', label: 'Jadwal', content: schedule }] }),
    h(TR.demo.Controls, { state: { reset: reset } },
      h(TR.Button, { onClick: function () { phase[1]('approved'); tab[1]('jadwal'); } }, 'Mitra menyetujui diskusi'),
      h(TR.Checkbox, { label: 'Penggantian jadwal gagal', checked: failReplace[0], onChange: failReplace[1] })));`
  },
  {
    name: 'PatternRelationship', group: 'Patterns', height: 1100, root: '',
    demo: `
  var FIELDS = [{ id: 'nama', label: 'Nama mitra', value: 'Mitra Demo A' }, { id: 'jenis', label: 'Jenis hubungan', value: 'Proyek' }, { id: 'cakupan', label: 'Cakupan', value: 'Validasi prototipe selama 6 bulan' }, { id: 'tanggal', label: 'Tanggal mulai', value: '1 Desember 2026' }, { id: 'nilai', label: 'Nilai dukungan', value: 'USD 25.000' }];
  var ALL = FIELDS.map(function (f) { return f.id; });
  var version = useState(1), mine = useState(ALL), mineConf = useState(null), otherConf = useState(null), restricted = useState([]), busy = useState(false);
  var nav = useState('pitching'), ctx = useState('pribadi'), asked = useState(false);
  var otherSelected = ['nama', 'jenis', 'cakupan', 'tanggal'];
  var v = version[0], both = mineConf[0] === v && otherConf[0] === v;
  function toggle(id, on) { mine[1](on ? mine[0].concat(id) : mine[0].filter(function (x) { return x !== id; })); }
  function confirm() { busy[1](true); setTimeout(function () { busy[1](false); mineConf[1](v); }, 500); }
  function correction() { version[1](2); mineConf[1](null); otherConf[1](null); asked[1](true); restricted[1]([]); }
  function reset() { version[1](1); mine[1](ALL); mineConf[1](null); otherConf[1](null); restricted[1]([]); asked[1](false); }
  var props = { version: v, type: 'Kerja Sama proyek. Hubungan ini bukan kepemilikan saham, walaupun memuat nilai uang.', fields: FIELDS,
    mine: { name: 'Rani', selected: mine[0], confirmedVersion: mineConf[0] }, other: { name: 'Mitra Demo A', selected: otherSelected, confirmedVersion: otherConf[0] }, restricted: restricted[0],
    summary: h(TR.SummaryList, { rows: [{ id: 'r1', label: 'Pihak', value: 'Rani (ClearSpring) dan Mitra Demo A' }, { id: 'r2', label: 'Ringkasan', value: v === 1 ? 'Validasi prototipe.' : 'Validasi prototipe selama 6 bulan, termasuk uji kapasitas 10 L/jam.' }] }),
    busy: busy[0], onToggle: toggle, onConfirm: confirm, onRequestChange: function () {}, onRestrict: function (id) { restricted[1](restricted[0].concat(id)); } };
  var pub = TR.effectiveFields(props);
  var next = both
    ? h(TR.NextStep, { who: 'other', title: 'Kerja Sama dikonfirmasi kedua pihak' }, 'Konfirmasi ini mencatat ringkasan yang disepakati. Ini bukan pelaksanaan transaksi hukum.')
    : mineConf[0] === v
      ? h(TR.NextStep, { who: 'other', title: 'Menunggu Mitra Demo A mengonfirmasi versi ' + v }, 'Satu konfirmasi belum berarti disepakati bersama.')
      : h(TR.NextStep, { title: 'Periksa dan konfirmasi versi ' + v }, asked[0] ? 'Mitra Demo A mengoreksi ringkasan, jadi konfirmasi versi 1 tidak berlaku lagi.' : 'Pilih data yang boleh tampil, lalu konfirmasi.');
  return h(TR.Screen, { current: nav[0], onNavigate: nav[1], provenance: X.provenance, title: 'Kerja Sama ClearSpring', subtitle: 'Dengan Mitra Demo A', next: next,
    context: h(TR.ContextSwitcher, { value: ctx[0], onChange: ctx[1], options: X.contexts }),
    aside: h('div', { className: 'tr-panel' }, h('h2', { className: 'tr-sys-type-heading-sm' }, 'Tampilan publik'),
      pub.length ? h(TR.SummaryList, { rows: FIELDS.filter(function (f) { return pub.indexOf(f.id) >= 0; }).map(function (f) { return { id: 'p-' + f.id, label: f.label, value: f.value }; }) })
        : h('p', { className: 'tr-muted' }, 'Belum ada yang tampil. Publik baru terlihat setelah kedua pihak mengonfirmasi versi yang sama.')) },
    h('section', { className: 'tr-panel' }, h(TR.PartnershipConsent, props)),
    h(TR.demo.Controls, { state: { reset: reset } },
      v === 1 ? h(TR.Button, { onClick: correction }, 'Mitra mengoreksi ke versi 2') : null,
      mineConf[0] === v && otherConf[0] !== v ? h(TR.Button, { onClick: function () { otherConf[1](v); } }, 'Mitra mengonfirmasi versi ' + v) : null));`
  }
];
