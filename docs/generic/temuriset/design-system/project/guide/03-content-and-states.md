# Content and states

## Shared glossary

| Meaning | Product copy |
|---|---|
| Main personas | Inovator; Investor/Mitra |
| Portfolio and navigation | Inovasi Saya; Temukan Investor/Mitra; Pitching dan Diskusi |
| Financial subjects | Dukungan Proyek; Pendanaan Perusahaan; Target Pendanaan; Kisaran kontribusi per investor |
| Action responsibility | Menunggu Anda; Menunggu pihak lain |
| Draft status | Belum tersimpan; Menyimpan; Tersimpan di demo ini; Gagal menyimpan |
| Evidence | Dilaporkan sumber; Disediakan, belum diperiksa; Diperiksa untuk kriteria ini; Belum diketahui |
| Capability timing | Saat ini; Direncanakan; Diminta |
| Pitch decisions | Setujui untuk diskusi; Minta revisi; Tolak |
| Revision responses | Dapat dipenuhi; Perlu diskusi; Belum dapat dipenuhi |
| Scheduling | Pilih waktu; Konfirmasi waktu; Usulkan waktu lain; Waktu sudah bentrok |
| Relationship | Kerja Sama; Menunggu konfirmasi; Dikonfirmasi kedua pihak |
| Company status | Perusahaan belum didirikan; Badan usaha telah disebutkan, status pemeriksaan ditampilkan terpisah |

## Independent state axes

Changing one axis never implies a change in another. *StateAxes* makes them operable, with buttons for the five required combinations.

| Axis | Values | Component | Rule |
|---|---|---|---|
| Draft saving | local, saving, saved, failed, conflict | `TR.SaveState` | Accurate location and time; input retained |
| File availability | CREATED, UPLOADING, QUARANTINED, AVAILABLE, REJECTED | `TR.DocumentItem` | Presence cannot bypass quarantine |
| Extraction | NOT_REQUESTED, PENDING, RUNNING, SUCCEEDED, FAILED, NEEDS_MANUAL_INPUT | `TR.DocumentItem` | A safe scan stays available without OCR |
| Review | PROVIDED_UNREVIEWED, REVIEWED_SUPPORTED, REVIEWED_UNSUPPORTED, NEEDS_CLARIFICATION, EXPIRED, SUPERSEDED | `TR.DocumentItem`, `TR.FactSource` | No automatic verified badge |
| Requirement | PASS, FAIL, UNKNOWN, NOT_APPLICABLE | `TR.RequirementRow` | Reason, stage and next action |
| Pitch | Dikirim, Sedang ditinjau, Revisi diminta, Disetujui untuk diskusi, Ditolak, Ditarik, Ditutup | `TR.Status`, `TR.NextStep` | Approval remains a discussion state |
| Scheduling | Open, selected, accepted, expired, superseded, cancelled | `TR.ScheduleSlotList` | No booking until acceptance succeeds |
| Relationship | Draf, Menunggu konfirmasi, Perubahan diminta, Ditolak, Dikonfirmasi kedua pihak | `TR.PartnershipConsent` | Exact version, separate public projection |
| Disclosure | Ceiling, per-party subset, effective intersection, restriction | `TR.PartnershipConsent`, `TR.effectiveFields` | No field beyond mutual and current permission |

## Tone mapping

| Tone | Used for | Never for |
|---|---|---|
| `success` | PASS, reviewed support, confirmed meeting, both parties confirmed | Pending work, uploads, single confirmations |
| `danger` | Known FAIL, rejected file, failed action | UNKNOWN or missing information |
| `warning` | UNKNOWN, needs confirmation, quarantine, conflict | Known failure |
| `neutral` | Waiting, unreviewed, later-stage work, not applicable | A result that needs action now |
| `action` | Your turn, selected but unconfirmed | Anything already finished |

## Money and time formatting

Use `TR.format`. Amounts are decimal strings and never pass through floating point.

| Call | Result |
|---|---|
| `money('USD', '500000')` | USD 500.000 |
| `range('USD', '50000', '100000')` | USD 50.000–100.000 |
| `range('USD', null, null)` | Belum ditentukan |
| `slotTime('2026-11-17T09:00:00Z', 60, 'Asia/Jakarta')` | 16.00–17.00 WIB (Asia/Jakarta) |
| `slotTime('2026-11-17T09:00:00Z', 60, 'Asia/Makassar')` | 17.00–18.00 WITA (Asia/Makassar) |
| `overlaps('…09:30', 60, '…09:00', 60)` | true |
| `overlaps('…10:00', 60, '…09:00', 60)` | false (half-open intervals) |
