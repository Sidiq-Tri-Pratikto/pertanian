import { TabList, TabSlot, Tabs, TabTrigger } from 'expo-router/ui';

import { HDTabBar, HDTabItem } from '@/components/hd/HDTabBar';
import { useLabels } from '@/features/localization/messages';

/** Exactly three destinations. Everything else is a secondary route inside a tab. */
export default function TabsLayout() {
  const labels = useLabels();
  return (
    <Tabs>
      <TabSlot />
      <TabList asChild>
        <HDTabBar>
          <TabTrigger name="(beranda)" href="/beranda" asChild>
            <HDTabItem icon="home" label={labels.home} />
          </TabTrigger>
          <TabTrigger name="(perangkat)" href="/perangkat" asChild>
            <HDTabItem icon="devices" label={labels.devices} />
          </TabTrigger>
          <TabTrigger name="(saran)" href="/saran" asChild>
            <HDTabItem icon="saran" label={labels.insights} />
          </TabTrigger>
        </HDTabBar>
      </TabList>
    </Tabs>
  );
}
