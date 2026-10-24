# IconButton

Icon-only (or icon + label) action with an Indonesian accessible name and a 48 × 48 hit area.

**Anatomy.** 48 hit area · 24 icon · optional visible label · reason line.

**Consumer provides.** `icon`, `label` (required, e.g. "Tutup"), `showLabel` for unfamiliar icons, `tooltip` (supplementary), `onClick`, `disabledReason`.

**Variants and states.** Default, hover, focus, disabled-with-reason.

**Keyboard and screen reader.** `aria-label` = `label` when the label is hidden. Tooltip is never the only name.

**Tokens.** `size-target-minimum`, `size-icon-default`, `color-text-primary`, `color-background-subtle`.

**Responsive.** Same at every width.

**Example.** Close a sheet: `icon: 'close', label: 'Tutup'`; back: `chevronLeft` + "Kembali".

**Limits.** No ambiguous unlabeled actions; no power symbol.
