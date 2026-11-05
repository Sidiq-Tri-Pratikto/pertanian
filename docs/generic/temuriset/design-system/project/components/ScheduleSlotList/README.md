# ScheduleSlotList

Proposed times in a person's own zone; a selection is not a booking.

**Anatomy.** Agenda, slot radios with date, time, zone and duration, the other party's time, actions.

**Consumer provides.** `slots` [{id, start (UTC ISO), minutes, conflict}], `zone`, `otherZone`, `selectedId`, `onSelect(id)`, `confirmedId`, `state` open | expired | superseded | cancelled, `onConfirm`, `onPropose`, `busy`, `agenda`, `error`.

**States.** Open, selected (not confirmed), confirmed, conflict, expired, superseded, cancelled.

**Keyboard and screen reader.** Native radios. Each slot reads full date, time and zone.

**Tokens.** `tr-sys-color-selected-*`, Status tones.

**Responsive.** One column; long dates wrap.

**Do.** Show the IANA-derived zone label and both parties' times.

**Don't.** Do not say booked until acceptance succeeds on the server.
