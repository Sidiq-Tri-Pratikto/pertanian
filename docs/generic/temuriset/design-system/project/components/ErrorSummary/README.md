# ErrorSummary

Focused list of what stopped a submission, linking to each field.

**Anatomy.** Focusable region, heading, linked list, optional retry.

**Consumer provides.** `errors` [{fieldId, message}], `focusKey` (change it on each failed attempt), `title`, `children`, `retry` {label, onClick}, `id`.

**States.** Field errors; global retry without a field target.

**Keyboard and screen reader.** Focus moves to the region only when `focusKey` changes, so a background save never steals focus. Each link focuses its field.

**Tokens.** `tr-sys-color-danger-*`, `tr-sys-size-borderSelected`.

**Responsive.** Full width at the top of the task.

**Do.** Repeat the words of the inline errors.

**Don't.** Do not replace it with a disappearing toast.
