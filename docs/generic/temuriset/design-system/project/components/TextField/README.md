# TextField

Labelled single-line input for text, email and decimal values.

**Anatomy.** Visible label, requiredness, hint, inline error, input, optional unit.

**Consumer provides.** `label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `type` text | email | decimal, `prefix`, `suffix`, `id`, `name`, `autoComplete`.

**States.** Default, focus, invalid (2 px boundary plus text), filled.

**Keyboard and screen reader.** `<label for>`, `aria-describedby` joins hint and error, `aria-invalid` on error. Decimal uses `inputMode="decimal"` and stays text, so an empty value is never turned into zero.

**Tokens.** `tr-comp-field-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`.

**Responsive.** Full width of its container; the unit stays beside the value.

**Do.** Keep nonsecret input on error and show the unit next to the number.

**Don't.** Do not use placeholder text as the label.
