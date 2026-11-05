# VersionConflict

Something changed underneath; the person's draft is safe.

**Anatomy.** Warning, what changed, current version, retained draft, recovery actions.

**Consumer provides.** `what`, `currentVersion`, `draft`, `onRefresh`, `refreshLabel`, `onCopy`, `onCompare`.

**States.** Single state with optional actions.

**Keyboard and screen reader.** Labelled group. Place focus on it or announce it after the failed action.

**Tokens.** `tr-sys-color-warning-*`, `tr-sys-color-surface-subtle`.

**Responsive.** Actions wrap.

**Do.** Offer one clear recovery and keep the text.

**Don't.** Do not merge consequential changes silently or reveal protected actor or source details.
