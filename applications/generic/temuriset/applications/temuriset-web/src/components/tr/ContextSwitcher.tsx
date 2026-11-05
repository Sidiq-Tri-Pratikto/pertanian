'use client';

import { Icon } from '@/components/tr/Icon';
import { Select } from '@/components/tr/Select';

export type ContextOption = { id: string; kind: 'personal' | 'organization'; name: string; disabledReason?: string };

const KIND = { personal: 'Pribadi', organization: 'Organisasi' } as const;

type ContextSwitcherProps = {
  value: string;
  options: ContextOption[];
  onChange?: (id: string) => void;
  /** Plain text before consequential actions: the selection is shown, not changed. */
  readOnly?: boolean;
  actionLabel?: string;
  label?: string;
  hint?: string;
  id?: string;
};

/** Port of TR.ContextSwitcher. A selection is never authority: the service checks membership on every request. */
export function ContextSwitcher({ value, options, onChange, readOnly, actionLabel, label, hint, id }: ContextSwitcherProps) {
  const current = options.find((option) => option.id === value) ?? options[0];
  if (readOnly) {
    return (
      <p className="tr-context">
        <Icon name={current.kind === 'organization' ? 'building' : 'user'} />
        <span>
          {`${actionLabel ?? 'Bertindak sebagai'}: `}
          <strong>{current.name}</strong>
          {` · ${KIND[current.kind]}`}
        </span>
      </p>
    );
  }
  return (
    <Select
      id={id}
      label={label ?? 'Bertindak sebagai'}
      hint={hint}
      value={value}
      emptyLabel={null}
      onChange={(next) => onChange?.(next)}
      options={options.map((option) => ({
        value: option.id,
        label: `${option.name} · ${KIND[option.kind]}`,
        disabledReason: option.disabledReason,
      }))}
    />
  );
}
