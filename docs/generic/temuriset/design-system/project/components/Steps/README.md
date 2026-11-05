# Steps

Progress through a fixed-order editor.

**Anatomy.** Current step sentence, ordered list with marks.

**Consumer provides.** `steps` [{id, label, done}], `current`, `onSelect(id)`, `label`.

**States.** Done (check plus hidden text), current (filled mark, `aria-current="step"`), to do.

**Keyboard and screen reader.** Navigation landmark with an ordered list. Other steps are buttons when `onSelect` is given.

**Tokens.** `tr-sys-color-action-primary-*`, `tr-sys-color-selected-*`.

**Responsive.** Grid wraps to one column on narrow screens; the sentence always names the current step.

**Do.** Allow jumping back without losing input.

**Don't.** Do not use it for resumable unordered work; that is a task list.
