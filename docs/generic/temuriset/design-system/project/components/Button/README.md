# Button

One action, named by its effect; at most one primary per task region.

**Anatomy.** Control (44 px comfortable minimum), optional icon or spinner, label, reason line when disabled.

**Consumer provides.** `children`, `intent` primary | secondary | danger, `onClick`, `type`, `icon`, `busy` + `busyLabel`, `disabledReason`, `fullWidth`, `id`, `form`, `describedBy`.

**States.** Default, hover, pressed, focus, busy (repeat clicks ignored, `aria-busy`), disabled-with-reason (dashed boundary, readable label, reason beside it).

**Keyboard and screen reader.** Native `<button>`, name from the visible label; Enter and Space work. Disabled uses `aria-disabled`, so it stays focusable and the reason is read through `aria-describedby`.

**Tokens.** `tr-comp-button-primary-*`, `tr-sys-color-action-*`, `tr-sys-color-disabled-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`, `tr-sys-motion-feedback`.

**Responsive.** Labels wrap. Use `fullWidth` in narrow footers.

**Do.** Say the effect: "Kirim pitching", "Setujui untuk diskusi", "Konfirmasi waktu".

**Don't.** Do not write "OK" or "Lanjutkan" for a consequential action. Do not dim a disabled button with opacity or hide why it is disabled.
