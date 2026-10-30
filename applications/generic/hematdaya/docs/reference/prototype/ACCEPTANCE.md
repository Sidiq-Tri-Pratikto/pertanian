# HematDaya prototype — acceptance and verification record

Status vocabulary: **pass** (behaviour observed in the named runtime and input), **fail**, **not run**, **blocked** (concrete limitation named). Provenance (simulated / import) is recorded separately and is never a pass by itself. All data below is simulated or user-imported test data; no participant, field, native, service or savings result exists.

## Runtimes used

| ID | Runtime | Input |
|---|---|---|
| R-node | Node v25.2.1, `node tests/domain.test.js --json tests/domain-results.json`, 2026-10-24 13:54 UTC | Generated fixtures `hd-fixtures-1`, inline CSV strings |
| R-web | Claude desktop built-in browser, Chrome/152.0.7977.167 (Linux x86_64), `standalone.html` served by `python3 -m http.server` on 127.0.0.1:8811, viewport emulation; interactions by DOM `click()` / React-compatible input setters (`tests/browser-helper.js`) plus real keyboard events for the sheet test, 2026-10-24 | Same files as the canvas; demo scenarios and the eight built-in CSV examples |
| R-canvas | Claude Design canvas Play | **blocked**: built-in browser not signed in to claude.ai; not attempted with your credentials |

## Fixture and boundary assertions (R-node, provenance: simulated)

| ID | Expected | Status |
|---|---|---|
| FX-01 | 2.688 hourly simulated rows per fixture, 4 disjoint assets, integer Wh | pass |
| AT-05 | H: day 2,100 kWh/Rp3.150; week 14,700/Rp22.050; 4 weeks 58,800/Rp88.200; Kulkas 8,400 = 57,14%; complete coverage | pass |
| AT-05b | H base: no change alert; Kulkas/Router continuous → no outside-use finding; no schedule/output prerequisite | pass |
| AT-17 | H change: TV 3,920 vs 2,520, +1,400 kWh (+55,56%), r = 0,168, threshold 0,840; site 16,100/Rp24.150 | pass |
| AT-06 | I: day 24,000/Rp36.000; week 144,000/Rp216.000; 4 weeks 576,000/Rp864.000; Oven 50%; Sunday measured 0 | pass |
| AT-22 | I optional: outside-schedule energy exactly 0; 0,050 kWh/unit; disabling metric keeps totals | pass |
| AT-18 | I change: outside +3,000 kWh vs 0, no percent; 147,000/Rp220.500; energy change not alerted | pass |
| FX-CUR | Now 21 Okt 12.00: H 0,870/Rp1.305, Mon–now 5,070/Rp7.605; I 13,000/Rp19.500, 61,000/Rp91.500 | pass |
| FX-NOW | "Hari ini" on virtual Monday 00.00 is empty (null), not 0 | pass |
| AT-36 | Parent 10 + child 1 never 11; each single view valid | pass |
| AT-35 | Alternative sources 2 kWh never 4; unresolved asset value withheld | pass |
| AT-36b | Unknown overlap refuses only the combined total | pass |
| AT-27a/b | 100 W × 30 min = 50 Wh; instantaneous blocked; counter 100→130→5 gives 30 Wh + unknown reset interval | pass |
| AT-13 / AT-15 / AT-12 | Overnight 8 inside / 2 outside; 16.30–17.30 → 30/30 estimated; merged windows counted once | pass |
| AT-19 / AT-16 / AT-21 | 50% coverage, no matched alert; learning + no tariff + partial; all-zero valid with no percentages | pass |
| AT-38 | Stale simulated source + offline client separate; retry fabricates no reading | pass |
| AT-09 / AT-08 | Tariff split Rp3.000; explicit 0 tariff valid Rp0; missing tariff unknown | pass |
| AT-23 / AT-24 | Zero/negative/missing output → no intensity; estimated partial day only with windows + uniform confirmation | pass |
| AT-30 / AT-28 / AT-29 / AT-31 / AT-32 / AT-33/34 | 2/10 ack + 8 rows, 3/10 blocked, counts reconcile; semicolon/decimal comma/BOM/quoted/CRLF/blank; unquoted decimal comma rejected; bad header/date/value messages; one-row/irregular need interval; 60-char names, 150.000-row limit; reject keeps data, interrupt → status lookup → one commit, reimport 0 added, conflict blocked | pass |
| AT-53 | Core-only composition: identical energy, cost/metric off, disabled capability rejected at mock boundary; invalid compositions rejected | pass |
| AT-39 / AT-40 / AT-51 / AT-42 | Feedback hide/snooze/restore, readings untouched; rejected/expired/offline saves keep confirmed values; timezone change keeps UTC readings; simulated source retry creates no duplicate | pass |

Result file: `tests/domain-results.json` (36/36 pass). These verify the browser simulation's arithmetic, not a server.

## Interaction walkthroughs (R-web)

| Case | Observed | Status |
|---|---|---|
| Household core (P01/P03, AT-01, AT-55) | Welcome → Coba demo → Rumah tangga → Beranda shows 19–25 Oktober 2026, scope 4 perangkat, 14,700 kWh, Rp22.050 (tarif simulasi), 100% completeness, ranking Kulkas 57,14%; "Lihat perangkat terbesar" opens Kulkas in **1 tap**; history chart + data table; Back restores Beranda, period and scroll (900 px); heading receives focus after each route change | pass |
| Household evidence (P04/P10, AT-17, AT-39) | Featured "TV naik 1,400 kWh (+55,56%)" → evidence in **1 tap**; ordered evidence, calculation detail with arithmetic; feedback with injected rejection → "Gagal menyimpan" → Coba lagi → confirmed; Sembunyikan → back to Beranda with restore link; Saran tersembunyi (1) → Pulihkan → observation visible again | pass |
| Industry core (AT-02) | 144,000 kWh/Rp216.000, Oven 50% largest (1 tap); no schedule or output requested | pass |
| Industry outside-window (AT-18) | "Energi Kompresor di luar jadwal bertambah 3,000 kWh", "Persentase tidak tersedia karena nilai pembanding nol", qualifier "belum tentu pemborosan", comparison table 3,000 vs 0,000 ×3 | pass |
| Optional metric (P06, AT-22/23) | Beranda shows 0,050 kWh/unit only when enabled; 0 output → ErrorSummary focused "Tidak dapat dihitung: keluaran nol", Simpan disabled with reason; Nonaktifkan removes the display, totals unchanged | pass |
| Schedule editor (P05, AT-12/13, UX-15) | Equal times and overnight-without-flag give linked errors; overnight preview "22.00 → hari berikutnya 06.00 (dihitung pada hari mulai)"; effective-now vs historical-correction previews; injected rejection keeps draft and the confirmed insight; retry saves | pass |
| Scope resolution (P09, AT-35/36) | Overlap scenario never shows a combined number; conflicted child never shown as 0; source authority chosen → "Meter utama 10,000 kWh" vs "Kulkas, Router, TV saja 1,600 kWh"; Konfirmasi disabled with reason until valid; injected rejection keeps the proposal; retry → 10,300 kWh/Rp15.450 after the user confirmed Pompa Air is separate | pass |
| CSV import + recovery (P02, AT-26–34, AT-58) | Empty input → ErrorSummary; mapping errors summary focused; 2/10 preview reconciles 10 = 8+2+0+0, confirm without ack → focused error, ack → interrupted commit → "Status penyimpanan belum diketahui" → Periksa status → "sudah dikonfirmasi… tidak diimpor dua kali"; landing on 20 Oktober 2026 with "Data impor historis"; 3/10 blocked with disabled reason; conflict 2 rows blocked; reimport 0 valid / 8 duplicates; semicolon file 3 rows; power_w needs meaning, instantaneous blocked, average accepted; one-row file requires interval; draft retained after leaving the import | pass |
| State combinations (AT-38, AT-57) | Learning + no tariff + partial (71% period, gaps 22 Okt 14.00–16.00 and 24–25 Okt); valid zero + no tariff ("Nol terukur", "Persentase tidak dihitung"); stale + offline (last capture, "bukan tanda perangkat mati", refresh fails keeping cache time); historical + offline (no stale claim); current period 0,870/Rp1.305 and Mon–now 5,070/Rp7.605; no "null/NaN/Infinity" rendered | pass |
| Source setup (P07, AT-42) | Shelly → "Integrasi belum tersedia pada prototipe ini"; simulated first reading labelled "Simulasi koneksi"; no "Terhubung"; name validation; saved asset shows binding effective time | pass |
| Asset edit/archive (AT-43 partial) | Empty name error; rename; archive with confirmation → listed under Diarsipkan → Pulihkan | pass |
| Context/timezone (AT-04, AT-51) | Context change previews "contoh berubah"; timezone confirmation text; after save subtitle Asia/Makassar, energy unchanged | pass |
| Composition (AT-53) | Core-only: same 14,700 kWh, "Estimasi biaya tidak aktif", tariff/schedule modules disabled in settings | pass |
| Demo reset (AT-43) | Confirmation names demo-only scope; reset restores scenario | pass |
| Browser back (UX-05) | Standalone: browser back = visible back, period kept; programmatic return after hide keeps confirmation | pass (standalone only) |
| Final regression after last edit | H, I, overlap, local import 12 rows, landing; no console errors | pass |

## Accessibility and responsive (R-web; selected checks, not a WCAG audit)

| Check | Observed | Status |
|---|---|---|
| Targets ≥ 48 CSS px (UX-07) | 0 controls under 48×48 on Beranda (16), Kulkas detail (12), Pengaturan (24) at 375 px and at 200% text | pass |
| Text contrast (UX-07) | Minimum computed ratio 5,67:1 over rendered text on those screens | pass |
| Non-text contrast | Token values from the system's report; not re-measured here | not run |
| Reflow 320 px and widths 360/390/430/768/1280/1440 (UX-09) | No horizontal overflow at any width; 360×560 short viewport keeps the tab bar visible | pass |
| 200% text (UX-08) | Root 32 px, metric 68 px, no overflow, no small targets | pass |
| 400% zoom at 1280 | — | not run |
| Keyboard sheet (UX-10) | Enter opens, focus to sheet title, Tab stays inside, Escape closes, focus returns to "Ubah detail" | pass |
| Full keyboard-only task sequence | Partial (sheet only) | not run |
| Reduced motion | CSS rule and in-app toggle present; behaviour not observed | not run |
| Screen readers (NVDA/JAWS/VoiceOver/TalkBack) | — | not run |

## Platform, export, service and research gates

| Gate | Status |
|---|---|
| Design canvas Play (editor) | blocked — not signed in from this session; please open the link and press Play |
| Claude Design HTML/ZIP export, exported interactions | blocked — export menu not reachable from this session; `standalone.html` is a separate local build, not the export |
| Canvas file inventory | pass — published files listed and fingerprinted (README §2, version 1792850244-f00b) |
| Android / iOS (AT-48, AT-45 native) | not run — no native build |
| Saved service, auth, ownership (AT-41), restore (AT-50), export (FR-16), injection-safe export (AT-44) | not run — not implemented |
| Live meter / adapter (G5) | not run — Shelly/TP-Link planned only |
| Household / industry participants (AT-52) | not run |
