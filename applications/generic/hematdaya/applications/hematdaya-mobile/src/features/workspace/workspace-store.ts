import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export type Period = { preset: string; start_date: string; end_date: string };

/** What the device holds for one workspace. The token is the user's only key to it. */
export type Workspace = {
  token: string;
  siteId: string;
  scenarioId: string;
  expiresAt: string;
  initialPeriod: Period;
};

const KEY = 'hematdaya.workspace.v1';

function isWorkspace(value: unknown): value is Workspace {
  const candidate = value as Partial<Workspace> | null;
  return (
    typeof candidate?.token === 'string' &&
    typeof candidate.siteId === 'string' &&
    typeof candidate.scenarioId === 'string' &&
    typeof candidate.expiresAt === 'string' &&
    typeof candidate.initialPeriod?.start_date === 'string'
  );
}

/** Secure storage on native. The web has no secure store, so a demo token lives in `sessionStorage` until 036. */
async function read(): Promise<string | null> {
  if (Platform.OS === 'web') {
    return globalThis.sessionStorage?.getItem(KEY) ?? null;
  }
  return SecureStore.getItemAsync(KEY);
}

export async function loadWorkspace(): Promise<Workspace | null> {
  try {
    const stored = await read();
    const parsed: unknown = stored ? JSON.parse(stored) : null;
    return isWorkspace(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export async function saveWorkspace(workspace: Workspace): Promise<void> {
  const value = JSON.stringify(workspace);
  if (Platform.OS === 'web') {
    globalThis.sessionStorage?.setItem(KEY, value);
  } else {
    await SecureStore.setItemAsync(KEY, value);
  }
}

export async function clearWorkspace(): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.sessionStorage?.removeItem(KEY);
  } else {
    await SecureStore.deleteItemAsync(KEY);
  }
}
