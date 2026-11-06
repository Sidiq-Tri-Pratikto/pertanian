# UX principles

These rules make the product easy for a first-time inventor and quick for a busy investor. Each one names the component that carries it, so following the component follows the rule. They are design decisions and hypotheses: no participant has tested them yet.

## 1. One next step

A person should never have to work out what to do. Open every workspace with `TR.NextStep`.

- Say whose turn it is in words: "Menunggu Anda" or "Menunggu pihak lain".
- Give one sentence of reason and one action named by its effect.
- When it waits on someone else, say that nothing is needed now. Do not offer busywork.
- Show one `primary` button per task region. Everything else is `secondary`.

## 2. Tell people what a result means for them

A label alone is not enough. Pair `TR.Status` with one sentence.

| Instead of | Write |
|---|---|
| Unknown | Belum diketahui. Kewenangan hak belum diperiksa. Ini bukan penolakan. |
| Approved | Disetujui untuk diskusi. Mitra bersedia berdiskusi. Ini belum berarti pendanaan atau kerja sama. |
| Revoked | Akses dicabut. Unduhan baru diblokir, tetapi salinan yang sudah diunduh tidak dapat ditarik. |

## 3. Work is never lost

Fear of losing work makes people stop. Protect it, then say so.

- Show `TR.SaveState` beside the page heading. Use a location: "Tersimpan di demo ini".
- A draft saves with gaps. Require support details when sending, not when saving.
- After an error, keep every nonsecret value. Focus `TR.ErrorSummary`, link to each field, and repeat the inline words.
- On a stale version, `TR.VersionConflict` shows the retained draft and one recovery.
- One failed upload never clears other answers.
- A failed replacement leaves the existing meeting in force, and the message says so.

## 4. Ask for less, reveal when relevant

- Show fields only for the selected purpose. Do not delete unrelated saved drafts when the purpose changes.
- Put the task first. Put ranking, provenance and score detail in `TR.Disclosure`.
- Keep blocking gaps visible at all times. List gaps first, and do not make people open anything to learn why they are blocked.
- Never require a company, patent or institution just to continue.

## 5. Explain the wait and the block

- A disabled action says why, right beside it: `disabledReason`.
- An empty result says why and offers a next action: `TR.EmptyState`. It never loosens a mandatory requirement on its own.
- A later-stage requirement is marked "Tidak menghalangi pengajuan". Future work never looks like today's blocker.

## 6. Check before anything consequential

- Use `TR.SummaryList` with `Ubah` links before sending, publishing or confirming.
- Show the acting context and the exact recipient and version.
- Use `TR.Dialog` for short confirmations. Use an ordinary page for long work.
- Save the word "terkirim" for after the server confirms.

## 7. Respect time and money

- Money always says what it is an amount of, with its unit and period: `TR.FinancialScope`.
- Times appear in the reader's zone with its label, and the other party's time beside it: `TR.ScheduleSlotList`.

## 8. Comfortable on a phone and with a keyboard

- Common controls are 44 CSS px. Whole rows are targets for choices.
- The phone bar shows four destinations plus Lainnya, and stops sticking when large text would make it cover content.
- Every action works by keyboard. Focus is always visible and is not hidden by sticky bars.
- Reading order stays the same at every width: task first, support after.

## Task-time goals to verify later

The PRD proposes these and they are not yet measured: at least 80% of defined tasks completed without help, a prepared pitch in under five minutes, slot selection in under two minutes, and correct understanding that approval is not funding. Run them with 5–8 people covering independent inventors, startup managers and investors or partners, including keyboard and mobile use.
