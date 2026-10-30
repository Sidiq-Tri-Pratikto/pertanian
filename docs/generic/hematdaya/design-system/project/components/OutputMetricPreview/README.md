# OutputMetricPreview

Optional energy-per-output intensity with explicit method; zero, missing or invalid output gives a reason, not infinity.

**Anatomy.** Label · value + unit · numerator ÷ denominator · method · qualifier.

**Consumer provides.** `enabled`, `energyKwh`, `output`, `unit`, `method` actual | estimated, `periodLabel`.

**Variants and states.** Actual (0,050 kWh/unit), estimated, zero output, missing, invalid; `enabled: false` renders nothing.

**Keyboard and screen reader.** Labelled section.

**Tokens.** Shared tokens.

**Responsive.** Wraps.

**Example.** 144,000 kWh ÷ 2.880 unit = 0,050 kWh/unit.

**Limits.** Hidden when not enabled; never a numeric intensity for zero output.
