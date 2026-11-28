# Implementation Plan: Investor finder revamp

**Branch**: `f/059-investor-finder` | **Spec**: [spec.md](spec.md) | **Track**: A | **Needs**: 057 and 058 merged (056 preferably merged, for TKT in cards)

## Files

```text
applications/temuriset-api/
├── app/matching/service/fit.py             # NEW: FitService.list(principal, partner_party_id?, invention_id?)
├── app/matching/model/schema.py            # FitItem, FitInvention, FitOpportunity
├── app/matching/router.py                  # GET /fit
├── app/matching/service/service.py         # extract preview_source(invention_version) (shared with 057 P2)
├── app/discovery/service/service.py        # partners list: best_fit when produk given (calls FitService)
├── tests/integration/matching/test_fit.py  # by investor, by product, preview, bounds, isolation of other parties' inventions
└── tests/integration/test_isolation.py     # GET /api/v1/fit
applications/temuriset-web/src/
├── app/discover/page.tsx                   # reads ?produk=, loads my products, calls /fit for the open investor
├── views/discovery/finder/FinderView.tsx   # NEW: inventor + partners layout (replaces the partners branch of DiscoverView)
├── views/discovery/finder/ProductPicker.tsx
├── views/discovery/finder/InvestorRow.tsx  # name, best label + bar, best product / count
├── views/discovery/finder/InvestorDetail.tsx  # summary + FitTable
├── views/discovery/finder/FitTable.tsx     # rows; expand → ScoreBreakdown (057) + ImprovementList (058) + action
├── views/discovery/DiscoverView.tsx        # inventions and funding branches unchanged; partners branch delegates to FinderView
├── features/discovery/fit.ts               # api call, sorting helpers, best-of helpers (pure, tested)
├── features/i18n/app-en/finder.ts
└── tests/finder.test.tsx
e2e/finder.spec.ts                          # journey: choose investor → see both products → open → recommendation link
```

## Contracts

```python
class FitInvention(BaseModel):
    id: UUID
    title: str
    stage: Stage | None
    tkt_level: int | None


class FitOpportunity(BaseModel):
    id: UUID
    title: str
    partner_party_id: UUID
    partner: str


class FitItem(BaseModel):
    invention: FitInvention
    source: MatchSource | None  # None = preview from the published product
    opportunity: FitOpportunity
    result: MatchResultResponse  # with breakdown (057) and recommendations (058)
    preview: bool


# GET /api/v1/fit?acting_party_id=…&partner_party_id=…&invention_id=…  → list[FitItem]
```

Discovery partners list with `produk`: each item gains `best_fit: {label, fit, invention_id, opportunity_id} | null`, and the list is ordered by `best_fit.fit.lower` desc, coverage desc, then incompatible last; without `produk` the order is unchanged.

## Service details

- `FitService.list`: load the acting party's published inventions (`PortfolioService.list_mine` filtered to published, newest version), pick a source per invention (FR-002), load `IntakeService.active_targets(acting_party)` filtered to `partner_party_id` when given, then `evaluate()` + `recommend()` for each pair. Reuse `source_of()` for need/raise sources so evidence and authority are read exactly as `/matches` reads them.
- Bounds: count first; refuse above 50 × 200 with `VALIDATION_FAILED` ("Terlalu banyak kombinasi; pilih satu produk atau satu investor.").
- No persistence, no audit event (read-only), no idempotency key (GET).

## Web details

- `FinderView` keeps the toolbar from spec 048 (search, filters, chips) and adds `ProductPicker` (native `select`, "Semua produk" + my published products) bound to `?produk=`.
- `InvestorDetail` calls `/fit?partner_party_id=` on open (client fetch with timeout and a skeleton); rows sorted: ready first, then lower bound, then coverage; incompatible last.
- Row expand uses a native `details` element (keyboard and no-JS friendly), content from 057 `ScoreBreakdown` and 058 `ImprovementList`; action as spec story 1.2.
- Preview rows show a `Status` "Pratinjau tanpa kebutuhan" with a Toggletip explaining preview.

## Tasks

1. `preview_source()` extracted and unit-tested (shared with 057 P2).
2. `FitService.list` + schema + route + isolation; integration tests: by investor, by product, preview flag, stranger cannot see another party's products, bound refusal.
3. Discovery partners `best_fit` ordering with `produk`; integration test with the demo scenario (Investor B first for Produk B).
4. Web: `fit.ts` helpers with tests; `ProductPicker`, `InvestorRow`, `InvestorDetail`, `FitTable`; wire into `discover/page.tsx`; phone list/detail turn-taking reused from 048.
5. Tests: render with fixtures (strong, weak, preview, incompatible, empty mandates), axe, keyboard expand.
6. `e2e/finder.spec.ts` at 1280 and a 320 overflow check through `e2e/routes.ts` entry `/discover?type=partners&produk=…` (inventor persona).
7. Demo: update `docs/demo/scenario.md` scenario 3 to run from the finder.
8. English in `app-en/finder.ts`.

## Done when

```bash
cd applications/temuriset-api && DEMO_MODE=false make check
cd ../temuriset-web && make check && cd .. && make e2e
```

Browser: as Inovator A, `/discover` → Investor B → both products with scores → open ClearSpring → recommendations link to `#tkt` works; same in English at 320 px.

## Do not

- Do not store preview results or show them as a pitchable match.
- Do not order by anything but fit.
- Do not remove `/matches`; the finder links to it.
- Do not change the inventions/funding branches of Jelajahi (investor persona) beyond delegating the partners branch.
