import { Platform } from 'react-native';

import type { ImportAnswers, ImportSource } from '@/api/client';

/** One commit intent. A resend keeps all three, so the service replays the first result (027 D5). */
export type CommitIntent = { importId: string; key: string; acknowledge: boolean };

/** What a reload can bring back: a file by its name only, since a browser cannot give its bytes back. */
export type StoredSource = { kind: 'file'; name: string } | { kind: 'paste'; text: string };

export type DraftSnapshot = {
  siteId: string;
  source: ImportSource | StoredSource | null;
  answers: ImportAnswers;
  intervalText: Record<string, string>;
  importId: string | null;
  intent: CommitIntent | null;
};

export type LoadedDraft = Omit<DraftSnapshot, 'source'> & {
  source: StoredSource | null;
  /** A file was chosen before the reload and must be picked again before its bytes are needed. */
  needsReselect: boolean;
  /** The paste did not fit the browser's storage and must be pasted again. */
  textDropped: boolean;
};

const KEY = 'hematdaya.import-draft.v1';

type Stored = Omit<DraftSnapshot, 'source'> & { source: StoredSource | null; textDropped: boolean };

function storedSource(source: DraftSnapshot['source']): StoredSource | null {
  if (!source) {
    return null;
  }
  if (source.kind === 'paste') {
    return { kind: 'paste', text: source.text };
  }
  return { kind: 'file', name: 'file' in source ? source.file.name : source.name };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isStoredSource(value: unknown): value is StoredSource | null {
  return (
    value === null ||
    (isRecord(value) && ((value.kind === 'file' && typeof value.name === 'string') || (value.kind === 'paste' && typeof value.text === 'string')))
  );
}

function isIntent(value: unknown): value is CommitIntent | null {
  return (
    value === null ||
    (isRecord(value) && typeof value.importId === 'string' && typeof value.key === 'string' && typeof value.acknowledge === 'boolean')
  );
}

function isStored(value: unknown): value is Stored {
  return (
    isRecord(value) &&
    typeof value.siteId === 'string' &&
    isStoredSource(value.source) &&
    isRecord(value.answers) &&
    isRecord(value.intervalText) &&
    (value.importId === null || typeof value.importId === 'string') &&
    isIntent(value.intent) &&
    typeof value.textDropped === 'boolean'
  );
}

function storage(): Storage | null {
  return Platform.OS === 'web' ? (globalThis.sessionStorage ?? null) : null;
}

/**
 * The web draft, read back after a reload or a restored session (027 D12). Native keeps the draft in memory only:
 * a re-import counts identical rows once, so losing it is safe, and persisting it is 034's.
 */
export function loadImportDraft(): LoadedDraft | null {
  try {
    const raw = storage()?.getItem(KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    if (!isStored(parsed)) {
      return null;
    }
    const { textDropped, ...draft } = parsed;
    return { ...draft, needsReselect: draft.source?.kind === 'file', textDropped };
  } catch {
    return null;
  }
}

/** Mirrors the user's input, the import ID and the commit intent. A paste over the quota is stored without its text. */
export function saveImportDraft(draft: DraftSnapshot & { textDropped?: boolean }): void {
  let target: Storage | null;
  try {
    target = storage();
  } catch {
    return;
  }
  if (!target) {
    return;
  }
  const { siteId, source, answers, intervalText, importId, intent, textDropped = false } = draft;
  const stored: Stored = { siteId, source: storedSource(source), answers, intervalText, importId, intent, textDropped };
  try {
    target.setItem(KEY, JSON.stringify(stored));
  } catch {
    try {
      const withoutText = stored.source?.kind === 'paste' ? { ...stored, source: null, textDropped: true } : stored;
      target.setItem(KEY, JSON.stringify(withoutText));
    } catch {
      // Storage is unavailable: the draft stays in memory for this page, as it does on native.
    }
  }
}

export function clearImportDraft(): void {
  try {
    storage()?.removeItem(KEY);
  } catch {
    // Nothing stored, or storage is unavailable: either way there is no draft to clear.
  }
}
