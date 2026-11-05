# InventionCard

One invention, led by problem, current solution and what it needs.

**Anatomy.** Category band or image, title, manager, facts, scoped money, reasons, gap, one action.

**Consumer provides.** `title`, `category`, `image` {src, alt}, `manager`, `problem`, `solution`, `maturity`, `support`, `financial` (FinancialScope props), `facts`, `reasons`, `gap`, `action`. Pass an authorized projection only.

**States.** With or without image, with or without gap, noncash.

**Keyboard and screen reader.** `<article>` with a heading. The fallback band is labelled text; a missing image is not a problem state.

**Tokens.** `tr-sys-color-surface`, `tr-sys-color-selected-surface`, `tr-sys-radius-surface`.

**Responsive.** Fits a 18 rem column; content stacks.

**Do.** Keep a short reason and one action. Label planned functionality.

**Don't.** Do not add ratings, follower counts, funding progress or invented photos.
