/* @ds-bundle: {"format":4,"namespace":"HD","components":[{"name":"Button"},{"name":"IconButton"},{"name":"TextField"},{"name":"NumericField"},{"name":"ChoiceGroup"},{"name":"PeriodSelector"},{"name":"TabNavigation"},{"name":"SheetDialog"},{"name":"Disclosure"},{"name":"Notice"},{"name":"ErrorSummary"},{"name":"ProgressStatus"},{"name":"EnergyMetric"},{"name":"CostEstimate"},{"name":"ScopeSummary"},{"name":"DataQuality"},{"name":"AssetRow"},{"name":"ContributionRanking"},{"name":"HistoryChart"},{"name":"ChartDataAlternative"},{"name":"InsightSummary"},{"name":"EvidencePanel"},{"name":"ImportPreview"},{"name":"ScheduleWindows"},{"name":"OutputMetricPreview"},{"name":"Screen"},{"name":"Icon"}]} */
/* HematDaya Design System 1.0.0-draft \u2014 window.HD. Hand-written, no build step; reads window.React. */
(function () {
  'use strict';
  var React = window.React;
  var h = React.createElement;
  var Fragment = React.Fragment;
  var useState = React.useState, useEffect = React.useEffect, useRef = React.useRef, useId = React.useId;

  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }
  function ids() { return Array.prototype.filter.call(arguments, Boolean).join(' ') || undefined; }

  /* ================= formatting (Indonesian display; canonical numbers stay numbers) ================= */
  var nf3 = new Intl.NumberFormat('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 });
  var nf2 = new Intl.NumberFormat('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var nf0 = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 0 });
  var nfAny = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 3 });
  var MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
  var MINUS = '\u2212';
  function finite(v) { return typeof v === 'number' && isFinite(v); }
  var format = {
    /** 14.7 -> "14,700 kWh"; null/NaN -> null (never "0"). */
    kwh: function (v, unit) { return finite(v) ? nf3.format(v) + ' ' + (unit || 'kWh') : null; },
    signedKwh: function (v) { return finite(v) ? (v > 0 ? '+' : v < 0 ? MINUS : '') + nf3.format(Math.abs(v)) + ' kWh' : null; },
    /** 22050 -> "Rp22.050"; rounds the unrounded product once, at display. */
    rupiah: function (v) { return finite(v) ? (v < 0 ? MINUS : '') + 'Rp' + nf0.format(Math.round(Math.abs(v))) : null; },
    /** ratio 0.5714 -> "57,14%"; null when the reference is zero or missing. */
    percent: function (part, whole) { return finite(part) && finite(whole) && whole !== 0 ? nf2.format((part / whole) * 100) + '%' : null; },
    signedPercent: function (delta, reference) { if (!finite(delta) || !finite(reference) || reference === 0) return null; var p = (delta / reference) * 100; return (p > 0 ? '+' : p < 0 ? MINUS : '') + nf2.format(Math.abs(p)) + '%'; },
    number: function (v) { return finite(v) ? nfAny.format(v) : null; },
    /** ("2026-10-19","2026-10-25") -> "19\u201325 Oktober 2026". */
    dateRange: function (start, end) {
      var a = start.split('-').map(Number), b = (end || start).split('-').map(Number);
      if (start === (end || start)) return a[2] + ' ' + MONTHS[a[1] - 1] + ' ' + a[0];
      if (a[0] === b[0] && a[1] === b[1]) return a[2] + '\u2013' + b[2] + ' ' + MONTHS[b[1] - 1] + ' ' + b[0];
      if (a[0] === b[0]) return a[2] + ' ' + MONTHS[a[1] - 1] + '\u2013' + b[2] + ' ' + MONTHS[b[1] - 1] + ' ' + b[0];
      return a[2] + ' ' + MONTHS[a[1] - 1] + ' ' + a[0] + '\u2013' + b[2] + ' ' + MONTHS[b[1] - 1] + ' ' + b[0];
    },
    /** "07:00" -> "07.00". */
    time: function (hhmm) { return String(hhmm).replace(':', '.'); },
    /**
     * Indonesian decimal input. "" -> {empty:true,value:null}; "1,5" -> 1.5; "1.500" -> 1500 (dot groups of three);
     * "1.5" is rejected with a correction instead of guessed.
     */
    parseDecimal: function (text) {
      var s = String(text == null ? '' : text).trim().replace(/\s/g, '');
      if (s === '') return { empty: true, valid: true, value: null };
      if (/^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$/.test(s)) return { empty: false, valid: true, value: Number(s.replace(/\./g, '').replace(',', '.')) };
      if (/^-?\d+\.\d{1,2}$|^-?\d+\.\d{4,}$/.test(s)) return { empty: false, valid: false, value: null, error: 'Gunakan koma untuk desimal, misalnya 1,5.' };
      return { empty: false, valid: false, value: null, error: 'Isi dengan angka, misalnya 1.500 atau 0,25.' };
    }
  };

  /* ================= Icon (own 24-unit stroke set, no external library) ================= */
  var ICONS = {
    home: 'M4 11 12 4l8 7M6 9.5V20h12V9.5M10 20v-5h4v5',
    devices: 'M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM8 8h8M12 17.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    saran: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.8.6 1.1 1.4 1.1 2.2v.5h5V16c0-.8.3-1.6 1.1-2.2A6 6 0 0 0 12 3z',
    chevronRight: 'M9 6l6 6-6 6', chevronLeft: 'M15 6l-6 6 6 6', chevronDown: 'M6 9l6 6 6-6',
    close: 'M6 6l12 12M18 6 6 18',
    info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01',
    attention: 'M12 4l9 15.5H3L12 4zM12 10v4M12 16.8h.01',
    error: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9 9l6 6M15 9l-6 6',
    success: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8 12.5l2.7 2.6L16 9.6',
    unknown: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.6 9.4a2.5 2.5 0 1 1 3.4 2.4c-.6.3-1 .8-1 1.5v.5M12 16.8h.01',
    refresh: 'M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5',
    calendar: 'M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM4 10h16M8 3v4M16 3v4',
    clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
    offline: 'M3 3l18 18M5 12.5a10 10 0 0 1 4.5-2.6M14.5 9.9A10 10 0 0 1 19 12.5M8.5 16a5 5 0 0 1 7 0M12 19.5h.01',
    upload: 'M12 15V4M7.5 8.5 12 4l4.5 4.5M5 15v5h14v-5',
    scope: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    file: 'M7 3h7l4 4v14H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM14 3v4h4M9 13h6M9 17h6'
  };
  function Icon(p) {
    return h('svg', { className: cx('hd-icon', p.size === 'small' && 'hd-icon--small', p.className), viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': 'true', focusable: 'false' },
      h('path', { d: ICONS[p.name] || ICONS.info }));
  }
  function Spinner() {
    return h('svg', { className: 'hd-spinner', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 3, strokeLinecap: 'round', 'aria-hidden': 'true', focusable: 'false' },
      h('path', { d: 'M12 3a9 9 0 1 1-9 9', opacity: 1 }));
  }
  function Tag(p) { return h('span', { className: 'hd-tag type-label-strong' }, p.children); }
  var PROVENANCE = { demo: 'Demo \u00b7 Data simulasi', import: 'Impor CSV', live: 'Sumber langsung' };
  function Heading(p) { return h('h' + (p.level || 2), { className: p.className, id: p.id }, p.children); }

  /* ================= primitives ================= */

  function Button(p) {
    var reasonId = useId();
    var variant = p.variant || 'secondary';
    var disabled = !!p.disabledReason;
    var busy = !!p.loading;
    function onClick(e) { if (disabled || busy) { e.preventDefault(); return; } if (p.onClick) p.onClick(e); }
    var btn = h('button', {
      type: p.type || 'button', id: p.id, form: p.form,
      className: cx('hd-root hd-btn', 'hd-btn--' + variant, p.fullWidth && 'hd-btn--full', 'type-body-strong'),
      'aria-disabled': disabled || busy ? 'true' : undefined,
      'aria-busy': busy ? 'true' : undefined,
      'aria-describedby': ids(disabled && reasonId, p.describedBy),
      onClick: onClick
    }, busy ? h(Spinner) : p.icon ? h(Icon, { name: p.icon, size: 'small' }) : null,
      h('span', null, busy ? (p.loadingLabel || 'Memproses\u2026') : p.children));
    if (!disabled) return btn;
    return h('span', { className: cx('hd-root hd-btn-wrap', p.fullWidth && 'hd-btn--full') }, btn,
      h('span', { id: reasonId, className: 'hd-btn-reason type-label' }, p.disabledReason));
  }

  function IconButton(p) {
    var reasonId = useId();
    var disabled = !!p.disabledReason;
    var btn = h('button', {
      type: 'button', className: cx('hd-root hd-iconbtn', !p.showLabel && 'hd-iconbtn--icon-only', 'type-label-strong'),
      'aria-label': p.showLabel ? undefined : p.label, title: p.tooltip,
      'aria-disabled': disabled ? 'true' : undefined, 'aria-describedby': disabled ? reasonId : undefined,
      onClick: function (e) { if (disabled) { e.preventDefault(); return; } if (p.onClick) p.onClick(e); }
    }, h(Icon, { name: p.icon }), p.showLabel ? h('span', null, p.label) : null);
    if (!disabled) return btn;
    return h('span', { className: 'hd-root hd-btn-wrap' }, btn, h('span', { id: reasonId, className: 'hd-btn-reason type-label' }, p.disabledReason));
  }

  function FieldShell(p) {
    var marker = p.required ? ' (wajib)' : p.optional ? ' (opsional)' : p.readOnly ? ' (hanya baca)' : null;
    return h('div', { className: cx('hd-root hd-field', p.error && 'hd-field--error') },
      h('label', { htmlFor: p.id, className: 'hd-field__label type-label-strong' }, p.label, marker && h('span', { className: 'hd-field__marker' }, marker)),
      p.help && h('p', { id: p.id + '-help', className: 'hd-field__help type-label' }, p.help),
      p.error && h('p', { id: p.id + '-error', className: 'hd-field__error type-label-strong' }, h(Icon, { name: 'error', size: 'small' }), h('span', null, p.error)),
      p.children,
      p.note && h('p', { id: p.id + '-note', className: 'hd-field__note type-label' }, p.note));
  }
  function describedBy(id, p, note) { return ids(p.help && id + '-help', p.error && id + '-error', note && id + '-note'); }

  function TextField(p) {
    var auto = useId(); var id = p.id || auto;
    var note = p.disabledReason || p.draftNote;
    var common = {
      id: id, className: 'hd-input type-body', value: p.value == null ? '' : p.value, name: p.name,
      required: p.required || undefined, readOnly: p.readOnly || !!p.disabledReason || undefined,
      'aria-disabled': p.disabledReason ? 'true' : undefined, 'aria-invalid': p.error ? 'true' : undefined,
      'aria-describedby': describedBy(id, p, note), autoComplete: p.autoComplete || 'off', placeholder: p.placeholder,
      onChange: function (e) { if (p.onChange) p.onChange(e.target.value); }, onBlur: p.onBlur
    };
    return h(FieldShell, { id: id, label: p.label, help: p.help, error: p.error, required: p.required, optional: p.optional, readOnly: p.readOnly, note: note },
      p.multiline ? h('textarea', Object.assign({ rows: p.rows || 3 }, common)) : h('input', Object.assign({ type: p.type || 'text' }, common)));
  }

  function NumericField(p) {
    var auto = useId(); var id = p.id || auto;
    var touched = useState(false);
    var parsed = format.parseDecimal(p.value);
    var ruleError = null;
    if (parsed.valid && !parsed.empty) {
      if (!p.allowNegative && parsed.value < 0) ruleError = 'Nilai tidak boleh negatif.';
      else if (p.max != null && parsed.value > p.max) ruleError = 'Nilai paling besar ' + format.number(p.max) + (p.unit ? ' ' + p.unit : '') + '.';
    }
    if (parsed.empty && p.required) ruleError = 'Isi ' + p.label.toLowerCase() + '.';
    var shownError = p.error || (touched[0] || p.showErrors ? (parsed.error || ruleError) : null);
    var interpretation = parsed.empty ? 'Kosong \u2014 belum diisi, tidak dianggap 0.' : parsed.valid && parsed.value === 0 ? 'Tercatat 0 sebagai nilai yang diisi.' : null;
    var note = p.disabledReason || p.note || interpretation;
    return h(FieldShell, { id: id, label: p.label, help: p.help, error: shownError, required: p.required, optional: p.optional, note: note },
      h('div', { className: cx('hd-field__control', p.unit && 'hd-field__control--unit') },
        h('input', {
          id: id, type: 'text', inputMode: 'decimal', className: 'hd-input type-body hd-num', value: p.value == null ? '' : p.value, name: p.name,
          'aria-invalid': shownError ? 'true' : undefined, 'aria-describedby': ids(describedBy(id, { help: p.help, error: shownError }, note), p.unit && id + '-unit'),
          readOnly: !!p.disabledReason || undefined, 'aria-disabled': p.disabledReason ? 'true' : undefined, autoComplete: 'off',
          onChange: function (e) { if (p.onChange) p.onChange(e.target.value, format.parseDecimal(e.target.value)); },
          onBlur: function () { touched[1](true); }
        }),
        p.unit && h('span', { id: id + '-unit', className: 'hd-field__unit type-body' }, p.unit)));
  }

  function ChoiceGroup(p) {
    var name = useId();
    var type = p.type || 'radio';
    if (type === 'select') {
      return h(FieldShell, { id: name, label: p.legend, help: p.help, error: p.error, required: p.required, optional: p.optional },
        h('select', { id: name, className: 'hd-input type-body', value: p.value == null ? '' : p.value, 'aria-invalid': p.error ? 'true' : undefined, 'aria-describedby': describedBy(name, p),
          onChange: function (e) { if (p.onChange) p.onChange(e.target.value); } },
          p.placeholder ? h('option', { value: '' }, p.placeholder) : null,
          p.options.map(function (o) { return h('option', { key: o.value, value: o.value, disabled: !!o.disabledReason }, o.label); })));
    }
    var selected = type === 'checkbox' ? (p.value || []) : p.value;
    function toggle(v) {
      if (!p.onChange) return;
      if (type === 'checkbox') p.onChange(selected.indexOf(v) >= 0 ? selected.filter(function (x) { return x !== v; }) : selected.concat([v]));
      else p.onChange(v);
    }
    return h('fieldset', { className: 'hd-root hd-choice', id: p.id, 'aria-describedby': ids(p.help && name + '-help', p.error && name + '-error') },
      h('legend', { className: 'hd-choice__legend type-label-strong' }, p.legend, p.optional ? h('span', { className: 'hd-field__marker' }, ' (opsional)') : null),
      p.help && h('p', { id: name + '-help', className: 'hd-field__help type-label' }, p.help),
      p.error && h('p', { id: name + '-error', className: 'hd-field__error type-label-strong' }, h(Icon, { name: 'error', size: 'small' }), h('span', null, p.error)),
      h('div', { className: cx('hd-choice__options', p.inline && 'hd-choice__options--inline') },
        p.options.map(function (o) {
          var checked = type === 'checkbox' ? selected.indexOf(o.value) >= 0 : selected === o.value;
          var reasonId = name + '-' + o.value + '-reason';
          return h('label', { key: o.value, className: cx('hd-choice__option', checked && 'is-selected', o.disabledReason && 'is-disabled') },
            h('input', { type: type, name: name, value: o.value, checked: checked, id: o.id,
              disabled: !!o.disabledReason, 'aria-describedby': o.disabledReason ? reasonId : undefined,
              onChange: function () { toggle(o.value); } }),
            h('span', { className: 'hd-choice__text' },
              h('span', { className: 'hd-choice__label type-body' }, o.label),
              o.description && h('span', { className: 'hd-choice__desc type-label' }, o.description),
              o.disabledReason && h('span', { id: reasonId, className: 'hd-choice__desc type-label' }, o.disabledReason)));
        })));
  }

  var PRESETS = [{ id: 'today', label: 'Hari ini' }, { id: 'last7', label: '7 hari lengkap terakhir' }, { id: 'range', label: 'Pilih tanggal' }];
  function addDays(iso, n) { var d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function presetRange(id, today) { return id === 'today' ? { start: today, end: today } : id === 'last7' ? { start: addDays(today, -7), end: addDays(today, -1) } : null; }
  function PeriodSelector(p) {
    var today = p.today; // local date in Asia/Jakarta, supplied by the app (virtual now in demos)
    var committed = p.value;
    var draft = useState(committed.preset);
    var start = useState(committed.start); var end = useState(committed.end);
    var err = useState(null);
    var groupLabel = useId();
    function choose(id) {
      draft[1](id); err[1](null);
      if (id !== 'range') { var r = presetRange(id, today); p.onCommit({ preset: id, start: r.start, end: r.end }); }
    }
    function apply() {
      if (!start[0] || !end[0]) { err[1]('Isi tanggal mulai dan sampai.'); return; }
      if (end[0] < start[0]) { err[1]('Tanggal sampai harus sama atau setelah tanggal mulai.'); return; }
      if (end[0] > today) { err[1]('Tanggal sampai tidak boleh setelah hari ini (' + format.dateRange(today) + ').'); return; }
      err[1](null); p.onCommit({ preset: 'range', start: start[0], end: end[0] });
    }
    var pending = draft[0] === 'range' && (committed.preset !== 'range' || start[0] !== committed.start || end[0] !== committed.end);
    var committedLabel = format.dateRange(committed.start, committed.end) + (committed.preset === 'today' ? ' (sampai sekarang)' : '');
    return h('div', { className: 'hd-root hd-period' },
      h('p', { id: groupLabel, className: 'type-label-strong' }, p.label || 'Periode'),
      h('div', { className: 'hd-period__presets', role: 'group', 'aria-labelledby': groupLabel },
        PRESETS.map(function (o) {
          var on = draft[0] === o.id;
          return h('button', { key: o.id, type: 'button', 'aria-pressed': on ? 'true' : 'false', className: 'hd-period__preset type-body',
            onClick: function () { choose(o.id); } }, on ? h(Icon, { name: 'success', size: 'small' }) : null, o.label);
        })),
      draft[0] === 'range' && h('div', { className: 'hd-period__range' },
        h(TextField, { label: 'Mulai', type: 'date', value: start[0], onChange: start[1] }),
        h(TextField, { label: 'Sampai', type: 'date', value: end[0], onChange: end[1] }),
        h(Button, { variant: 'primary', onClick: apply }, 'Terapkan')),
      err[0] && h('p', { className: 'hd-field__error type-label-strong', role: 'alert' }, h(Icon, { name: 'error', size: 'small' }), h('span', null, err[0])),
      h('p', { className: 'hd-period__current type-label', 'aria-live': 'polite' }, h(Icon, { name: 'calendar', size: 'small' }),
        h('span', null, h('strong', null, 'Periode aktif: '), committedLabel, ' \u00b7 ', p.timezone || 'Asia/Jakarta', pending ? ' \u00b7 Pilihan tanggal belum diterapkan' : '')));
  }

  var DESTINATIONS = [{ id: 'beranda', label: 'Beranda', icon: 'home' }, { id: 'perangkat', label: 'Perangkat', icon: 'devices' }, { id: 'saran', label: 'Saran', icon: 'saran' }];
  function TabNavigation(p) {
    return h('nav', { className: 'hd-root hd-tabs', 'aria-label': 'Navigasi utama' },
      h('ul', { className: 'hd-tabs__list' }, DESTINATIONS.map(function (d) {
        var current = p.current === d.id;
        return h('li', { key: d.id }, h('a', {
          href: (p.hrefs && p.hrefs[d.id]) || '#' + d.id, className: 'hd-tabs__item', 'aria-current': current ? 'page' : undefined,
          onClick: function (e) { if (p.onNavigate) { e.preventDefault(); p.onNavigate(d.id); } }
        }, h(Icon, { name: d.icon }), h('span', { className: 'hd-tabs__label type-label' }, d.label)));
      })));
  }

  function SheetDialog(p) {
    var ref = useRef(null), titleRef = useRef(null), returnTo = useRef(null);
    var titleId = useId();
    useEffect(function () {
      var d = ref.current; if (!d) return;
      if (p.open && !d.open) {
        returnTo.current = document.activeElement;
        d.showModal();
        var target = d.querySelector('[data-autofocus]') || titleRef.current;
        if (target) target.focus();
      } else if (!p.open && d.open) {
        d.close();
        if (returnTo.current && returnTo.current.focus) returnTo.current.focus();
      }
    }, [p.open]);
    function requestClose(reason) { if (p.onClose) p.onClose(reason); }
    return h('dialog', {
      ref: ref, className: 'hd-root hd-sheet', 'aria-labelledby': titleId,
      onCancel: function (e) { e.preventDefault(); requestClose('escape'); }
    },
      h('div', { className: 'hd-sheet__header' },
        h('h2', { id: titleId, ref: titleRef, tabIndex: -1, className: 'hd-sheet__title type-section' }, p.title),
        h(IconButton, { icon: 'close', label: p.closeLabel || 'Tutup', onClick: function () { requestClose('close'); } })),
      h('div', { className: 'hd-sheet__body type-body' }, p.children),
      p.footer && h('div', { className: 'hd-sheet__footer' }, p.footer));
  }

  function Disclosure(p) {
    return h('details', { className: 'hd-root hd-disclosure', open: p.defaultOpen || undefined, onToggle: p.onToggle },
      h('summary', { className: 'hd-disclosure__summary type-body-strong' }, h(Icon, { name: 'chevronDown', className: 'hd-disclosure__chevron' }), h('span', null, p.summary)),
      h('div', { className: 'hd-disclosure__body type-body' }, p.children));
  }

  var TONES = { info: ['info', 'Info'], attention: ['attention', 'Perhatian'], error: ['error', 'Kesalahan'], success: ['success', 'Berhasil'], neutral: ['info', null] };
  function Notice(p) {
    var tone = TONES[p.tone] ? p.tone : 'neutral';
    return h('div', { className: cx('hd-root hd-notice', 'hd-notice--' + tone), role: p.live ? (tone === 'error' ? 'alert' : 'status') : undefined },
      h(Icon, { name: p.icon || TONES[tone][0] }),
      h('div', { className: 'hd-notice__body' },
        h('p', { className: 'type-body-strong' }, TONES[tone][1] && h('span', { className: 'hd-sr-only' }, TONES[tone][1] + ': '), p.title),
        p.children && h('div', { className: 'type-body' }, p.children),
        p.action && h('div', { className: 'hd-notice__action' }, p.action)));
  }

  function focusTarget(id) {
    var el = document.getElementById(id); if (!el) return;
    if (el.tabIndex < 0 && !/^(INPUT|SELECT|TEXTAREA|BUTTON|A)$/.test(el.tagName)) el.setAttribute('tabindex', '-1');
    el.focus(); if (el.scrollIntoView) el.scrollIntoView({ block: 'center' });
  }
  function ErrorSummary(p) {
    var ref = useRef(null); var titleId = useId();
    useEffect(function () { if (p.autoFocus !== false && ref.current) ref.current.focus(); }, [p.submitCount]);
    if (!p.errors || !p.errors.length) return null;
    return h('div', { ref: ref, tabIndex: -1, className: 'hd-root hd-errsum', role: 'alert', 'aria-labelledby': titleId },
      h('h2', { id: titleId, className: 'type-section' }, p.title || ('Periksa ' + p.errors.length + ' isian berikut')),
      p.convention && h('p', { className: 'type-label' }, p.convention),
      h('ul', { className: 'hd-errsum__list type-body' }, p.errors.map(function (e) {
        return h('li', { key: e.targetId + e.text }, h('a', { href: '#' + e.targetId, onClick: function (ev) { ev.preventDefault(); focusTarget(e.targetId); } }, e.text));
      })));
  }

  var PROGRESS = {
    loading: { label: 'Memuat data\u2026' }, saving: { label: 'Menyimpan\u2026' },
    unknown: { label: 'Status penyimpanan belum diketahui', icon: 'unknown', detail: 'Koneksi terputus sebelum server mengonfirmasi. Data belum tentu tersimpan; periksa sebelum mengirim ulang.' },
    success: { label: 'Tersimpan', icon: 'success' },
    failure: { label: 'Gagal menyimpan', icon: 'error', detail: 'Server menolak atau tidak menjawab. Isian Anda masih ada di layar ini.' }
  };
  function ProgressStatus(p) {
    var s = PROGRESS[p.state];
    return h('div', { className: cx('hd-root hd-progress', s && 'hd-progress--' + p.state), role: 'status', 'aria-live': 'polite' },
      s ? h(Fragment, null,
        s.icon ? h(Icon, { name: s.icon }) : h(Spinner),
        h('div', { className: 'hd-progress__body' },
          h('p', { className: 'type-body-strong' }, p.label || s.label),
          (p.detail || s.detail) && h('p', { className: 'type-label hd-secondary' }, p.detail || s.detail),
          p.state === 'unknown' && p.onCheck && h('div', { className: 'hd-row' }, h(Button, { variant: 'secondary', icon: 'refresh', onClick: p.onCheck, loading: p.checking, loadingLabel: 'Memeriksa\u2026' }, 'Periksa status')),
          p.state === 'failure' && p.onRetry && h('div', { className: 'hd-row' }, h(Button, { variant: 'secondary', icon: 'refresh', onClick: p.onRetry }, 'Coba lagi')))) : null);
  }

  /* ================= domain ================= */

  function EnergyMetric(p) {
    var titleId = useId();
    var quality = p.quality || 'complete';
    var hasValue = quality !== 'unavailable' && finite(p.kwh);
    return h('section', { className: 'hd-root hd-metric', 'aria-labelledby': titleId },
      h('div', { className: 'hd-row', style: { justifyContent: 'space-between' } },
        h(Heading, { level: p.headingLevel, id: titleId, className: 'type-label-strong' }, p.label || 'Energi yang dipantau'),
        p.provenance && h(Tag, null, PROVENANCE[p.provenance] || p.provenance)),
      h('p', { className: 'hd-metric__context type-label' }, [p.periodLabel, p.scopeLabel].filter(Boolean).join(' \u00b7 ')),
      hasValue
        ? h('p', { className: 'hd-metric__value hd-num' }, h('span', { className: 'type-metric' }, nf3.format(p.kwh)), h('span', { className: 'type-section' }, p.unit || 'kWh'))
        : h('div', { className: 'hd-empty' }, h('p', { className: 'type-section' }, 'Belum ada data energi'),
            h('p', { className: 'type-body hd-secondary' }, p.emptyDetail || 'Tidak ada pengukuran untuk periode dan cakupan ini. Tidak ditampilkan sebagai 0 kWh.'),
            p.emptyAction),
      hasValue && quality === 'partial' && h('p', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: 'attention', size: 'small' }),
        h('span', null, 'Sebagian data belum tersedia', finite(p.completeness) ? ' \u00b7 Kelengkapan data: ' + nf0.format(p.completeness * 100) + '% periode' : '', p.gapLabel ? ' \u00b7 ' + p.gapLabel : '', '. Angka ini hanya energi yang terekam.')),
      hasValue && quality === 'complete' && p.kwh === 0 && h('p', { className: 'hd-qualifier hd-qualifier--neutral type-label' }, h(Icon, { name: 'info', size: 'small' }),
        h('span', null, 'Nol terukur dengan data lengkap \u2014 bukan data kosong.')),
      p.children);
  }

  function CostEstimate(p) {
    var titleId = useId();
    var body;
    if (!finite(p.kwh)) {
      body = h('p', { className: 'type-body' }, 'Biaya belum dapat dihitung \u2014 belum ada data energi.');
    } else if (p.tariff == null) {
      body = h(Fragment, null,
        h('p', { className: 'type-body-strong' }, 'Biaya belum dihitung \u2014 tarif belum diatur'),
        h('p', { className: 'type-label hd-secondary' }, 'Energi tetap ditampilkan. Biaya tidak dianggap Rp0.'),
        p.onSetTariff && h('div', null, h(Button, { variant: 'text', onClick: p.onSetTariff }, 'Atur tarif (opsional)')));
    } else {
      var cost = p.kwh * p.tariff; // computed from the unrounded energy, rounded once for display
      body = h(Fragment, null,
        h('p', { className: 'hd-metric__value hd-num' }, h('span', { className: 'type-title' }, format.rupiah(cost))),
        h('p', { className: 'type-label' }, (p.tariffSource === 'synthetic' ? 'Tarif simulasi ' : 'Tarif ') + format.rupiah(p.tariff) + '/kWh \u00d7 ' + format.kwh(p.kwh)),
        p.tariff === 0 && h('p', { className: 'hd-qualifier hd-qualifier--neutral type-label' }, h(Icon, { name: 'info', size: 'small' }), h('span', null, 'Tarif diatur Rp0/kWh. Periksa pengaturan tarif bila ini tidak disengaja.')),
        p.partial && h('p', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: 'attention', size: 'small' }), h('span', null, 'Dihitung dari energi yang terekam saja; sebagian data belum tersedia.')),
        h('p', { className: 'type-label hd-secondary' }, 'Bukan tagihan listrik. Hanya energi terpantau dalam cakupan ini.'));
    }
    return h('section', { className: 'hd-root hd-cost', 'aria-labelledby': titleId },
      h(Heading, { level: p.headingLevel, id: titleId, className: 'type-label-strong' }, 'Estimasi biaya energi terpantau'), body);
  }

  function ScopeSummary(p) {
    var included = p.included || [], excluded = p.excluded || [];
    var unit = p.unitLabel || 'perangkat';
    var count = p.count != null ? p.count : included.length;
    var overlap = p.overlap || 'none';
    return h('section', { className: 'hd-root hd-scope', 'aria-label': 'Cakupan pengukuran' },
      h('p', { className: 'hd-row type-label-strong' }, h(Icon, { name: 'scope', size: 'small' }), 'Cakupan pengukuran: ' + count + ' ' + unit),
      excluded.length > 0 && h('p', { className: 'type-label' }, excluded.length + ' ' + unit + ' lain tidak termasuk: ' + excluded.join(', ') + '.'),
      overlap === 'parentChild' && h(Fragment, null,
        h(Notice, { tone: 'info', title: p.parent.name + ' sudah mencakup ' + p.child.name },
          'Nilai keduanya tidak dijumlahkan. Pilih satu tampilan: ' + p.parent.name + ' ' + format.kwh(p.parent.kwh) + ', atau ' + p.child.name + ' saja ' + format.kwh(p.child.kwh) + '.'),
        h(ChoiceGroup, { legend: 'Tampilkan cakupan', value: p.view, onChange: p.onViewChange, options: [
          { value: 'parent', label: p.parent.name + ' \u2014 ' + format.kwh(p.parent.kwh), description: p.parent.description || 'Seluruh beban di belakang meteran ini, termasuk ' + p.child.name + '.' },
          { value: 'child', label: p.child.name + ' saja \u2014 ' + format.kwh(p.child.kwh), description: p.child.description || 'Hanya sub-meteran ' + p.child.name + '.' }] })),
      overlap === 'unknown' && h(Fragment, null,
        h(Notice, { tone: 'attention', title: 'Total gabungan belum dapat ditampilkan' },
          'Hubungan cakupan antar sumber belum diketahui, sehingga nilainya bisa tumpang tindih. Lihat nilai masing-masing atau pilih satu tampilan yang valid.'),
        p.values && h('ul', { className: 'hd-scope__values type-body' }, p.values.map(function (v) {
          return h('li', { key: v.name }, h('span', null, v.name), h('span', { className: 'hd-num type-body-strong' }, format.kwh(v.kwh)));
        }))),
      included.length > 0 && h(Disclosure, { summary: 'Lihat ' + unit + ' yang termasuk' }, h('ul', { className: 'type-body' }, included.map(function (n) { return h('li', { key: n }, n); }))));
  }

  function QualityRow(p) {
    return h('div', { className: cx('hd-quality__row', p.attention && 'is-attention') },
      h('dt', { className: 'type-label-strong' }, h(Icon, { name: p.icon, size: 'small' }), h('span', null, p.term)), h('dd', { className: 'type-label' }, p.children));
  }
  function DataQuality(p) {
    var rows = [];
    if (p.completeness !== undefined) {
      var pct = finite(p.completeness) ? nf0.format(p.completeness * 100) + '% periode' : 'Belum diketahui';
      rows.push(h(QualityRow, { key: 'c', icon: p.completeness < 1 ? 'attention' : 'success', attention: p.completeness < 1, term: 'Kelengkapan data' },
        h('span', null, pct), p.gaps && h('span', null, 'Tidak ada data: ' + p.gaps), p.completeness < 1 && h('span', { className: 'hd-secondary' }, 'Kelengkapan waktu, bukan tingkat akurasi.')));
    }
    var f = p.freshness;
    if (f) {
      if (f.state === 'stale') rows.push(h(QualityRow, { key: 'f', icon: 'clock', attention: true, term: 'Kesegaran sumber' },
        h('span', null, 'Data belum diperbarui \u00b7 pengukuran terakhir ' + f.lastMeasurement),
        h('span', { className: 'hd-secondary' }, 'Ini tentang sumber data, bukan tanda perangkat mati.'),
        p.onCheckSource && h(Button, { variant: 'text', icon: 'refresh', onClick: p.onCheckSource, loading: p.checkingSource, loadingLabel: 'Memeriksa sumber\u2026' }, 'Periksa sumber')));
      else if (f.state === 'historical') rows.push(h(QualityRow, { key: 'f', icon: 'file', term: 'Kesegaran sumber' },
        h('span', null, 'Data impor historis \u00b7 ' + f.importRange), h('span', { className: 'hd-secondary' }, 'Bukan sambungan langsung yang gagal.'),
        p.onViewPeriod && h(Button, { variant: 'text', icon: 'calendar', onClick: p.onViewPeriod }, 'Lihat periode data')));
      else rows.push(h(QualityRow, { key: 'f', icon: 'clock', term: 'Kesegaran sumber' }, h('span', null, 'Pengukuran terakhir ' + f.lastMeasurement)));
    }
    if (p.client === 'offline') rows.push(h(QualityRow, { key: 'o', icon: 'offline', attention: true, term: 'Koneksi aplikasi' },
      h('span', null, 'Aplikasi sedang luring \u00b7 menampilkan data terkonfirmasi ' + (p.cachedAge || '')),
      h('span', { className: 'hd-secondary' }, 'Perubahan disimpan sebagai draf dan belum terkirim.')));
    if (p.source) rows.push(h(QualityRow, { key: 's', icon: p.source === 'demo' ? 'info' : p.source === 'import' ? 'upload' : 'devices', term: 'Asal data' }, h('span', null, PROVENANCE[p.source] || p.source)));
    return h('section', { className: 'hd-root', 'aria-label': p.label || 'Kualitas data' }, h('dl', { className: 'hd-quality' }, rows));
  }

  var KINDS = { device: 'Perangkat', circuit: 'Sirkuit', group: 'Grup beban', meter: 'Meteran utama' };
  var QUALITY_TEXT = { partial: 'Sebagian data belum tersedia', stale: 'Data belum diperbarui', unavailable: 'Belum ada data energi' };
  function AssetRow(p) {
    var q = p.quality && p.quality !== 'complete' ? (p.qualityLabel || QUALITY_TEXT[p.quality]) : null;
    var value = p.quality === 'unavailable' ? null : format.kwh(p.kwh);
    return h('a', { className: 'hd-root hd-asset', href: p.href || '#', onClick: function (e) { if (p.onOpen) { e.preventDefault(); p.onOpen(); } } },
      h('span', { className: 'hd-asset__main' },
        h('span', { className: 'type-body-strong' }, p.name),
        h('span', { className: 'type-label hd-secondary' }, [KINDS[p.kind] || p.kind, p.location].filter(Boolean).join(' \u00b7 ')),
        q && h('span', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: p.quality === 'stale' ? 'clock' : 'attention', size: 'small' }), h('span', null, q))),
      h('span', { className: 'hd-asset__value' }, value ? h('span', { className: 'type-body-strong hd-num' }, value) : h('span', { className: 'type-label' }, '\u2014 kWh')),
      h(Icon, { name: 'chevronRight', className: 'hd-asset__chev' }));
  }

  function ContributionRanking(p) {
    var titleId = useId();
    var items = (p.items || []).slice().sort(function (a, b) { return b.kwh - a.kwh; });
    var total = items.reduce(function (s, i) { return s + i.kwh; }, 0);
    var zero = total === 0;
    return h('section', { className: 'hd-root hd-rank', 'aria-labelledby': titleId },
      h(Heading, { level: p.headingLevel, id: titleId, className: 'type-section' }, p.title || 'Kontributor terbesar'),
      h('p', { className: 'type-label' }, [p.periodLabel, (zero ? 'Total ' : 'Dari total ') + format.kwh(total) + ' ' + (p.denominatorLabel || 'perangkat terukur yang dipilih')].filter(Boolean).join(' \u00b7 ')),
      !zero && items.length > 0 && h('p', { className: 'type-body' }, h('strong', null, items[0].name), ' terbesar di antara ' + (p.denominatorLabel || 'perangkat terukur yang dipilih') + '. Ini bukan penilaian boros atau hemat.'),
      zero && h(Notice, { tone: 'neutral', title: 'Persentase tidak dihitung' }, 'Total energi terukur 0,000 kWh, jadi tidak ada pembagian untuk dibandingkan.'),
      h('ol', { className: 'hd-rank__list' }, items.map(function (i) {
        var pct = format.percent(i.kwh, total);
        return h('li', { key: i.name, className: 'hd-rank__item' },
          h('div', { className: 'hd-rank__line' }, h('span', { className: 'hd-rank__name type-body' }, i.name),
            h('span', { className: 'type-body-strong hd-num' }, format.kwh(i.kwh) + (pct ? ' \u00b7 ' + pct : ''))),
          h('div', { className: 'hd-rank__track', 'aria-hidden': 'true' }, h('div', { className: 'hd-rank__bar', style: { width: zero ? '0%' : (i.kwh / total) * 100 + '%' } })));
      })));
  }

  function niceMax(v) { if (!(v > 0)) return 1; var m = Math.pow(10, Math.floor(Math.log10(v))); var n = v / m; return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * m; }
  function HistoryChart(p) {
    var titleId = useId(); var descId = useId();
    var points = p.points || [];
    var hasRef = points.some(function (d) { return d.reference !== undefined; });
    var max = niceMax(1.2 * Math.max.apply(null, points.map(function (d) { return Math.max(finite(d.current) ? d.current : 0, finite(d.reference) ? d.reference : 0); }))); // headroom so a full bar never reads as the scale edge
    var missing = points.filter(function (d) { return d.current === null; });
    function bar(v, kind, key) {
      if (v === null) return h('span', { key: key, className: 'hd-chart__bar hd-bar--missing' });
      if (!finite(v)) return null;
      if (v === 0) return h('span', { key: key, className: 'hd-chart__bar hd-bar--zero' });
      return h('span', { key: key, className: 'hd-chart__bar hd-bar--' + kind, style: { height: (v / max) * 100 + '%' } });
    }
    return h('figure', { className: cx('hd-root hd-chart', p.dense && 'hd-chart--dense'), 'aria-labelledby': titleId },
      h(Heading, { level: p.headingLevel, id: titleId, className: 'type-section' }, p.title),
      h('p', { className: 'type-label' }, [p.periodLabel, p.scopeLabel, 'Satuan: ' + (p.unit || 'kWh')].filter(Boolean).join(' \u00b7 ')),
      h('div', { className: 'hd-chart__legend type-label' },
        h('span', { className: 'hd-chart__key' }, h('span', { className: 'hd-chart__swatch hd-bar--current' }), p.currentLabel || 'Periode ini (batang penuh)'),
        hasRef && h('span', { className: 'hd-chart__key' }, h('span', { className: 'hd-chart__swatch hd-bar--reference' }), p.referenceLabel || 'Periode pembanding (garis putus-putus)'),
        missing.length > 0 && h('span', { className: 'hd-chart__key' }, h('span', { className: 'hd-chart__swatch hd-bar--missing' }), 'Tidak ada data (arsir)')),
      h('div', { className: 'hd-chart__scale type-caption', 'aria-hidden': 'true' }, h('span', null, 'Skala 0\u2013' + format.number(max) + ' ' + (p.unit || 'kWh')), h('span', null, 'Nilai tepat di tabel data')),
      h('div', { role: 'img', 'aria-labelledby': titleId, 'aria-describedby': descId },
        h('div', { className: 'hd-chart__plot' }, h('span', { className: 'hd-chart__grid', 'aria-hidden': 'true' }),
          points.map(function (d, i) { return h('div', { key: i, className: 'hd-chart__col' }, bar(d.current, 'current', 'c'), hasRef ? bar(d.reference, 'reference', 'r') : null); })),
        h('div', { className: 'hd-chart__labels type-label', 'aria-hidden': 'true' }, points.map(function (d, i) {
          return h('span', { key: i }, h('span', null, d.label), p.dense ? null : h('span', { className: 'hd-num type-label-strong' }, d.current === null ? '\u2014' : format.number(d.current)));
        }))),
      h('figcaption', { id: descId, className: 'type-body' }, p.summary,
        missing.length > 0 && h('span', { className: 'hd-qualifier type-label-strong', style: { marginTop: 'var(--space-8)' } }, h(Icon, { name: 'attention', size: 'small' }),
          h('span', null, p.gapNote || ('Tidak ada data: ' + missing.map(function (d) { return d.label; }).join(', ') + '. Celah tidak digambar sebagai 0 dan tidak diperkirakan.')))),
      p.children);
  }

  function ChartDataAlternative(p) {
    var table = h('table', { className: 'hd-table hd-table--stack type-label' },
      h('caption', { className: 'type-label-strong' }, p.caption),
      h('thead', null, h('tr', null, p.columns.map(function (c) { return h('th', { key: c.key, scope: 'col', className: c.numeric ? 'hd-table__num' : undefined }, c.label); }))),
      h('tbody', null, p.rows.map(function (r, i) {
        return h('tr', { key: i }, p.columns.map(function (c, j) {
          var v = r[c.key];
          var text = v === null ? 'Tidak ada data' : c.format ? c.format(v) : c.numeric ? format.number(v) : v;
          return j === 0 ? h('th', { key: c.key, scope: 'row', 'data-label': c.label }, text) : h('td', { key: c.key, 'data-label': c.label, className: c.numeric ? 'hd-table__num' : undefined }, text);
        }));
      })));
    return h('div', { className: 'hd-root' }, p.summary && h('p', { className: 'type-body', style: { marginBottom: 'var(--space-8)' } }, p.summary),
      p.collapsed === false ? table : h(Disclosure, { summary: p.toggleLabel || 'Lihat data dalam tabel' }, table));
  }

  function InsightSummary(p) {
    var titleId = useId();
    var kind = p.kind || 'change';
    if (kind === 'none') return h(Notice, { tone: 'neutral', title: 'Belum ada perubahan yang memenuhi syarat untuk ditampilkan' }, (p.periodLabel ? p.periodLabel + '. ' : '') + 'Ini bukan penilaian efisiensi atau keamanan; data terukur tetap dapat dilihat.');
    if (kind === 'learning') return h(Notice, { tone: 'neutral', title: 'Belum cukup periode pembanding' }, p.detail || 'Total terukur tetap tersedia. Perbandingan muncul setelah ada periode sebanding yang cukup.');
    return h('section', { className: 'hd-root hd-insight', 'aria-labelledby': titleId },
      h(Heading, { level: p.headingLevel, id: titleId, className: 'type-body-strong' }, p.title),
      h('p', { className: 'type-label' }, [p.periodLabel, p.comparison && p.comparison.eligible ? p.comparison.label : null].filter(Boolean).join(' \u00b7 ')),
      p.comparison && !p.comparison.eligible && h('p', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: 'attention', size: 'small' }), h('span', null, 'Belum dapat dibandingkan: ' + p.comparison.reason)),
      h('p', { className: 'type-label hd-secondary' }, p.cause || 'Penyebab perubahan belum diketahui.'),
      p.qualification && h('p', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: 'attention', size: 'small' }), h('span', null, p.qualification)),
      p.onOpenEvidence && h('div', null, h(Button, { variant: 'text', onClick: p.onOpenEvidence }, p.evidenceLabel || 'Lihat bukti')));
  }

  var FEEDBACK = { saving: 'saving', success: 'success', failure: 'failure', unknown: 'unknown' };
  function EvidencePanel(p) {
    var steps = [
      ['Yang teramati', p.observed], ['Pembanding', p.comparison], ['Kualitas dan cakupan data', p.qualityScope],
      ['Yang belum diketahui', p.unknown], ['Saran umum', p.guidance]
    ].filter(function (s) { return s[1]; });
    return h('section', { className: 'hd-root hd-evidence', 'aria-label': p.label || 'Bukti dan batasan' },
      h('ol', null, steps.map(function (s, i) {
        return h('li', { key: s[0], className: 'hd-evidence__step' }, h('span', { className: 'hd-evidence__index type-label-strong', 'aria-hidden': 'true' }, i + 1),
          h('div', { className: 'hd-evidence__content' }, h('h3', { className: 'type-body-strong' }, s[0]),
            s[0] === 'Saran umum' && h('p', { className: 'type-label hd-secondary' }, 'Panduan umum untuk diperiksa, bukan diagnosis perangkat Anda.'),
            h('div', { className: 'type-body' }, s[1])));
      })),
      p.onFeedback && h('div', { className: 'hd-evidence__step' }, h('span', { className: 'hd-evidence__index type-label-strong', 'aria-hidden': 'true' }, steps.length + 1),
        h('div', { className: 'hd-evidence__content' }, h('h3', { className: 'type-body-strong' }, 'Apakah penjelasan ini membantu?'),
          h('p', { className: 'type-label hd-secondary' }, 'Opsional. Jawaban hanya memperbaiki penjelasan; tidak mengubah data atau perangkat.'),
          p.feedbackState !== 'success' && h('div', { className: 'hd-row' },
            h(Button, { variant: 'secondary', onClick: function () { p.onFeedback('helpful'); }, loading: p.feedbackState === 'saving' && p.feedbackChoice === 'helpful', loadingLabel: 'Mengirim\u2026' }, 'Membantu'),
            h(Button, { variant: 'secondary', onClick: function () { p.onFeedback('notHelpful'); }, loading: p.feedbackState === 'saving' && p.feedbackChoice === 'notHelpful', loadingLabel: 'Mengirim\u2026' }, 'Kurang membantu')),
          h(ProgressStatus, { state: FEEDBACK[p.feedbackState] && p.feedbackState !== 'saving' ? p.feedbackState : null, label: p.feedbackState === 'success' ? 'Terima kasih, jawaban tercatat' : undefined,
            detail: p.feedbackState === 'success' ? 'Dikonfirmasi server.' : p.feedbackState === 'failure' ? 'Jawaban belum terkirim. Tidak ada yang berubah.' : undefined,
            onRetry: p.onFeedbackRetry, onCheck: p.onFeedbackCheck }))),
      p.metadata && h(Disclosure, { summary: 'Detail perhitungan' }, h('dl', { className: 'hd-meta type-label' }, p.metadata.map(function (m) {
        return h('div', { key: m[0] }, h('dt', { className: 'type-label-strong' }, m[0]), h('dd', null, m[1]));
      }))));
  }

  function ImportPreview(p) {
    var ackId = useId();
    var threshold = p.maxInvalidShare != null ? p.maxInvalidShare : 0.2;
    var total = p.totalRows, invalid = p.invalidRows || 0, dup = p.duplicateRows || 0, conflicts = p.conflictRows || 0;
    var valid = total - invalid - dup - conflicts;
    var maxInvalid = Math.floor(total * threshold + 1e-9);
    var tooMany = invalid > maxInvalid;
    var blocked = tooMany || conflicts > 0;
    var needsAck = !blocked && invalid > 0;
    var done = p.saveState === 'success';
    var blockReason = tooMany ? invalid + ' dari ' + total + ' baris tidak valid, melebihi batas ' + maxInvalid + '. Perbaiki file lalu unggah ulang.'
      : conflicts > 0 ? conflicts + ' baris bertentangan dengan data yang sudah ada. Selesaikan konflik terlebih dahulu.' : null;
    function count(label, v, attention) { return h('div', null, h('span', { className: 'type-label hd-secondary' }, label), h('span', { className: cx('type-section hd-num', attention && 'hd-qualifier') }, format.number(v))); }
    return h('section', { className: 'hd-root hd-import', 'aria-label': 'Pratinjau impor' },
      h('div', { className: 'hd-row' }, h(Icon, { name: 'file' }), h('p', { className: 'type-body-strong' }, p.fileName), p.periodLabel && h('span', { className: 'type-label hd-secondary' }, '\u00b7 ' + p.periodLabel)),
      h('div', { className: 'hd-counts' }, count('Baris data', total), count('Valid dan unik', valid), count('Tidak valid', invalid, invalid > 0), count('Duplikat (dihitung sekali)', dup), count('Konflik', conflicts, conflicts > 0)),
      p.mapping && h(Disclosure, { summary: 'Pemetaan kolom dan asumsi' },
        h('ul', { className: 'type-body' }, p.mapping.map(function (m) { return h('li', { key: m[0] }, h('strong', null, m[0]), ' \u2192 ' + m[1]); })),
        p.assumptions && h('ul', { className: 'type-label' }, p.assumptions.map(function (a) { return h('li', { key: a }, a); }))),
      p.errors && p.errors.length > 0 && h('div', { className: 'hd-stack hd-stack--tight' },
        h('h3', { className: 'type-body-strong' }, 'Baris yang tidak valid'),
        h('p', { className: 'type-label hd-secondary' }, 'Nomor baris data tidak menghitung header. Baris file = baris data + 1.'),
        h('ul', { className: 'hd-rowerrors' }, p.errors.map(function (e) {
          return h('li', { key: e.id, id: e.id, tabIndex: -1 }, h('span', { className: 'type-body-strong' }, 'Baris data ' + e.dataRow + ' (baris file ' + (e.dataRow + 1) + ') \u00b7 kolom ' + e.field), h('span', { className: 'type-body' }, e.message));
        }))),
      blockReason && h(Notice, { tone: 'error', title: 'Impor tidak dapat dilanjutkan' }, blockReason),
      needsAck && !done && h(ChoiceGroup, { type: 'checkbox', legend: 'Konfirmasi baris yang dilewati', error: p.ackError, value: p.acknowledged ? ['ack'] : [], onChange: function (v) { if (p.onAcknowledge) p.onAcknowledge(v.length > 0); },
        options: [{ value: 'ack', id: p.ackInputId || ackId, label: 'Saya mengerti ' + invalid + ' baris tidak valid tidak akan diimpor.', description: valid + ' baris valid akan disimpan. Data yang sudah terkonfirmasi tidak berubah.' }] }),
      h(ProgressStatus, { state: p.saveState === 'saving' ? null : p.saveState, label: done ? valid + ' baris diimpor' : undefined, detail: done ? 'Dikonfirmasi server' + (p.confirmedAt ? ' ' + p.confirmedAt : '') + '.' : p.saveState === 'failure' ? 'Pratinjau dan pilihan Anda tetap tersimpan. Tidak ada baris yang diimpor.' : undefined,
        onRetry: p.onConfirm, onCheck: p.onCheckStatus, checking: p.checking }),
      !done && p.saveState !== 'unknown' && p.saveState !== 'failure' && h('div', { className: 'hd-row' },
        h(Button, { variant: 'primary', onClick: p.onConfirm, loading: p.saveState === 'saving', loadingLabel: 'Mengimpor\u2026', disabledReason: blocked ? 'Tidak dapat mengimpor: ' + (tooMany ? 'terlalu banyak baris tidak valid.' : 'ada konflik data.') : null }, blocked ? 'Impor baris valid' : 'Impor ' + valid + ' baris'),
        p.onCancel && h(Button, { variant: 'text', onClick: p.onCancel }, 'Batal')));
  }

  var SCHEDULE_MODES = [
    { value: 'none', label: 'Tanpa jadwal', description: 'Pemantauan dan saran inti tetap lengkap.' },
    { value: 'continuous', label: 'Beroperasi 24 jam', description: 'Dipilih secara eksplisit, bukan anggapan.' },
    { value: 'inherit', label: 'Ikuti jadwal lokasi' },
    { value: 'windows', label: 'Jendela mingguan khusus', description: 'Boleh lebih dari satu, termasuk melewati tengah malam.' }
  ];
  function ScheduleWindows(p) {
    var modes = SCHEDULE_MODES.map(function (m) { return m.value === 'inherit' ? Object.assign({}, m, { description: p.inheritLabel || 'Jadwal lokasi belum diatur.', disabledReason: p.inheritLabel ? null : 'Lokasi belum punya jadwal.' }) : m; });
    return h('section', { className: 'hd-root hd-schedule', 'aria-label': 'Jadwal operasi' },
      h(ChoiceGroup, { legend: 'Jadwal operasi', optional: true, help: p.help || 'Hanya untuk membandingkan pemakaian di dalam dan di luar jam operasi.', value: p.mode, onChange: p.onModeChange, options: modes }),
      p.mode === 'windows' && h('ul', { className: 'hd-windows type-body' }, (p.windows || []).map(function (w, i) {
        return h('li', { key: i }, h('span', { className: 'type-body-strong' }, w.days),
          h('span', { className: 'hd-num' }, format.time(w.start) + '\u2013' + format.time(w.end) + (w.nextDay ? ' (berakhir hari berikutnya)' : '')));
      })),
      p.mode === 'windows' && (!p.windows || !p.windows.length) && h('p', { className: 'type-label hd-secondary' }, 'Belum ada jendela. Tambahkan minimal satu atau pilih Tanpa jadwal.'));
  }

  function OutputMetricPreview(p) {
    var titleId = useId();
    if (!p.enabled) return null; // optional capability: absent when not enabled, core stays complete
    var unit = p.unit || 'unit';
    var state = p.output == null ? 'missing' : !finite(p.output) || p.output < 0 ? 'invalid' : p.output === 0 ? 'zero' : !finite(p.energyKwh) ? 'noEnergy' : 'ok';
    var message = {
      missing: 'Intensitas belum dihitung \u2014 data output belum diisi.',
      invalid: 'Intensitas tidak dihitung \u2014 data output tidak valid. Periksa angka output.',
      zero: 'Intensitas tidak dihitung \u2014 output tercatat 0 ' + unit + '.',
      noEnergy: 'Intensitas tidak dihitung \u2014 belum ada data energi.'
    }[state];
    return h('section', { className: 'hd-root hd-output', 'aria-labelledby': titleId },
      h(Heading, { level: p.headingLevel, id: titleId, className: 'type-label-strong' }, 'Energi per output (opsional)'),
      state === 'ok' ? h(Fragment, null,
        h('p', { className: 'hd-metric__value hd-num' }, h('span', { className: 'type-title' }, nf3.format(p.energyKwh / p.output)), h('span', { className: 'type-body-strong' }, 'kWh/' + unit)),
        h('p', { className: 'type-label' }, format.kwh(p.energyKwh) + ' \u00f7 ' + format.number(p.output) + ' ' + unit + ' \u00b7 output ' + (p.method === 'estimated' ? 'estimasi' : 'aktual') + (p.periodLabel ? ' \u00b7 ' + p.periodLabel : ''))) :
        h('p', { className: 'hd-qualifier hd-qualifier--neutral type-body' }, h(Icon, { name: 'info', size: 'small' }), h('span', null, message)),
      p.method === 'estimated' && state === 'ok' && h('p', { className: 'hd-qualifier type-label-strong' }, h(Icon, { name: 'attention', size: 'small' }), h('span', null, 'Output berupa estimasi, bukan hitungan aktual.')));
  }

  function Screen(p) {
    var titleId = useId();
    return h('div', { className: cx('hd-root hd-screen', p.aside && 'hd-screen--aside') },
      h('header', { className: 'hd-screen__top' },
        p.back ? h(IconButton, { icon: 'chevronLeft', label: p.back.label, showLabel: true, onClick: p.back.onClick }) : h('span', { className: 'hd-screen__wordmark type-body' }, 'HematDaya'),
        p.provenance && h(Tag, null, PROVENANCE[p.provenance] || p.provenance)),
      h('main', { className: 'hd-screen__body', 'aria-labelledby': titleId },
        h('div', { className: 'hd-screen__head' }, h('h1', { id: titleId, className: 'type-title' }, p.title), p.subtitle && h('p', { className: 'type-label hd-secondary' }, p.subtitle)),
        h('div', { className: 'hd-screen__main' }, p.children),
        p.aside && h('aside', { className: 'hd-screen__aside', 'aria-label': p.asideLabel || 'Informasi pendukung' }, p.aside)),
      p.current && h('div', { className: 'hd-screen__nav' }, h(TabNavigation, { current: p.current, onNavigate: p.onNavigate })));
  }

  var HD = {
    Button: Button, IconButton: IconButton, TextField: TextField, NumericField: NumericField, ChoiceGroup: ChoiceGroup,
    PeriodSelector: PeriodSelector, TabNavigation: TabNavigation, SheetDialog: SheetDialog, Disclosure: Disclosure, Notice: Notice,
    ErrorSummary: ErrorSummary, ProgressStatus: ProgressStatus,
    EnergyMetric: EnergyMetric, CostEstimate: CostEstimate, ScopeSummary: ScopeSummary, DataQuality: DataQuality, AssetRow: AssetRow,
    ContributionRanking: ContributionRanking, HistoryChart: HistoryChart, ChartDataAlternative: ChartDataAlternative,
    InsightSummary: InsightSummary, EvidencePanel: EvidencePanel, ImportPreview: ImportPreview, ScheduleWindows: ScheduleWindows,
    OutputMetricPreview: OutputMetricPreview, Screen: Screen, Icon: Icon,
    format: format, version: '1.0.0-draft'
  };
  window.HD = Object.assign(window.HD || {}, HD);
})();
