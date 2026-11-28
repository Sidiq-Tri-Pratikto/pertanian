# Implementation Plan: TKT foundation

**Branch**: `f/055-tkt-foundation` | **Spec**: [spec.md](spec.md) | **Track**: B, day 1 | **Unblocks**: 056, 057

## Files

```text
applications/temuriset-api/
├── migrations/versions/0026_tkt_readiness.py            # new table + nullable column, nothing else
├── app/portfolio/repository/sqlalchemy/models.py        # InventionReadinessRecord
├── app/portfolio/model/schema.py                        # ReadinessInput, ReadinessResponse, DraftRequest.readiness, *Response.readiness
├── app/portfolio/service/service.py                     # save, copy on new draft, freeze on publish, public projection
├── app/intake/repository/sqlalchemy/models.py           # OpportunityVersionRecord.min_tkt
├── app/intake/model/schema.py                           # OpportunityContent.min_tkt, OpportunityVersionResponse.min_tkt
├── app/intake/service/service.py                        # persist min_tkt
├── app/matching/engine/inputs.py                        # Source.tkt, Target.min_tkt (default None)
├── app/matching/service/service.py                      # fill them in source_of / target_of
├── app/discovery/service/projection.py                  # card "tkt_level"
├── app/subscriptions/service/service.py + model/schema.py  # TeaserResponse.tkt_level
└── tests/
    ├── integration/portfolio/test_readiness.py
    ├── integration/intake/test_min_tkt.py
    └── unit/matching/test_inputs_tkt.py
applications/temuriset-web/src/
├── features/portfolio/tkt.ts                            # TKT_LEVELS, tktLabel(), TKT_GROUPS
├── components/tr/Toggletip.tsx                          # web port
├── features/i18n/app-en.ts → app-en/{core,tkt,matching,finder,mail}.ts
├── views/portfolio/EditorView.tsx, features/needs/SupportForm.tsx, views/needs/NeedsViews.tsx  # ids only
└── tests/toggletip.test.tsx, tests/tkt-levels.test.ts
docs/generic/temuriset/design-system/project/
├── components/bundle.css, bundle.js, index.d.ts         # .tr-tip, TR.Toggletip
└── tools/catalog.mjs                                    # docs and demo for Toggletip
```

## Contracts

```python
class ReadinessInput(BaseModel):  # in DraftRequest as `readiness: ReadinessInput | None = None`
    model_config = ConfigDict(extra="forbid")
    tkt_level: int = Field(ge=1, le=9)
    note: str = Field(default="", max_length=500)
    evidence: DocumentVersionChoice | None = None  # {document_id: UUID, version: int >= 1}


class ReadinessResponse(BaseModel):
    tkt_level: int
    note: str
    provenance: Literal["SELF_DECLARED"] = "SELF_DECLARED"
    has_evidence: bool
    evidence: DocumentVersionChoice | None = None  # owner view only; None for everyone else
```

- `InventionVersionResponse.readiness: ReadinessResponse | None` (owner view includes `evidence`).
- `PublicInventionResponse.readiness: ReadinessResponse | None` (never `evidence`).
- `OpportunityContent.min_tkt: int | None = Field(default=None, ge=1, le=9)`; echoed on versions.
- Discovery invention card JSON gains `"tkt_level": int | None`; `TeaserResponse.tkt_level: int | None`.
- `Source.tkt: int | None = None`; `Target.min_tkt: int | None = None` (dataclass fields with defaults, so existing tests build them unchanged).

## Data

| Table | Columns |
|---|---|
| `invention_readiness` (new) | `id`, `created_at`, `updated_at`, `version`, `version_id` FK `invention_versions.id` ON DELETE CASCADE, **unique**; `tkt_level` smallint CHECK 1–9; `note` text CHECK length ≤ 500; `evidence_version_id` FK `document_versions.id` ON DELETE SET NULL, nullable |
| `opportunity_versions.min_tkt` (new column) | smallint, nullable, **no** check constraint (validated in the API) |

Follow `0023_public_invention_page.py` on `main` for style: a new table carries its own constraints; existing tables only gain nullable columns.

## Tasks

1. **Migration 0026** and `InventionReadinessRecord` + `OpportunityVersionRecord.min_tkt`. Test: upgrade → downgrade → upgrade, `alembic check` clean. Run `deployment/temuriset/tests/migration_compat.sh` if available locally.
2. **Schemas** as in Contracts. Unit test: 0, 10, 501-character note rejected; `None` accepted.
3. **Save readiness** in `PortfolioService.save_draft`: upsert/delete the row for the draft version. Evidence goes through the same owned-file check as the public photo (`owned_public_image` is image-only; add `owned_document_version(session, party_id, document_id, number) -> UUID` beside it in `app/documents/service/service.py`, accepting any AVAILABLE file the party owns). Errors: `FILE_NOT_AVAILABLE` (not owned, not available), `VALIDATION_FAILED` (`["body","readiness","tkt_level"]`).
4. **Copy on new draft**: where a draft successor copies facts and claims from the published version, copy the readiness row too.
5. **Read paths**: owner view, public view (`has_evidence` only), discovery projection card, teaser. Test each in `test_readiness.py`, including that a stranger never receives `evidence`.
6. **Mandate `min_tkt`** through `OpportunityContent` and versions. Test in `test_min_tkt.py`.
7. **Engine inputs**: `Source.tkt` (lowest stated TKT across linked inventions), `Target.min_tkt`. Unit test with a fake projection.
8. **`tkt.ts`**: the nine levels (table below), `tktLabel(level, stageLabel?)` → `"TKT 6 · Prototipe"`. Test: nine entries, ascending, groups correct.
9. **Toggletip**: design-system CSS/JS + `components/tr/Toggletip.tsx`. Props `{ label: string; children: ReactNode; id?: string }`; a `button` with `aria-expanded`, `aria-controls`, accessible name "Penjelasan: {label}"; content in a `role="status"` region so it is announced. Test: opens on click and Enter, closes on Escape and outside click, axe clean. Run `node tools/build.mjs`, then `make design`.
10. **Dictionary split**: move current `APP_EN` to `app-en/core.ts`; create empty `tkt.ts`, `matching.ts`, `finder.ts`, `mail.ts`; `app-en.ts` exports `{ ...core, ...tkt, ...matching, ...finder, ...mail }`. The guard test `tests/app-i18n.test.tsx` keeps passing unchanged.
11. **Deep-link ids** (FR-007) on existing elements. Test: render editor steps and the need page and assert the ids exist.
12. **Isolation and contract**: no new route, so only `make openapi` + `make generate-api`. Commit both.

### TKT levels (`tkt.ts`, also used by tooltips in 056)

| Level | Indonesian name | Meaning (ID) | Example evidence |
|---|---|---|---|
| 1 | Prinsip dasar | Prinsip dasar teknologi sudah diteliti dan dilaporkan. | Kajian pustaka, laporan penelitian |
| 2 | Konsep teknologi | Konsep dan kemungkinan penerapan teknologi sudah dirumuskan. | Rancangan konsep, analisis awal |
| 3 | Bukti konsep | Fungsi utama terbukti secara analitis dan lewat percobaan awal. | Hasil percobaan, simulasi |
| 4 | Uji laboratorium | Komponen atau sistem sudah divalidasi di laboratorium. | Laporan uji laboratorium |
| 5 | Uji lingkungan relevan | Komponen atau sistem sudah divalidasi di lingkungan yang menyerupai kondisi nyata. | Laporan uji lapangan terbatas |
| 6 | Prototipe teruji | Prototipe sudah didemonstrasikan di lingkungan yang relevan. | Foto atau video prototipe, laporan demonstrasi |
| 7 | Prototipe di kondisi nyata | Prototipe sistem sudah didemonstrasikan di lingkungan sebenarnya. | Laporan uji di lokasi pengguna |
| 8 | Sistem lengkap teruji | Sistem lengkap sudah memenuhi syarat melalui pengujian di lingkungan sebenarnya. | Sertifikat uji, standar yang dipenuhi |
| 9 | Terbukti beroperasi | Teknologi sudah terbukti lewat operasi atau penjualan yang berhasil. | Bukti penjualan, laporan operasi |

Groups: 1–3 "Riset dasar", 4–6 "Riset terapan", 7–9 "Pengembangan dan komersialisasi". Short definition for the TKT tooltip: "TKT (Tingkat Kesiapterapan Teknologi) menunjukkan seberapa siap teknologi diterapkan, dari 1 (prinsip dasar) sampai 9 (terbukti beroperasi). Skala ini mengikuti Permenristekdikti No. 42 Tahun 2016. Nilainya dinyatakan inovator, bukan hasil penilaian TemuRiset."

## Done when

```bash
cd applications/temuriset-api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head && uv run alembic check
DEMO_MODE=false make check
cd ../temuriset-web && make generate-api && make check
```

All green; PR opened and merged the same day so Track A can rebase.

## Do not

- Do not add a CHECK or FK to `invention_versions`, `inventions` or `opportunity_versions`; the compatibility guard rejects new constraints on existing tables.
- Do not expose `evidence` (document id) to anyone but the managing party.
- Do not change match scores here; 057 owns scoring.
- Do not translate TKT names in the database; screens map levels to text.
