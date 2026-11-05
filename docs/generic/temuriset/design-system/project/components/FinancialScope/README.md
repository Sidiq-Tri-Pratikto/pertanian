# FinancialScope

An amount that always says what it is an amount of.

**Anatomy.** Subject, amount with unit, period, scope, estimate date, assumptions, optional fields.

**Consumer provides.** `subject` project | companyTarget | contribution | investorCheck | partner | license, `currency`, `min`, `max` (decimal strings; null means unknown), `period`, `scope`, `estimateDate`, `assumptions`, `noncash`, `terms`, `compact`, `edit`, `label`.

**States.** Range, single value, unknown ("Belum ditentukan"), noncash.

**Keyboard and screen reader.** Text only. Amount and unit never split across lines.

**Tokens.** `tr-sys-type-amount`, `tr-sys-color-surface-subtle`.

**Responsive.** Amount stays together; the period wraps to the next line.

**Do.** Keep duration beside the range. Compare only like with like.

**Don't.** Do not convert currency, show funding progress or percentages, or render unknown as zero.
