# Implementation Plan: Match breakdown per aspect

**Branch**: `f/057-match-breakdown` | **Spec**: [spec.md](spec.md) | **Track**: A | **Needs**: 055 merged for TKT (engine work can start before, with `tkt=None`)

## Files

```text
applications/temuriset-api/
├── app/matching/engine/breakdown.py      # NEW, pure: dimensions, statuses, raw values
├── app/matching/engine/evaluate.py       # call breakdown(); topic and readiness features; POLICY_VERSIONS
├── app/matching/engine/fit.py            # topic_overlap(); readiness_feature()
├── app/matching/engine/inputs.py         # Source.text_terms (title/summary/problem/solution words) — built in service
├── app/matching/model/schema.py          # Dimension, MatchResultResponse.breakdown
├── app/matching/service/service.py       # fill Source.text_terms; preview source (P2)
├── app/matching/router.py                # GET /inventions/{id}/fit (P2) — or app/portfolio/router.py if cleaner
├── app/pitches/service/submission.py     # snapshot["match"]
├── app/pitches/model/schema.py           # recipient view exposes snapshot match
├── tests/unit/matching/test_breakdown.py # NEW, table-driven
├── tests/integration/matching/test_matches.py + golden/*.json (UPDATE_GOLDEN=1)
└── tests/integration/pitches/test_snapshot_match.py
applications/temuriset-web/src/
├── features/discovery/breakdown.ts       # dimension order, labels, sentence formatter (pure)
├── components/tr/ScoreBreakdown.tsx      # rows with bar, %, status, sentence, Toggletip
├── views/discovery/MatchCard.tsx         # show ScoreBreakdown under the label (open by default)
├── views/pitches/WorkspaceView.tsx       # recipient summary: "Kecocokan dengan mandat Anda"
├── features/i18n/app-en/matching.ts
└── tests/score-breakdown.test.tsx
docs/generic/temuriset/design-system/project/components/bundle.css   # .tr-meter (bar) if no suitable class exists
```

## Contracts

```python
DimensionId = Literal["sector", "topic", "readiness", "money", "form", "requirements", "evidence", "availability"]
DimensionStatus = Literal["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_APPLICABLE"]


class Dimension(BaseModel):
    id: DimensionId
    score: int | None  # 0–100, None when unknown or not applicable
    status: DimensionStatus
    weight: str | None  # decimal string of its weight in fit; None for requirements/evidence
    values: dict[str, Any]  # raw values for the sentence, per id:
    # sector:       {"source": "Energi", "target": ["Energi"]}
    # topic:        {"matched": ["surya", "desa"], "missing": ["baterai"]}
    # readiness:    {"stage": "PROTOTYPE", "accepted_stages": [...], "tkt": 4, "min_tkt": 6}
    # money:        {"source": Money json, "target": Money json, "accepts_partial": bool}
    # form:         {"source": "PROJECT", "target": ["PROJECT"]}
    # requirements: {"passed": 2, "failed": ["Berkas uji fungsi"], "unknown": [], "total": 3}
    # evidence:     {"provided": 1, "reviewed": 0, "applicable": 3}
    # availability: {"available": true, "reason": null}


class MatchResultResponse(...):
    breakdown: list[Dimension] = []
```

Recipient pitch view: `submission.snapshot.match = {"label": str, "fit": FitResponse, "breakdown": list[Dimension]}`.

P2 preview: `GET /api/v1/inventions/{invention_id}/fit?acting_party_id=` → `list[MatchResultResponse]` (one per own active mandate), source built from the published version only: `budget=None`, `relationship=None`, `documents={}`.

## Engine details

- `topic_overlap(target_keywords, source_terms) -> (Decimal, matched, missing)`: `source_terms` is the set of casefolded words from keywords (multi-word keywords kept whole too), title, summary, problem and solution, split on non-letters. A mandate keyword matches when it is in the set, or, for multi-word keywords, when the phrase appears in the joined text.
- `readiness_feature(source, target) -> Decimal | None`: as the spec table; this value becomes side A's `stage` feature (so TKT now affects fit). With no TKT anywhere it equals today's stage feature exactly, which keeps goldens without TKT stable except for topic.
- `money`: call `compare_budget` (or `compare_contribution` for a raise) even when the mandate has no budget requirement row, so the financial feature is known whenever both ranges are comparable. The requirement row, when present, still decides eligibility.
- `relevant` stays "topic overlap > 0 or retrieval evidence".
- Rounding: `int(half_up(value * 100))`.

## Tasks

1. `breakdown.py` + `test_breakdown.py`: one parametrized table per dimension, including unknown and not-applicable cases, and the status thresholds (79 → PARTIAL, 80 → MATCH, 39 → MISMATCH).
2. `topic_overlap` and `readiness_feature` in `fit.py`, wired into `evaluate()`; `POLICY_VERSIONS["fit-features"] = 2`.
3. Service: build `Source.text_terms` (add the field with default `()` in `inputs.py`).
4. Schema + response; old stored results return `breakdown: []`.
5. Goldens: `UPDATE_GOLDEN=1 uv run pytest tests/integration/matching -k golden`; review the diff; paste a summary into the PR.
6. Demo labels: rerun `tests/integration/demo/test_scenario.py`; update expected labels only if the new topic rule changes them, and say so in the PR.
7. Pitch snapshot `match` + recipient view + test (frozen across resubmission).
8. Web: `breakdown.ts` formatter (sentence per id, both languages through `t()`), `ScoreBreakdown`, `MatchCard` integration (shown open; "Mengapa cocok?" keeps reasons and requirement rows), pitch room panel. Tests: rendering all statuses, unknown shows "Belum diketahui", axe.
9. P2 preview endpoint + isolation case + Jelajahi detail panel for investors (only when the acting party has active mandates).
10. English in `app-en/matching.ts`.

## Done when

```bash
cd applications/temuriset-api && DEMO_MODE=false make check
cd ../temuriset-web && make check && cd .. && make e2e
```

Browser: demo scenario 3 shows the dimension rows in ID and EN; Investor B's pitch room shows the frozen breakdown.

## Do not

- Do not let a high dimension hide a failed required item.
- Do not show 0% for unknown.
- Do not send dimension sentences from the API; send values.
- Do not change MatchCard's primary action logic (058 extends it).
