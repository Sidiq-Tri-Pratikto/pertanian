# Feature Specification: Decision path (revamp R2b)

**Feature Branch**: `049-decision-path`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, third PR of six revamps; stacked on 048
**Depends on**: 024, 026, 028, 047
**Covers**: S11, S13, UX-11
**Size**: M
**Sources**: `reports/TemuRiset UI redesign directions.md` (pitch room, preflight recap, Beranda)

## Context

The pitch room showed the status and whose turn it was, but not who the counterpart was, which mandate or which version, and the next step never linked to the tab where the work sits. The preflight's last panel explained the effect of sending without a recap of what the recipient gets. An inventor with an unfinished first draft and nothing else waiting landed on Beranda with no way back to the draft.

## User Scenarios & Testing

### User Story 1 - Pitch room top cluster (Priority: P1)

**Given** a pitch room, **When** it opens, **Then** above the tabs it shows the counterpart (Penerima or Pengirim), the mandate, the active version (Kiriman N) and the status, then the next step. **When** it is this party's turn and the work sits on another tab, **Then** the next step links there ("Jawab revisi", "Catat hasil pertemuan", "Periksa ringkasan Kerja Sama", otherwise "Buka {tab}"). Deciding keeps its buttons right below, and proposing a summary keeps its own button. The six tabs keep their deep links.

### User Story 2 - "Yang akan diterima {nama}" (Priority: P1)

**Given** the preflight, **When** the inventor reaches the send button, **Then** a recap lists who sends, the brief's opening words and the files the recipient can download, with **Ubah** links to the brief and the file choice. **Kirim pitching kepada {nama}** stays the commit point.

### User Story 3 - Beranda resumes the work (Priority: P2)

1. **Given** an inventor with a never-published draft and nothing waiting on them, **When** Beranda opens, **Then** the next step is **Lanjutkan draf** at the first editor step with a missing field, or the public preview when nothing is missing. An open need's matches follow it.
2. **Given** a partner, **When** Beranda opens, **Then** it links to the inventions they saved.

## Requirements

- **FR-001**: No API change. The next step's `tab` and `action` come from the existing next-action projection.
- **FR-002**: Pure helpers `primaryFor()` (`features/pitches/workspace.ts`), `briefPreview()` (preflight) and `resumeStep()` (`features/portfolio/editor-state.ts`) are unit-tested.
