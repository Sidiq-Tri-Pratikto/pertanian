# HistoryChart

Aligned daily (or hourly) bars with current/reference distinguished beyond colour and real gaps hatched.

**Anatomy.** Heading · period/scope/unit · legend · scale note · plot · day labels + values · summary + gap note.

**Consumer provides.** `title`, `points[{label,current,reference}]`, `periodLabel`, `scopeLabel`, `unit`, `summary`, `gapNote`, `dense`.

**Variants and states.** Current only, current + reference, gap (null), measured zero (tick), dense 24-hour.

**Keyboard and screen reader.** Plot is `role=img` labelled by the heading and described by the summary; pair with `HD.ChartDataAlternative`.

**Tokens.** `color-chart-*`, `size-stroke-chart`, `size-chart-plotHeight`.

**Responsive.** Columns shrink; `dense` drops per-bar values.

**Example.** TV 3,920 vs 2,520 kWh; Kulkas 12 of 24 hours.

**Limits.** No smoothing, interpolation or inferred values for appearance; no hover-only values.
