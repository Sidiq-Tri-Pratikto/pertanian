import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { ContextPresetProvider } from '@/features/context-preset';
import { ImportDraftProvider } from '@/features/imports/ImportDraftProvider';
import { NavigationContextProvider } from '@/features/navigation-context/NavigationContextProvider';
import { installConnectivity } from '@/features/offline/useConnectivity';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'web') {
      document.documentElement.lang = 'id';
    }
  }, []);

  useEffect(installConnectivity, []);

  return (
    <WorkspaceProvider>
      <NavigationContextProvider>
        <ImportDraftProvider>
          <ContextPresetProvider>
            <Stack screenOptions={{ headerShown: false }} />
          </ContextPresetProvider>
        </ImportDraftProvider>
      </NavigationContextProvider>
    </WorkspaceProvider>
  );
}
