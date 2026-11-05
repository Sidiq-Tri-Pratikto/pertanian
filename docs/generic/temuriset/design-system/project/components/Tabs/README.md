# Tabs

Related views inside one pitch workspace.

**Anatomy.** Tab list, tabs, one panel.

**Consumer provides.** `label`, `tabs` [{id, label, content}], `value`, `onChange(id)`.

**States.** Default, hover, focus, selected (2 px bar, weight and surface).

**Keyboard and screen reader.** ARIA tabs with automatic activation. Arrow keys, Home and End move between tabs; Tab moves to the panel.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-color-border-control`.

**Responsive.** Tabs wrap to more rows, so every tab stays reachable without hidden scrolling.

**Do.** Keep a logical heading in each panel.

**Don't.** Do not use tabs for ordered steps; use `TR.Steps`.
