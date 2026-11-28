# Implementation Plan: Recommendations to improve a match

**Branch**: `f/058-match-recommendations` | **Spec**: [spec.md](spec.md) | **Track**: A | **Needs**: 057 merged

## Files

```text
applications/temuriset-api/
├── app/matching/engine/recommend.py        # NEW, pure: rules + what-if estimates
├── app/matching/engine/evaluate.py         # unchanged API; recommend() calls it on modified sources
├── app/matching/model/schema.py            # Recommendation, MatchResultResponse.recommendations
├── app/matching/service/service.py         # attach on applicant runs; pass invention ids for links
└── tests/unit/matching/test_recommend.py   # table-driven per rule; ordering; honesty (no estimate for sector/stage)
applications/temuriset-web/src/
├── features/discovery/recommendations.ts   # kind → sentence + href (deep-link contract) + place label
├── components/tr/ImprovementList.tsx       # list, estimate badge, "Lihat semua"
├── views/discovery/MatchCard.tsx           # section "Cara meningkatkan kecocokan"
├── views/discovery/MatchesView.tsx         # top summary (P2); previous-run delta from sessionStorage
├── views/portfolio/EditorView.tsx          # ?return= link "Kembali ke kecocokan"           ← Track B file, small, see below
├── views/needs/NeedsViews.tsx / features/needs/SupportForm.tsx   # ?return= link            ← Track B file, small
├── features/i18n/app-en/matching.ts
└── tests/recommendations.test.tsx
```

**Touching Track B files**: only the `?return=` link (a few lines each). Coordinate in chat before starting; if 056 is open on the same files, add the link after 056 merges.

## Contracts

```python
RecommendationKind = Literal[
    "requirement",
    "topic",
    "tkt_below",
    "tkt_missing",
    "stage",
    "money_missing",
    "money_gap",
    "form",
    "evidence",
    "sector",
    "availability",
    "no_need",
]


class Estimate(BaseModel):
    label: str  # engine label after the what-if, e.g. "Kecocokan potensial"
    fit: FitResponse  # lower/upper/coverage after the what-if
    gain: str  # lower-bound gain as a decimal string, for ordering


class Recommendation(BaseModel):
    kind: RecommendationKind
    blocking: bool  # True for a failed/unknown required item at entry
    dimension: DimensionId | None
    target: dict[str, Any]  # e.g. {"invention_id": ..., "need_id": ..., "field": "keywords"} — what the web links to
    values: dict[
        str, Any
    ]  # e.g. {"missing": ["pertanian", "irigasi"]}, {"tkt": 4, "min_tkt": 6}, {"label": ..., "reason": ...}
    estimate: Estimate | None


class MatchResultResponse(...):
    recommendations: list[Recommendation] = []
```

## Engine details

- What-ifs are copies of `Source` (or a stand-in requirement result for required items) passed back through `evaluate()`; no new scoring logic, so estimates can never disagree with real results.
- Ordering: blocking first; then `gain` descending; then a fixed kind order (`requirement`, `tkt_below`, `topic`, `money_*`, `form`, `evidence`, `tkt_missing`, `stage`, `sector`, `availability`).
- `stage` and `sector` never get an estimate (spec principle).
- `requirement` uses the existing row `action` (`complete-budget`, `complete-contribution`, `add-document`, `add-fact`); unknown actions map to `requirement` with no link.

## Web details

- `recommendations.ts`: `hrefOf(rec, source)` implements the deep-link table in `docs/roadmap/revamp-2-demo-feedback.md` §3, appending `?return=/matches?source=…`; `placeOf(rec)` → "Perbarui kata kunci", "Perbarui TKT", "Lengkapi kisaran", "Lampirkan berkas", "Lihat investor lain".
- Delta: before a run, MatchesView reads the previous run's breakdown for this source from `sessionStorage` (`tr_match_prev_{sourceId}`), and after the new run shows changed dimensions as "Topik 25 → 100". Wrap storage access in try/catch.

## Tasks

1. `recommend.py` + tests: one row per rule in the spec table; estimates equal a direct `evaluate()` on the modified source; ordering; sector/stage without estimate.
2. Schema and service wiring; recipient pitch view and the 057 preview return no recommendations (test).
3. Web formatter + `ImprovementList` + MatchCard section; tests for each kind's sentence and link, both languages.
4. `?return=` support in editor and need pages (validate: must start with `/` and not `//`).
5. Delta display in MatchesView + test.
6. P2 top summary.
7. Demo: add a step to `docs/demo/scenario.md` ("Perbaiki Produk A: tambahkan TKT dan kata kunci, lihat skornya naik").
8. English in `app-en/matching.ts`.

## Done when

```bash
cd applications/temuriset-api && DEMO_MODE=false make check
cd ../temuriset-web && make check && cd .. && make e2e
```

Browser: Produk A against Investor A → follow "Perbarui TKT" → set TKT 6 → publish → return → "Tahap dan TKT 25 → 50" shown.

## Do not

- Do not write recommendation sentences in the API.
- Do not show recommendations to investors.
- Do not suggest changing sector or stage as a way to score higher.
