# NumericField

Decimal-comma number input with unit, explicit empty-versus-zero meaning and no silent conversion.

**Anatomy.** Label · help · error · input + unit suffix · interpretation note.

**Consumer provides.** `label`, `value` (raw text), `onChange(text, parsed)`, `unit`, `allowNegative`, `max`, `required` | `optional`, `showErrors`, `error`, `note`.

**Variants and states.** Empty ("Kosong — belum diisi, tidak dianggap 0."), zero ("Tercatat 0 sebagai nilai yang diisi."), valid (`1.500` = 1500, `0,25`), invalid (`1.5` asks for a comma), negative rejected unless allowed.

**Keyboard and screen reader.** `inputmode=decimal`; unit is in `aria-describedby`; parse errors show after blur or when `showErrors`.

**Tokens.** Same as TextField plus `color-background-subtle` for the unit.

**Responsive.** Unit stays attached to the input at every width.

**Example.** "Tarif listrik" in Rp/kWh; "Output produksi" in unit.

**Limits.** Never turn empty into 0; never guess a dot decimal. Use `HD.format.parseDecimal` for the canonical value.
