'use client';

import { useRouter } from 'next/navigation';
import { useState, type ReactNode } from 'react';

import { Tabs } from '@/components/tr/Tabs';
import { TABS, type TabId } from '@/features/pitches/workspace';

type Props = { pitchId: string; value: TabId; panels: Record<TabId, ReactNode> };

/** S13 tabs, kept in the address (`?tab=`) so Back and a shared link land on the same view. */
export function WorkspaceTabs({ pitchId, value, panels }: Props) {
  const router = useRouter();
  const [current, setCurrent] = useState<TabId>(value);
  const [shown, setShown] = useState<TabId>(value);
  // Back and Forward change the address; follow it without an effect.
  if (value !== shown) {
    setShown(value);
    setCurrent(value);
  }
  return (
    <Tabs
      label="Ruang pitching"
      value={current}
      tabs={TABS.map((tab) => ({ id: tab.id, label: tab.label, content: panels[tab.id] }))}
      onChange={(id) => {
        setCurrent(id as TabId);
        router.push(`/pitches/${pitchId}?tab=${id}`, { scroll: false });
      }}
    />
  );
}
