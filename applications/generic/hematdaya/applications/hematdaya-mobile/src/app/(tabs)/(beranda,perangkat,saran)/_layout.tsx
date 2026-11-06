import { Stack } from 'expo-router';

// Each tab keeps its own stack. Shared detail routes live here so the tab bar stays visible and back stays in the tab.
export const unstable_settings = {
  beranda: { anchor: 'beranda' },
  perangkat: { anchor: 'perangkat' },
  saran: { anchor: 'saran' },
};

export default function TabStackLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
