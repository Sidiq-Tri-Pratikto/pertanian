# ContextSwitcher

Shows and changes the personal or organization context a person acts in.

**Anatomy.** Labelled select; read-only line before consequential actions.

**Consumer provides.** `value`, `onChange(id)`, `options` [{id, kind personal | organization, name, disabledReason}], `readOnly`, `actionLabel`, `label`, `hint`.

**States.** Personal, organization, unavailable with a safe reason, read-only.

**Keyboard and screen reader.** Native select. Read-only form is plain text.

**Tokens.** `tr-comp-field-*`.

**Responsive.** Sits in the top bar; full width on phones.

**Do.** Show the read-only line before send, decide and confirm.

**Don't.** Do not treat a selection as authority: the server checks membership. Do not force a person to create an organization.
