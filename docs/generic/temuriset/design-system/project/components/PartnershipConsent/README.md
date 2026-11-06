# PartnershipConsent

Both parties confirm one exact version; only what both allow can go public.

**Anatomy.** Version heading, state, summary, field rows with each party's choice and result, actions.

**Consumer provides.** `version`, `type`, `summary`, `fields` [{id, label, value}], `mine` {name, selected, confirmedVersion}, `other` {name, selected, confirmedVersion}, `restricted` [ids], `onToggle(id, checked)`, `onConfirm`, `onRequestChange`, `onRestrict(id)`, `busy`, `readOnly`, `error`.

**States.** Draf, Menunggu konfirmasi, Dikonfirmasi kedua pihak, field private, field public, field hidden by a live restriction.

**Keyboard and screen reader.** Checkboxes before you confirm; plain text after. Results are text with icons.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** One column per field.

**Do.** Say that hiding a field cannot recall a download.

**Don't.** One confirmation is never mutual. A new version inherits no confirmation. Amounts stay private by default.
