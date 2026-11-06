# ChoiceGroup

Radio, checkbox or native select for ordinary settings, with selection shown beyond colour.

**Anatomy.** Fieldset + legend · help · error · option rows (input, label, description, disabled reason).

**Consumer provides.** `type` radio | checkbox | select, `legend`, `options[{value,label,description,disabledReason}]`, `value`, `onChange`, `inline`, `optional`, `error`.

**Variants and states.** Unselected, selected (green fill + 3 px border + semibold + native mark), focus (ring around row), disabled-with-reason (dashed, reason text), error.

**Keyboard and screen reader.** Native inputs: arrows move within radios, Space toggles checkboxes. Disabled options use `disabled` and expose their reason via `aria-describedby`.

**Tokens.** `color-selection-*`, `color-border-control`, `size-border-selected`, `size-target-minimum`.

**Responsive.** Options stack; `inline` wraps.

**Example.** "Konteks penggunaan": Rumah tangga / Usaha / Industri (changes examples, not permissions).

**Limits.** Not a toggle for operating appliances.
