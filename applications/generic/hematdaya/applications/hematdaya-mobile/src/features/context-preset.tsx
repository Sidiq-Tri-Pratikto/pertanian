import { currentCopy } from '@/features/localization/messages';
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

export type ContextPreset = 'household' | 'business' | 'industry' | 'unspecified';

export function contextOptions(): { value: ContextPreset; label: string }[] {
  return [
    { value: 'household', label: currentCopy('Rumah tangga', 'Household') },
    { value: 'business', label: currentCopy('Usaha', 'Business') },
    { value: 'industry', label: currentCopy('Industri', 'Industrial') },
    { value: 'unspecified', label: currentCopy('Belum memilih', 'No preference') },
  ];
}

/** The preset changes examples only. It never changes data, permissions, calculations or schedules. */
export function contextExample(preset: ContextPreset): string {
  return {
    household: currentCopy('Misalnya kulkas, router, atau pompa air.', 'Examples: fridge, router or water pump.'),
    business: currentCopy('Misalnya lampu toko, pendingin, atau komputer kasir.', 'Examples: shop lighting, refrigeration or checkout computer.'),
    industry: currentCopy('Misalnya oven, kompresor, atau mesin press.', 'Examples: oven, compressor or press.'),
    unspecified: currentCopy('Misalnya perangkat, sirkuit, atau meter lokasi.', 'Examples: device, circuit or site meter.'),
  }[preset];
}

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
