# FactSource

Whether a fact exists now, and how far it has been checked.

**Anatomy.** Value, timing tag, provenance tag, review scope, source link.

**Consumer provides.** `value`, `timing` CURRENT | PLANNED | REQUESTED, `provenance` SOURCE_REPORTED | SELF_DECLARED | PROVIDED | REVIEWED | UNKNOWN, `reviewScope`, `sourceHref`, `sourceLabel`.

**States.** Planned and requested tags use a dashed boundary. Only REVIEWED gets a success check.

**Keyboard and screen reader.** Text labels; the source link carries hidden context.

**Tokens.** `tr-sys-color-border-control`, `tr-sys-color-success-*`.

**Responsive.** Wraps.

**Do.** Put it next to the claim it qualifies.

**Don't.** Do not let a source link reveal a protected title. An upload is not a review.
