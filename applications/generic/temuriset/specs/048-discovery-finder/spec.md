# Feature Specification: Discovery and Investor finder (revamp R2a)

**Feature Branch**: `048-discovery-finder`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, second of six; stacked on 047 (design system 1.1)
**Depends on**: 018, 020, 047
**Covers**: FR04, FR05, S03, S10, UX-07
**Size**: M
**Sources**: `reports/TemuRiset UI redesign directions.md`, `reports/TemuRiset five revamp proposals.md` (proposal 2, Investor finder)

## Context

Discovery put a seven-control form before the first result on a phone, and showed every result as a full card. Match cards led with eligibility, readiness, score range and coverage before the one thing an inventor needs: who takes pitches and what decides. A partner who reached an invention from discovery or an email saw a disabled "Simpan inovasi" although saving already worked in discovery.

## User Scenarios & Testing

### User Story 1 - Search, narrow and compare quickly (Priority: P1)

**Acceptance Scenarios**:

1. **Given** Jelajahi or Temukan, **When** it opens, **Then** the keyword field and **Cari** come first, sector, stage and "only saved" sit behind **Filter (n)**, and each filter the service applied shows as a chip with a remove link and **Hapus semua filter**.
2. **Given** results, **When** shown, **Then** each is one compact row (name, one deciding fact, "Disimpan" when saved) and the full card of one result opens beside the list from 64 rem; the address carries `selected`.
3. **Given** a phone, **When** a row is opened, **Then** only that result shows with focus on it, and **Kembali ke hasil** returns to the same search with focus on the same row.

### User Story 2 - Investor finder on Kecocokan (Priority: P1)

**Acceptance Scenarios**:

1. **Given** recommended mandates, **When** matching finishes, **Then** a compact list sits beside one open match, and on a phone they take turns with **Kembali ke daftar** restoring focus.
2. **Given** a match, **When** read, **Then** it leads with the partner, the mandate, the label, **Penerimaan** (whether it takes pitches), **Syarat penentu** (the blocking or missing requirement, or that none blocks) and one action. Reasons, eligibility, readiness, score range and evidence sit under **Mengapa cocok?**; requirement rows under **Rincian syarat**. A blocking requirement never hides there.
3. The label's tone comes from the eligibility and readiness enums, not from its words.

### User Story 3 - Save from the invention page (Priority: P2)

**Given** someone else's published invention, **When** the acting party presses **Simpan inovasi**, **Then** it is saved for that party only (`PUT /saved-items/INVENTION/{id}`), and the button reads **Hapus dari simpanan** after refresh.

## Requirements

- **FR-001**: No API change. `selected` is stripped before the discovery request.
- **FR-002**: `tr-listdetail` (design system) hides the list or the detail below 64 rem; `tr-rowbutton` and `tr-linkbutton` join the bundle.
- **FR-003**: Web deviation D15 is replaced by `tr-listdetail`.
