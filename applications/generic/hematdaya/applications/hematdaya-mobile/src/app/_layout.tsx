import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { ContextPresetProvider } from '@/features/context-preset';
import { NavigationContextProvider } from '@/features/navigation-context/NavigationContextProvider';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'web') {
      document.documentElement.lang = 'id';
    }
  }, []);

  return (
    <WorkspaceProvider>
      <NavigationContextProvider>
        <ContextPresetProvider>
          <Stack screenOptions={{ headerShown: false }} />
        </ContextPresetProvider>
      </NavigationContextProvider>
    </WorkspaceProvider>
  );
}
