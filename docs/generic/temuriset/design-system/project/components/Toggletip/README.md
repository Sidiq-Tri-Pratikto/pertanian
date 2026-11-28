# Toggletip

Explains a term in place on click or keyboard activation, never hover-only.

**Anatomy.** 24 px icon button with question mark and a live-region panel.

**Consumer provides.** `label` (term explained), `children` (short explanation), `id`.

**States.** Collapsed, expanded, hover, focus.

**Keyboard and screen reader.** Button with `aria-expanded`, `aria-controls` and accessible name "Penjelasan: {label}". Panel mounts inside `role="status"`. Opens on click or Enter; closes on Escape or outside click.

**Tokens.** `tr-sys-color-surface`, `tr-sys-color-border-control`, `tr-sys-color-selected-*`, `tr-sys-shadow-dialog`.

**Responsive.** Panel width caps at viewport width minus gutter so 320 px never overflows.

**Do.** Use for short definitions such as TKT levels or match dimensions.

**Don't.** Do not put interactive forms or long sections inside a toggletip; use Disclosure or Dialog.
