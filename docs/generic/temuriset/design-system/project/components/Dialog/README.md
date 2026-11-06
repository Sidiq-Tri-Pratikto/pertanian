# Dialog

Modal for one short decision, with safe focus handling.

**Anatomy.** Title, close button, body, primary and secondary effect.

**Consumer provides.** `open`, `onClose`, `title`, `children`, `primary` {label, onClick, busy, busyLabel, intent, disabledReason}, `secondary` {label, onClick}, `initialFocusId`, `returnFocusId`.

**States.** Closed, open, busy, recoverable error shown inside the body.

**Keyboard and screen reader.** Native modal `<dialog>`, labelled by its title. Initial focus lands on the title unless `initialFocusId` is set. Tab and Shift+Tab stay inside. Escape closes without committing. Focus returns to the opener.

**Tokens.** `tr-sys-radius-dialog`, `tr-sys-shadow-dialog`, `tr-sys-color-overlay`.

**Responsive.** Width caps at 40 rem; the body scrolls and the footer stays reachable.

**Do.** Use for a short confirmation, such as sharing one document version.

**Don't.** Do not put multi-step work in a dialog. Prefer an ordinary page. It owns focus, not authorization.
