# Tasks: CSV parser

**Input**: `specs/024-csv-parser/spec.md`, `plan.md`, generated against `origin/main` at `a952723`
**Branch**: `m5/csv-parser`
**Lane**: P2, roadmap round 2, internal MVP. 025 stacks on this work in the same branch.
**Prerequisites**: 006 is merged (PR #25), so the spec's `Depends on: 006` is met. The parser still imports nothing from M1 (D1).
**Tests**: Required and first (constitution principle 2, roadmap step 4). Each story phase writes its tests, then a checkpoint task runs them and records the failure, and only then writes the code. Tests follow rule 003, including the Condition/Expected docstring.

**Paths** start at `applications/generic/hematdaya/`. Commands run from `applications/hematdaya-api/`. `domain.js` means `docs/reference/prototype/hematdaya-domain.js` and `domain.test.js` means `docs/reference/prototype/domain.test.js`. Line numbers refer to those files at `a952723`.

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | The seven parser modules (`app/imports/model/models.py`, `app/imports/service/{dialect,columns,numbers,times,cadence,parser}.py`) import nothing from `app.measurements`, `app.sites`, `app.energy`, `app.assets`, `app.identity`, `app.audit`, `app.core.database` or `app.core.settings`. This feature adds no route, migration, table or error code. T004 enforces the imports and T042 the rest. | The plan makes this a pure parser. M1 being merged changes nothing here: 025 is the layer that meets M1. |
| D2 | Tests may import M1, production parser modules may not. AT-27a's 50 Wh and AT-27b's 30 Wh delta are asserted by feeding parser rows into `normalize` and `counter_deltas` from `app/measurements/service/normalize.py`. The parser itself never converts. Every requirement can be met here. | 006's plan keeps conversion in one place "so no adapter can bypass it". A second conversion would also disagree on ties: 006 rounds half to even, the prototype's `Math.round` half up. |
| D3 | Vocabulary follows the merged 006, not the PRD or the prototype. `ValueKind` values are `interval_energy`, `average_power` and `counter`, which match `MeasurementKind` in `app/assets/model/models.py`. `unit` is exactly `Wh` or `W`, the case-sensitive keys of `MWH_PER_UNIT` and `MILLIWATT_PER_UNIT`. `value_milli` is the exact integer. `RowResult.value` is the same number as a `Decimal` with three places. | The PRD says `cumulative_energy` and `instant_power`, and the prototype says `wh`, `w`, `cum`. `same_observation` compares `format(value, "f")`, so `10`, `10.0` and `10,000` must reach 006 as one canonical `10.000` or a reimport becomes a revision. |
| D4 | Failures are data. The parser returns `StructuralError`, `MeaningQuestion` and `RowError`, raises no `AppError` and registers no code. They carry a snake_case `reason`, as 006's `Rejection.reason` does, and reuse 006's words where the meaning matches (`negative`, `interval_reversed`). `APP-IMPORT-*` belongs to 025. `csv.Error` and `UnicodeDecodeError` are translated in `dialect.py` only, and their text never reaches a message. A bug raises through to the registered `APP-UNKNOWN` fallback. The parser logs nothing. Rule 003's envelope, `request_id`, record and recovery assertions are tested in 025, where a boundary exists. Here tests assert reason, exact message, positions and that nothing is logged. | Rule 008 normalizes failures at the boundary that exposes them, and a pure parser exposes nothing. A row error is an expected result, so it gets no `reference_id`. |
| D5 | From `domain.js` this feature ports `tokenize`, `detectDelimiter`, `parseDecimal`, `parseTime`, `parseCsv`, `inferCadence`, the meaning part of `mappingIssues` (L713–L720) and the row checks of `buildPreview` (L742–L767, including `bad`). Asset and scope issues (L722–L733), conflicts, duplicates, thresholds, counts, assumption text and counter deltas stay with 025 and 006. | The spec's exact message comes from `bad` and L767 in `buildPreview`, which the plan's Prototype Reference did not list. |
| D6 | Streaming is two passes over a seekable binary source. `parse(source, ...)` reads every row and keeps only what the file-level answers need (per-stream timestamps, names, counts). `iter_rows(source, parsed)` is a generator that re-reads the file and yields one `RowResult` at a time. Nothing holds the whole text or a list of rows. | `csv.reader` takes a line iterator, so tokenizing streams. A row's end still depends on a cadence that needs every timestamp, so one pass cannot finish a row. The spike's peak was 5.9 MiB against 248.8 MiB for a list of rows (Notes). |
| D7 | Decode with `io.TextIOWrapper(source, encoding="utf-8-sig", newline="")`, seek to 0 before each pass, and `detach()` in a `finally`. Never call `str.splitlines`. Any `UnicodeDecodeError` or a NUL character becomes `not_utf8`. | The BOM must go before `csv.reader`, or a quoted first header keeps literal quotes (Notes). `newline=""` splits on `\n`, `\r` and `\r\n` only, while `splitlines` also splits on `\x0b`, `\x85` and ` `. Without `detach`, garbage collection closes the caller's file. Postgres text and JSONB reject NUL, so it must stop here. |
| D8 | `csv.reader(lines, delimiter=delimiter, strict=True)`. `dialect.py` never calls `csv.field_size_limit`. `unexpected end of data` and `field larger than field limit` become `quote_unclosed`, and any other `csv.Error` becomes `quote_malformed`. A quote error replaces all other structural errors, as L656 does. | The default mode silently swallows an unterminated quote and every row after it into one field (Notes). The field limit is process-global, so changing it would break purity. A 128 KiB field is never real data here, since names stop at 60. `"A"b` is now an error where the prototype read `Ab`: the plan asks for standard quoting. |
| D9 | `file_line` is the previous `reader.line_num + 1`. Peek leading lines for the delimiter, then chain them back so the count stays right. A bare `\r` inside quotes counts as a line break. | `line_num` is the last physical line of a record, while L589 reports the first. L594 counts only `\n` inside quotes although L597 treats a bare `\r` as a line end outside them. |
| D10 | `parse_decimal(raw, delimiter)` has no `quoted` argument. In a comma file, a cell containing a comma must have been quoted, because an unquoted comma splits the row. The first message at L623 is unreachable, in the prototype too, and is not ported. Unquoted `12,5` gets the `column_count` message with its hint. | `csv.reader` exposes no quoted flag. `QUOTE_NOTNULL` only marks empty cells and `QUOTE_STRINGS` converts to float (Notes). |
| D11 | Numbers parse by shape first, with `[0-9]` patterns and `fullmatch`, then integer arithmetic on the digits. Reject before `int()` when the integer part has more than 16 digits after leading zeros. `value_too_large` applies above `2**63 - 1` milli-units, the `measurements.energy_mwh` BIGINT limit. No float and no `Decimal` arithmetic. | `Decimal()` accepts `NaN`, `Infinity`, `1e5`, `1_000`, `+5` and `١٢`. `\d` matches Unicode digits. `Decimal * 1000` rounds to 28 digits, `int()` raises above 4,300 digits, and JavaScript loses exactness above 2^53. L629 only fires near 300 digits, so it is replaced. |
| D12 | Three inputs diverge from the prototype and are rejected as ambiguous: `0.250` and `1.250` in a semicolon file, and `"1,250"` in a comma file. Still accepted: `1.250,5`, `1.250.000` and `1,250` in a semicolon file, and `"12,5"`, `"12,50"` and `"0,250"` in a comma file. | The prototype reads them as 250 Wh, 1,250 Wh and 1.25 Wh, each up to 1,000 times off (Notes). The spec says ambiguous numbers are rejected with an example, and every meaning keeps an unambiguous spelling. No prototype test pins the old reading, so SC-001 holds. |
| D13 | Times parse with the regex from L633 (with `re.ASCII` and `fullmatch`) and an explicit `datetime(...)` from its groups. Never use `datetime.fromisoformat`. Keep fractions to microseconds, truncating further digits. `+24:00`, `+07:60` and any `OverflowError` from `astimezone` or adding a duration give `time_impossible`. Date-only values give `time_format`, as the prototype does. | `fromisoformat("2026-10-20 08.30")` returns 08:00:00.3, 30 minutes off with no error (Notes), and the prototype accepts that shape on purpose. L641 accepts `+99:99`, a shift of four days. L633 drops fractions, which would reverse a sub-second interval. |
| D14 | `parse_time` returns naive or UTC, and everything downstream works in UTC. A naive value gets `ZoneInfo(site_timezone)` only when `answers.timezone_confirmed` is true. Compare fold 0 and fold 1 offsets, then round-trip through UTC, to tell `time_nonexistent` from `time_ambiguous`. There is no offset table and no default zone. | `ZoneInfo` never raises on a gap. Arithmetic between datetimes sharing a `ZoneInfo` is wall-clock, so an hour across a DST change comes out wrong (Notes). L686 hard-codes `Asia/Jakarta` and L25 falls back to +7 for any other zone. Indonesian zones have no DST, so tests must use `America/New_York`. |
| D15 | `has_naive_timestamps` looks at every time cell, including `interval_end`. | L684–L685 check only `timestamp` or `interval_start`, so a naive end beside an offset start resolves silently with no question (Notes). |
| D16 | Aliases are the PRD §10.2 list plus `interval_start`, `interval_end`, `cumulative_wh` and the prototype's `source`, `sumber`, `source_id`. Match on `.strip().lower()`. There is no kWh alias: `energy_kwh` is an ignored column. The stream key is `(source cell or asset name).strip().lower()`. | The spec's "mapped source" needs a source column the PRD alias sentence omits. Accepting kWh under a Wh meaning would be the silent unit guess the spec forbids. |
| D17 | Two headers with one role (`energy_wh` and `wh`) are `duplicate_role`, a structural error (L668). Two value roles (`energy_wh` and `average_power_w`) are a `value_kind` question (L713). Only the chosen column is read, so bad text in the other column is not an error. | AT-29 and US2-2 need both behaviours. |
| D18 | A `timestamp` column beside `interval_start` or `interval_end` is `competing_time_columns`, a structural error. | L754 lets `timestamp` win and drops the explicit bounds without a word (Notes). |
| D19 | Every average-power alias needs a confirmed meaning, not only `power_w`. Until `power_meaning` is `average`, power rows stay `pending`. `instantaneous` keeps a blocking question and rows stay `pending`. The parser never emits `instantaneous_power`. | AT-27a applies the rule to `average_power_w`, and SC-001 keeps it. 006 can store instantaneous points, but PRD §10.2 and US2-1 block them for CSV. |
| D20 | A declared duration is per stream: `answers.interval_minutes[stream_key]`, an integer from 1 to 1440. It applies to that stream only. | L770 applies one value to every stream, so declaring 60 minutes for one source rewrites a 15-minute source too (Notes). That breaks US2-5. |
| D21 | Cadence works on integer microseconds and compares in doubled units, with no `statistics.median`. A gap agrees when `abs(gap - median) <= 1 s`, and inference succeeds when `agreeing * 10 >= gaps * 9`. Any row with a nonblank name and a valid timestamp contributes, whatever its value or column count (L686). Counter streams are skipped. While the timezone is unanswered, naive values are treated as UTC wall clock, and `cadences` is final only after confirmation. | `statistics.median` returns a float on an even count. L686's rule keeps a negative value from opening a false gap. Instants, not wall clocks, give the right hour across DST. |
| D22 | Name length is `len()` after `.strip()`, in code points, at most 60. A `source` cell has the same limit, with its own reason. Names stay verbatim apart from that strip, so `=SUM(A1)` stays plain text. | `assets.name` is `CHECK (char_length(name) BETWEEN 1 AND 60)`, which counts characters where JavaScript `.length` counts UTF-16 units. `sources.label` allows 120, and 025 prefixes the source name with `Impor CSV · `. L686 has no limit. |
| D23 | Size is checked first with `source.seek(0, io.SEEK_END)`, without decoding. The message rounds up to one decimal in integer arithmetic. Row counting continues past 150,000 without building rows, so the message keeps the true count. | L650's rounding prints `Ukuran 10 MiB melebihi batas 10 MiB.` at 10,485,761 bytes (Notes). Python's `round` and `f"{x:.1f}"` would differ from JavaScript anyway. The file is at most 10 MiB, so counting is bounded. |
| D24 | The contract types are frozen Pydantic models in `model/models.py`, named as the spec names them, without a `Model` suffix. | Rule 005 asks for Pydantic and the spike found no cost: 1.45 s against 1.50 s for a dataclass at 150,000 rows. Merged code keeps the suffix for stored entities and drops it for value types (`IngestResult`, `MeasurementRow`). |
| D25 | Spec Kit scripts refuse this branch name. Run them with `SPECIFY_FEATURE=024-csv-parser`. | `common.sh` honours that variable. The roadmap's `NNN-name` branch rule is a known deviation here, as on `m0/android-smoke-ci`. |

## Parser contract

The full contract is in [plan.md](plan.md), under Parser contract. Names used below come from it.

## Messages

Text is exact. `{…}` is filled at runtime. `new` means no prototype text exists, and SC-001 does not apply to that row.

### Structural (`StructuralReason`)

| Reason | Message | Source |
|---|---|---|
| `empty_input` | `Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV.` | L648 |
| `too_large` | `Ukuran {size} MiB melebihi batas 10 MiB.` | L650, D23 |
| `not_utf8` | `Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.` | new |
| `delimiter_ambiguous` | `Pemisah kolom ambigu: header memakai koma dan titik koma. Gunakan salah satu, misalnya "timestamp;perangkat;energi_wh".` | L609 |
| `single_column` | `Header hanya memiliki satu kolom. Pisahkan kolom dengan koma atau titik koma.` | L610 |
| `quote_unclosed` | `Tanda kutip tidak ditutup mulai baris file {line}.` | L601 |
| `quote_malformed` | `Tanda kutip tidak valid pada baris file {line}. Tutup tanda kutip tepat sebelum pemisah kolom.` | new |
| `duplicate_role` | `Kolom "{first}" dan "{second}" memiliki arti yang sama. Hapus salah satunya.` | L668 |
| `competing_time_columns` | `Kolom "{timestamp}" dan "{interval}" sama-sama menyatakan waktu. Gunakan timestamp saja atau pasangan interval_start dan interval_end.` | new |
| `missing_asset` | `Kolom perangkat tidak ditemukan. Gunakan header asset, perangkat, mesin, device, nama atau alat.` | L672 |
| `missing_time` | `Kolom waktu tidak ditemukan. Gunakan timestamp (atau waktu/tanggal) atau pasangan interval_start dan interval_end.` | L673 |
| `missing_value` | `Kolom nilai tidak ditemukan. Gunakan energy_wh/energi_wh, average_power_w/daya_w, atau cumulative_wh.` | L674 |
| `counter_needs_timestamp` | `Kolom cumulative_wh memerlukan kolom timestamp titik waktu.` | L675 |
| `too_many_rows` | `{count} baris data melebihi batas 150.000 baris.` | L676 |
| `no_data_rows` | `Tidak ada baris data setelah header.` | L677 |

Not ported: L660 `Header tidak ditemukan.` is unreachable, since a nonblank first line always yields a header.

### Questions (`QuestionKind`)

| Kind | When | Message | Source |
|---|---|---|---|
| `value_kind` | More than one value role and no valid answer | `Berkas memiliki lebih dari satu kolom nilai. Pilih satu jenis nilai; nilai energi dan daya tidak dijumlahkan.` | L713 |
| `power_meaning` | Power column, unanswered | `Konfirmasi arti kolom daya: rata-rata selama interval atau daya sesaat.` | L714 |
| `power_meaning` | Answered `instantaneous` | `Daya sesaat tidak dapat diubah menjadi energi. Impor diblokir; gunakan data energi interval atau daya rata-rata interval.` | L714 |
| `timezone` | Naive timestamp, unconfirmed | `Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai {site_timezone}.` | L715 |
| `interval_duration` | Declared value out of range | `Panjang interval harus bilangan bulat 1–1440 menit.` | L717 |
| `interval_duration` | A timestamp-only stream has no cadence and no declared value | `Interval tidak dapat disimpulkan untuk: {stream keys joined by ", "} (satu baris atau jarak tidak teratur). Isi panjang interval.` | L720 |

### Rows (`RowReason`)

The full message is `Baris data {data_row}{ (baris file {file_line}) when file_line != data_row + header_line}, {field}: {text}` (L742). `field` is the header as written after strip, or `baris` for `column_count`.

| Reason | Text | Source |
|---|---|---|
| `column_count` | `jumlah kolom {got} tidak sama dengan header ({expected}).`, and in a comma file only, followed by ` Koma desimal harus diberi tanda kutip, misalnya "12,5".` | L748 |
| `asset_empty` | `nama perangkat kosong.` | L750 |
| `asset_too_long` | `nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.` | L751 |
| `source_too_long` | `nama sumber lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.` | new |
| `time_format` | `format waktu tidak dikenali. Gunakan 2026-10-20 00:00 atau 2026-10-20T00:00:00+07:00.` | L634 |
| `time_impossible` | `tanggal atau jam tidak ada ({raw}).` | L637 |
| `time_nonexistent` | `waktu lokal {raw} tidak ada di zona {zone}. Tambahkan offset atau perbaiki waktunya.` | new |
| `time_ambiguous` | `waktu lokal {raw} terjadi dua kali di zona {zone}. Tambahkan offset untuk memilih salah satunya.` | new |
| `interval_reversed` | `akhir interval harus setelah awal interval.` | L761 |
| `value_empty` | `nilai kosong. Isi angka 0 atau lebih; kosong tidak dianggap 0.` | L765 |
| `value_ambiguous` | `angka "{raw}" ambigu pada berkas titik koma. Gunakan koma desimal, misalnya 12,5.` | L619 |
| `value_ambiguous_comma` | `angka "{raw}" ambigu pada berkas koma. Gunakan titik desimal, misalnya 1.25, atau tulis tanpa pemisah ribuan, misalnya 1250.` | new, D12 |
| `value_not_number` | `"{raw}" bukan angka.` | L620, L623 |
| `value_too_precise` | `gunakan paling banyak 3 angka desimal.` | L627 |
| `value_too_large` | `angka "{raw}" terlalu besar. Periksa nilai dan satuannya.` | new, replaces L629 |
| `negative` | `gunakan angka 0 atau lebih.` | L767 |

## Prototype assertions: what moves where

This table is what SC-001 means. `AT-26` has no test in `domain.test.js`, and `AT-30` and `AT-33/34` are preview and commit tests.

| Assertion | `domain.test.js` | Here | Elsewhere |
|---|---|---|---|
| AT-26 aliases and meaning | none | New test from the two CSV blocks in PRD §10.2 | |
| AT-27a blocked, `sesaat tidak dapat` | L127–L130 | `power_meaning` question on `average_power_w`, rows `pending`, full message | `blocked` flag in 025 |
| AT-27a 50 Wh | L131–L132 | No questions after `average`. The row (100,000 mW, 30 minutes) through 006 `normalize` gives `energy_mwh == 50000` | |
| AT-27b 30 Wh, reset | L136–L141 | Three point rows, no duration question. Through 006 `counter_deltas` they give one delta of `30000` | `tidak diketahui` assumption text in 025 |
| AT-28 all | L230–L235 | Everything, including `delimiter`, `asset_names`, `blank_lines`, and values 12,500 and 1,250,500 | |
| AT-29 all | L239–L243 | Everything, with exact messages | |
| AT-30 first error | L224 | `Baris data 1, energi_wh: gunakan angka 0 atau lebih.` | Counts and thresholds in 025 |
| AT-31 all | L247–L254 | Everything, with `interval_minutes={"a": 60}` for L250 | |
| AT-32 all | L258–L263 | Everything, with the exact `tidak dipotong` and `150.000` messages | Invalid counts in 025 |
| AT-33/34 | L266–L280 | Nothing | 025, 026 |

---

## Phase 1: Setup

**Purpose**: Record the baseline and create the empty module.

- [X] T001 From `applications/hematdaya-api/`, run `make install`, `make test-unit` and `uv run python --version`, and record the pass count and Python version (must be 3.13) in this file's Notes section
- [X] T002 Create empty `applications/hematdaya-api/app/imports/__init__.py`, `app/imports/model/__init__.py` and `app/imports/service/__init__.py`, matching `app/capabilities/`. Create no `router.py` and no `repository/`

## Phase 2: Foundational

**Purpose**: The boundary test, test helpers and contract types every story uses.

- [X] T003 [P] Write `applications/hematdaya-api/tests/unit/imports/conftest.py` with fixture `parse_text`, signature `(text: str | bytes, *, answers: MeaningAnswers | None = None, site_timezone: str = "Asia/Jakarta") -> tuple[ParsedFile, list[RowResult]]`. It builds a `BytesIO`, encoding `str` as UTF-8, calls `parse`, then `list(iter_rows(...))`. Import `app.imports` inside the fixture so other test modules still collect
- [X] T004 [P] Write `applications/hematdaya-api/tests/unit/imports/test_module_boundary.py` for D1. `PURE_MODULES` lists the seven modules. Helper `_forbidden(source: str) -> list[str]` uses `ast` to flag imports rooted at `app.measurements`, `app.sites`, `app.energy`, `app.assets`, `app.identity`, `app.audit`, `app.core.database`, `app.core.settings`, `sqlalchemy`, `fastapi`, `logging`, `os`, `time` or `asyncio`, and calls to `.now`, `.utcnow` and `field_size_limit`. Tests: every pure module exists; none has a forbidden item; parametrized samples prove the helper flags `from app.sites.service.service import SiteService`, `import logging`, `datetime.now()` and `csv.field_size_limit(1)`. Scope it to these seven files so 025 can add `router.py` and `repository/`
- [X] T005 [P] Write `applications/hematdaya-api/tests/unit/imports/test_models.py`. `RowResult.value` for `value_milli` 10000 is `Decimal("10.000")` with `format(value, "f") == "10.000"`, 12500 gives `12.500`, None gives None. Models are frozen. Vocabulary against merged 006 (D3): every `ValueKind` value is in `app.assets.model.models.MeasurementKind`, `Wh` is in `MWH_PER_UNIT`, and `W` is in `MILLIWATT_PER_UNIT`
- [X] T006 Run `uv run pytest tests/unit/imports -q`, confirm T004 and T005 fail, and record the failure in Notes for `applications/hematdaya-api/tests/unit/imports/`
- [X] T007 Write every type from plan.md's Parser contract and the three reason and question enums from Messages in `applications/hematdaya-api/app/imports/model/models.py`, using `ConfigDict(frozen=True)`, with Google-style docstrings per rule 002. Create `app/imports/service/{dialect,columns,numbers,times,cadence,parser}.py` holding only a module docstring. T004 and T005 now pass

## Phase 3: User Story 1 - Read real files (Priority: P1) MVP

**Goal**: Every accepted format reads with aliases resolved and values and names unchanged, one row at a time.

**Independent Test**: `uv run pytest tests/unit/imports/test_parser.py -k read tests/unit/imports/test_numbers.py tests/unit/imports/test_dialect.py tests/unit/imports/test_columns.py`.

### Tests first

- [X] T008 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_numbers.py` for `parse_decimal(raw, delimiter) -> int | CellFailure | None`, the port of `parseDecimal` (L613), parametrized. Comma file: `10`→10000, `12.5`→12500, `0`→0, `0.001`→1, `00012`→12000, `-1`→-1000, `-0`→0, `12,5`→12500, `12,50`→12500, `0,250`→250. Semicolon file: `12,5`→12500, `1.250,5`→1250500, `1.250.000`→1250000000, `1,250`→1250, `12,500`→12500, `-1.250,5`→-1250500, `10`→10000. Blank and whitespace give None. `value_ambiguous` in a semicolon file: `12.5`, `1.25`, `0.250`, `1.250`. `value_ambiguous_comma` in a comma file: `1,250`, `12,500`, `-1,250`. `value_not_number`: `1,250.5`, `1.250,5` (comma file), `12.345.6` (semicolon file), `+5`, `.5`, `5.`, `1e5`, `NaN`, `Infinity`, `sNaN`, `1_000`, `١٢`, `0x10`, `dua`. `value_too_precise`: `1.2345`, `1.0000`, `1,2345`. Bound: `9223372036854775.807` gives 9223372036854775807, and `9223372036854775.808`, `"9" * 400` and `"1" * 5000` give `value_too_large` without an exception
- [X] T009 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_dialect.py`, porting `detectDelimiter` (L605) and `tokenize` (L586) onto `detect_delimiter(source) -> str | StructuralError` and `read_records(source, delimiter) -> Iterator[Record | StructuralError]`. Delimiter: quoted delimiters are ignored (`"a,b";c` gives `;`), leading blank lines are skipped, a CR-only file works, both delimiters give `delimiter_ambiguous`, none gives `single_column`, and empty bytes, whitespace only and BOM only give `empty_input`. Records: BOM with a quoted first header gives header `waktu`; `a,b\r\nc,d\re,f\n` gives file lines 1, 2, 3; a blank line yields a blank record and keeps numbering; `   ` and `""` are blank; `,,` is not; no trailing record after a final newline; `\x0b`, `\x85` and ` ` inside a name do not split it; `"Mesin ""A"""` reads `Mesin "A"`. Failures: `a,b\n"x,1\n2,3\n` gives `quote_unclosed` at line 2, a 200,000-character unterminated field gives the same, `"x"y,1` gives `quote_malformed` at line 2, `caf\xe9` deep in a file and a UTF-16 BOM give `not_utf8`, and a NUL gives `not_utf8`. Purity: the source stays open after a full pass and after closing the generator early, a second pass gives equal records, and `csv.field_size_limit()` is unchanged
- [X] T010 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_columns.py` for `resolve_columns(headers: list[str]) -> ColumnMap`, the port of L663–L675 plus D18. Parametrize every alias from D16 to its role, also upper-cased and with surrounding spaces. `energi` is energy, never counter. `energy_kwh`, `kwh` and `daya_kw` land in `ignored_columns`, and alone give `missing_value`. `energy_wh,wh` gives `duplicate_role` with `Kolom "energy_wh" dan "wh" memiliki arti yang sama. Hapus salah satunya.` `foo,bar` gives `missing_asset`, `missing_time` and `missing_value`, in that order, with exact text. `interval_start,interval_end,asset,cumulative_wh` gives `counter_needs_timestamp`. `timestamp,interval_start,interval_end,asset,wh` gives `competing_time_columns`. `value_kinds` lists roles present, in the order energy, power, counter
- [X] T011 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_times.py` for `parse_time(raw) -> datetime | CellFailure`, the port of `parseTime` (L632), parametrized. Naive results: `2026-10-20 00:00`, `2026-10-20 08.30` (08:30, not 08:00:00.3), `2026-10-20 08.30.15`, `2026-10-20 08:30.15` (seconds 15), `2026-10-20T08:30:15`. UTC results: `2026-10-20T00:00:00+07:00` and `2026-10-20 00:00 +0700` give 2026-10-19T17:00:00Z, and `2026-10-20T00:00:00Z`. Fractions: `...00.5Z` gives 500000 µs, `...00.123456789Z` gives 123456 µs. `time_impossible` with exact text: `2026-02-30 00:00` gives `tanggal atau jam tidak ada (2026-02-30 00:00).`, also `2026-10-20 24:00`, `2026-10-20 00:60`, `2026-10-20 00:00:60`, `2026-10-20 00:00+24:00`, `2026-10-20 00:00+07:60`, `2026-10-20 00:00+99:99`, `0000-10-20 00:00`, `0001-01-01 00:00+07:00`, `9999-12-31 23:59-07:00`. `time_format`: `2026-02-30`, `2026-10-20`, `20261020`, `2026-W43-2`, `2026-10-20T08`, `٢٠٢٦-10-20 00:00`, `2026-10-20t00:00`, blank, `kemarin`
- [X] T012 [US1] Write `applications/hematdaya-api/tests/unit/imports/test_parser.py`, read tests, using `parse_text`. Scenario 1: `timestamp,perangkat,energi_wh` from PRD §10.2 gives `kind == interval_energy`, `unit == "Wh"`, `value_milli == 10000`, asset `Router`, status `pending` with no answers. Scenario 2: the explicit block from PRD §10.2 gives status `parsed`, start 2026-10-19T17:00:00Z, end 18:00:00Z, basis `explicit`, no `interval_duration` question, assets `Router` and `Kulkas`. Scenario 3: AT-28's file keeps `raw_value` `12,5` and `1.250,5`, value 12500 and 1250500, name `Lampu; Gudang`, `had_bom` true, `blank_lines` 1. Scenario 4: `cumulative_wh` with offset timestamps gives `kind == counter`, `measured_at` set, interval fields None. Also: an extra `catatan` column lands in `ignored_columns`; the canonical `value` of `10`, `10.0` and (semicolon) `10,000` formats to `10.000`; parsing twice gives equal output; `iter_rows` twice gives equal rows; the source stays open
- [X] T013 [US1] Write `applications/hematdaya-api/tests/unit/imports/test_prototype_oracles.py` with AT-26 (new, from PRD §10.2) and AT-28 (`domain.test.js` L230–L235), per the assertion table
- [X] T014 [US1] Write `applications/hematdaya-api/tests/unit/imports/test_performance.py` with a module-scoped 150,000-row fixture of explicit offsets (`2026-01-01T00:00:00+07:00,2026-01-01T01:00:00+07:00,Mesin 12,123.456`). Assert it is at most 10,485,760 bytes. Tests: `parse` plus full `iter_rows` under 60 seconds with no invalid row, printing elapsed seconds, bytes and shape; after `next(iter_rows(...))`, `source.tell()` is under 1 MiB; with `tracemalloc`, peak under 64 MiB for `parse` and under 16 MiB for `iter_rows` while discarding rows
- [X] T015 [US1] Run the new test files, confirm each fails on missing behavior, and record it in Notes for `applications/hematdaya-api/tests/unit/imports/`

### Code

- [X] T016 [P] [US1] Implement `parse_decimal` in `applications/hematdaya-api/app/imports/service/numbers.py` per D10, D11 and D12. Semicolon order: grouped pattern `-?[1-9][0-9]{0,2}(\.[0-9]{3})+(,[0-9]+)?` accepted only with a decimal comma or two or more groups; then `-?[0-9]+(,[0-9]+)?`; then `-?[0-9]+\.[0-9]+` gives `value_ambiguous`; else `value_not_number`. Comma order: `-?[1-9][0-9]{0,2},[0-9]{3}` gives `value_ambiguous_comma`; `-?[0-9]+,[0-9]+` is a decimal comma; `-?[0-9]+(\.[0-9]+)?` is plain; else `value_not_number`. Then more than 3 decimals gives `value_too_precise`, then the digit guard and bound give `value_too_large`. Return failures as `CellFailure`. T008 passes
- [X] T017 [P] [US1] Implement `source_size`, `detect_delimiter` and `read_records` in `applications/hematdaya-api/app/imports/service/dialect.py` per D7, D8 and D9. One function translates `csv.Error`. A peeked prefix is chained back before `csv.reader`, and `Record.file_line` is the previous `line_num + 1`. T009 passes
- [X] T018 [P] [US1] Implement `ALIASES`, `Role`, `ColumnMap` and `resolve_columns` in `applications/hematdaya-api/app/imports/service/columns.py` per D16, D17 and D18. T010 passes
- [X] T019 [P] [US1] Implement `parse_time` in `applications/hematdaya-api/app/imports/service/times.py` per D13, using `re.ASCII`, `fullmatch` and an explicit `datetime(...)`, never `fromisoformat`. Offset values normalize to `UTC` immediately. T011 passes
- [X] T020 [US1] Implement `parse` and `iter_rows` in `applications/hematdaya-api/app/imports/service/parser.py`: size check, delimiter, header, first pass (`total_rows`, `blank_lines`, `asset_names` in first-seen order), row pass yielding `RowResult` with raw cells, kind, unit, stream key and `value_milli`. Explicit offset intervals become `parsed`. A naive time or a timestamp-only row without a duration stays `pending`. A cell failure sets `status == invalid`, with the message filled in T037. Keep `iter_rows` free of accumulated lists. T012, T013 and the streaming test pass
- [X] T021 [US1] Run `uv run pytest tests/unit/imports -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`. Tests for US2 and US3 do not exist yet

## Phase 4: User Story 2 - Preserve meaning (Priority: P1) MVP

**Goal**: Power, timezone, duration and counter meaning are never guessed. Each stream keeps its own cadence.

**Independent Test**: `uv run pytest tests/unit/imports/test_parser.py -k meaning tests/unit/imports/test_cadence.py`.

### Tests first

- [X] T022 [P] [US2] Add to `applications/hematdaya-api/tests/unit/imports/test_times.py` for `resolve_local(naive, zone, raw) -> datetime | CellFailure`. `Asia/Jakarta` `2026-10-20 00:00` gives 2026-10-19T17:00:00Z, `Asia/Makassar` gives 16:00Z. `America/New_York` `2026-03-08 02:30` gives `time_nonexistent` with `waktu lokal 2026-03-08 02:30 tidak ada di zona America/New_York. Tambahkan offset atau perbaiki waktunya.`; `2026-11-01 01:30` gives `time_ambiguous` with `waktu lokal 2026-11-01 01:30 terjadi dua kali di zona America/New_York. Tambahkan offset untuk memilih salah satunya.`; `01:30-04:00` and `01:30-05:00` on that date parse to 05:30Z and 06:30Z. Results are in UTC, and an hour added from `2026-03-08 01:00` is 07:00Z
- [X] T023 [P] [US2] Write `applications/hematdaya-api/tests/unit/imports/test_cadence.py` for `infer_cadence(timestamps: Iterable[int]) -> timedelta | None`, the port of `inferCadence` (L694), in microseconds. No timestamps, one, or only repeats give None. Repeats leave the denominator: `00:00, 00:00, 01:00, 02:00` gives 1 hour. 9 of 10 agreeing gives the median, exactly at 90%; 8 of 9 gives None. A gap exactly 1 s from the median agrees, 1.000001 s does not. Even count `[3600 s, 3601 s]` gives `timedelta(seconds=3600, microseconds=500000)`. Input order does not matter
- [X] T024 [US2] Add meaning tests to `applications/hematdaya-api/tests/unit/imports/test_parser.py`. Scenario 1: `power_w` gives a `power_meaning` question and `pending` rows with value kept; `instantaneous` gives the exact blocked message and `pending` rows; `average` gives no question and `parsed` rows with `unit == "W"`. Scenario 2: `energy_wh,average_power_w` gives a `value_kind` question and `pending` rows; each answer reads only its column, and bad text in the other column is not an error; `energy_wh,cumulative_wh` behaves the same. Scenario 3: naive rows give `Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai Asia/Jakarta.` and `pending` rows with no instant; after `timezone_confirmed=True` they are UTC; `site_timezone="Asia/Makassar"` changes both the message and the instant; offset rows ask nothing; an offset start beside a naive end asks (D15). Scenario 4: one row and an irregular stream each give the `interval_duration` question naming the stream; `interval_minutes={"a": 60}` gives `[t, t+60m)` with basis `declared`; 0 and 1441 give `Panjang interval harus bilangan bulat 1–1440 menit.`; explicit bounds never ask. Scenario 5: sources `S1` every 15 minutes and `S2` hourly with one long gap keep `cadences` 15 minutes and 1 hour; every row including the last spans its stream's cadence; the row before the gap ends one hour later, not at the next row; declaring `{"c": 60}` for a third one-row stream leaves `s1` at 15 minutes (D20). Scenario 6: counters give `cadences == {}`, no `interval_duration` question, `measured_at` set, values 100000, 130000, 5000. Across DST: hourly naive rows in `America/New_York` through 2026-03-08 give a cadence of 1 hour once confirmed. Bad value rows still count toward cadence (D21)
- [X] T025 [US2] Add AT-27a, AT-27b and AT-31 to `applications/hematdaya-api/tests/unit/imports/test_prototype_oracles.py`, per the assertion table. AT-27a builds `ReadingInput(value=row.value, unit=row.unit, interval_start=..., interval_end=...)` and asserts `normalize(reading, MeasurementKind.AVERAGE_POWER).energy_mwh == 50000`. AT-27b maps rows to `CounterPoint(measured_at, value_milli)` and asserts `counter_deltas` gives one delta of `30000`. Also add a second shape to `tests/unit/imports/test_performance.py`: confirmed timestamp-only over 40 streams, which needs this story's code, under the same 60-second assertion
- [X] T026 [US2] Run the new tests, confirm they fail on missing behavior, and record it in Notes for `applications/hematdaya-api/tests/unit/imports/`

### Code

- [X] T027 [P] [US2] Add `resolve_local` to `applications/hematdaya-api/app/imports/service/times.py` per D14, normalizing to UTC and catching `OverflowError`. T022 passes
- [X] T028 [P] [US2] Implement `infer_cadence` in `applications/hematdaya-api/app/imports/service/cadence.py` per D21, with `abs(2 * gap - doubled_median) <= 2_000_000` and `agreeing * 10 >= len(gaps) * 9`. T023 passes
- [X] T029 [US2] In `applications/hematdaya-api/app/imports/service/parser.py`, the first pass collects `has_naive_timestamps` from every time cell and per-stream timestamps per D21, and sets `cadences`. Build `questions` with the exact messages in Messages, in the order `value_kind`, `power_meaning`, `timezone`, `interval_duration`, porting L713–L720 per D19 and D20. An answer naming a value kind absent from the file leaves the question open
- [X] T030 [US2] In `applications/hematdaya-api/app/imports/service/parser.py`, `iter_rows` applies answers: the chosen column per D17, instants through `resolve_local`, `[t, t + duration)` computed in UTC with basis `inferred` or `declared`, `measured_at` for counters, `pending` wherever a required answer is missing (D19). T024 and T025 pass
- [X] T031 [US2] Run `uv run pytest tests/unit/imports -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 5: User Story 3 - Say exactly what is wrong (Priority: P1) MVP

**Goal**: Every failure names its row, field and correction, and structural errors, questions and row errors stay separate.

**Independent Test**: `uv run pytest tests/unit/imports/test_parser.py -k wrong`.

### Tests first

- [X] T032 [US3] Add a parametrized bad-input table to `applications/hematdaya-api/tests/unit/imports/test_parser.py` asserting `status`, `reason`, `data_row`, `file_line`, `field` and exact `message` for every row in Messages. It must include: a seventh data row of `-1` under `energy_wh` gives `Baris data 7, energy_wh: gunakan angka 0 atau lebih.`; unquoted `12,5` on data row 2 of a comma file gives `Baris data 2, baris: jumlah kolom 4 tidak sama dengan header (3). Koma desimal harus diberi tanda kutip, misalnya "12,5".`; the semicolon case has no hint; `2026-02-30 00:00` gives `Baris data 1, timestamp: tanggal atau jam tidak ada (2026-02-30 00:00).`; `2026-02-30` gives the format message; neither rolls into March; header `Energy_WH` appears as written; a 61-character name gives `Baris data 1, asset: nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.`, and 60 characters and 60 emoji pass; a 61-character `source` gives `source_too_long`. Formula names `=SUM(A1)`, `+62811`, `-1+1`, `@cmd` and `<script>` return verbatim. A test asserts every `RowReason` member appears in the table
- [X] T033 [US3] Add numbering tests to `applications/hematdaya-api/tests/unit/imports/test_parser.py`. Blank lines: the negative row becomes `Baris data 7 (baris file 9), energy_wh: gunakan angka 0 atau lebih.` Quoted newline: `timestamp,asset,wh\n2026-10-20 00:00,"A\nB",-1\n\n2026-10-20 01:00,C,-1\n` gives `Baris data 1, wh: …` and `Baris data 2 (baris file 5), wh: …`, the prototype's output. Leading blank lines: header on line 3, data row 1 on line 4 has no parenthesis. Mixed `\r\n`, `\n`, `\r` count one line each. Bare `\r` inside quotes counts one line (D9)
- [X] T034 [US3] Add structural and limit tests to `applications/hematdaya-api/tests/unit/imports/test_parser.py`, asserting `reason` and exact message for every row in the structural table, and a test that every `StructuralReason` member appears. Size, padding with `\n`: exactly 10,485,760 bytes has no structural error; 10,485,761 gives `Ukuran 10,1 MiB melebihi batas 10 MiB.`; exactly 11 MiB gives `Ukuran 11 MiB melebihi batas 10 MiB.`; an oversize file with invalid UTF-8 still reports size. Rows: 150,000 with blanks passes; 150,001 gives `150001 baris data melebihi batas 150.000 baris.` Precedence: `foo,bar\n"x` gives only `quote_unclosed`. Separation (FR-005): a file with a row error has empty `structural_errors`, a file with a question has no row error from that question, and `iter_rows` yields nothing when `structural_errors` is not empty. Logging: `caplog` records nothing for a file holding the fake value `Bearer RAHASIA-PALSU-123`, in valid and invalid rows
- [X] T035 [US3] Add AT-29, AT-32 and the AT-30 first-error message to `applications/hematdaya-api/tests/unit/imports/test_prototype_oracles.py`, per the assertion table
- [X] T036 [US3] Run the new tests, confirm they fail on missing behavior, and record it in Notes for `applications/hematdaya-api/tests/unit/imports/`

### Code

- [X] T037 [US3] In `applications/hematdaya-api/app/imports/service/parser.py`, implement row validation in the prototype's order (L748–L767): column count, asset empty, asset too long, source too long, then `pending` when no value column is known, then time cells, then reversed bounds when both are comparable, then value empty, value failure, negative. The first failure wins. `_row_error` builds the message from L742. A row with a naive bound and no confirmed zone still reports value errors (T030's `pending` applies only when no error was found). T032, T033 pass
- [X] T038 [US3] Enforce limits in `applications/hematdaya-api/app/imports/service/parser.py`: `too_large` before any decoding with the rounding from D23, `too_many_rows` with the true count, quote and decode errors replacing all others, and `iter_rows` yielding nothing on structural errors. T034 and T035 pass
- [X] T039 [US3] Run `uv run pytest tests/unit/imports -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 6: Polish

- [X] T040 Measure SC-002: run `uv run pytest tests/unit/imports/test_performance.py -s -q`, `sysctl -n machdep.cpu.brand_string`, `sysctl -n hw.memsize` and `uname -sr`. Record seconds per shape, peak memory, bytes, machine and date in this file's Notes and on the Performance line of `specs/024-csv-parser/plan.md`
- [X] T041 Run `uv run pytest tests/unit/imports --cov=app/imports --cov-report=term-missing` and add a test for any uncovered branch that holds a rule in `applications/hematdaya-api/tests/unit/imports/`
- [X] T042 Confirm D1's limits: `make openapi` leaves `contracts/openapi.json` unchanged, and `git diff --name-only origin/main` lists only `applications/hematdaya-api/app/imports/`, `tests/unit/imports/`, `specs/024-csv-parser/`, `specs/025-import-preview/` (this preparation's task files) and the README row from T043. `app/main.py`, `migrations/`, `app/core/errors/` and `docs/error-handling/catalog.md` are unchanged
- [X] T043 [P] Add a `tests/unit/imports/` row (`CSV parser`, needs `Nothing`) to the test table in `applications/hematdaya-api/README.md`
- [X] T044 [P] Set **Status** in `specs/024-csv-parser/spec.md` to `Built, awaiting review`
- [X] T045 Run `python3 docs/roadmap/check_traceability.py`, then `make check` in `applications/hematdaya-api/` (it needs `make run-dependencies`; without Docker, report that as an environment blocker and run `make lint` and `make test-unit`), then `SKIP=no-commit-to-branch uv run pre-commit run -c ../../.pre-commit-config.yaml --all-files`, and read the output
- [X] T046 Only when the owner asks: commit as `feat(api): add the pure CSV parser (spec 024)`, staging explicit paths. See `specs/025-import-preview/tasks.md` D1 for the shared PR

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 | T010, T018 |
| FR-002 pure | T004, T009, T012, T042 |
| FR-002 stream | T009, T014, T017, T020 |
| FR-003 | T023, T024, T028, T029, T030 |
| FR-004 | T005, T008, T012, T016 |
| FR-005 | T034, T038 |
| US1 scenarios 1–4 | T012, T013, T020 |
| US2 scenario 1 | T024, T025, T029, T030 |
| US2 scenario 2 | T024, T029, T030 |
| US2 scenario 3 | T022, T024, T027, T029 |
| US2 scenario 4 | T024, T025, T029, T030 |
| US2 scenarios 5, 6 | T024, T025, T028, T030 |
| US3 scenario 1 | T032, T035, T037 |
| US3 scenario 2 | T009, T033, T037 |
| US3 scenario 3 | T011, T032, T035 |
| US3 scenario 4 | T032, T037 |
| Edge: 10 MiB, 150,000 rows | T034, T035, T038 |
| Edge: 60-character names | T032, T035, T037 |
| Edge: formula-looking name | T032 |
| Edge: ambiguous delimiter or number | T008, T009, T016, T017 |
| Edge: offset keeps its instant | T011, T012, T019 |
| Plan: BOM, mixed endings, nonexistent time | T009, T022, T033 |
| SC-001 | T013, T025, T035 |
| SC-002 | T014, T040 |

## Dependencies & Execution Order

- **Setup (T001–T002) → Foundational (T003–T007) → US1 (T008–T021) → US2 (T022–T031) → US3 (T032–T039) → Polish (T040–T046).**
- The stories share `parser.py`, so they run in order. Each is independently testable through its own test selection.
- In each story the test tasks and the checkpoint come before any code the tests cover.
- T040 runs after T037, so the measurement includes every row check.
- T043 and T044 can run any time after T039.

### Parallel example

T008, T009, T010 and T011 touch different test files and can run together. So can T016, T017, T018 and T019. So can T022 with T023, and T027 with T028.

## Implementation Strategy

All three stories are P1, and 025 needs all of them, so the MVP for this spec is the whole spec with SC-001 and SC-002. US1 is the first stopping point for review: it reads every format but does not resolve meaning. Stop after each checkpoint task and read the failure before writing code.

## Notes

Record baseline results, failing-test checkpoints and the SC-002 measurement here as tasks finish.

### Baseline (T001, 2026-11-07)

`make test-unit` at `a952723`: 105 passed. `uv run python --version`: Python 3.13.16.

### Failing-test checkpoints

Each ran before the code it covers, with `uv run pytest tests/unit/imports -q`, adding `--continue-on-collection-errors` from T015 on.

| Task | Observed | Why it failed |
|---|---|---|
| T006 | `test_models.py` did not collect. `test_module_boundary.py`: 14 failed, 10 passed | `No module named 'app.imports.model.models'`; the seven modules did not exist. The 10 that passed are the helper's own samples |
| T015 | 6 modules did not collect, and 4 oracle tests errored in the fixture | `cannot import name` `parse_decimal`, `Record`, `ALIASES`, `parse_time` and `iter_rows`. No code existed yet, so no test could run further |
| T026 | 38 failed, 261 passed, 2 modules did not collect (`test_times.py`, `test_cadence.py`) | Missing `resolve_local` and `infer_cadence`. Assertions failed on absent questions and cadences (`assert {} == {'a': None}`). The 261 are US1 tests and meaning cases US1 already satisfied, such as a confirmed average over explicit bounds and counter points |
| T036 | 43 failed, 99 passed (`test_parser.py`, `test_prototype_oracles.py`) | No row-message prefix, no name, source, empty-value or reversed-bounds checks, no row limit, and `Ukuran` not rounded up. The 99 are earlier tests and behaviour already delivered, such as quote precedence and code-point counting |

### SC-002 measurement (T040, 2026-11-07)

`uv run pytest tests/unit/imports/test_performance.py -s -q`: 5 passed. Apple M3, 17,179,869,184 bytes (16 GiB), Darwin 27.2.0, Python 3.13.16. Time is `parse` plus a full `iter_rows`. Peak is `tracemalloc`, so Python allocations only, in a separate run with rows discarded.

| Shape | Rows | Bytes | Seconds | Peak `parse` | Peak `iter_rows` |
|---|---|---|---|---|---|
| Explicit offsets | 150,000 | 10,312,544 | 1.99 | 0.04 MiB | 0.04 MiB |
| Confirmed naive timestamps, 40 streams | 150,000 | 5,062,526 | 1.50 | 6.05 MiB | 0.05 MiB |

After one row, `source.tell()` was 8,192. A one-off run of two further shapes, not part of the test file: 10,485,760 bytes that are almost all blank lines took 3.50 s to parse and 3.09 s to read, the slowest shape found, and 150,000 short rows with 150,000 distinct names took 0.88 s and 1.07 s.

### Implementation notes

Nothing here changes a decision.

- D9, T017: `detect_delimiter` and `read_records` each seek to 0 and open their own wrapper, as D7 asks of each pass, because T009 gives them separate signatures. So `read_records` has no peeked prefix to chain back, and `file_line` is still the previous `line_num + 1`.
- T017, T019: `dialect.has_bom` fills `ParsedFile.had_bom`, and `times.impossible_time` gives the row pass D13's message when adding a duration overflows. Neither is named in a task.
- T018, T017: `ColumnMap` is a frozen dataclass and `Record` a `NamedTuple`. They are internal, not contract types, so D24 does not apply, and `Record` is built once per line.
- D15: `has_naive_timestamps` counts cells that parse as naive times. L685 tests the shape, so a naive-looking impossible date such as `2026-02-30 00:00` raised the prototype's question too. Here it is only a row error, which a timezone answer could not fix.
- T037: two naive bounds count as comparable before confirmation, since they share a zone and an unambiguous wall-clock order matches instant order. A reversed pair is reported at once.
- T025: added `test_at_28_confirmed_rows_are_parsed`, because AT-28's accepted rows need this story's confirmation and cadence.
- T025: added a memory test for the timestamp-only shape, which is the shape that keeps timestamps.
- T045: `pre-commit run --all-files` covers tracked files only, so the new untracked files were also checked with `--files`, without staging them.
- T045: the `ruff-format` hook also formats Python fences in Markdown. Its first run expanded the contract block in `plan.md` to one statement per line. Its AST and comments match the earlier text, and no other file changed. Leaving it compact would make the hook rewrite it at commit.

### Evidence behind the decisions (2026-11-06, read-only)

Python 3.13.16 from the API's `.venv`. Node v16.20.2 ran a scratchpad copy of the prototype, where `domain.test.js` passed 36 of 36.

| Input | Result | Decision |
|---|---|---|
| `datetime.fromisoformat("2026-10-20 08.30")` | `08:00:00.300000` | D13 |
| `csv.reader` default on `"x,1\n2,3\n` | One field `x,1\n2,3\n`, no error | D8 |
| `strict=True` on the same | `csv.Error: unexpected end of data` | D8 |
| 200,000-character unterminated quote | `field larger than field limit (131072)` | D8 |
| `﻿"waktu";alat` without BOM removal | Header reads `﻿"waktu"` | D7 |
| `quoting=QUOTE_NOTNULL`, `QUOTE_STRINGS` | No quoted flag; `QUOTE_STRINGS` raises on text | D10 |
| `Decimal("123456789012345678901234567890.123") * 1000` | `1.234567890123456789012345679E+32` | D11 |
| `int("1" * 5000)` | `ValueError` | D11 |
| Prototype: `0.250`, `1.250` (semicolon), `"1,250"` (comma) | 250,000, 1,250,000 and 1,250 mWh | D12 |
| Prototype: 9007199254740993 Wh | 9007199254740992000 mWh | D11 |
| Prototype: offset `+99:99` | Accepted, shifted four days | D13 |
| Prototype: naive `interval_end` beside an offset start | `naive` false, resolved at +7, not blocked | D15 |
| Prototype: timestamp beside explicit bounds | Timestamp wins, bounds ignored | D18 |
| Prototype: declare 60 with cadences 15 min, 1 h, none | All three become 60 minutes | D20 |
| Prototype: 10,485,761 bytes | `Ukuran 10 MiB melebihi batas 10 MiB.` | D23 |
| `datetime(2026, 3, 8, 2, 30, tzinfo=New_York)` | No error; round-trips to 03:30 | D14 |
| Same-`ZoneInfo` subtraction, 01:30 to 03:30 on that date | 2:00:00, where UTC says 1:00:00 | D14 |

### Feasibility spike (not SC-002 evidence, 2026-11-06)

A scratchpad two-pass `csv.reader` over 150,000 explicit-offset rows (9.95 MiB) on an Apple M3, 16 GiB: Pydantic rows 1.45 s total, dataclass rows 1.50 s. Peak 5.9 MiB in the first pass and about 0 in the second with rows discarded, against 248.8 MiB for a list of Pydantic rows. After one row, `source.tell()` was 8,192. The real parser does more per row, so T040 must still measure it.

### What 025 relies on

`parse`, `iter_rows`, `RowResult.value`, `stream_key`, `ParsedFile.cadences`, the blocking questions and the reason codes. 025 maps `too_large` and `too_many_rows` to `APP-IMPORT-TOO-LARGE`, and every other structural reason to `APP-IMPORT-STRUCTURE`. Parser calls are CPU work, so 025 runs them through `asyncio.to_thread` (rule 006). `specs/025-import-preview/tasks.md` holds the handoffs that remain open, including cadence jitter.
