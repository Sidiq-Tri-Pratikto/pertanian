import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

export type ContextPreset = 'household' | 'business' | 'industry' | 'unspecified';

export const CONTEXT_OPTIONS: { value: ContextPreset; label: string }[] = [
  { value: 'household', label: 'Rumah tangga' },
  { value: 'business', label: 'Usaha' },
  { value: 'industry', label: 'Industri' },
  { value: 'unspecified', label: 'Belum memilih' },
];

/** The preset changes examples only. It never changes data, permissions, calculations or schedules. */
export const CONTEXT_EXAMPLES: Record<ContextPreset, string> = {
  household: 'Misalnya kulkas, router, atau pompa air.',
  business: 'Misalnya lampu toko, pendingin, atau komputer kasir.',
  industry: 'Misalnya oven, kompresor, atau mesin press.',
  unspecified: 'Misalnya perangkat, sirkuit, atau meter lokasi.',
};

type ContextPresetValue = { preset: ContextPreset; setPreset: (preset: ContextPreset) => void };

const PresetContext = createContext<ContextPresetValue>({ preset: 'unspecified', setPreset: () => undefined });

export function ContextPresetProvider({ children }: { children: ReactNode }) {
  const [preset, setPreset] = useState<ContextPreset>('unspecified');
  const value = useMemo(() => ({ preset, setPreset }), [preset]);
  return <PresetContext.Provider value={value}>{children}</PresetContext.Provider>;
}

export function useContextPreset() {
  return useContext(PresetContext);
}
