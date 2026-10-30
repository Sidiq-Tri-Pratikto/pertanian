# DataQuality

Separate rows for temporal completeness, source freshness, client offline and provenance — no accuracy score.

**Anatomy.** Rows: icon + term · value · explanation · optional action.

**Consumer provides.** `completeness`, `gaps`, `freshness` {state fresh | stale | historical, lastMeasurement, importRange}, `client`, `cachedAge`, `source`, `onCheckSource`, `onViewPeriod`.

**Variants and states.** Partial, stale live source ("bukan tanda perangkat mati"), historical import ("Lihat periode data"), client offline (drafts retained), demo provenance.

**Keyboard and screen reader.** Description list (`dl`).

**Tokens.** `color-status-attention-foreground`, `color-text-secondary`, `size-icon-small`.

**Responsive.** Stacks.

**Example.** Partial + stale; historical import + offline.

**Limits.** Never merge these into one status or call completeness accuracy.
