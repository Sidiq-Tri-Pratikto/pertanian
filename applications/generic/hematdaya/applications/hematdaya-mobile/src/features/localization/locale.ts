import AsyncStorage from '@react-native-async-storage/async-storage';
import { useSyncExternalStore } from 'react';

export type Locale = 'id' | 'en';

const KEY = 'hematdaya.locale.v1';
const listeners = new Set<() => void>();
let locale: Locale = 'id';
let changed = false;
let writes: Promise<void> = Promise.resolve();

export function getLocale(): Locale {
  return locale;
}

function publish(next: Locale) {
  if (locale === next) return;
  locale = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export async function restoreLocale(): Promise<void> {
  const saved = await AsyncStorage.getItem(KEY).catch(() => null);
  if (!changed) publish(saved === 'en' ? 'en' : 'id');
}

export function setLocale(next: Locale): Promise<void> {
  changed = true;
  publish(next);
  // Keep storage in selection order when the user changes language twice quickly.
  writes = writes.then(() => AsyncStorage.setItem(KEY, next)).catch(() => undefined);
  return writes;
}

export function useLocale(): Locale {
  return useSyncExternalStore(subscribe, getLocale, getLocale);
}
