# ScheduleWindows

Optional weekly schedule: none, explicit 24 hours, inherit from site, or custom windows including overnight.

**Anatomy.** Mode choice · window list.

**Consumer provides.** `mode`, `onModeChange`, `inheritLabel`, `windows[{days,start,end,nextDay}]`.

**Variants and states.** No schedule, continuous, inherit (disabled with reason when site has none), windows, empty windows.

**Keyboard and screen reader.** ChoiceGroup semantics.

**Tokens.** Shared tokens.

**Responsive.** Stacks.

**Example.** Senin–Jumat 07.00–17.00; Senin–Sabtu 22.00–06.00 (berakhir hari berikutnya).

**Limits.** Optional; the core never depends on it.
