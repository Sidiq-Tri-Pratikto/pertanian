# FieldError

Plain correction message tied to one field.

**Anatomy.** Icon, hidden "Kesalahan:" prefix, message.

**Consumer provides.** `id`, `children`, `code` (stable error code stored as `data-code`).

**States.** Single state; shown only when the field is invalid.

**Keyboard and screen reader.** Linked from the field through `aria-describedby`. The same words appear in `TR.ErrorSummary`.

**Tokens.** `tr-sys-color-danger-text`.

**Responsive.** Wraps.

**Do.** Say what to fix: "Biaya maksimum tidak boleh lebih kecil dari biaya minimum."

**Don't.** Do not show stack traces, HTTP codes or another party's data. Do not erase the value.
