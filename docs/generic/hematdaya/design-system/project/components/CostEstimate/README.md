# CostEstimate

Qualified energy-cost estimate from an optional tariff; missing tariff is unknown, not Rp0.

**Anatomy.** Label · value · tariff × energy line · qualifiers · bill limitation · optional Atur tarif.

**Consumer provides.** `kwh`, `tariff` (null | 0 | number per kWh), `tariffSource` synthetic | user, `partial`, `onSetTariff`.

**Variants and states.** Known (Rp22.050), missing tariff, explicit zero tariff, partial energy, no energy.

**Keyboard and screen reader.** Labelled section; plain text.

**Tokens.** `type-title`, `color-text-*`.

**Responsive.** Wraps.

**Example.** 14,700 kWh × Rp1.500 = Rp22.050 (computed unrounded, rounded once).

**Limits.** Not a utility bill; never compute from a displayed, rounded number.
