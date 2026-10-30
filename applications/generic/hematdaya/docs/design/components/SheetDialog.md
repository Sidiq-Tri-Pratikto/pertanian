# SheetDialog

Non-destructive modal sheet (bottom sheet on phones, centred dialog from 768 px) with focus placement, containment and return.

**Anatomy.** Backdrop · sheet · header (title, Tutup) · body · footer actions.

**Consumer provides.** `open`, `title`, `onClose(reason)`, `children`, `footer`.

**Variants and states.** Closed, open, draft present, error inside.

**Keyboard and screen reader.** Native `<dialog>` `showModal()`: background inert, Tab contained, Escape → `onClose('escape')`. Focus goes to the title (or `[data-autofocus]`) and returns to the opener on close.

**Tokens.** `shadow-overlay`, `color-overlay-backdrop`, `radius-sheet`, `size-sheet-maxWidth`, `duration-overlay`.

**Responsive.** Full width at the bottom below 768 px; 560 px centred above; footer respects safe area.

**Example.** "Atur tarif": Escape/Tutup/Batal close without saving, the typed draft stays until Simpan or Buang draf.

**Limits.** Not for destructive confirmation copy without a clear cancel. `::backdrop` reads the token only in browsers where it inherits custom properties.
