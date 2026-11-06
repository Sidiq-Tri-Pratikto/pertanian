# Button

One action, labelled with a verb in Indonesian; at most one primary per task step.

**Anatomy.** Container (48 min height) · optional icon or spinner · label · reason line when disabled.

**Consumer provides.** `children` label, `variant` primary | secondary | text | destructive, `onClick`, optional `type`, `icon`, `loading` + `loadingLabel`, `disabledReason`, `fullWidth`.

**Variants and states.** Default, hover, pressed, focus (ring), loading (spinner + "Menyimpan…", clicks ignored, `aria-busy`), disabled-with-reason (dashed border, readable label, reason shown under it and linked with `aria-describedby`).

**Keyboard and screen reader.** Native `<button>`; Enter/Space. Disabled uses `aria-disabled` so it stays focusable and the reason is read. Loading never announces success — pair with `HD.ProgressStatus`.

**Tokens.** `button-primary-*`, `color-action-*`, `color-disabled-*`, `space-control-padding*`, `radius-control`, `size-target-minimum`, `duration-feedback`.

**Responsive.** Labels wrap; `fullWidth` in narrow sheets and footers.

**Example.** Primary "Simpan tarif"; text "Atur tarif"; destructive "Buang draf".

**Limits.** No power/on/off actions. Destructive is for discarding drafts or imports, never for energy values. Do not blanket-dim disabled buttons.
