# Pattern assemblies

All names, evidence, amounts and activity are fictional DEMO contracts, not customers, investor interest, reviewed inventions or funding outcomes. Pattern controls simulate state in the browser and prove nothing about file scanning, grant enforcement, simultaneous booking or legal authority.

Assumptions this stage adds to the fixtures: the slot dates (16 and 17 November 2026), the names Rani and Mitra Demo A/B/D, and the short problem sentences. The handoff gives times and amounts but no calendar dates or display names. P04 also uses an illustrative agreed amount, USD 25.000, and start date, 1 December 2026, because the handoff gives field names without values.

## P01 PatternDiscovery

Composes `TR.Screen`, `TR.NextStep`, `TR.Tabs`, `TR.InventionCard`, `TR.FundingRequestCard`, `TR.FinancialScope`, `TR.FactSource`, `TR.Disclosure`, then for preflight `TR.SummaryList`, `TR.RequirementRow`, `TR.ContextSwitcher`, `TR.TextArea` and `TR.VersionConflict`.

Shows a compatible opportunity (F01, "Siap dikirim"), an unknown gap (F02, "Perlu konfirmasi") and a known mismatch (F03, "Tidak cocok untuk mitra ini"). Company funding sits in its own tab. The card shows FRaise01 once, with two linked inventions and no duplicate amounts. The score 71,72–80,00 is behind a disclosure and labelled a review-priority index, not a funding probability.

Three fixtures appear together so one page shows all three outcomes. The application shows results for one selected source request.

Try: Siapkan pitching, then Kirim pitching. Tick "Persyaratan berubah sebelum kirim" first to see a stale preflight keep the message.

## P02 PatternPortfolio

Composes `TR.Steps`, `TR.SaveState`, `TR.TextField`, `TR.TextArea`, `TR.DocumentItem`, `TR.ErrorSummary`, `TR.InventionCard`, `TR.Checkbox`, `TR.ContextSwitcher` and `TR.Dialog`.

Four ordered steps: basics; what exists and evidence; support and financial scope; public preview. F01 starts with an AVAILABLE scan that needs manual input and is unreviewed. "Tanpa anggaran" shows the missing-budget variant: the draft stays saved, the preview reads "Belum ditentukan", and sending is disabled with its reason. "Penyimpanan berikutnya gagal" shows a retained save failure with retry. Typing -1 or a maximum below the minimum on step 3 triggers the error summary. The final send names one recipient, one document and one version.

## P03 PatternRevisionSchedule

Composes `TR.NextStep`, `TR.Tabs`, `TR.RevisionItem`, `TR.ErrorSummary`, `TR.ScheduleSlotList`, `TR.Status` and `TR.FinancialScope`.

A required pilot-budget question and an optional planned-feature question keep their answers. "Belum dapat dipenuhi" is accepted on resubmission once required items are answered. After "Mitra menyetujui diskusi", three slots appear. The 09:30–10:30 UTC slot conflicts with the 09:00–10:00 booking; 10:00–11:00 does not. 09:00 UTC reads 16.00 WIB and 17.00 WITA. A selected slot says "Dipilih, belum dikonfirmasi". With "Penggantian jadwal gagal" ticked, a replacement fails and the original meeting stays in force.

## P04 PatternRelationship

Composes `TR.NextStep`, `TR.PartnershipConsent`, `TR.SummaryList` and `TR.effectiveFields`.

Confirm version 1, then press "Mitra mengoreksi ke versi 2": the correction clears both confirmations. Confirm version 2, then press "Mitra mengonfirmasi versi 2". Only the four fields both parties allow appear publicly. The amount stays private because only one party permits it. "Sembunyikan" narrows a field at once and the copy states it cannot recall downloads. A project relationship is stated not to create equity, even with a monetary amount.
