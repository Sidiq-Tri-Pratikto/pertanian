import type { Claim, Fact, Invention, InventionVersion } from '@/features/portfolio/model';

/** Everything the editor shows, kept across steps, failed saves and stale versions. */
export type DraftValues = {
  title: string;
  summary: string;
  problem: string;
  solution: string;
  intended_users: string;
  sector: string;
  stage: string;
  keywords: string;
  facts: Fact[];
  claims: Claim[];
  private_notes: string;
};

export type SaveStatus = 'local' | 'saving' | 'saved' | 'failed' | 'conflict';

export type EditorState = {
  values: DraftValues;
  /** The invention version the next save is made against. */
  version: number;
  status: SaveStatus;
  /** Kept until a save succeeds, so a retry of the same save reuses it and is never applied twice. */
  pendingKey: string | null;
  currentVersion: number | null;
};

export const EMPTY_FACT: Fact = { label: '', value: '', unit: '', timing: 'CURRENT', provenance: 'SELF_DECLARED' };
export const EMPTY_CLAIM: Claim = { kind: 'creator', subject_name: '', scope: '', status: 'asserted', source: '' };

export function valuesFrom(version: InventionVersion | null | undefined): DraftValues {
  return {
    title: version?.title ?? '',
    summary: version?.summary ?? '',
    problem: version?.problem ?? '',
    solution: version?.solution ?? '',
    intended_users: version?.intended_users ?? '',
    sector: version?.sector ?? '',
    stage: version?.stage ?? '',
    keywords: (version?.keywords ?? []).join(', '),
    facts: (version?.facts ?? []).map((fact) => ({ ...fact })),
    claims: (version?.claims ?? []).map((claim) => ({ ...claim })),
    private_notes: version?.private_notes ?? '',
  };
}

export function initialState(invention: Invention): EditorState {
  return {
    values: valuesFrom(invention.draft ?? invention.published),
    version: invention.version,
    status: invention.draft ? 'saved' : 'local',
    pendingKey: null,
    currentVersion: null,
  };
}

/** The draft request body. Empty rows are dropped, so an unfinished row never blocks a save. */
export function draftRequest(values: DraftValues, version: number, actingPartyId: string) {
  return {
    acting_party_id: actingPartyId,
    expected_version: version,
    title: values.title,
    summary: values.summary,
    problem: values.problem,
    solution: values.solution,
    intended_users: values.intended_users,
    sector: values.sector,
    stage: values.stage || null,
    keywords: values.keywords
      .split(',')
      .map((keyword) => keyword.trim())
      .filter(Boolean),
    facts: values.facts.filter((fact) => fact.label.trim() && fact.value.trim()),
    claims: values.claims.filter((claim) => claim.subject_name.trim()),
    private_notes: values.private_notes,
  };
}

export type EditorEvent =
  | { type: 'edit'; values: DraftValues }
  | { type: 'save'; key: string }
  | { type: 'saved'; version: number }
  | { type: 'failed' }
  | { type: 'conflict'; currentVersion: number }
  | { type: 'reloaded'; invention: Invention };

/** The save state machine: local -> saving -> saved | failed | conflict. Values are never lost on any path. */
export function reduce(state: EditorState, event: EditorEvent): EditorState {
  switch (event.type) {
    case 'edit':
      // A change after a failure is a new save: it needs a new key.
      return { ...state, values: event.values, status: 'local', pendingKey: state.status === 'failed' ? null : state.pendingKey };
    case 'save':
      return { ...state, status: 'saving', pendingKey: state.pendingKey ?? event.key };
    case 'saved':
      return { ...state, status: 'saved', version: event.version, pendingKey: null, currentVersion: null };
    case 'failed':
      return { ...state, status: 'failed' };
    case 'conflict':
      return { ...state, status: 'conflict', pendingKey: null, currentVersion: event.currentVersion };
    case 'reloaded':
      return { ...initialState(event.invention), status: 'saved' };
  }
}

/** Which step holds each field the API may name in a publication error. */
export const FIELD_STEP: Record<string, number> = {
  title: 1,
  summary: 1,
  problem: 1,
  solution: 1,
  intended_users: 1,
  stage: 1,
  facts: 2,
};

export const FIELD_ID: Record<string, string> = {
  title: 'judul',
  summary: 'ringkasan',
  problem: 'masalah',
  solution: 'solusi',
  intended_users: 'pengguna',
  stage: 'tahap',
  facts: 'fakta-0-label',
};
