# ImportPreview

CSV preview with counts, mapping, assumptions, row errors, threshold rule and explicit confirmation; save states keep the draft.

**Anatomy.** File + period · counts · mapping/assumptions disclosure · row errors · block notice or acknowledgment · status · confirm.

**Consumer provides.** `fileName`, `totalRows`, `invalidRows`, `duplicateRows`, `conflictRows`, `maxInvalidShare` (0.2), `mapping`, `assumptions`, `errors`, `acknowledged`, `onAcknowledge`, `ackError`, `saveState`, `onConfirm`, `onCheckStatus`.

**Variants and states.** 2/10 invalid needs acknowledgment then imports 8; 3/10 blocked; conflicts block; duplicates counted once; saving, failure (retry), unknown (check), success.

**Keyboard and screen reader.** Row errors are focusable targets for ErrorSummary; confirm is disabled-with-reason when blocked.

**Tokens.** Shared tokens.

**Responsive.** Counts wrap into a grid.

**Example.** energi-oktober.csv, 10 rows.

**Limits.** Never show success before confirmation or import twice after an unknown result.
