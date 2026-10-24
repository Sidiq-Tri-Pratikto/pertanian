# ScopeSummary

What is in the measured scope, what is excluded, and how parent/child or unknown overlaps are resolved without adding.

**Anatomy.** Scope line · exclusions · overlap notice · view choice or individual values · included list (disclosure).

**Consumer provides.** `included`, `excluded`, `count`, `unitLabel`, `overlap` none | parentChild | unknown, `parent`, `child`, `view`, `onViewChange`, `values`.

**Variants and states.** Plain scope; parent/child (choose Meteran Utama 10 or Kulkas 1); unknown overlap (no combined total).

**Keyboard and screen reader.** Uses ChoiceGroup and Notice semantics.

**Tokens.** Inherits Notice/ChoiceGroup tokens.

**Responsive.** Stacks.

**Example.** Main meter 10 kWh includes refrigerator 1 kWh: show 10 or 1, never 11.

**Limits.** Do not render a sum when overlap is unknown.
