import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { Platform, TurboModuleRegistry } from 'react-native';

import { ContextPresetProvider } from '@/features/context-preset';
import { ImportDraftProvider } from '@/features/imports/ImportDraftProvider';
import { NavigationContextProvider } from '@/features/navigation-context/NavigationContextProvider';
import { WorkspaceProvider } from '@/features/workspace/WorkspaceProvider';

// M0 evidence only. The Android smoke job must fail and capture this missing native module.
if (Platform.OS === 'android') {
  TurboModuleRegistry.getEnforcing('HematDayaMissingModule');
}

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'web') {
      document.documentElement.lang = 'id';
    }
  }, []);

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
