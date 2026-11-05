# Select

Native selection with a visible empty choice.

**Anatomy.** Label, hint, error, browser select.

**Consumer provides.** `label`, `value`, `onChange(value)`, `options` [{value, label, disabledReason}], `emptyLabel` (null removes it), `hint`, `required`, `error`.

**States.** Default, focus, invalid, disabled option with its reason in the text.

**Keyboard and screen reader.** Native keyboard and screen-reader behaviour.

**Tokens.** `tr-comp-field-*`.

**Responsive.** Full width; the platform picker opens on phones.

**Do.** Start empty when no choice has been made.

**Don't.** Do not silently pick a sector, currency or company.
