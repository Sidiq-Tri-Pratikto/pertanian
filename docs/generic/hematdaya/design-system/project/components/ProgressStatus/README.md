# ProgressStatus

Inspectable state of loading or saving, including unknown result, with retry or check — never premature success.

**Anatomy.** Spinner or icon · label · detail · action.

**Consumer provides.** `state` null | loading | saving | unknown | success | failure, `label`, `detail`, `onRetry`, `onCheck`, `checking`.

**Variants and states.** Loading, saving, unknown ("Status penyimpanan belum diketahui" + Periksa status), success (after server confirmation), failure ("Gagal menyimpan" + Coba lagi).

**Keyboard and screen reader.** Always-mounted `role=status` polite region; never moves focus.

**Tokens.** `color-status-*`, `duration-progressCycle`.

**Responsive.** Full width.

**Example.** Unknown → check finds the first save → success, not saved twice.

**Limits.** Do not resend automatically after an unknown result.
