# HematDaya energy-feedback UX research

Research date: 21 October 2026. Context read: `docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md` (Generic 1.1). This is research input for the updated PRDs and standalone English design handoff. The product requirements and all recommendations below are proposed design decisions, not results of a HematDaya usability study. Six primary research sources were opened in full, including author manuscripts/preprints. No additional agents were used.

## 1. What feedback can help people understand electricity use without overstating savings?

### Takeaway

Use recorded kWh as the stable measurement, offer clearly qualified cost when a tariff exists, and explain changes through named measured assets and matched periods. Treat comprehension, successful investigation and measured savings as different outcomes; existing research does not prove that this app saves energy or is intuitive for Indonesian households or industrial users.

### Cited Findings

- Hargreaves, Nye and Burgess (2010), *Making energy visible*, reports qualitative interviews with 15 UK households within a 275-household eastern England monitor trial; 12 interviewed households had displays. Quantitative consumption results were not yet available in this paper. Interviewees often found money more meaningful than abstract energy/carbon units, but cost figures were undermined by absent or incorrectly entered tariffs. Rapid annual extrapolations from instantaneous demand became implausibly large when short-duration loads ran. Named-appliance comparisons made consumption more relatable; household routines and negotiations constrained what people could change. This is qualitative contextual evidence, not a causal savings estimate or evidence about Indonesia/industry. — [Full primary paper, Energy Policy 38:6111–6119](https://www.wren.uk.com/images/documents/publications/hargreaves_smart_meters.pdf)
- Bonino, Corno and De Russis (2012), *Home Energy Consumption Feedback: A User Survey*, evaluated video mockups of direct power feedback and daily energy goals. Of 1,807 starters, 992 completed the questionnaire; respondents were predominantly young, technically educated and Italian (95.26% Italy; mean age 23). Many located peak/appliance information correctly. Understanding of room goal colour thresholds was less consistent: 43.28% selected the intended relative-goal meaning of the green-room threshold, while 41.30% chose a concrete 1 kWh threshold. These are mockup comprehension and self-reported preference results, not demonstrated household behaviour change. — [University-hosted full preprint](https://iris.polito.it/bitstream/11583/2465381/1/energySurvey.pdf)
- Froehlich, Findlater and Landay (2010), *The Design of Eco-Feedback Technology*, surveys 89 environmental-psychology and 44 HCI/UbiComp papers. It distinguishes design/usability evaluation from rigorous behaviour-change evaluation and calls for comparative controls or baseline data when testing behaviour change. Its design discussion includes units, feedback frequency, granularity, accessibility and comparison; these were not settled into one universally best design. This is a literature synthesis across contexts, not a HematDaya intervention trial. — [Author laboratory full paper, CHI 2010](https://makeabilitylab.cs.washington.edu/media/publications/Froehlich_TheDesignOfEcoFeedbackTechnology_CHI2010.pdf)

### Inferences

The following are recommendations for HematDaya, inferred from the evidence and product contract, not study findings:

- Define a user-goal hierarchy for every screen: **understand what was measured → compare valid evidence → choose what to investigate → optionally review after an action**. Saving money is a possible later outcome, not a promised dashboard result. Do not turn engagement, number of dismissed suggestions or declining consumption into a savings claim.
- Beranda first answers “Berapa energi yang dipantau pada periode ini?” with explicit period and scope immediately adjacent to kWh. Suggested order: selected site/period; measured scope; kWh; optional cost; quality; largest contributors; one eligible observation. Use short descriptions and expandable evidence rather than a wall of formulas.
- Show `Energi yang dipantau · 14,70 kWh` and, only with a confirmed tariff, `Estimasi biaya energi terpantau · Rp22.050`. Show the tariff/effective period and `Estimasi ini tidak sama dengan tagihan listrik` in the supporting detail. Tariff absent means `Biaya belum dihitung` plus optional `Tambah tarif`, never Rp0.
- A compact educational explanation can say `kWh menunjukkan energi yang tercatat selama periode ini.` Show `Daya (W)` only on a source/detail view when the source actually provides power. Do not imply W and kWh are interchangeable. Test whether these Indonesian labels are understood.
- Prefer relatable measured comparisons such as `Kulkas 8,40 kWh · terbesar dari 4 perangkat yang dipantau`; never assert that a high contributor is inherently wasteful. A refrigerator/router may need continuous operation. Do not add fictional rooms, inferred occupancy, appliance identification or a household/factory total from partial plug measurements.
- Explain an observation using a fixed small narrative: `Yang tercatat` → `Dibandingkan dengan` → `Yang belum diketahui` → `Langkah pemeriksaan`. Example: `TV memakai 3,92 kWh pada 19–25 Oktober. Median tiga minggu pembanding: 2,52 kWh. Penyebab perubahan belum diketahui. Periksa apakah waktu pemakaian berubah.` Amounts are fixture values, not real user results.
- Avoid extrapolating a momentary load into an annual bill. Historical period cost is already useful. No live animations or red “money leaking” messages are needed to create urgency.
- Keep optional schedules, output metrics and tariffs in relevant setup/detail journeys. No compulsory AC, production field or operating schedule. A neutral `Lewati` keeps the complete CSV/demo path usable.
- Do not introduce points, streaks, competitive household rankings or default energy budgets in generic v1. They create extra interpretation and value judgments without solving the current core task. An energy goal, if later added, must state its unit, period, scope and provenance; the user must choose it knowingly.

### Gaps

- None of these sources validates Indonesian terminology, the three-tab navigation, local tariff comprehension, or industrial decision-making. The correct treatment is separate local usability testing, not transferring published success percentages.
- No evidence was collected for a specific savings percentage, a universal change threshold, or a guaranteed “three taps” comprehension result. Those can only be product acceptance targets pending tests.
- Five participants per segment, if used in the PRD, constitute a practical formative round; do not present that count or a four-of-five target as a statistically established universal standard or proof of population usability.

## 2. How should comparisons, scope and incomplete data be presented honestly?

### Takeaway

Support comparisons with simple aligned graphics and precise text. Show measured zero, missing intervals, partial scope, source freshness and unavailable comparisons as distinct meanings; a visually clean chart must not erase uncertainty or turn unknown values into measurements.

### Cited Findings

- Heer and Bostock (2010), *Crowdsourcing Graphical Perception*, replicated proportional judgment tasks and tested additional encodings using Mechanical Turk. Experiment 1A requested 50 judgments per chart across 70 charts. Position encodings performed better than angle and circular area in these controlled proportion judgments. The authors explicitly note environmental/display variation and interactions between encoding/context. This supports careful use of aligned position for quantity comparisons, not a claim that one complete dashboard is universally best or that a phone energy app has been tested. — [Stanford author-hosted full paper, CHI 2010](https://hci.stanford.edu/publications/2010/crowd-perception/heer-chi2010.pdf)
- Song and Szafir (2019; IEEE VIS 2018), *Where’s My Data? Evaluating Visualizations with Missing Data*, studied average/trend estimation and confidence/data-quality judgments for incomplete time series using line and bar charts. Their experiments compared visual treatments and imputation approaches including zero fill, linear interpolation and marginal means. Representation affected perceived quality and interpretation; breaking visual continuity could itself bias interpretation. The paper offers preliminary design guidance, not a universal missing-data treatment. Study-specific participant counts were not extracted in this research pass. — [Author-linked full manuscript](https://cmci.colorado.edu/visualab/papers/song_VIS_2018.pdf); [author-linked project page](https://cmci.colorado.edu/visualab/MissingData/)
- Hullman (2019), *Why Authors Don’t Visualize Uncertainty*, surveyed a convenience sample of 90 visualization authors and interviewed 13 influential designers. Authors described uncertainty omission for reasons including anticipated confusion, lack of uncertainty information and credibility concerns. The study characterizes practitioners’ beliefs; it does not establish that consumers prefer omission or that a particular uncertainty display increases trust. Selection bias and context matter. — [Full author-submitted paper](https://arxiv.org/html/1908.01697v1)

### Inferences

These are product-specific design recommendations, not claims directly tested by those papers:

- Use a sorted horizontal bar/list for “Kontributor terbesar”. Keep a common zero baseline, direct asset labels, kWh values, and a visible denominator such as `Dari 4 perangkat yang dipantau`. Direct values allow precise reading without estimating shapes. On narrow screens, a ranked list with short bars is sufficient. A donut is unnecessary for the primary ranking task.
- Use daily energy bars on the compact weekly view. A detail chart may use a time series when its cadence and gaps are clear. Compare current/reference with aligned periods and shared scales; do not overlay incompatible time support or compare a partial day with a full day. Include direct `+1,40 kWh` and a percentage only when the reference permits it. Baseline zero means percentage unavailable, never infinity or a manufactured large percent.
- Provide an accessible text equivalent: period, scope, total, largest contributor, number of missing intervals and comparison status. Tooltips cannot be the sole path on touch devices or for keyboard/screen-reader users.
- Scope and coverage need separate labels: `Cakupan pengukuran: 4 perangkat` concerns what equipment is measured; `Kelengkapan data: 92% periode` concerns how much expected time has valid observations. Avoid a single opaque “92% akurat” score. Neither completeness nor freshness is a measurement-accuracy certificate.
- Put the compact quality explanation near the number it qualifies. Example: `12,4 kWh tercatat · data sebagian` with `Lihat bagian yang belum tersedia`. The detail can show actual available versus expected intervals and exact dates; do not create confidence percentages unsupported by calculations.
- For a chart gap, use an absent segment/slot plus an explicit textual annotation (`Data 14.00–16.00 belum tersedia`) and a distinguishable unavailable region or marker. Test comprehension: visual gaps alone can be missed or overinterpreted. Never draw an unlabelled continuous line across missing readings. Do not zero-fill or impute energy merely to make a chart look complete.
- Separate independent states: source latest timestamp; selected period completeness; live connection status; historical CSV date range; phone offline cache state. Historical CSV from last month is not an “offline device”. A disconnected meter is not proof the appliance is off. Preserve the last confirmed measurement with its timestamp.
- If a parent meter covers a refrigerator meter, scope resolution should preview valid alternatives as `Meter utama: 10 kWh` or `Kulkas: 1 kWh`; do not display an additive 11 kWh. Explain `Pengukuran ini dapat mencakup perangkat yang sama` and offer `Pilih cakupan`. Keep individual readings available while a combined total is blocked.
- Do not place an attractive giant total above a tiny scope disclaimer. If the selected view is only plugs, say `Perangkat yang dipantau`, and leave unmeasured energy unknown. A main meter may have separate child detail, but child values cannot silently be added again.
- Where comparison cannot be supported, say `Belum dapat dibandingkan` followed by the actual reason and the next useful action (`Lihat data` / `Periksa sumber` / `Pilih periode data`). This is different from a valid comparison with `Tidak ada perubahan yang memenuhi kriteria`.

### Gaps

- No selected study establishes the best specific Indonesian coverage wording, the right visual treatment for HematDaya gaps, or a universal coverage threshold. The PRD’s calculation/readiness rules remain engineering policies to implement and calibrate.
- The missing-data paper shows that presentation changes judgments; it does not authorize imputation in this monitoring product or imply that higher perceived data quality is always desirable.
- Research about uncertainty and trust must not be simplified into “disclosure always increases trust.” The desired outcome is calibrated interpretation: users know what is recorded and what cannot be concluded.

## 3. What complete, testable interaction model should the design handoff require?

### Takeaway

Keep three stable destinations and disclose complexity at the point of need. A standalone handoff should include complete success and recovery journeys with realistic household and industrial data, and define how designers will test understanding instead of claiming the result is already intuitive.

### Cited Findings

- Source evidence for this section is the contextual and evaluation material summarized under Question 1 and the graphical/missing-data studies under Question 2. This section introduces no additional empirical findings; all proposed journeys and copy below are design inferences. In particular, the reviewed HCI synthesis treats understandability/usability work and longitudinal behaviour-change evaluation as distinct activities. — [Froehlich et al., full paper](https://makeabilitylab.cs.washington.edu/media/publications/Froehlich_TheDesignOfEcoFeedbackTechnology_CHI2010.pdf)

### Inferences

**Stable navigation and progressive detail**

- `Beranda`: understand the selected period, monitored scope, kWh, optional cost and quality; find the largest measured contributor and one eligible observation.
- `Perangkat`: list any measured device/group/circuit, read a visible type/scope label, inspect history/provenance/quality, import/add a supported source, archive where appropriate. Never imply a tappable power-control switch.
- `Saran`: distinguish personalized observations, data-quality recovery and labelled general guidance. Detail reveals measured value, reference, period, source, completeness and limitations. Hiding a suggestion cannot delete measurements or alter equipment.
- Settings/import/scope resolution/optional metric setup remain secondary routes. The current period and scope persist across relevant screens. A first-time user should not need to learn internal ingestion or module terminology.
- Use three disclosure levels: (1) plain-language summary and meaning-changing qualification visible; (2) detail view with comparison and next action; (3) expandable calculation/provenance. Never bury a qualification that reverses the apparent meaning of the main number.

**Mandatory designed states**

- Empty Beranda: `Belum ada data energi` + primary `Impor data`, secondary `Coba demo`; explain supported meter setup only when actually available. No fake zeros or warning about absent appliances.
- Learning Saran: `Belum cukup periode pembanding` + explain what period/history is missing and link to available measured history. Largest contributor can already be useful. Avoid a percentage progress meter unless its completion calculation is real.
- No eligible finding: `Belum ada perubahan yang memenuhi kriteria pada periode ini`; preserve history. Do not say the site is efficient, safe, normal, or free of waste.
- Partial data: available amount plus conspicuous qualifier and exact gap detail. No tariff: kWh remains useful. No schedule/output: no permanent empty industrial cards or pressure to configure them.
- Live stale/source issue: last timestamp and inspection/retry path. Client offline: cached-data age and preserved drafts. Historic import: exact date range and `Lihat periode data`.
- Duplicate source/physical overlap: explain affected scope, allow individual review, preview valid alternatives, then confirm. Never resolve a conflict by silently discarding a source.
- Success must require a confirmed save/import. Loading, pressed, saving, failure, retry, cancellation and expired-session transitions need distinct designs. Preserve entered values and files where the platform permits.

**CSV is a complete first-use journey**

1. Choose a file or paste data; show a downloadable/copyable example and readable requirements.
2. Detect/map columns and confirm measurement semantics, unit, timezone and interval. Explain an unresolved field beside it in Indonesian. Do not force category, schedule, tariff, production or AC.
3. Map each source to a named asset and measurement boundary; prevent ambiguous name-only merges and parent/child double counting.
4. Preview valid, invalid, duplicate and conflicting rows with counts and sample row-level messages. Show accepted/skipped totals before commitment; make it clear which problems block the import.
5. Confirm the declared accepted rows; show in-progress and retry-safe result. An error preserves existing readings and setup input. No “success” before server confirmation.
6. Land on a populated Beranda for the actual imported date range with visible `Impor CSV` provenance. Importing old data must not land on a falsely empty “today” without an obvious route to the imported period.

**Evidence-first suggestions and harmless feedback**

- Detail order: observed statement → current/reference chart/table → quality/scope → unknown cause → optional human investigation → feedback (`Berguna`, `Tidak sesuai`, `Sembunyikan`, restore path). Do not use `Terapkan` for something that might imply operating equipment.
- For scheduled consumption: `Pemakaian di luar jadwal` is a description of an explicit user schedule, not a diagnosis. Suggest checking whether a legitimate activity required it. Without a schedule, this insight type does not appear.
- Optional output metrics require scope, denominator, unit, exact period and actual/estimated method; households without them retain a clean core UI. Positive energy with zero output is not infinity, and missing output is not zero.
- Do not render explanatory formulas and quality facts as an “AI confidence” badge. Deterministic evidence is sufficient. Prototype data must carry `Demo · Data simulasi` throughout relevant views.

**Prototype validation to specify in the handoff**

- Use distinct household and business/industry fixtures, both without AC. Household: refrigerator/router/pump/TV; industrial: oven/compressor/press/lighting. Same navigation and calculation semantics, context-specific examples only.
- Give neutral tasks: identify the largest measured contributor; explain what the home number includes; distinguish a missing interval from true zero; interpret cost without assuming it is the bill; read a suggestion and name what remains unknown; import and repair a bad CSV; recover from overlap without adding parent and child energy.
- Record unaided completion, time, wrong turns, assistance, scope mistakes, quality mistakes and unsafe interpretations separately for household and business/industrial participants. Test no tariff and no optional configuration. Do not hide a failing segment in a combined average.
- Evaluate accessible chart alternatives, keyboard/focus flow on web, touch targets, large text and narrow screens. These are implementation checks, not properties proven by visual mockups.
- Final design handoff must name every interactive control, next screen/state, pending/failed/success response, retained context, required data and user-facing qualification. A decorative screen gallery is incomplete.

### Gaps

- No HematDaya participant research was conducted during this assignment. Personas, hierarchy, copy, graphics and paths above are design hypotheses requiring formative tests.
- No prototype, native runtime, source hardware, tariff configuration or live data integration was tested. Research does not verify implementation, field measurement accuracy, real savings, electrical suitability or general industrial scale.
- The full PRD’s numerical rules, acceptance targets and deterministic fixtures must be carried into the handoff from the authoritative specification; this research does not replace those exact contracts.
