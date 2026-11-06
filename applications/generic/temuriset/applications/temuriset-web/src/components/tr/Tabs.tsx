'use client';

import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react';

type Tab = { id: string; label: string; content: ReactNode };

type TabsProps = { label: string; tabs: Tab[]; value: string; onChange: (id: string) => void };

/** Port of TR.Tabs: ARIA tabs with automatic activation; arrows, Home and End move, Tab moves to the panel. */
export function Tabs({ label, tabs, value, onChange }: TabsProps) {
  const auto = useId();
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  function key(event: KeyboardEvent, index: number) {
    const count = tabs.length;
    const to = ({ ArrowRight: (index + 1) % count, ArrowLeft: (index - 1 + count) % count, Home: 0, End: count - 1 } as Record<string, number>)[event.key];
    if (to === undefined) return;
    event.preventDefault();
    onChange(tabs[to].id);
    refs.current[tabs[to].id]?.focus();
  }
  return (
    <div className="tr-tabs">
      <div role="tablist" aria-label={label} className="tr-tabs__list">
        {tabs.map((tab, index) => {
          const on = tab.id === value;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`${auto}${tab.id}`}
              ref={(element) => {
                refs.current[tab.id] = element;
              }}
              aria-selected={on}
              aria-controls={`${auto}${tab.id}p`}
              tabIndex={on ? 0 : -1}
              className={on ? 'tr-tab tr-sys-type-label is-selected' : 'tr-tab tr-sys-type-label'}
              onClick={() => onChange(tab.id)}
              onKeyDown={(event) => key(event, index)}>
              {tab.label}
            </button>
          );
        })}
      </div>
      {tabs.map((tab) => (
        <div key={tab.id} role="tabpanel" id={`${auto}${tab.id}p`} aria-labelledby={`${auto}${tab.id}`} tabIndex={0} hidden={tab.id !== value} className="tr-tabs__panel">
          {tab.id === value ? tab.content : null}
        </div>
      ))}
    </div>
  );
}
