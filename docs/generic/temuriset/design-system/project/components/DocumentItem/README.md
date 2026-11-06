# DocumentItem

A document with file safety, text reading, evidence review and sharing kept apart.

**Anatomy.** Title, version, three independent status axes, sharing sentence, action.

**Consumer provides.** `title`, `version`, `file`, `extraction`, `review`, `grant` {recipient, version, revoked}, `denied`, `action`.

**States.** Every combination of the three axes; denied (no title shown); revoked with its truthful limit.

**Keyboard and screen reader.** `<dl>` of axis names and results. Each result is text.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** Axes form one column on phones.

**Do.** Say the sharing limit: one named recipient, one version.

**Don't.** Do not let an upload imply review, or a quarantined file open. Never show a protected title to someone without access.
