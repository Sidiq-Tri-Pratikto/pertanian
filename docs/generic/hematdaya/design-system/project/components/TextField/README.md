# TextField

Labelled single- or multi-line text input with help, error, required/optional and draft states.

**Anatomy.** Label + (wajib)/(opsional)/(hanya baca) marker · help · error (above input) · input · note (draft or disabled reason).

**Consumer provides.** `label`, `value`, `onChange(value)`, optional `help`, `error`, `required` | `optional`, `readOnly`, `disabledReason`, `draftNote`, `multiline`, `type`, `id`.

**Variants and states.** Empty, filled, focus, error (2 px red border + message), read-only (dashed, focusable, copyable), disabled-with-reason (read-only + `aria-disabled` + visible reason), long value, retained draft note.

**Keyboard and screen reader.** Label is a real `<label for>`; help, error and note are joined in `aria-describedby`; `aria-invalid` on error.

**Tokens.** `field-border`, `field-border-error`, `color-text-*`, `color-disabled-*`, `space-control-padding*`, `radius-control`.

**Responsive.** Full width of its column.

**Example.** "Nama perangkat" (wajib) with "Pompa Air Area Produksi Belakang".

**Limits.** Do not put errors only in placeholder text or colour.
