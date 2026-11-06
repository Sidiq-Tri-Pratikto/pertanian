# Notice

Persistent explanation with a tone word, icon and optional action — not a colour-only toast.

**Anatomy.** Icon · title (hidden tone word prefix) · body · action.

**Consumer provides.** `tone` info | attention | error | success | neutral, `title`, `children`, `action`, `live`.

**Variants and states.** Each tone; success only after confirmation.

**Keyboard and screen reader.** Hidden prefix ("Perhatian:", "Kesalahan:") so meaning is not colour-only. `live` adds `role=status` (or `alert` for error) when it appears in response to an action.

**Tokens.** `color-status-*`, `radius-surface`, `space-16`.

**Responsive.** Full width.

**Example.** Attention "Sebagian data belum tersedia" with "Lihat jam tanpa data".

**Limits.** No stacking several notices for one cause; no success before acknowledgment.
