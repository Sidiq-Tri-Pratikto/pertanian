# TextArea

Labelled multiline answer that keeps its text through errors and retries.

**Anatomy.** Label, hint, error, resizable area, optional character count.

**Consumer provides.** `label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `rows`, `limit`, `id`.

**States.** Default, focus, invalid, over limit (text and colour).

**Keyboard and screen reader.** Count is linked by `aria-describedby` and is not a live region, so typing is not announced key by key.

**Tokens.** `tr-comp-field-*`, `tr-sys-color-danger-text`.

**Responsive.** Full width; the person can resize it vertically.

**Do.** Size it to the expected answer. State the limit in the hint or count.

**Don't.** Do not cut text at the limit; let the person edit it down.
