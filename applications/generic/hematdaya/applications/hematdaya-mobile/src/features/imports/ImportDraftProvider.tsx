import { useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import {
  commitImport,
  getImport,
  getImportErrors,
  previewImport,
  type ImportAnswers,
  type ImportCommit,
  type ImportPreview,
  type ImportQuestion,
  type ImportResult,
  type ImportRowError,
  type ImportSource,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import {
  clearLegacyDraft, loadLegacyDraft, readDraft, readRecovery, storeDraft, writeRecovery,
  type CommitIntent, type LoadedDraft, type StoredSource,
} from '@/features/imports/draft-store';
import { answerFor, commitOutcome, previewOutcome, readMinutes, type AnswerValue, type CommitOutcome, type Control, type PreviewOutcome } from '@/features/imports/import-model';
import { isKnownOffline } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { randomToken } from '@/lib/random';

/** The source as the draft holds it: a file after a web reload is a name only, to be picked again. */
export type DraftSource = ImportSource | StoredSource;

export type CheckState =
  | { kind: 'idle' }
  | { kind: 'pending' }
  | { kind: 'failed'; error: ApiError; outcome: PreviewOutcome };

export type CommitState =
  | { kind: 'idle' }
  | { kind: 'pending' }
  /** The service may or may not have committed. Only Periksa status is offered (027 D5). */
  | { kind: 'unknown'; error: ApiError | null; checkError: ApiError | null }
  | { kind: 'checking' }
  | { kind: 'notYet' }
  /** A definite refusal; the intent is dropped. `error` is null when a status check found the preview expired. */
  | { kind: 'refused'; error: ApiError | null; outcome: CommitOutcome }
  | { kind: 'committed'; result: ImportCommit | ImportResult; found: boolean };

export type MoreState = { kind: 'idle' } | { kind: 'pending' } | { kind: 'failed'; error: ApiError };

type Draft = {
  siteId: string | null;
  owner: number | null;
  unsent: ApiError | null;
  persistenceFailed: boolean;
  legacyHandled: boolean;
  source: DraftSource | null;
  needsReselect: boolean;
  textDropped: boolean;
  answers: ImportAnswers;
  intervalText: Record<string, string>;
  /** The answers the current preview was made with, so an unchanged set is not posted again (027 D15). */
  sentAnswers: ImportAnswers | null;
  preview: ImportPreview | null;
  /** Every question asked in this draft, so an answer stays visible and changeable after the service accepts it. */
  asked: ImportQuestion[];
  importId: string | null;
  errors: ImportRowError[];
  nextCursor: string | null;
  more: MoreState;
  acknowledged: boolean;
  intent: CommitIntent | null;
  check: CheckState;
  commit: CommitState;
  /** Previews made in this draft, for the error summary's focus (027 D36). */
  previews: number;
  resultShown: boolean;
};

const EMPTY: Draft = {
  siteId: null, owner: null, unsent: null, persistenceFailed: false, legacyHandled: false,
  source: null,
  needsReselect: false,
  textDropped: false,
  answers: {},
  intervalText: {},
  sentAnswers: null,
  preview: null,
  asked: [],
  importId: null,
  errors: [],
  nextCursor: null,
  more: { kind: 'idle' },
  acknowledged: false,
  intent: null,
  check: { kind: 'idle' },
  commit: { kind: 'idle' },
  previews: 0,
  resultShown: false,
};

/** The largest file or paste the service accepts, checked before an upload when the size is known. */
export const MAX_IMPORT_BYTES = 10_485_760;

function recoveredDraft(data: LoadedDraft | null, intent: CommitIntent | null): Partial<Draft> {
  return {
    source: data?.source ?? null,
    needsReselect: data?.needsReselect ?? false,
    textDropped: data?.textDropped ?? false,
    answers: data?.answers ?? {},
    intervalText: data?.intervalText ?? {},
    importId: intent?.importId ?? data?.importId ?? null,
    intent,
    acknowledged: intent?.acknowledge ?? false,
    legacyHandled: data?.legacyHandled ?? false,
    commit: intent ? { kind: 'unknown', error: null, checkError: null } : { kind: 'idle' },
  };
}

function questionKey(question: ImportQuestion): string {
  return [question.kind, question.asset_name ?? '', ...(question.streams ?? [])].join('\u0000');
}

/** Earlier questions keep their place; a question asked again takes the service's newest wording. */
function mergeQuestions(asked: ImportQuestion[], latest: ImportQuestion[]): ImportQuestion[] {
  const fresh = new Map(latest.map((question) => [questionKey(question), question]));
  const kept = asked.map((question) => fresh.get(questionKey(question)) ?? question);
  const known = new Set(asked.map(questionKey));
  return [...kept, ...latest.filter((question) => !known.has(questionKey(question)))];
}

/** Bytes are needed and the source can give them. */
export function uploadable(source: DraftSource | null): source is ImportSource {
  return source !== null && (source.kind === 'paste' || 'file' in source || 'uri' in source);
}

function sourceName(source: DraftSource): string {
  if (source.kind === 'paste') {
    return 'tempelan.csv';
  }
  return 'file' in source ? source.file.name : source.name;
}

type ImportDraftValue = Draft & {
  ready: boolean;
  /** Content, answers or a preview that a new source would replace (027 D16). */
  hasContent: boolean;
  sourceName: string | null;
  setText: (text: string) => void;
  /** Replaces the source and drops answers, preview and intent. */
  replaceSource: (source: ImportSource) => void;
  /** The original file name was picked again. Keep the answers and preview the new upload. */
  reselect: (source: ImportSource) => void;
  clearSource: () => void;
  setAnswer: (control: Control, value: AnswerValue | undefined) => void;
  setIntervalText: (control: Extract<Control, { kind: 'interval_duration' }>, text: string) => void;
  setAcknowledged: (acknowledged: boolean) => void;
  /** Posts a preview of the current source and answers. Resolves to the new preview, or null on failure. */
  runPreview: () => Promise<ImportPreview | null>;
  /** Reads the stored preview again after a web reload. */
  reloadPreview: () => Promise<void>;
  /** Sends the commit intent, making it when there is none. False when the acknowledgment is missing. */
  confirm: () => Promise<boolean>;
  checkStatus: () => Promise<void>;
  resend: () => Promise<void>;
  loadMoreErrors: () => Promise<void>;
  markResultShown: () => void;
  /** Ends the draft: after a shown result, or to import another file. */
  finish: () => void;
};

const ImportDraftContext = createContext<ImportDraftValue | null>(null);

/**
 * The import draft, above the tabs, so it survives leaving S10, tab switches and each tab's stack (027 D11).
 * Operation results stay in this state as `useFeedback` keeps its result; only the user's input, the import ID
 * and the commit intent are mirrored to web storage (027 D12, D35). Plain calls only: nothing here retries.
 */
export function ImportDraftProvider({ children }: { children: ReactNode }) {
  const { status, workspace, credential, storage, legacyImport, credentialGeneration, isCurrentCredential, advanceScope } = useWorkspace();
  const queryClient = useQueryClient();
  const [stored, setDraft] = useState<Draft>(EMPTY);
  const draftRef = useRef(EMPTY);
  const adopted = useRef(false);
  const legacy = useRef<CommitIntent | null>(null);
  const inFlight = useRef<object | null>(null);
  const siteId = workspace?.siteId ?? null;
  const ready = status === 'ready' && (siteId === null || stored.owner === credentialGeneration);
  const draft = ready && stored.owner === (siteId ? credentialGeneration : null) ? stored : EMPTY;

  const currentOwner = useCallback(() => isCurrentCredential(credentialGeneration) &&
    (credential === null || credential.current()), [credential, credentialGeneration, isCurrentCredential]);

  const update = useCallback((change: (current: Draft) => Draft) => {
    if (!currentOwner()) return;
    const current = draftRef.current;
    if (siteId !== current.siteId || (siteId && current.owner !== credentialGeneration)) return;
    const next = change(current);
    draftRef.current = next;
    setDraft(next);
  }, [credentialGeneration, currentOwner, siteId]);

  useEffect(() => {
    if (status !== 'ready') return;
    let live = true;
    const previous = draftRef.current;
    if (previous.owner !== credentialGeneration) {
      inFlight.current = null;
      legacy.current = null;
    }
    if (!siteId) {
      if (previous.owner !== null) {
        draftRef.current = EMPTY;
        setDraft(EMPTY);
      }
      return;
    }
    const adopt = previous.owner === credentialGeneration || (!adopted.current && previous.owner === null) ? previous : EMPTY;
    adopted.current = true;
    const hydrate = async () => {
      const data = storage ? readDraft(await storage.read('import-draft')) : null;
      if (!live || !currentOwner()) return;
      const intent = storage ? readRecovery(storage.epoch) : null;
      const old = legacyImport && !data?.legacyHandled && !intent ? loadLegacyDraft(siteId) : null;
      const owner = { siteId, owner: credentialGeneration };
      let next: Draft = { ...adopt, ...owner };
      if (data || intent || old) next = { ...EMPTY, ...owner, ...recoveredDraft(data ?? old?.draft ?? null, intent) };
      if (old?.intent) {
        legacy.current = old.intent;
        next = { ...EMPTY, ...owner, importId: old.intent.importId, commit: { kind: 'unknown', error: null, checkError: null } };
      } else if (old) {
        next.legacyHandled = true;
        if (storage && await storage.write('import-draft', storeDraft(next))) clearLegacyDraft();
      }
      if (!live || !currentOwner()) return;
      draftRef.current = next;
      setDraft(next);
    };
    void hydrate();
    return () => { live = false; };
  }, [credentialGeneration, currentOwner, legacyImport, siteId, status, storage]);

  const { source, answers, intervalText, importId, textDropped, legacyHandled } = draft;
  const snapshot = useMemo(() => ({ source, answers, intervalText, importId, textDropped, legacyHandled }),
    [source, answers, intervalText, importId, textDropped, legacyHandled]);
  useEffect(() => {
    if (!ready || !siteId || legacy.current || !currentOwner()) return;
    if (!storage) {
      if (snapshot.source && !draft.persistenceFailed) {
        void Promise.resolve().then(() => update((state) => ({ ...state, persistenceFailed: true })));
      }
      return;
    }
    let live = true;
    void (async () => {
      const written = await storage.write('import-draft', storeDraft(snapshot));
      if (!written && snapshot.source?.kind === 'paste') {
        await storage.write('import-draft', storeDraft(snapshot, true));
      }
      if (live && (!written || (snapshot.source?.kind === 'paste' && snapshot.source.text.length > 512_000))) {
        update((state) => ({ ...state, persistenceFailed: true }));
      }
    })();
    return () => { live = false; };
  }, [currentOwner, draft.persistenceFailed, ready, siteId, snapshot, storage, update]);

  const clearRecovery = useCallback(() => {
    if (storage && currentOwner() && !writeRecovery(storage.epoch, null)) {
      update((state) => ({ ...state, persistenceFailed: true }));
    }
  }, [currentOwner, storage, update]);

  const reportUnsent = useCallback((error = ApiError.offline()) =>
    update((state) => ({ ...state, unsent: error })), [update]);

  const failSession = useCallback((error: ApiError) => !currentOwner() ||
    error.code === 'WORKSPACE_CHANGED' || error.code === 'SESSION_EXPIRED' || error.code === 'UNAUTHORIZED', [currentOwner]);

  const setText = useCallback(
    (text: string) =>
      update((current) => ({
        ...current,
        source: text ? { kind: 'paste', text } : null,
        needsReselect: false,
        textDropped: false,
        preview: null,
        importId: null,
        intent: null,
        sentAnswers: null,
        acknowledged: false,
        commit: { kind: 'idle' },
        check: { kind: 'idle' },
      })),
    [update],
  );

  const replaceSource = useCallback(
    (source: ImportSource) =>
      update((current) => ({ ...EMPTY, siteId: current.siteId, owner: current.owner, legacyHandled: current.legacyHandled, source, previews: current.previews })),
    [update],
  );

  const reselect = useCallback(
    (source: ImportSource) => update((current) => ({ ...current, source, needsReselect: false, sentAnswers: null, check: { kind: 'idle' } })),
    [update],
  );

  const clearSource = useCallback(() => update((current) => ({ ...EMPTY, siteId: current.siteId, owner: current.owner, legacyHandled: current.legacyHandled, previews: current.previews })), [update]);

  const setAnswer = useCallback(
    (control: Control, value: AnswerValue | undefined) =>
      update((current) =>
        current.preview ? { ...current, answers: answerFor(current.preview, control, value, current.answers) } : current,
      ),
    [update],
  );

  const setIntervalText = useCallback(
    (control: Extract<Control, { kind: 'interval_duration' }>, text: string) =>
      update((current) => {
        if (!current.preview) {
          return current;
        }
        const minutes = readMinutes(text);
        return {
          ...current,
          intervalText: { ...current.intervalText, [control.streamKey]: text },
          answers: answerFor(current.preview, control, typeof minutes === 'number' ? minutes : undefined, current.answers),
        };
      }),
    [update],
  );

  const setAcknowledged = useCallback(
    (acknowledged: boolean) =>
      update((current) =>
        current.intent
          ? current
          : { ...current, acknowledged },
      ),
    [update],
  );

  const runPreview = useCallback(async (): Promise<ImportPreview | null> => {
    const current = draftRef.current;
    if (inFlight.current || !workspace || !credential || !currentOwner() || !ready || current.intent || !uploadable(current.source)) {
      return null;
    }
    if (isKnownOffline()) {
      reportUnsent();
      return null;
    }
    const operation = {};
    inFlight.current = operation;
    const answers = current.answers;
    update((state) => ({ ...state, check: { kind: 'pending' }, unsent: null }));
    try {
      const preview = await previewImport(workspace.siteId, current.source, answers, credential);
      if (!currentOwner()) return null;
      // Each preview is a new import: an earlier intent and acknowledgment belong to the one it replaces.
      update((state) => ({
        ...state,
        preview,
        asked: mergeQuestions(state.asked, preview.questions),
        importId: preview.id,
        sentAnswers: answers,
        errors: preview.errors,
        nextCursor: preview.next_error_cursor,
        more: { kind: 'idle' },
        acknowledged: false,
        intent: null,
        check: { kind: 'idle' },
        commit: { kind: 'idle' },
        previews: state.previews + 1,
        resultShown: false,
      }));
      return preview;
    } catch (failure) {
      const error = ApiError.from(failure);
      if (error.code === 'OFFLINE_UNSENT') {
        update((state) => ({ ...state, check: { kind: 'idle' }, unsent: error }));
      } else if (!failSession(error)) {
        const outcome = previewOutcome(error);
        update((state) => ({
          ...state,
          check: { kind: 'failed', error, outcome },
          // The chosen asset is gone: its answer is cleared and every other answer stays.
          answers: outcome.kind === 'assetGone' ? { ...state.answers, asset_map: undefined } : state.answers,
        }));
      }
      return null;
    } finally {
      if (inFlight.current === operation) inFlight.current = null;
    }
  }, [credential, currentOwner, failSession, ready, reportUnsent, update, workspace]);

  const reloadPreview = useCallback(async () => {
    const current = draftRef.current;
    if (inFlight.current || !credential || !currentOwner() || !ready || isKnownOffline() || !current.importId || current.preview) {
      return;
    }
    const operation = {};
    inFlight.current = operation;
    try {
      const preview = await getImport(current.importId, credential);
      update((state) => ({
        ...state,
        preview,
        asked: mergeQuestions(state.asked, preview.questions),
        sentAnswers: state.answers,
        errors: preview.errors,
        nextCursor: preview.next_error_cursor,
      }));
    } catch (failure) {
      const error = ApiError.from(failure);
      if (!failSession(error)) {
        update((state) => ({ ...state, importId: state.intent ? state.importId : null, check: { kind: 'failed', error, outcome: previewOutcome(error) } }));
      }
    } finally {
      if (inFlight.current === operation) inFlight.current = null;
    }
  }, [credential, currentOwner, failSession, ready, update]);

  const send = useCallback(async (intent: CommitIntent) => {
    if (inFlight.current || !credential || !currentOwner() || !ready) return;
    if (isKnownOffline()) {
      reportUnsent();
      return;
    }
    const operation = {};
    inFlight.current = operation;
    try {
      const result = await commitImport(intent.importId, intent.acknowledge, intent.key, credential, () => {
        const persisted = storage ? writeRecovery(storage.epoch, intent) : false;
        update((state) => ({ ...state, intent, unsent: null, commit: { kind: 'pending' },
          persistenceFailed: state.persistenceFailed || !persisted }));
      });
      if (!currentOwner()) return;
      await advanceScope();
      if (!currentOwner()) return;
      clearRecovery();
      update((state) => ({ ...state, intent: null, commit: { kind: 'committed', result, found: false } }));
      await queryClient.invalidateQueries();
    } catch (failure) {
      const error = ApiError.from(failure);
      if (failSession(error)) return;
      if (error.code === 'OFFLINE_UNSENT') {
        reportUnsent(error);
        return;
      }
      const outcome = commitOutcome(error);
      if (outcome.kind === 'unknown') {
        update((state) => ({ ...state, commit: { kind: 'unknown', error, checkError: null } }));
        return;
      }
      clearRecovery();
      update((state) => ({ ...state, intent: null, commit: { kind: 'refused', error, outcome } }));
      if (outcome.reason === 'blocked') {
        const preview = await getImport(intent.importId, credential).catch(() => null);
        if (preview) update((state) => ({ ...state, preview, errors: preview.errors, nextCursor: preview.next_error_cursor }));
      }
    } finally {
      if (inFlight.current === operation) inFlight.current = null;
    }
  }, [advanceScope, clearRecovery, credential, currentOwner, failSession, queryClient, ready, reportUnsent, storage, update]);

  const confirm = useCallback(async (): Promise<boolean> => {
    const current = draftRef.current;
    if (!current.preview || current.preview.blocked || current.intent) {
      return false;
    }
    if (current.preview.needs_acknowledgment && !current.acknowledged) {
      return false;
    }
    const acknowledge = current.preview.needs_acknowledgment && current.acknowledged;
    await send({ importId: current.preview.id, key: randomToken(16), acknowledge });
    return true;
  }, [send]);

  const resend = useCallback(async () => {
    const { intent, commit } = draftRef.current;
    if (intent && commit.kind === 'notYet') {
      await send(intent);
    }
  }, [send]);

  const checkStatus = useCallback(async () => {
    const current = draftRef.current;
    const pendingLegacy = legacy.current;
    const intent = current.intent ?? pendingLegacy;
    if (inFlight.current || !credential || !currentOwner() || !ready || current.commit.kind !== 'unknown' || !intent) return;
    const originalError = current.commit.error;
    if (isKnownOffline()) {
      update((state) => ({ ...state, commit: { kind: 'unknown', error: originalError, checkError: ApiError.offline() } }));
      return;
    }
    const operation = {};
    inFlight.current = operation;
    update((state) => ({ ...state, unsent: null, commit: { kind: 'checking' } }));
    try {
      const found = await getImport(intent.importId, credential);
      if (!currentOwner()) return;
      if (pendingLegacy) {
        const old = siteId ? loadLegacyDraft(siteId) : null;
        if (!old || old.intent?.key !== intent.key) throw ApiError.unexpected();
        const safe = { ...recoveredDraft(old.draft, intent), legacyHandled: true };
        const moved = storage && writeRecovery(storage.epoch, intent) &&
          await storage.write('import-draft', storeDraft({ ...old.draft, legacyHandled: true }));
        if (!currentOwner()) return;
        if (moved) clearLegacyDraft();
        legacy.current = null;
        update((state) => ({ ...state, ...safe, persistenceFailed: state.persistenceFailed || !moved }));
      }
      if (found.result) {
        const result = found.result;
        await advanceScope();
        if (!currentOwner()) return;
        clearRecovery();
        update((state) => ({ ...state, preview: state.preview ?? found, intent: null, commit: { kind: 'committed', result, found: true } }));
        await queryClient.invalidateQueries();
      } else if (found.status === 'previewed') {
        update((state) => ({ ...state, preview: state.preview ?? found, commit: { kind: 'notYet' } }));
      } else {
        clearRecovery();
        update((state) => ({ ...state, intent: null, commit: { kind: 'refused', error: null, outcome: { kind: 'gone', reason: 'other' } } }));
      }
    } catch (failure) {
      const error = ApiError.from(failure);
      if (failSession(error)) return;
      if (error.code === 'NOT_FOUND') {
        if (pendingLegacy) {
          legacy.current = null;
          clearLegacyDraft();
        }
        clearRecovery();
        update((state) => ({ ...state, intent: null, legacyHandled: state.legacyHandled || Boolean(pendingLegacy),
          commit: { kind: 'refused', error, outcome: { kind: 'gone', reason: 'other' } } }));
      } else {
        update((state) => ({ ...state, commit: { kind: 'unknown', error: originalError, checkError: error } }));
      }
    } finally {
      if (inFlight.current === operation) inFlight.current = null;
    }
  }, [advanceScope, clearRecovery, credential, currentOwner, failSession, queryClient, ready, siteId, storage, update]);

  const loadMoreErrors = useCallback(async () => {
    const current = draftRef.current;
    if (!credential || !currentOwner() || !ready || isKnownOffline() || !current.importId || !current.nextCursor || current.more.kind === 'pending') {
      return;
    }
    update((state) => ({ ...state, more: { kind: 'pending' } }));
    try {
      const page = await getImportErrors(current.importId, current.nextCursor, credential);
      update((state) => ({ ...state, errors: [...state.errors, ...page.items], nextCursor: page.next_cursor, more: { kind: 'idle' } }));
    } catch (failure) {
      const error = ApiError.from(failure);
      if (!failSession(error)) {
        update((state) => ({ ...state, more: { kind: 'failed', error } }));
      }
    }
  }, [credential, currentOwner, failSession, ready, update]);

  const markResultShown = useCallback(() => update((state) => (state.resultShown ? state : { ...state, resultShown: true })), [update]);

  const finish = useCallback(() => {
    clearRecovery();
    update((state) => ({ ...EMPTY, siteId: state.siteId, owner: state.owner, legacyHandled: state.legacyHandled }));
  }, [clearRecovery, update]);

  const value = useMemo<ImportDraftValue>(
    () => ({
      ...draft, ready,
      hasContent: draft.source !== null || Object.keys(draft.answers).length > 0 || draft.preview !== null,
      sourceName: draft.source ? sourceName(draft.source) : null,
      setText,
      replaceSource,
      reselect,
      clearSource,
      setAnswer,
      setIntervalText,
      setAcknowledged,
      runPreview,
      reloadPreview,
      confirm,
      checkStatus,
      resend,
      loadMoreErrors,
      markResultShown,
      finish,
    }),
    [draft, ready, setText, replaceSource, reselect, clearSource, setAnswer, setIntervalText, setAcknowledged, runPreview, reloadPreview, confirm, checkStatus, resend, loadMoreErrors, markResultShown, finish],
  );

  return <ImportDraftContext.Provider value={value}>{children}</ImportDraftContext.Provider>;
}

export function useImportDraft(): ImportDraftValue {
  const value = useContext(ImportDraftContext);
  if (!value) {
    throw new Error('useImportDraft needs ImportDraftProvider');
  }
  return value;
}

/** For helpers that also run outside the provider, such as navigation in a test harness. */
export function useOptionalImportDraft(): ImportDraftValue | null {
  return useContext(ImportDraftContext);
}
