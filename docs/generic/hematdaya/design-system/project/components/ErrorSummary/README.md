# ErrorSummary

After submit, lists every error as a link to its field or row and takes focus.

**Anatomy.** Heading "Periksa N isian berikut" · row-number convention · links.

**Consumer provides.** `errors[{targetId,text}]`, `submitCount` (increment per submit), `convention`, `title`.

**Variants and states.** Hidden when empty; visible and focused after each submit.

**Keyboard and screen reader.** `role=alert`, focus moves to the summary; each link focuses its target (making rows focusable when needed) and scrolls it into view.

**Tokens.** `color-status-error-*`, `size-focus-ringWidth`, `size-target-minimum`.

**Responsive.** Full width at the top of the form.

**Example.** "Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor" → checkbox.

**Limits.** Inline messages must use the same wording as the summary.
