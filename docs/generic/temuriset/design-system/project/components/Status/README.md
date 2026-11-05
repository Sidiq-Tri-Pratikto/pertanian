# Status

A domain result in words, supported by icon and colour.

**Anatomy.** Label with icon; with `children` it becomes a notice with an explanation.

**Consumer provides.** `label`, `tone` neutral | success | danger | warning | action, `icon` (null removes it), `children`, `live` true | alert.

**States.** Five tones. Pending work stays neutral; UNKNOWN is warning with a question mark; FAIL is danger with a cross.

**Keyboard and screen reader.** Meaning is always in the text. `live` adds `role="status"` or `alert` without moving focus.

**Tokens.** `tr-sys-color-success-*`, `tr-sys-color-danger-*`, `tr-sys-color-warning-*`, `tr-sys-color-selected-*`, `tr-sys-color-surface-subtle`.

**Responsive.** Wraps.

**Do.** Pass the real result from the domain and add one sentence on what it means.

**Don't.** Do not derive PASS or approval from colour. Do not paint pending work as success.
