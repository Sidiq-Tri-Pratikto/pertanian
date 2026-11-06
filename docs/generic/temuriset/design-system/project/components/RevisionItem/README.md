# RevisionItem

One revision question, its reason, and an answer that may honestly be no.

**Anatomy.** Round and item heading, required flag, question, reason, due date, response, explanation, attachments, review result.

**Consumer provides.** `round`, `index`, `question`, `reason`, `required`, `due`, `value` {response, text}, `onChange(value)`, `attachments`, `review`, `error`, `id`.

**States.** Required, optional, answered, invalid, reviewed.

**Keyboard and screen reader.** Uses `TR.ChoiceGroup` and `TR.TextArea`.

**Tokens.** As its parts.

**Responsive.** One column.

**Do.** Keep each answer in place when one upload fails.

**Don't.** Do not treat "Perlu diskusi" or "Belum dapat dipenuhi" as approval or as an error.
