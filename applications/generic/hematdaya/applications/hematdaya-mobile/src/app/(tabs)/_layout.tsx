import { TabList, TabSlot, Tabs, TabTrigger } from 'expo-router/ui';

import { HDTabBar, HDTabItem } from '@/components/hd/HDTabBar';

/** Exactly three destinations. Everything else is a secondary route inside a tab. */
export default function TabsLayout() {
  return (
    <Tabs>
      <TabSlot />
      <TabList asChild>
        <HDTabBar>
          <TabTrigger name="(beranda)" href="/beranda" asChild>
            <HDTabItem icon="home" label="Beranda" />
          </TabTrigger>
          <TabTrigger name="(perangkat)" href="/perangkat" asChild>
            <HDTabItem icon="devices" label="Perangkat" />
          </TabTrigger>
          <TabTrigger name="(saran)" href="/saran" asChild>
            <HDTabItem icon="saran" label="Saran" />
          </TabTrigger>
        </HDTabBar>
      </TabList>
    </Tabs>
  );
}
