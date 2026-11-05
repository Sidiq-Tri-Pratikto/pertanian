# Link

Navigation by descriptive text, including contextual change links.

**Anatomy.** Underlined text, optional hidden context, external-route icon with hidden note.

**Consumer provides.** `href`, `children`, `external`, `context` (hidden text naming the field), `onClick` (in-page handling).

**States.** Default, hover, focus.

**Keyboard and screen reader.** Native `<a>`. `context` makes "Ubah" read as "Ubah judul inovasi". External links announce "(membuka situs lain)".

**Tokens.** `tr-sys-color-link`.

**Responsive.** Wraps inside running text.

**Do.** Label an external route as an external route.

**Don't.** Do not imply that opening an external application submitted an in-app pitch.
