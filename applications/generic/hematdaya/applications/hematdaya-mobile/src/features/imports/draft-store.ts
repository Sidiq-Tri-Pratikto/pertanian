import { Platform } from 'react-native';

import type { ImportAnswers, ImportSource } from '@/api/client';
import { ownerStorageKey } from '@/features/offline/owner-storage';

/** A web-only recovery record for a commit that was actually dispatched. */
export type CommitIntent = { importId: string; key: string; acknowledge: boolean };
export type StoredSource = { kind: 'file'; name: string } | { kind: 'paste'; text: string };
export type DraftSnapshot = {
  source: ImportSource | StoredSource | null;
  answers: ImportAnswers;
  intervalText: Record<string, string>;
  importId: string | null;
  textDropped?: boolean;
  legacyHandled?: boolean;
};

export type LoadedDraft = Omit<DraftSnapshot, 'source'> & {
  source: StoredSource | null;
  needsReselect: boolean;
};

const LEGACY_KEY = 'hematdaya.import-draft.v1';
const MAX_PASTE = 512_000;

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function reference(value: unknown): value is string {
  return typeof value === 'string' && /^[\w-]{1,100}$/.test(value);
}

function isIntent(value: unknown): value is CommitIntent {
  return record(value) && reference(value.importId) && reference(value.key) && typeof value.acknowledge === 'boolean';
}

function smallMap<T>(value: unknown, accept: (item: unknown) => item is T): Record<string, T> {
  if (!record(value)) return {};
  return Object.fromEntries(Object.entries(value).slice(0, 100).flatMap(([key, item]) =>
    key.length <= 200 && accept(item) ? [[key, item] as const] : []));
}

function answers(value: unknown): ImportAnswers {
  if (!record(value)) return {};
  const { value_kind, power_meaning, timezone_confirmed, interval_minutes, asset_map, scope } = value;
  return {
    ...(value_kind === 'interval_energy' || value_kind === 'average_power' || value_kind === 'counter' ? { value_kind } : {}),
    ...(power_meaning === 'average' || power_meaning === 'instantaneous' ? { power_meaning } : {}),
    ...(typeof timezone_confirmed === 'boolean' ? { timezone_confirmed } : {}),
    ...(record(interval_minutes) ? { interval_minutes: smallMap(interval_minutes, (item): item is number =>
      typeof item === 'number' && Number.isSafeInteger(item) && item > 0 && item <= 1440) } : {}),
    ...(record(asset_map) ? { asset_map: smallMap(asset_map, reference) } : {}),
    ...(scope === 'disjoint' || scope === 'unknown_overlap' ? { scope } : {}),
  };
}

function projection(value: Record<string, unknown>): LoadedDraft {
  const item = record(value.source) ? value.source : null;
  const paste = item?.kind === 'paste' && typeof item.text === 'string' ? item.text : null;
  const name = item?.kind === 'file' && typeof item.name === 'string' ? item.name.slice(0, 200) : null;
  const source: StoredSource | null = name ? { kind: 'file', name } :
    paste && paste.length <= MAX_PASTE ? { kind: 'paste', text: paste } : null;
  return {
    source, needsReselect: source?.kind === 'file',
    answers: answers(value.answers),
    intervalText: smallMap(value.intervalText, (item): item is string => typeof item === 'string' && item.length <= 40),
    importId: reference(value.importId) ? value.importId : null,
    textDropped: value.textDropped === true || (paste !== null && paste.length > MAX_PASTE),
    legacyHandled: value.legacyHandled === true,
  };
}

function parse(raw: string | null): unknown {
  try {
    return raw && raw.length <= 11_000_000 ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function readDraft(raw: string | null): LoadedDraft | null {
  const value = parse(raw);
  return record(value) && value.version === 1 ? projection(value) : null;
}

/** The general draft contains only bounded input and a preview reference. */
export function storeDraft(value: DraftSnapshot, omitPaste = false): string {
  let { source } = value;
  if (source?.kind === 'file' && 'file' in source) source = { kind: 'file', name: source.file.name };
  const clean = projection({ ...value, source });
  if (omitPaste && clean.source?.kind === 'paste') {
    clean.source = null;
    clean.textDropped = true;
  }
  return JSON.stringify({ version: 1, ...clean });
}

export function loadLegacyDraft(siteId: string): { draft: LoadedDraft; intent: CommitIntent | null } | null {
  try {
    if (Platform.OS !== 'web') return null;
    const value = parse(globalThis.sessionStorage.getItem(LEGACY_KEY));
    if (!record(value) || value.siteId !== siteId) return null;
    const draft = projection(value);
    const intent = isIntent(value.intent) && value.intent.importId === draft.importId ? value.intent : null;
    if (value.intent !== null && !intent) return null;
    return { draft, intent };
  } catch {
    return null;
  }
}

export function clearLegacyDraft(): void {
  try {
    globalThis.sessionStorage.removeItem(LEGACY_KEY);
  } catch {
    // A durable migration marker prevents the legacy input from being adopted again.
  }
}

export function readRecovery(epoch: string): CommitIntent | null {
  try {
    if (Platform.OS !== 'web') return null;
    const value = parse(globalThis.sessionStorage.getItem(ownerStorageKey(epoch, 'import-recovery')));
    return record(value) && value.version === 1 && isIntent(value.intent) ? value.intent : null;
  } catch {
    return null;
  }
}

/** Invoked synchronously at dispatch so an offline tap cannot create a recovery intent. */
export function writeRecovery(epoch: string, intent: CommitIntent | null): boolean {
  if (Platform.OS !== 'web') return true;
  try {
    const key = ownerStorageKey(epoch, 'import-recovery');
    if (intent) globalThis.sessionStorage.setItem(key, JSON.stringify({ version: 1, intent }));
    else globalThis.sessionStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}
