# TabNavigation

The three persistent destinations Beranda, Perangkat and Saran — fixed, labelled, current page marked.

**Anatomy.** Bar · three items (icon + label) · current indicator bar + fill + semibold.

**Consumer provides.** `current`, `onNavigate` or `hrefs`.

**Variants and states.** Default, hover, focus, current.

**Keyboard and screen reader.** `<nav aria-label="Navigasi utama">` with links; current has `aria-current="page"`.

**Tokens.** `tab-selected-*`, `color-text-secondary`, `size-border-selected`, `size-target-minimum`.

**Responsive.** Sticky at the bottom inside `HD.Screen` at every width; bottom padding adds `env(safe-area-inset-bottom)`; labels stay visible.

**Example.** `current: 'beranda'`.

**Limits.** Cannot add a fourth destination; no badges that imply urgency.
