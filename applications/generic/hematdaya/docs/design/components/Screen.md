# Screen

Intentional addition: the shared screen frame so pattern assemblies are compositions, not unnamed copies.

**Anatomy.** Top bar (wordmark or back + provenance tag) · title + subtitle · main column · optional aside · sticky TabNavigation.

**Consumer provides.** `title`, `subtitle`, `children`, `aside`, `current`, `onNavigate`, `back`, `provenance`.

**Variants and states.** With/without aside, with back.

**Keyboard and screen reader.** `<main>` labelled by the `h1`; aside labelled.

**Tokens.** `space-page-gutter*`, `size-content-*`, `space-section-gap`.

**Responsive.** One column below 768 px; main + aside above.

**Example.** Beranda · Rumah Bandung · Asia/Jakarta.

**Limits.** Not an app router or shell framework.
