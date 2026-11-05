import type { ReactNode } from 'react';

type Choice = { value: string; label: string; hint?: string };

type ChoiceGroupProps = {
  legend: ReactNode;
  /** Form field name; option ids derive from it. */
  name: string;
  options: Choice[];
  defaultValue?: string;
  hint?: string;
  required?: boolean;
};

/**
 * Port of TR.ChoiceGroup for uncontrolled forms, so a server action receives the value without JavaScript.
 * Selection styling comes from `:has(:checked)` in `src/design/app.css`, which mirrors `.is-selected`.
 */
export function ChoiceGroup({ legend, name, options, defaultValue, hint, required }: ChoiceGroupProps) {
  const hintId = `${name}-hint`;
  return (
    <fieldset className="tr-fieldset" aria-describedby={hint ? hintId : undefined}>
      <legend className="tr-field__label tr-sys-type-label">
        {legend}
        {required ? <span className="tr-field__req tr-sys-type-support"> (wajib)</span> : null}
      </legend>
      {hint ? (
        <p id={hintId} className="tr-field__hint tr-sys-type-support">
          {hint}
        </p>
      ) : null}
      <div className="tr-choices">
        {options.map((option) => {
          const id = `${name}-${option.value}`;
          return (
            <label key={option.value} htmlFor={id} className="tr-choice">
              <input type="radio" id={id} name={name} value={option.value} defaultChecked={option.value === defaultValue} required={required} />
              <span className="tr-choice__body">
                <span className="tr-sys-type-label">{option.label}</span>
                {option.hint ? <span className="tr-choice__hint tr-sys-type-support">{option.hint}</span> : null}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
