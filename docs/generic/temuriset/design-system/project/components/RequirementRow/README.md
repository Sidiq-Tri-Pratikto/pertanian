# RequirementRow

One requirement, its result in words and what to do about it.

**Anatomy.** Label, result, stage, mandatory flag, verification mode, reason, source, action.

**Consumer provides.** `label`, `result` PASS | FAIL | UNKNOWN | NOT_APPLICABLE, `stage` SUBMISSION | DISCUSSION | PILOT | COMMERCIALIZATION, `mandatory`, `mode` DECLARATION | DOCUMENT_PRESENT | REVIEWER_CONFIRMED, `reason`, `source`, `action`. Render inside `<ul class="tr-reqs">`.

**States.** Four results, plus later-stage work drawn neutral with "Tidak menghalangi pengajuan".

**Keyboard and screen reader.** List item with a heading; results are text.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** Result wraps under the label.

**Do.** Show gaps first and say the next action.

**Don't.** Do not turn UNKNOWN into FAIL, or a planned capability into PASS.
