# Checkbox

Independent yes or no choice; consent stays unchecked until really given.

**Anatomy.** Row label, checkbox, hint, reason. `Checkbox.Group` adds fieldset and legend.

**Consumer provides.** `label`, `checked`, `onChange(checked)`, `hint`, `disabledReason`, `error`, `id`. Group: `legend`, `hint`, `children`.

**States.** Unchecked, checked, focus, disabled with reason, invalid.

**Keyboard and screen reader.** Native checkbox; Space toggles. The row is the `<label>`.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.

**Responsive.** One column.

**Do.** Ask for one named permission at a time.

**Don't.** Do not precheck a blanket permission for private files or publication.
