# NextStep

Tells a person whose turn it is and the one thing to do now.

**Anatomy.** Responsibility label, heading, reason, optional due date, one action.

**Consumer provides.** `who` you | other, `title`, `children`, `due`, `action`.

**States.** Menunggu Anda (selected surface, 2 px boundary), Menunggu pihak lain (plain surface, no action needed).

**Keyboard and screen reader.** Section labelled by its heading. Responsibility is in words.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.

**Responsive.** Full width at the top of the task, before supporting detail.

**Do.** Open every workspace with it. Write one sentence and one effect-named action.

**Don't.** Do not stack several next steps. When it waits on someone else, say so and ask for nothing.
