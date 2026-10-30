# PeriodSelector

Choose today, the last 7 complete local days or an explicit range; presets commit when chosen, a range commits on "Terapkan".

**Anatomy.** Group label · preset buttons (pressed state + check) · two date fields + Terapkan · error · "Periode aktif" line with timezone and pending note.

**Consumer provides.** `value` {preset,start,end} (committed), `onCommit`, `today` (local ISO date in Asia/Jakarta, virtual now in demos), optional `label`, `timezone`.

**Variants and states.** Preset selected, range draft pending ("Pilihan tanggal belum diterapkan"), invalid range, committed.

**Keyboard and screen reader.** Presets are buttons with `aria-pressed`; the active period line is a polite live region.

**Tokens.** `color-selection-*`, `size-border-selected`, `space-*`.

**Responsive.** Presets wrap; range fields stack below 20 rem.

**Example.** today 2026-10-26 → "7 hari lengkap terakhir" = 19–25 Oktober 2026.

**Limits.** Never label a completed week "Minggu ini" on Monday. The app computes data for the committed period only.
