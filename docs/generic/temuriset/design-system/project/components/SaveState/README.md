# SaveState

Says truthfully whether work is saved, and where.

**Anatomy.** Icon or spinner, label, recovery note and retry when failed.

**Consumer provides.** `state` local | saving | saved | failed | conflict, `location` demo | server, `savedAt`, `timeZone`, `onRetry`.

**States.** Belum tersimpan, Menyimpan, Tersimpan di demo ini, Gagal menyimpan, Versi sudah berubah.

**Keyboard and screen reader.** The label is `role="status"`, announced once per state and never per keystroke; focus does not move.

**Tokens.** `tr-sys-color-success-text`, `tr-sys-color-danger-text`, `tr-sys-color-warning-text`.

**Responsive.** Wraps; keep it beside the page heading.

**Do.** State the location. A demo says "Tersimpan di demo ini".

**Don't.** Do not draw a check before the save is acknowledged, or while offline.
