# Screen

The app frame: acting context, navigation, title, next step, task and support.

**Anatomy.** Skip link, top bar with wordmark, provenance and context, heading, main column, supporting column, phone tab bar.

**Consumer provides.** `persona` inovator | mitra, `current`, `onNavigate(id)`, `title`, `subtitle`, `back`, `save`, `next`, `aside`, `context`, `provenance`, `children`.

**States.** Inovator or Investor/Mitra navigation; phone bar with Lainnya; static bar when large text would make it cover content.

**Keyboard and screen reader.** Skip link, `<main>`, labelled navigation, `aria-current="page"`.

**Tokens.** `tr-sys-layout-*`, `tr-sys-color-selected-*`.

**Responsive.** Below 48 rem a bar shows four destinations plus Lainnya and support stacks after the task. Above it, five top links and a 20 rem aside.

**Do.** Put the active task before the timeline and context in reading order.

**Don't.** Do not add a third persona or top-level pages for states.
