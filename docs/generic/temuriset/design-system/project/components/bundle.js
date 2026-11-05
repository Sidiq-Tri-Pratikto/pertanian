/* @ds-bundle: {"format":4,"namespace":"TR","components":[{"name":"Button"},{"name":"Link"},{"name":"TextField"},{"name":"TextArea"},{"name":"Select"},{"name":"ChoiceGroup"},{"name":"Checkbox"},{"name":"FieldError"},{"name":"ErrorSummary"},{"name":"Dialog"},{"name":"Disclosure"},{"name":"Tabs"},{"name":"Status"},{"name":"EmptyState"},{"name":"SaveState"},{"name":"ContextSwitcher"},{"name":"InventionCard"},{"name":"FundingRequestCard"},{"name":"FinancialScope"},{"name":"RequirementRow"},{"name":"FactSource"},{"name":"DocumentItem"},{"name":"RevisionItem"},{"name":"ScheduleSlotList"},{"name":"PartnershipConsent"},{"name":"VersionConflict"},{"name":"NextStep"},{"name":"Steps"},{"name":"SummaryList"},{"name":"Screen"},{"name":"Icon"}]} */
/* TemuRiset Design System 1.0.0-draft — window.TR. Hand-written, no build step; reads window.React. */
(function () {
  'use strict';
  var React = window.React;
  var h = React.createElement;
  var useState = React.useState, useEffect = React.useEffect, useRef = React.useRef, useId = React.useId;
  var UNKNOWN_AMOUNT = 'Belum ditentukan';
  var DEFAULT_ZONE = 'Asia/Jakarta';

  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }
  function ids() { return Array.prototype.filter.call(arguments, Boolean).join(' ') || undefined; }
  // when() evaluates its node eagerly: use a ternary when the node reads a property of the condition.
  function when(cond, node) { return cond ? node : null; }

  /* ================= formatting (Indonesian display; amounts stay decimal strings) ================= */
  // Amounts are never parsed to floats: grouping works on the digits as given.
  function amount(v) {
    var s = String(v), neg = s.charAt(0) === '-';
    if (neg) s = s.slice(1);
    var p = s.split('.'), frac = (p[1] || '').replace(/0+$/, '');
    return (neg ? '-' : '') + p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (frac ? ',' + frac : '');
  }
  // The no-break space keeps a currency with its digits; a long range can still wrap after its dash.
  function money(currency, v) { return v == null ? UNKNOWN_AMOUNT : currency + ' ' + amount(v); }
  function range(currency, min, max) {
    if (min == null && max == null) return UNKNOWN_AMOUNT;
    if (min == null) return 'Hingga ' + money(currency, max);
    if (max == null) return 'Mulai ' + money(currency, min);
    if (String(min) === String(max)) return money(currency, min);
    return currency + ' ' + amount(min) + '–' + amount(max);
  }
  function dt(iso, zone, opts) {
    return new Intl.DateTimeFormat('id-ID', Object.assign({ timeZone: zone || DEFAULT_ZONE }, opts)).format(new Date(iso));
  }
  function date(iso, zone) { return dt(iso, zone, { day: 'numeric', month: 'long', year: 'numeric' }); }
  function longDate(iso, zone) { return dt(iso, zone, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }
  function time(iso, zone) { return dt(iso, zone, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }); }
  var ZONES = { 'Asia/Jakarta': 'WIB', 'Asia/Makassar': 'WITA', 'Asia/Jayapura': 'WIT' };
  function zoneLabel(zone) { return ZONES[zone] ? ZONES[zone] + ' (' + zone + ')' : zone; }
  function slotTime(iso, minutes, zone) {
    var end = new Date(new Date(iso).getTime() + minutes * 60000).toISOString();
    return time(iso, zone) + '–' + time(end, zone) + ' ' + zoneLabel(zone);
  }
  // Half-open intervals: 09:00–10:00 and 10:00–11:00 do not overlap.
  function overlaps(aStart, aMin, bStart, bMin) {
    var a = new Date(aStart).getTime(), b = new Date(bStart).getTime();
    return a < b + bMin * 60000 && b < a + aMin * 60000;
  }
  var format = { amount: amount, money: money, range: range, date: date, longDate: longDate, time: time, zoneLabel: zoneLabel, slotTime: slotTime, overlaps: overlaps };

  /* ================= icons: own stroke set, 24 grid, currentColor ================= */
  var ICONS = {
    check: 'M5 12.5l4.5 4.5L19 7.5',
    cross: 'M6 6l12 12M18 6L6 18',
    question: 'M9 9.2a3 3 0 1 1 4.6 2.5c-1 .7-1.6 1.3-1.6 2.5M12 17.6v.1',
    minus: 'M6 12h12',
    alert: 'M12 4l9 16H3L12 4zM12 10v4.5M12 17.2v.1',
    clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7.5V12l3 2',
    lock: 'M7 11V8a5 5 0 0 1 10 0v3M6 11h12v9H6z',
    shield: 'M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6l8-3z',
    file: 'M7 3h7l4 4v14H7zM14 3v4h4',
    upload: 'M12 16V5M8 9l4-4 4 4M5 19h14',
    external: 'M10 5H5v14h14v-5M13 4h7v7M20 4l-9 9',
    down: 'M6 9l6 6 6-6',
    right: 'M9 6l6 6-6 6',
    left: 'M15 6l-6 6 6 6',
    arrow: 'M5 12h14M13 6l6 6-6 6',
    close: 'M6 6l12 12M18 6L6 18',
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20.5c1-4 4-6 7.5-6s6.500 2 7.500 6',
    building: 'M5 21V4h10v17M15 10h4v11M3 21h18M8.500 8h3M8.500 12h3M8.500 16h3',
    search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM16.200 16.200L21 21',
    home: 'M4 11l8-7 8 7M6 9.500V20h12V9.500',
    bulb: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.600 10.800c.7.6 1 1.200 1.100 2.200h5c.1-1 .4-1.600 1.100-2.200A6 6 0 0 0 12 3z',
    chat: 'M4 5h16v11H9l-5 4V5z',
    inbox: 'M4 13l2.500-8h11L20 13v6H4zM4 13h5l1 2.500h4l1-2.500h5',
    calendar: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
    more: 'M5 12h.1M12 12h.1M19 12h.1',
    refresh: 'M20 11a8 8 0 0 0-14.300-4.500L4 8.500M4 4v4.500h4.500M4 13a8 8 0 0 0 14.300 4.500L20 15.500M20 20v-4.500h-4.500',
    edit: 'M4 20l1-4L16 5l3 3L8 19l-4 1z',
    eye: 'M2.500 12S6 5.500 12 5.500 21.500 12 21.500 12 18 18.500 12 18.500 2.500 12 2.500 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    eyeOff: 'M4 4l16 16M9.900 5.800A9 9 0 0 1 12 5.500c6 0 9.500 6.500 9.500 6.500a17 17 0 0 1-3 3.700M6.300 7.700A16 16 0 0 0 2.500 12S6 18.500 12 18.500a9 9 0 0 0 4.200-1',
    partner: 'M3 9.500L8 7l4 2 4-2 5 2.500M3 9.500V16l3 1M21 9.500V16l-3 1M12 9l-4 4 2 2 3-2 3 3 2-2'
  };
  function Icon(p) {
    return h('svg', { className: cx('tr-icon', p.size === 'small' && 'tr-icon--small', p.className), viewBox: '0 0 24 24', 'aria-hidden': true, focusable: 'false' },
      h('path', { d: ICONS[p.name] || ICONS.minus }));
  }
  function Spinner() { return h('span', { className: 'tr-spinner', 'aria-hidden': true }); }

  /* ================= actions ================= */
  function Button(p) {
    var auto = useId(), reasonId = auto + 'r', blocked = !!p.disabledReason;
    function click(e) {
      if (blocked || p.busy) { e.preventDefault(); return; }
      if (p.onClick) p.onClick(e);
    }
    var btn = h('button', {
      id: p.id, type: p.type || 'button', form: p.form, onClick: click,
      className: cx('tr-btn', 'tr-btn--' + (p.intent || 'secondary'), p.fullWidth && 'tr-btn--full'),
      'aria-disabled': blocked || undefined, 'aria-busy': p.busy || undefined, 'aria-describedby': ids(blocked && reasonId, p.describedBy)
    }, p.busy ? h(Spinner) : when(p.icon, h(Icon, { name: p.icon })), h('span', null, p.busy ? (p.busyLabel || 'Memproses…') : p.children));
    if (!blocked) return btn;
    return h('span', { className: cx('tr-btn-wrap', p.fullWidth && 'tr-btn-wrap--full') }, btn,
      h('span', { id: reasonId, className: 'tr-reason tr-sys-type-support' }, p.disabledReason));
  }

  function Link(p) {
    return h('a', { id: p.id, href: p.href || '#', className: 'tr-link', target: p.external ? '_blank' : undefined, rel: p.external ? 'noopener noreferrer' : undefined,
      onClick: p.onClick ? function (e) { e.preventDefault(); p.onClick(e); } : undefined },
      p.children,
      when(p.context, h('span', { className: 'tr-sr' }, ' ' + p.context)),
      when(p.external, h(React.Fragment, null, h(Icon, { name: 'external', size: 'small' }), h('span', { className: 'tr-sr' }, ' (membuka situs lain)'))));
  }

  /* ================= fields ================= */
  function useField(p) {
    var auto = useId(), id = p.id || auto;
    return { id: id, hintId: id + '-hint', errorId: id + '-error', describedBy: ids(p.hint && id + '-hint', p.error && id + '-error', p.describedBy) };
  }
  function Label(p) {
    return h(p.as || 'label', { className: 'tr-field__label tr-sys-type-label', htmlFor: p.as ? undefined : p.htmlFor }, p.children,
      when(p.required, h('span', { className: 'tr-field__req tr-sys-type-support' }, ' (wajib)')));
  }
  function FieldError(p) {
    return h('p', { id: p.id, className: 'tr-field-error tr-sys-type-label', 'data-code': p.code },
      h(Icon, { name: 'alert', size: 'small' }), h('span', null, h('span', { className: 'tr-sr' }, 'Kesalahan: '), p.children));
  }
  function Field(p) {
    var f = p.f;
    return h('div', { className: cx('tr-field', p.error && 'tr-field--error') },
      h(Label, { htmlFor: f.id, required: p.required }, p.label),
      when(p.hint, h('p', { id: f.hintId, className: 'tr-field__hint tr-sys-type-support' }, p.hint)),
      when(p.error, h(FieldError, { id: f.errorId, code: p.errorCode }, p.error)),
      p.children);
  }
  function TextField(p) {
    var f = useField(p), decimal = p.type === 'decimal';
    var input = h('input', {
      id: f.id, name: p.name, value: p.value == null ? '' : p.value, className: 'tr-input',
      type: decimal ? 'text' : (p.type || 'text'), inputMode: decimal ? 'decimal' : undefined, autoComplete: p.autoComplete || 'off',
      required: p.required || undefined, 'aria-invalid': p.error ? true : undefined, 'aria-describedby': f.describedBy,
      onChange: function (e) { if (p.onChange) p.onChange(e.target.value); }
    });
    return h(Field, { f: f, label: p.label, hint: p.hint, error: p.error, errorCode: p.errorCode, required: p.required },
      p.prefix || p.suffix
        ? h('div', { className: 'tr-affix' }, when(p.prefix, h('span', { className: 'tr-affix__unit' }, p.prefix)), input, when(p.suffix, h('span', { className: 'tr-affix__unit' }, p.suffix)))
        : input);
  }
  function TextArea(p) {
    var f = useField(p), len = (p.value || '').length, over = p.limit && len > p.limit, countId = f.id + '-count';
    return h(Field, { f: f, label: p.label, hint: p.hint, error: p.error, errorCode: p.errorCode, required: p.required },
      h('textarea', {
        id: f.id, name: p.name, value: p.value || '', rows: p.rows || 5, className: 'tr-input tr-textarea', required: p.required || undefined,
        'aria-invalid': p.error ? true : undefined, 'aria-describedby': ids(f.describedBy, p.limit && countId),
        onChange: function (e) { if (p.onChange) p.onChange(e.target.value); }
      }),
      when(p.limit, h('p', { id: countId, className: cx('tr-count tr-sys-type-support', over && 'is-over') },
        over ? 'Lebih ' + (len - p.limit) + ' karakter dari batas ' + p.limit : len + ' dari ' + p.limit + ' karakter')));
  }
  function Select(p) {
    var f = useField(p);
    return h(Field, { f: f, label: p.label, hint: p.hint, error: p.error, errorCode: p.errorCode, required: p.required },
      h('select', {
        id: f.id, name: p.name, value: p.value == null ? '' : p.value, className: 'tr-input tr-select', required: p.required || undefined,
        'aria-invalid': p.error ? true : undefined, 'aria-describedby': f.describedBy,
        onChange: function (e) { if (p.onChange) p.onChange(e.target.value); }
      }, when(p.emptyLabel !== null, h('option', { value: '' }, p.emptyLabel || 'Pilih salah satu')),
        p.options.map(function (o) { return h('option', { key: o.value, value: o.value, disabled: !!o.disabledReason }, o.label + (o.disabledReason ? ' — ' + o.disabledReason : '')); })));
  }
  function ChoiceGroup(p) {
    var auto = useId(), name = p.name || auto, hintId = name + '-hint', errorId = name + '-error';
    return h('fieldset', { className: cx('tr-fieldset', p.error && 'tr-fieldset--error'), 'aria-describedby': ids(p.hint && hintId, p.error && errorId), 'aria-invalid': p.error ? true : undefined },
      h('legend', { className: 'tr-field__label tr-sys-type-label' }, p.legend, when(p.required, h('span', { className: 'tr-field__req tr-sys-type-support' }, ' (wajib)'))),
      when(p.hint, h('p', { id: hintId, className: 'tr-field__hint tr-sys-type-support' }, p.hint)),
      when(p.error, h(FieldError, { id: errorId }, p.error)),
      h('div', { className: 'tr-choices' }, p.options.map(function (o, i) {
        var selected = p.value === o.value, blocked = !!o.disabledReason, oid = (i === 0 && p.id) || name + '-' + o.value;
        return h('label', { key: o.value, htmlFor: oid, className: cx('tr-choice', selected && 'is-selected', blocked && 'is-disabled') },
          h('input', { type: 'radio', id: oid, name: name, value: o.value, checked: selected, disabled: blocked, onChange: function () { if (p.onChange) p.onChange(o.value); } }),
          h('span', { className: 'tr-choice__body' },
            h('span', { className: 'tr-sys-type-label' }, o.label),
            when(o.hint, h('span', { className: 'tr-choice__hint tr-sys-type-support' }, o.hint)),
            when(blocked, h('span', { className: 'tr-choice__hint tr-sys-type-support' }, o.disabledReason))));
      })));
  }
  function Checkbox(p) {
    var auto = useId(), id = p.id || auto, blocked = !!p.disabledReason;
    return h('label', { htmlFor: id, className: cx('tr-choice', p.checked && 'is-selected', blocked && 'is-disabled') },
      h('input', { type: 'checkbox', id: id, name: p.name, checked: !!p.checked, disabled: blocked, 'aria-invalid': p.error ? true : undefined,
        onChange: function (e) { if (p.onChange) p.onChange(e.target.checked); } }),
      h('span', { className: 'tr-choice__body' },
        h('span', { className: 'tr-sys-type-label' }, p.label),
        when(p.hint, h('span', { className: 'tr-choice__hint tr-sys-type-support' }, p.hint)),
        when(blocked, h('span', { className: 'tr-choice__hint tr-sys-type-support' }, p.disabledReason)),
        when(p.error, h(FieldError, null, p.error))));
  }
  Checkbox.Group = function (p) {
    return h('fieldset', { className: 'tr-fieldset' },
      h('legend', { className: 'tr-field__label tr-sys-type-label' }, p.legend),
      when(p.hint, h('p', { className: 'tr-field__hint tr-sys-type-support' }, p.hint)),
      h('div', { className: 'tr-choices' }, p.children));
  };

  function ErrorSummary(p) {
    var ref = useRef(null);
    // Focus moves only on a new failed attempt, so background saves never steal it.
    useEffect(function () { if (p.focusKey && ref.current) ref.current.focus(); }, [p.focusKey]);
    return h('div', { ref: ref, tabIndex: -1, className: 'tr-error-summary', role: 'group', 'aria-labelledby': (p.id || 'tr-errors') + '-t', id: p.id || 'tr-errors' },
      h('h2', { id: (p.id || 'tr-errors') + '-t', className: 'tr-sys-type-heading-sm' }, p.title || 'Masih ada yang perlu diperbaiki'),
      when(p.errors && p.errors.length, h('ul', { className: 'tr-error-summary__list' }, (p.errors || []).map(function (e) {
        return h('li', { key: e.fieldId }, h('a', { className: 'tr-link', href: '#' + e.fieldId, onClick: function (ev) {
          ev.preventDefault();
          var el = document.getElementById(e.fieldId);
          if (el) { el.focus(); el.scrollIntoView({ block: 'center' }); }
        } }, e.message));
      }))),
      when(p.children, h('p', null, p.children)),
      p.retry ? h('div', { className: 'tr-row' }, h(Button, { intent: 'secondary', icon: 'refresh', onClick: p.retry.onClick }, p.retry.label)) : null);
  }

  /* ================= overlays and disclosure ================= */
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex="0"]';
  function Dialog(p) {
    var ref = useRef(null), head = useRef(null), opener = useRef(null), titleId = useId();
    useEffect(function () {
      var d = ref.current;
      if (p.open && !d.open) {
        opener.current = document.activeElement;
        d.showModal();
        var first = p.initialFocusId && document.getElementById(p.initialFocusId);
        (first || head.current).focus();
      } else if (!p.open && d.open) {
        d.close();
        var back = (p.returnFocusId && document.getElementById(p.returnFocusId)) || opener.current;
        if (back) back.focus();
      }
    }, [p.open]);
    // Native modality keeps the page inert; this also keeps Tab from leaving through the browser chrome.
    function key(e) {
      if (e.key !== 'Tab') return;
      var list = ref.current.querySelectorAll(FOCUSABLE), first = list[0], last = list[list.length - 1], at = document.activeElement;
      if (e.shiftKey && (at === first || at === head.current)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && at === last) { e.preventDefault(); first.focus(); }
    }
    return h('dialog', { ref: ref, className: 'tr-root tr-dialog', 'aria-labelledby': titleId, onKeyDown: key,
      onCancel: function (e) { e.preventDefault(); if (p.onClose) p.onClose(); } },
      when(p.open, h(React.Fragment, null,
        h('div', { className: 'tr-dialog__head' },
          h('h2', { id: titleId, ref: head, tabIndex: -1, className: 'tr-sys-type-heading-md' }, p.title),
          h('button', { type: 'button', className: 'tr-icon-btn', 'aria-label': 'Tutup', onClick: p.onClose }, h(Icon, { name: 'close' }))),
        h('div', { className: 'tr-dialog__body tr-stack' }, p.children),
        h('div', { className: 'tr-dialog__foot' },
          p.primary ? h(Button, { intent: p.primary.intent || 'primary', busy: p.primary.busy, busyLabel: p.primary.busyLabel, disabledReason: p.primary.disabledReason, onClick: p.primary.onClick }, p.primary.label) : null,
          h(Button, { intent: 'secondary', onClick: (p.secondary && p.secondary.onClick) || p.onClose }, (p.secondary && p.secondary.label) || 'Batal')))));
  }
  function readOpen(key, fallback) {
    try { var v = key && sessionStorage.getItem(key); return v ? v === '1' : !!fallback; } catch (e) { return !!fallback; }
  }
  function Disclosure(p) {
    var open = useState(function () { return readOpen(p.storageKey, p.defaultOpen); });
    return h('details', { className: 'tr-disclosure', open: open[0], onToggle: function (e) {
      var v = e.currentTarget.open;
      open[1](v);
      try { if (p.storageKey) sessionStorage.setItem(p.storageKey, v ? '1' : '0'); } catch (err) { /* state just resets */ }
    } },
      h('summary', { className: 'tr-disclosure__toggle tr-sys-type-label' }, h(Icon, { name: 'right', className: 'tr-disclosure__chev' }), h('span', null, p.label)),
      h('div', { className: 'tr-disclosure__body' }, p.children));
  }
  function Tabs(p) {
    var auto = useId(), refs = useRef({}), own = useState(p.tabs[0].id), value = p.value || own[0];
    function pick(id, focus) {
      own[1](id);
      if (p.onChange) p.onChange(id);
      if (focus && refs.current[id]) refs.current[id].focus();
    }
    function key(e, i) {
      var n = p.tabs.length, to = { ArrowRight: (i + 1) % n, ArrowLeft: (i - 1 + n) % n, Home: 0, End: n - 1 }[e.key];
      if (to === undefined) return;
      e.preventDefault();
      pick(p.tabs[to].id, true);
    }
    return h('div', { className: 'tr-tabs' },
      h('div', { role: 'tablist', 'aria-label': p.label, className: 'tr-tabs__list' }, p.tabs.map(function (t, i) {
        var on = t.id === value;
        return h('button', { key: t.id, type: 'button', role: 'tab', id: auto + t.id, ref: function (el) { refs.current[t.id] = el; }, 'aria-selected': on, 'aria-controls': auto + t.id + 'p',
          tabIndex: on ? 0 : -1, className: cx('tr-tab tr-sys-type-label', on && 'is-selected'), onClick: function () { pick(t.id); }, onKeyDown: function (e) { key(e, i); } }, t.label);
      })),
      p.tabs.map(function (t) {
        return h('div', { key: t.id, role: 'tabpanel', id: auto + t.id + 'p', 'aria-labelledby': auto + t.id, tabIndex: 0, hidden: t.id !== value, className: 'tr-tabs__panel' }, t.id === value ? t.content : null);
      }));
  }

  /* ================= feedback ================= */
  var TONE_ICON = { neutral: 'clock', success: 'check', danger: 'cross', warning: 'question', action: 'arrow' };
  function Status(p) {
    var tone = p.tone || 'neutral', icon = p.icon === null ? null : (p.icon || TONE_ICON[tone]);
    var label = h('span', { className: 'tr-status tr-status--' + tone }, when(icon, h(Icon, { name: icon, size: 'small' })), h('span', null, p.label));
    var live = p.live ? { role: p.live === 'alert' ? 'alert' : 'status' } : {};
    if (!p.children) return h('span', Object.assign({ className: 'tr-status-wrap' }, live), label);
    return h('div', Object.assign({ className: 'tr-notice tr-notice--' + tone }, live), label, h('div', { className: 'tr-notice__body' }, p.children));
  }
  var EMPTY = {
    noInventions: { icon: 'bulb', title: 'Belum ada inovasi yang terbit', text: 'Inovasi Anda baru terlihat oleh investor dan mitra setelah Anda menerbitkannya.' },
    noMatches: { icon: 'search', title: 'Belum ada yang cocok', text: 'Tidak ada hasil untuk filter ini. Syarat wajib tidak kami longgarkan tanpa persetujuan Anda.' },
    closedIntake: { icon: 'clock', title: 'Penerimaan pitching sudah ditutup', text: 'Pitching baru tidak dapat dikirim. Diskusi yang sudah berjalan tetap dapat dibuka.' },
    denied: { icon: 'lock', title: 'Anda belum memiliki akses', text: 'Halaman ini hanya dapat dibuka oleh pihak yang diberi izin.' }
  };
  function EmptyState(p) {
    var k = EMPTY[p.kind] || {};
    return h('div', { className: 'tr-empty' }, h(Icon, { name: p.icon || k.icon || 'minus' }),
      h('h3', { className: 'tr-sys-type-heading-sm' }, p.title || k.title),
      h('p', null, p.children || k.text),
      when(p.action, h('div', { className: 'tr-row tr-row--center' }, p.action)));
  }
  function SaveState(p) {
    var state = p.state || 'local', where = p.location === 'server' ? 'Tersimpan' : 'Tersimpan di demo ini';
    var view = {
      local: { icon: 'edit', label: 'Belum tersimpan' },
      saving: { spin: true, label: 'Menyimpan…' },
      saved: { icon: 'check', label: where + (p.savedAt ? ' · ' + time(p.savedAt, p.timeZone) + ' ' + (ZONES[p.timeZone || DEFAULT_ZONE] || '') : '') },
      failed: { icon: 'alert', label: 'Gagal menyimpan' },
      conflict: { icon: 'alert', label: 'Versi sudah berubah' }
    }[state];
    return h('div', { className: 'tr-save tr-save--' + state },
      h('span', { role: 'status', className: 'tr-save__label tr-sys-type-support-strong' }, view.spin ? h(Spinner) : h(Icon, { name: view.icon, size: 'small' }), view.label),
      when(state === 'failed', h('span', { className: 'tr-sys-type-support' }, 'Isian Anda masih ada di halaman ini.')),
      when(state === 'failed' && p.onRetry, h(Button, { intent: 'secondary', icon: 'refresh', onClick: p.onRetry }, 'Coba lagi')));
  }

  /* ================= context and shell ================= */
  var KIND = { personal: 'Pribadi', organization: 'Organisasi' };
  function ContextSwitcher(p) {
    var cur = p.options.filter(function (o) { return o.id === p.value; })[0];
    if (p.readOnly) {
      return h('p', { className: 'tr-context' }, h(Icon, { name: cur.kind === 'organization' ? 'building' : 'user' }),
        h('span', null, (p.actionLabel || 'Bertindak sebagai') + ': ', h('strong', null, cur.name), ' · ' + KIND[cur.kind]));
    }
    return h(Select, { id: p.id, label: p.label || 'Bertindak sebagai', hint: p.hint, value: p.value, emptyLabel: null, onChange: p.onChange,
      options: p.options.map(function (o) { return { value: o.id, label: o.name + ' · ' + KIND[o.kind], disabledReason: o.disabledReason }; }) });
  }
  var NAV = {
    inovator: [{ id: 'beranda', label: 'Beranda', icon: 'home' }, { id: 'inovasi', label: 'Inovasi Saya', icon: 'bulb' }, { id: 'temukan', label: 'Temukan Investor/Mitra', short: 'Temukan', icon: 'search' }, { id: 'pitching', label: 'Pitching dan Diskusi', short: 'Pitching', icon: 'chat' }, { id: 'profil', label: 'Profil', icon: 'user' }],
    mitra: [{ id: 'jelajahi', label: 'Jelajahi', icon: 'search' }, { id: 'mandat', label: 'Kebutuhan/Mandat', short: 'Mandat', icon: 'file' }, { id: 'masuk', label: 'Pitching Masuk', short: 'Masuk', icon: 'inbox' }, { id: 'diskusi', label: 'Diskusi dan Jadwal', short: 'Diskusi', icon: 'calendar' }, { id: 'profil', label: 'Profil', icon: 'user' }]
  };
  function Screen(p) {
    var items = NAV[p.persona || 'inovator'], more = useState(false), bar = useRef(null), main = useRef(null), fixed = useState(true);
    // A tab bar that grows with large text must not cover the focused control.
    useEffect(function () {
      function fit() { if (bar.current) fixed[1](bar.current.offsetHeight < window.innerHeight * 0.25); }
      fit();
      window.addEventListener('resize', fit);
      return function () { window.removeEventListener('resize', fit); };
    }, []);
    function go(id) { return function (e) { e.preventDefault(); more[1](false); if (p.onNavigate) p.onNavigate(id); }; }
    function item(n, cls, short) {
      return h('a', { key: n.id, href: '#' + n.id, className: cls, 'aria-current': p.current === n.id ? 'page' : undefined, onClick: go(n.id) },
        short ? h(Icon, { name: n.icon }) : null, h('span', null, short ? (n.short || n.label) : n.label));
    }
    var primary = items.slice(0, 4), rest = items.slice(4);
    return h('div', { className: 'tr-root tr-screen' },
      h('a', { className: 'tr-skip tr-link', href: '#isi', onClick: function (e) { e.preventDefault(); main.current.focus(); } }, 'Langsung ke isi utama'),
      h('header', { className: 'tr-bar' }, h('div', { className: 'tr-bar__in' },
        h('span', { className: 'tr-wordmark tr-sys-type-body-strong' }, 'TemuRiset'),
        when(p.provenance, h('span', { className: 'tr-provenance tr-sys-type-support' }, p.provenance)),
        h('nav', { className: 'tr-topnav', 'aria-label': 'Navigasi utama' }, items.map(function (n) { return item(n, 'tr-topnav__item tr-sys-type-label'); })),
        when(p.context, h('div', { className: 'tr-bar__context' }, p.context)))),
      h('div', { className: cx('tr-page', p.aside && 'tr-page--aside') },
        h('main', { id: 'isi', ref: main, tabIndex: -1, className: 'tr-page__main tr-section' },
          h('div', { className: 'tr-page__head' },
            when(p.back, h('div', null, p.back)),
            h('h1', { className: 'tr-sys-type-heading-lg' }, p.title),
            when(p.subtitle, h('p', { className: 'tr-muted' }, p.subtitle)),
            when(p.save, p.save)),
          p.next, p.children),
        when(p.aside, h('aside', { className: 'tr-page__aside tr-section', 'aria-label': 'Informasi pendukung' }, p.aside))),
      h('nav', { ref: bar, className: cx('tr-tabbar', !fixed[0] && 'is-static'), 'aria-label': 'Navigasi utama' },
        when(more[0], h('ul', { className: 'tr-tabbar__more' }, rest.map(function (n) { return h('li', { key: n.id }, item(n, 'tr-tabbar__moreItem tr-sys-type-label')); }))),
        h('div', { className: 'tr-tabbar__row' },
          primary.map(function (n) { return item(n, 'tr-tabbar__item tr-sys-type-support', true); }),
          h('button', { type: 'button', className: 'tr-tabbar__item tr-sys-type-support', 'aria-expanded': more[0], onClick: function () { more[1](!more[0]); } }, h(Icon, { name: 'more' }), h('span', null, 'Lainnya')))));
  }
  function NextStep(p) {
    var mine = p.who !== 'other', id = useId();
    return h('section', { className: cx('tr-next', mine && 'tr-next--you'), 'aria-labelledby': id },
      h(Status, { tone: mine ? 'action' : 'neutral', label: mine ? 'Menunggu Anda' : 'Menunggu pihak lain' }),
      h('h2', { id: id, className: 'tr-sys-type-heading-sm' }, p.title),
      when(p.children, h('p', null, p.children)),
      p.due ? h('p', { className: 'tr-muted tr-sys-type-support' }, 'Batas waktu: ' + date(p.due)) : null,
      when(p.action, h('div', { className: 'tr-row' }, p.action)));
  }
  function Steps(p) {
    var i = p.steps.map(function (s) { return s.id; }).indexOf(p.current);
    return h('nav', { className: 'tr-steps', 'aria-label': p.label || 'Langkah pengisian' },
      h('p', { className: 'tr-sys-type-label' }, 'Langkah ' + (i + 1) + ' dari ' + p.steps.length + ': ' + p.steps[i].label),
      h('ol', { className: 'tr-steps__list' }, p.steps.map(function (s, n) {
        var done = n < i || s.done, on = n === i;
        var inner = h(React.Fragment, null,
          h('span', { className: 'tr-steps__mark' }, done && !on ? h(Icon, { name: 'check', size: 'small' }) : n + 1),
          h('span', { className: 'tr-steps__text tr-sys-type-support' }, s.label, when(done && !on, h('span', { className: 'tr-sr' }, ' (selesai)'))));
        return h('li', { key: s.id, className: cx('tr-steps__item', on && 'is-current', done && 'is-done') },
          p.onSelect && !on
            ? h('button', { type: 'button', className: 'tr-steps__btn', onClick: function () { p.onSelect(s.id); } }, inner)
            : h('span', { className: 'tr-steps__btn', 'aria-current': on ? 'step' : undefined }, inner));
      })));
  }
  function SummaryList(p) {
    return h('dl', { className: 'tr-summary' }, p.rows.map(function (r) {
      return h('div', { key: r.id, className: 'tr-summary__row' },
        h('dt', { className: 'tr-sys-type-label' }, r.label),
        h('dd', { className: 'tr-summary__value' }, r.value),
        when(r.onChange, h('dd', { className: 'tr-summary__change' }, h(Link, { href: '#' + r.id, onClick: r.onChange, context: r.label.toLowerCase() }, 'Ubah'))));
    }));
  }

  /* ================= domain: money and evidence ================= */
  var SUBJECT = { project: 'Dukungan Proyek', companyTarget: 'Target Pendanaan', contribution: 'Kisaran kontribusi per investor', investorCheck: 'Kisaran investasi investor', partner: 'Kisaran dukungan mitra', license: 'Ketentuan lisensi' };
  function FinancialScope(p) {
    var main = p.noncash || p.terms || range(p.currency, p.min, p.max);
    return h('div', { className: cx('tr-fin', p.compact && 'tr-fin--compact') },
      h('p', { className: 'tr-fin__subject tr-sys-type-support-strong' }, p.label || SUBJECT[p.subject]),
      h('p', { className: 'tr-fin__line' },
        h('span', { className: 'tr-fin__amount tr-sys-type-amount' }, main),
        when(p.period, h('span', { className: 'tr-fin__period' }, ' selama ' + p.period))),
      when(p.scope, h('p', { className: 'tr-muted tr-sys-type-support' }, 'Cakupan: ' + p.scope)),
      p.estimateDate ? h('p', { className: 'tr-muted tr-sys-type-support' }, 'Perkiraan per ' + date(p.estimateDate)) : null,
      when(p.assumptions, h('p', { className: 'tr-muted tr-sys-type-support' }, 'Asumsi: ' + p.assumptions)),
      when(p.edit, h('div', { className: 'tr-fin__edit' }, p.edit)));
  }
  var RESULT = { PASS: ['Terpenuhi', 'success'], FAIL: ['Tidak terpenuhi', 'danger'], UNKNOWN: ['Belum diketahui', 'warning'], NOT_APPLICABLE: ['Tidak berlaku', 'neutral'] };
  var STAGE = { SUBMISSION: 'Saat pengajuan', DISCUSSION: 'Saat diskusi', PILOT: 'Saat pilot', COMMERCIALIZATION: 'Saat komersialisasi' };
  var MODE = { DECLARATION: 'Pernyataan', DOCUMENT_PRESENT: 'Dokumen tersedia', REVIEWER_CONFIRMED: 'Diperiksa peninjau' };
  function RequirementRow(p) {
    var r = RESULT[p.result], later = p.stage && p.stage !== 'SUBMISSION' && p.result !== 'PASS';
    return h('li', { className: 'tr-req' },
      h('div', { className: 'tr-req__head' },
        h('h4', { className: 'tr-sys-type-label' }, p.label),
        // Later-stage work keeps its real result but is never styled as a submission blocker.
        h(Status, { tone: later ? 'neutral' : r[1], icon: p.result === 'NOT_APPLICABLE' ? 'minus' : undefined, label: r[0] })),
      h('p', { className: 'tr-muted tr-sys-type-support' }, [STAGE[p.stage], p.mandatory === false ? 'Preferensi' : 'Wajib', MODE[p.mode]].filter(Boolean).join(' · ')),
      when(later, h('p', { className: 'tr-sys-type-support' }, 'Untuk tahap berikutnya. Tidak menghalangi pengajuan.')),
      when(p.reason, h('p', null, p.reason)),
      when(p.source, h('p', { className: 'tr-muted tr-sys-type-support' }, 'Sumber: ' + p.source)),
      when(p.action, h('div', { className: 'tr-row' }, p.action)));
  }
  var TIMING = { CURRENT: 'Saat ini', PLANNED: 'Direncanakan', REQUESTED: 'Diminta' };
  var SOURCE = { SOURCE_REPORTED: 'Dilaporkan sumber', SELF_DECLARED: 'Dinyatakan sendiri', PROVIDED: 'Disediakan, belum diperiksa', REVIEWED: 'Diperiksa untuk kriteria ini', UNKNOWN: 'Belum diketahui' };
  function FactSource(p) {
    var reviewed = p.provenance === 'REVIEWED';
    return h('span', { className: 'tr-fact' },
      when(p.value, h('strong', { className: 'tr-fact__value' }, p.value)),
      when(p.timing, h('span', { className: cx('tr-tag tr-sys-type-support', 'tr-tag--' + String(p.timing).toLowerCase()) }, TIMING[p.timing])),
      when(p.provenance, reviewed ? h(Status, { tone: 'success', label: SOURCE.REVIEWED }) : h('span', { className: 'tr-tag tr-sys-type-support' }, SOURCE[p.provenance])),
      when(reviewed && p.reviewScope, h('span', { className: 'tr-muted tr-sys-type-support' }, p.reviewScope)),
      when(p.sourceHref, h(Link, { href: p.sourceHref, context: 'untuk fakta ini' }, p.sourceLabel || 'Lihat sumber')));
  }
  var FILE = { CREATED: ['Belum diunggah', 'neutral', 'file'], UPLOADING: ['Sedang diunggah', 'neutral', 'upload'], QUARANTINED: ['Sedang diperiksa keamanannya', 'warning', 'shield'], AVAILABLE: ['Aman dan tersedia', 'success', 'check'], REJECTED: ['Ditolak saat pemeriksaan keamanan', 'danger', 'cross'] };
  var EXTRACT = { NOT_REQUESTED: ['Tidak diminta', 'neutral', 'minus'], PENDING: ['Menunggu giliran', 'neutral', 'clock'], RUNNING: ['Sedang dibaca', 'neutral', 'clock'], SUCCEEDED: ['Teks berhasil dibaca', 'success', 'check'], FAILED: ['Gagal dibaca', 'danger', 'cross'], NEEDS_MANUAL_INPUT: ['Perlu diisi manual', 'warning', 'edit'] };
  var REVIEW = { PROVIDED_UNREVIEWED: ['Disediakan, belum diperiksa', 'neutral', 'clock'], REVIEWED_SUPPORTED: ['Diperiksa, mendukung kriteria', 'success', 'check'], REVIEWED_UNSUPPORTED: ['Diperiksa, tidak mendukung kriteria', 'danger', 'cross'], NEEDS_CLARIFICATION: ['Perlu klarifikasi', 'warning', 'question'], EXPIRED: ['Sudah kedaluwarsa', 'warning', 'clock'], SUPERSEDED: ['Diganti versi baru', 'neutral', 'minus'] };
  function axis(label, def) {
    return h('div', { className: 'tr-doc__axis' }, h('dt', { className: 'tr-sys-type-support' }, label), h('dd', null, h(Status, { tone: def[1], icon: def[2], label: def[0] })));
  }
  function DocumentItem(p) {
    if (p.denied) {
      return h('article', { className: 'tr-doc' }, h('div', { className: 'tr-doc__head' }, h(Icon, { name: 'lock' }), h('h4', { className: 'tr-sys-type-label' }, 'Dokumen terbatas')),
        h('p', null, 'Anda tidak memiliki akses ke dokumen ini.'), when(p.action, h('div', { className: 'tr-row' }, p.action)));
    }
    var g = p.grant;
    return h('article', { className: 'tr-doc' },
      h('div', { className: 'tr-doc__head' }, h(Icon, { name: 'file' }), h('h4', { className: 'tr-sys-type-label' }, p.title), when(p.version, h('span', { className: 'tr-muted tr-sys-type-support' }, 'Versi ' + p.version))),
      h('dl', { className: 'tr-doc__axes' },
        axis('Berkas', FILE[p.file || 'CREATED']),
        axis('Pembacaan teks', EXTRACT[p.extraction || 'NOT_REQUESTED']),
        axis('Pemeriksaan bukti', REVIEW[p.review || 'PROVIDED_UNREVIEWED'])),
      when(g, h('p', { className: 'tr-sys-type-support' }, g && (g.revoked
        ? 'Akses ' + g.recipient + ' dicabut. Unduhan baru diblokir, tetapi salinan yang sudah diunduh tidak dapat ditarik.'
        : 'Dibagikan hanya kepada ' + g.recipient + ', hanya versi ' + (g.version || p.version) + '.'))),
      when(!g, h('p', { className: 'tr-muted tr-sys-type-support' }, 'Privat. Belum dibagikan kepada siapa pun.')),
      when(p.file === 'QUARANTINED', h('p', { className: 'tr-sys-type-support' }, 'Jawaban lain tetap tersimpan. Berkas ini belum dapat dipakai sampai pemeriksaan selesai.')),
      when(p.file === 'REJECTED', h('p', { className: 'tr-sys-type-support' }, 'Berkas ini tidak dapat dipakai. Unggah berkas lain.')),
      when(p.action, h('div', { className: 'tr-row' }, p.action)));
  }

  /* ================= domain: cards ================= */
  function Art(p) {
    if (p.image) return h('img', { className: 'tr-art', src: p.image.src, alt: p.image.alt });
    return h('div', { className: 'tr-art' }, h(Icon, { name: p.icon }), h('span', { className: 'tr-sys-type-support-strong' }, p.category));
  }
  function Reasons(p) {
    return when(p.items && p.items.length, h('ul', { className: 'tr-reasons' }, (p.items || []).map(function (r) { return h('li', { key: r }, r); })));
  }
  function Facts(p) {
    return h('dl', { className: 'tr-facts' }, p.rows.filter(function (r) { return r[1]; }).map(function (r) {
      return h('div', { key: r[0] }, h('dt', { className: 'tr-sys-type-support-strong' }, r[0]), h('dd', null, r[1]));
    }));
  }
  function InventionCard(p) {
    return h('article', { className: 'tr-card' },
      h(Art, { image: p.image, category: p.category, icon: 'bulb' }),
      h('div', { className: 'tr-card__body' },
        h('h3', { className: 'tr-sys-type-heading-sm' }, p.title),
        when(p.manager, h('p', { className: 'tr-muted tr-sys-type-support' }, p.manager)),
        h(Facts, { rows: [['Masalah', p.problem], ['Solusi saat ini', p.solution], ['Tahap', p.maturity], ['Dukungan dicari', p.support]] }),
        when(p.financial, h(FinancialScope, Object.assign({ compact: true }, p.financial))),
        when(p.facts, p.facts),
        h(Reasons, { items: p.reasons }),
        when(p.gap, p.gap),
        when(p.action, h('div', { className: 'tr-row' }, p.action))));
  }
  function FundingRequestCard(p) {
    var linked = p.inventions || [];
    return h('article', { className: 'tr-card' },
      h(Art, { category: 'Pendanaan Perusahaan', icon: 'building' }),
      h('div', { className: 'tr-card__body' },
        h('h3', { className: 'tr-sys-type-heading-sm' }, p.company),
        h('p', { className: 'tr-muted tr-sys-type-support' }, p.proposedEntity ? 'Perusahaan belum didirikan' : 'Badan usaha telah disebutkan, status pemeriksaan ditampilkan terpisah'),
        h(Facts, { rows: [['Tahap pendanaan', p.stage], ['Bentuk', p.form], ['Tujuan', p.purpose]] }),
        h(FinancialScope, { compact: true, subject: 'companyTarget', currency: p.currency, min: p.target, max: p.target }),
        h(FinancialScope, { compact: true, subject: 'contribution', currency: p.currency, min: p.desiredMin, max: p.desiredMax }),
        when(p.partialAccepted, h('p', { className: 'tr-sys-type-support' }, 'Menerima pendanaan sebagian dan bersama investor lain.')),
        h('p', { className: 'tr-sys-type-label' }, linked.length + ' inovasi terkait'),
        when(linked.length, h('ul', { className: 'tr-reasons tr-reasons--plain' }, linked.map(function (i) { return h('li', { key: i }, i); }))),
        h(Reasons, { items: p.reasons }),
        when(p.gap, p.gap),
        when(p.action, h('div', { className: 'tr-row' }, p.action))));
  }

  /* ================= domain: collaboration ================= */
  var RESPONSES = [
    { value: 'CAN', label: 'Dapat dipenuhi' },
    { value: 'DISCUSS', label: 'Perlu diskusi' },
    { value: 'CANNOT', label: 'Belum dapat dipenuhi', hint: 'Jawaban jujur ini tetap sah untuk dikirim. Ini bukan persetujuan.' }
  ];
  function RevisionItem(p) {
    var v = p.value || {};
    function set(k, val) { if (p.onChange) p.onChange(Object.assign({}, v, (function () { var o = {}; o[k] = val; return o; })())); }
    return h('article', { className: 'tr-revision' },
      h('div', { className: 'tr-req__head' },
        h('h3', { className: 'tr-sys-type-label' }, 'Putaran ' + (p.round || 1) + ' · Pertanyaan ' + (p.index || 1)),
        h(Status, { tone: p.required ? 'action' : 'neutral', icon: null, label: p.required ? 'Wajib dijawab' : 'Opsional' })),
      h('p', { className: 'tr-sys-type-body-strong' }, p.question),
      when(p.reason, h('p', null, h('span', { className: 'tr-muted' }, 'Alasan: '), p.reason)),
      p.due ? h('p', { className: 'tr-muted tr-sys-type-support' }, 'Batas waktu: ' + date(p.due)) : null,
      h(ChoiceGroup, { id: p.id, legend: 'Tanggapan Anda', required: p.required, value: v.response, onChange: function (x) { set('response', x); }, options: RESPONSES, error: p.error }),
      h(TextArea, { label: 'Penjelasan', hint: 'Anda dapat menjelaskan apa yang sudah ada dan apa yang belum.', rows: 3, value: v.text, onChange: function (x) { set('text', x); } }),
      when(p.attachments, p.attachments),
      when(p.review, p.review));
  }
  function ScheduleSlotList(p) {
    var auto = useId(), zone = p.zone || DEFAULT_ZONE, closed = p.state === 'expired' || p.state === 'superseded' || p.state === 'cancelled';
    var note = { expired: 'Usulan waktu ini sudah kedaluwarsa.', superseded: 'Usulan ini sudah diganti usulan baru.', cancelled: 'Usulan ini dibatalkan.' }[p.state];
    return h('div', { className: 'tr-slots' },
      when(p.agenda, h('p', null, h('span', { className: 'tr-muted' }, 'Agenda: '), p.agenda)),
      when(note, h(Status, { tone: 'neutral', label: note })),
      h('fieldset', { className: 'tr-fieldset' },
        h('legend', { className: 'tr-field__label tr-sys-type-label' }, 'Pilih waktu'),
        h('p', { className: 'tr-field__hint tr-sys-type-support' }, 'Waktu ditampilkan dalam ' + zoneLabel(zone) + '.'),
        h('div', { className: 'tr-choices' }, p.slots.map(function (s) {
          var selected = p.selectedId === s.id, confirmed = p.confirmedId === s.id, blocked = closed || !!s.conflict, id = auto + s.id;
          return h('label', { key: s.id, htmlFor: id, className: cx('tr-choice', selected && 'is-selected', blocked && 'is-disabled') },
            h('input', { type: 'radio', id: id, name: auto, checked: selected || confirmed, disabled: blocked || !!p.confirmedId, onChange: function () { if (p.onSelect) p.onSelect(s.id); } }),
            h('span', { className: 'tr-choice__body' },
              h('span', { className: 'tr-sys-type-label' }, longDate(s.start, zone)),
              h('span', { className: 'tr-num' }, slotTime(s.start, s.minutes, zone)),
              h('span', { className: 'tr-choice__hint tr-sys-type-support' }, s.minutes + ' menit' + (p.otherZone ? ' · Pihak lain: ' + slotTime(s.start, s.minutes, p.otherZone) : '')),
              when(s.conflict, h(Status, { tone: 'warning', icon: 'alert', label: 'Waktu sudah bentrok' })),
              when(selected && !confirmed, h(Status, { tone: 'action', icon: 'clock', label: 'Dipilih, belum dikonfirmasi' })),
              when(confirmed, h(Status, { tone: 'success', label: 'Waktu dikonfirmasi' }))));
        }))),
      when(p.error, p.error),
      when(!closed && !p.confirmedId, h('div', { className: 'tr-row' },
        h(Button, { intent: 'primary', busy: p.busy, busyLabel: 'Mengonfirmasi…', disabledReason: p.selectedId ? null : 'Pilih satu waktu terlebih dahulu.', onClick: p.onConfirm }, 'Konfirmasi waktu'),
        h(Button, { intent: 'secondary', onClick: p.onPropose }, 'Usulkan waktu lain'))));
  }
  var CONSENT = { none: ['Draf', 'neutral'], one: ['Menunggu konfirmasi', 'neutral'], both: ['Dikonfirmasi kedua pihak', 'success'] };
  // Public fields: both parties confirmed this version, both consent, and no live restriction.
  function effectiveFields(p) {
    var both = p.mine.confirmedVersion === p.version && p.other.confirmedVersion === p.version, cut = p.restricted || [];
    return !both ? [] : p.fields.map(function (f) { return f.id; }).filter(function (id) {
      return p.mine.selected.indexOf(id) >= 0 && p.other.selected.indexOf(id) >= 0 && cut.indexOf(id) < 0;
    });
  }
  function PartnershipConsent(p) {
    var mineDone = p.mine.confirmedVersion === p.version, otherDone = p.other.confirmedVersion === p.version;
    var state = CONSENT[mineDone && otherDone ? 'both' : mineDone || otherDone ? 'one' : 'none'], pub = effectiveFields(p), cut = p.restricted || [];
    function partyCell(party, id, done) {
      var on = party.selected.indexOf(id) >= 0;
      return h('span', { className: 'tr-sys-type-support' }, done ? (on ? 'Diizinkan' : 'Tidak diizinkan') : 'Belum memilih');
    }
    return h('div', { className: 'tr-consent' },
      h('div', { className: 'tr-req__head' }, h('h3', { className: 'tr-sys-type-heading-sm' }, 'Ringkasan Kerja Sama · Versi ' + p.version), h(Status, { tone: state[1], label: state[0] })),
      when(p.type, h('p', { className: 'tr-muted' }, p.type)),
      p.summary,
      h('h4', { className: 'tr-sys-type-label' }, 'Yang boleh tampil di publik'),
      h('p', { className: 'tr-sys-type-support' }, 'Hanya data yang diizinkan kedua pihak yang tampil. Data lain tetap privat.'),
      h('ul', { className: 'tr-consent__list' }, p.fields.map(function (f) {
        var isPublic = pub.indexOf(f.id) >= 0, restricted = cut.indexOf(f.id) >= 0;
        return h('li', { key: f.id, className: 'tr-consent__row' },
          p.readOnly || mineDone
            ? h('p', { className: 'tr-sys-type-label' }, f.label)
            : h(Checkbox, { label: f.label, checked: p.mine.selected.indexOf(f.id) >= 0, onChange: function (v) { if (p.onToggle) p.onToggle(f.id, v); } }),
          when(f.value, h('p', { className: 'tr-muted tr-sys-type-support' }, f.value)),
          h('p', { className: 'tr-consent__parties' }, h('span', { className: 'tr-sys-type-support' }, (p.mine.name || 'Anda') + ': '), partyCell(p.mine, f.id, mineDone), h('span', { className: 'tr-sys-type-support' }, ' · ' + p.other.name + ': '), partyCell(p.other, f.id, otherDone)),
          h('div', { className: 'tr-consent__result' },
            h(Status, { tone: isPublic ? 'success' : 'neutral', icon: isPublic ? 'eye' : 'eyeOff', label: isPublic ? 'Tampil di publik' : restricted ? 'Disembunyikan' : 'Tetap privat' }),
            when(isPublic && p.onRestrict, h(Button, { intent: 'secondary', onClick: function () { p.onRestrict(f.id); } }, 'Sembunyikan'))));
      })),
      when(cut.length, h('p', { className: 'tr-sys-type-support' }, 'Data yang disembunyikan langsung hilang dari tampilan publik. Salinan yang sudah diunduh pihak lain tidak dapat ditarik.')),
      when(p.error, p.error),
      when(!mineDone && !p.readOnly, h('div', { className: 'tr-row' },
        h(Button, { intent: 'primary', busy: p.busy, busyLabel: 'Mengonfirmasi…', onClick: p.onConfirm }, 'Konfirmasi versi ' + p.version),
        h(Button, { intent: 'secondary', onClick: p.onRequestChange }, 'Minta perubahan'))));
  }
  function VersionConflict(p) {
    return h('div', { className: 'tr-conflict', role: 'group', 'aria-label': 'Versi berubah' },
      h(Status, { tone: 'warning', icon: 'alert', label: 'Versi sudah berubah' }, h('p', null, p.what)),
      when(p.currentVersion, h('p', null, 'Versi terbaru: ' + p.currentVersion)),
      when(p.draft, h('div', null,
        h('p', { className: 'tr-sys-type-label' }, 'Draf Anda masih aman:'),
        h('blockquote', { className: 'tr-quote' }, p.draft))),
      h('div', { className: 'tr-row' },
        when(p.onRefresh, h(Button, { intent: 'primary', icon: 'refresh', onClick: p.onRefresh }, p.refreshLabel || 'Muat versi terbaru')),
        when(p.onCopy, h(Button, { intent: 'secondary', onClick: p.onCopy }, 'Salin draf saya')),
        when(p.onCompare, h(Button, { intent: 'secondary', onClick: p.onCompare }, 'Bandingkan'))));
  }

  /* ================= fictional demo fixtures and test controls (workbench only) ================= */
  var fixtures = {
    provenance: 'Demo · Data fiktif',
    contexts: [
      { id: 'pribadi', kind: 'personal', name: 'Rani' },
      { id: 'tim', kind: 'organization', name: 'Tim Air Bersih Demo' },
      { id: 'lain', kind: 'organization', name: 'Demo Circular Materials Ltd', disabledReason: 'Anda belum menjadi anggota' }
    ],
    F01: { title: 'ClearSpring', category: 'Air bersih', manager: 'Dikelola Rani · Pribadi', problem: 'Keluarga tanpa akses air bersih perlu cara menyaring air yang mudah dirawat.', solution: 'Prototipe filter air yang sudah berfungsi.', maturity: 'Prototipe', support: 'Validasi prototipe', financial: { subject: 'project', currency: 'USD', min: '20000', max: '30000', period: '6 bulan', scope: 'Validasi prototipe' } },
    F02: { title: 'FieldDry', category: 'Pertanian', manager: 'Dikelola tim komunitas', problem: 'Hasil panen perlu dikeringkan tanpa bergantung pada cuaca.', solution: 'Proses pengeringan pada tahap pilot.', maturity: 'Pilot', support: 'Fasilitas uji', financial: { subject: 'project', noncash: 'Tanpa dana tunai: fasilitas uji' } },
    F03: { title: 'QueueNest', category: 'Perangkat lunak', manager: 'Dikelola tim perangkat lunak', problem: 'Tim layanan perlu mengatur antrean walau koneksi tidak stabil.', solution: 'Aplikasi penjadwalan dengan ekspor luring.', maturity: 'Sudah berfungsi', support: 'Diskusi lisensi', financial: { subject: 'license', terms: 'Belum ditentukan' } },
    F04: { title: 'LoopMaterial', category: 'Material', maturity: 'Prototipe' },
    F05: { title: 'ReFormPress', category: 'Manufaktur' },
    F06: { title: 'GridShare', category: 'Energi', manager: 'Dikelola tim nirlaba', problem: 'Komunitas perlu memantau pemakaian energi bersama.', solution: 'Konsep pemantauan energi komunitas.', maturity: 'Ide', support: 'Pendampingan', financial: { subject: 'project', noncash: 'Pendampingan, kebutuhan dana belum diketahui' } },
    FRaise01: { company: 'Demo Circular Materials Ltd', stage: 'Pre-seed', form: 'Ekuitas', purpose: 'Mengembangkan dua inovasi perusahaan', currency: 'USD', target: '500000', desiredMin: '50000', desiredMax: '100000', partialAccepted: true, inventions: ['LoopMaterial', 'ReFormPress'] },
    slots: [
      { id: 's1', start: '2026-11-16T09:30:00Z', minutes: 60 },
      { id: 's2', start: '2026-11-16T10:00:00Z', minutes: 60 },
      { id: 's3', start: '2026-11-17T09:00:00Z', minutes: 60 }
    ],
    booked: { start: '2026-11-16T09:00:00Z', minutes: 60 }
  };
  function useAxes(initial) {
    var s = useState(initial);
    return { value: s[0], set: function (k, v) { s[1](function (o) { var n = Object.assign({}, o); n[k] = v; return n; }); }, reset: function () { s[1](initial); } };
  }
  function Controls(p) {
    return h('section', { className: 'tr-controls', 'aria-label': 'Kontrol uji, bukan bagian produk' },
      h('p', { className: 'tr-sys-type-support-strong' }, 'Kontrol uji · bukan bagian produk'),
      h('div', { className: 'tr-controls__row' },
        (p.axes || []).map(function (a) {
          return h('label', { key: a.id, className: 'tr-controls__axis tr-sys-type-support' }, a.label,
            h('select', { className: 'tr-input tr-select', value: p.state.value[a.id], onChange: function (e) { p.state.set(a.id, e.target.value); } },
              a.options.map(function (o) { return h('option', { key: o, value: o }, o); })));
        }),
        p.children,
        when(p.state && p.state.reset, h(Button, { intent: 'secondary', icon: 'refresh', onClick: p.state && p.state.reset }, 'Atur ulang'))));
  }

  window.TR = {
    version: '1.0.0-draft',
    format: format,
    effectiveFields: effectiveFields,
    demo: { fixtures: fixtures, Controls: Controls, useAxes: useAxes },
    Button: Button, Link: Link, TextField: TextField, TextArea: TextArea, Select: Select, ChoiceGroup: ChoiceGroup, Checkbox: Checkbox,
    FieldError: FieldError, ErrorSummary: ErrorSummary, Dialog: Dialog, Disclosure: Disclosure, Tabs: Tabs, Status: Status, EmptyState: EmptyState,
    SaveState: SaveState, ContextSwitcher: ContextSwitcher, InventionCard: InventionCard, FundingRequestCard: FundingRequestCard, FinancialScope: FinancialScope,
    RequirementRow: RequirementRow, FactSource: FactSource, DocumentItem: DocumentItem, RevisionItem: RevisionItem, ScheduleSlotList: ScheduleSlotList,
    PartnershipConsent: PartnershipConsent, VersionConflict: VersionConflict, NextStep: NextStep, Steps: Steps, SummaryList: SummaryList, Screen: Screen, Icon: Icon
  };
})();
