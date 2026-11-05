# ChoiceGroup

Mutually exclusive radio choices with whole-row targets.

**Anatomy.** Fieldset, legend, hint, error, rows with label, hint and optional disabled reason.

**Consumer provides.** `legend`, `options` [{value, label, hint, disabledReason}], `value`, `onChange(value)`, `hint`, `required`, `error`, `id` (first radio), `name`.

**States.** Default, hover, focus, selected (2 px boundary plus filled radio), disabled with reason, invalid.

**Keyboard and screen reader.** Native radios: Tab enters the group, arrows move within it. The row is the `<label>`.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-color-border-control`, `tr-sys-size-borderSelected`.

**Responsive.** One column at every width, so long labels stay readable.

**Do.** Use for support type, relationship type and current or planned status.

**Don't.** Do not delete unrelated saved drafts when the purpose changes.
