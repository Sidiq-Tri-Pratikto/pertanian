import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { ContextPresetProvider } from '@/features/context-preset';

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'web') {
      document.documentElement.lang = 'id';
    }
  }, []);

  return (
    <ContextPresetProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </ContextPresetProvider>
  );
}
