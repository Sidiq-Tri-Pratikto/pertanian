# ContributionRanking

Sorted horizontal bars on a zero baseline with direct labels and a visible denominator.

**Anatomy.** Heading · period + denominator · largest-among sentence · list of name, value · share, bar.

**Consumer provides.** `items[{name,kwh}]`, `periodLabel`, `denominatorLabel`, `title`.

**Variants and states.** Normal; zero total (no percentages, neutral notice).

**Keyboard and screen reader.** Ordered list; values are text, bars are `aria-hidden`.

**Tokens.** `color-chart-current`, `color-chart-track`, `color-chart-baseline`, `size-chart-barThickness`.

**Responsive.** Labels wrap above bars.

**Example.** Kulkas 8,400 kWh · 57,14% of 14,700 kWh selected devices.

**Limits.** Largest is not waste; no donut as the main ranking.
