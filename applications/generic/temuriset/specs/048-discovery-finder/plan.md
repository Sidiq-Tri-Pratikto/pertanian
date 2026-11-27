# Implementation Plan: Discovery and Investor finder (revamp R2a)

**Spec**: [spec.md](spec.md)

1. `features/discovery/model.ts`: `discoverHref(type, filters, selected)`, `FILTER_LABELS`, `appliedFilters()`, `filterCount()`.
2. `views/discovery/DiscoverView.tsx`: toolbar form (keyword + **Cari**, `<details>` **Filter (n)**), chips, `tr-listdetail` with rows and the existing result card as the detail; `features/discovery/FocusFromHash.tsx` moves focus to `#detail` or `#hasil-{id}`. `app/discover/page.tsx` reads `selected`.
3. `views/discovery/MatchCard.tsx`: action-first card, `labelTone()` from enums, **Mengapa cocok?**. `MatchesView.tsx`: `MatchList` with client selection and focus return.
4. `features/discovery/SaveButton.tsx` extracted from `ItemActions.tsx`; `InventionViews.tsx` and `app/inventions/[id]/page.tsx` use it with the saved state from `/api/v1/saved-items`.
5. Design system `bundle.css`: phone rules for `tr-listdetail`, `tr-rowbutton`, `tr-linkbutton`; `make design`.
6. Tests: `tests/discovery.test.tsx` (chips, rows, detail, back link, match list and focus), `tests/portfolio.test.tsx` (save); `e2e/routes.ts` adds an opened result; `e2e/discovery-list.spec.ts` checks the phone keyboard round trip.
