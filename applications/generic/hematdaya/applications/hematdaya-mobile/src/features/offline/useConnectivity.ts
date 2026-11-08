import NetInfo from '@react-native-community/netinfo';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { useSyncExternalStore } from 'react';
import { AppState, Platform } from 'react-native';

export type Connectivity = 'unknown' | 'online' | 'offline';

let connectivity: Connectivity = 'unknown';
const listeners = new Set<() => void>();

export function connectivityFromNative({ isConnected, isInternetReachable }: {
  isConnected: boolean | null;
  isInternetReachable: boolean | null;
}): Connectivity {
  if (isConnected === false) return 'offline';
  // Public internet validation cannot tell whether the local API is reachable.
  return isConnected === true && isInternetReachable !== false ? 'online' : 'unknown';
}

function update(value: Connectivity) {
  connectivity = value;
  onlineManager.setOnline(value !== 'offline');
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** Both the UI and fetch boundary use the live state, including a browser event pending delivery. */
export function isKnownOffline(): boolean {
  return connectivity === 'offline' || !onlineManager.isOnline() || globalThis.navigator?.onLine === false;
}

export function useConnectivity(): Connectivity {
  return useSyncExternalStore(subscribe, () => connectivity, () => 'unknown');
}

/** Install once at the app root. Unknown reachability permits a bounded request. */
export function installConnectivity(): () => void {
  if (Platform.OS === 'web') {
    const online = () => update(globalThis.navigator?.onLine === false ? 'offline' : 'online');
    online();
    globalThis.addEventListener?.('online', online);
    globalThis.addEventListener?.('offline', online);
    return () => {
      globalThis.removeEventListener?.('online', online);
      globalThis.removeEventListener?.('offline', online);
    };
  }

  update('unknown');
  const stop = NetInfo.addEventListener((state) => update(connectivityFromNative(state)));
  const foreground = AppState.addEventListener('change', (state) => {
    focusManager.setFocused(state === 'active');
    if (state === 'active') void NetInfo.refresh().catch(() => undefined);
  });
  return () => {
    stop();
    foreground.remove();
    focusManager.setFocused(undefined);
  };
}
