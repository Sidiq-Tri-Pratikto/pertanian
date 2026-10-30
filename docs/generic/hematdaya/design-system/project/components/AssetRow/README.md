# AssetRow

One measured asset, circuit, group or meter as a single row link with energy and quality.

**Anatomy.** Name (wraps) · kind · location · quality qualifier · value · chevron.

**Consumer provides.** `name`, `kind` device | circuit | group | meter, `location`, `kwh`, `quality`, `href` or `onOpen`.

**Variants and states.** Complete, partial, stale, unavailable ("— kWh").

**Keyboard and screen reader.** The whole row is one `<a>`; no nested buttons.

**Tokens.** `color-background-surface`, `color-border-decorative`, `size-target-minimum`.

**Responsive.** Name wraps; value stays right.

**Example.** "Pompa Air Area Produksi Belakang" · Perangkat · Area Belakang.

**Limits.** No inline switches or secondary buttons.
