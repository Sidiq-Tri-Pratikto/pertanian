import { CryptoDigestAlgorithm, digestStringAsync } from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { ApiError } from '@/api/errors';
import { randomToken } from '@/lib/random';

export type Period = { preset: string; start_date: string; end_date: string };

/** What the device holds for one workspace. The credential stays inside this storage boundary. */
export type Workspace = {
  token: string;
  siteId: string;
  scenarioId: string | null;
  expiresAt: string;
  initialPeriod: Period;
};

export type Attestation = {
  epoch: string;
  fingerprint: string;
  /** Only a successfully upgraded original credential can inspect legacy import data. */
  legacyImport: boolean;
};

export type WorkspaceRecord = { workspace: Workspace } & (
  | { kind: 'legacy' | 'revoked' }
  | { kind: 'confirmed'; attestation: Attestation }
);

const KEY = 'hematdaya.workspace.v1';
const CONTROL_VERSION = 2;

export function isUnexpired(workspace: Workspace): boolean {
  const expires = Date.parse(workspace.expiresAt);
  return Number.isFinite(expires) && expires > Date.now();
}

function isWorkspace(value: unknown): value is Workspace {
  const candidate = value as Partial<Workspace> | null;
  const period = candidate?.initialPeriod;
  return (
    typeof candidate?.token === 'string' && candidate.token.length > 0 &&
    typeof candidate.siteId === 'string' && candidate.siteId.length > 0 &&
    typeof candidate.scenarioId === 'string' && candidate.scenarioId.length > 0 &&
    typeof candidate.expiresAt === 'string' &&
    typeof period?.preset === 'string' &&
    typeof period.start_date === 'string' && typeof period.end_date === 'string'
  );
}

function isAttestation(value: unknown): value is Attestation {
  const candidate = value as Partial<Attestation> | null;
  return typeof candidate?.epoch === 'string' && /^[\w-]{22}$/.test(candidate.epoch) &&
    typeof candidate.fingerprint === 'string' && /^[a-f0-9]{64}$/.test(candidate.fingerprint) &&
    typeof candidate.legacyImport === 'boolean';
}

function fingerprint(workspace: Workspace, epoch: string, legacyImport: boolean): Promise<string> {
  return digestStringAsync(CryptoDigestAlgorithm.SHA256,
    JSON.stringify(['hematdaya/demo-owner/v2', workspace.siteId, workspace.token, workspace.expiresAt, epoch, legacyImport]));
}

/** Call only after an owned server response. Every activation uses a new durable epoch. */
export async function attestWorkspace(workspace: Workspace, legacyImport = false): Promise<Attestation> {
  if (workspace.scenarioId === null) throw ApiError.storage();
  if (!isUnexpired(workspace)) throw ApiError.expired();
  const epoch = randomToken(16);
  return { epoch, fingerprint: await fingerprint(workspace, epoch, legacyImport), legacyImport };
}

function webStorage(): Storage {
  if (!globalThis.sessionStorage) throw ApiError.storage();
  return globalThis.sessionStorage;
}

async function read(): Promise<string | null> {
  return Platform.OS === 'web' ? webStorage().getItem(KEY) : SecureStore.getItemAsync(KEY);
}

async function write(value: unknown): Promise<void> {
  const serialized = JSON.stringify(value);
  if (Platform.OS === 'web') webStorage().setItem(KEY, serialized);
  else await SecureStore.setItemAsync(KEY, serialized);
}

export async function loadWorkspaceRecord(): Promise<WorkspaceRecord | null> {
  const stored = await read();
  if (stored === null) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(stored);
  } catch {
    return null;
  }
  if (isWorkspace(parsed) && !('version' in parsed)) return { workspace: parsed, kind: 'legacy' };
  const candidate = parsed as { version?: number; workspace?: unknown; attestation?: unknown } | null;
  if (candidate?.version !== CONTROL_VERSION || !isWorkspace(candidate.workspace)) return null;
  if (candidate.attestation === null) return { workspace: candidate.workspace, kind: 'revoked' };
  if (!isAttestation(candidate.attestation) || candidate.attestation.fingerprint !== await fingerprint(candidate.workspace, candidate.attestation.epoch, candidate.attestation.legacyImport)) {
    return null;
  }
  return { workspace: candidate.workspace, kind: 'confirmed', attestation: candidate.attestation };
}

/** Compatibility reader for the credential store. Only the provider grants an offline namespace. */
export async function loadWorkspace(): Promise<Workspace | null> {
  try {
    return (await loadWorkspaceRecord())?.workspace ?? null;
  } catch {
    return null;
  }
}

export async function saveWorkspace(workspace: Workspace, attestation?: Attestation): Promise<void> {
  await write(attestation ? { version: CONTROL_VERSION, workspace, attestation } : workspace);
}

export async function revokeWorkspace(workspace: Workspace): Promise<void> {
  await write({ version: CONTROL_VERSION, workspace, attestation: null });
}

/** A terminal teardown can erase the credential even when deleting its storage entry fails. */
export async function tombstoneWorkspace(): Promise<void> {
  await write({ version: CONTROL_VERSION, workspace: null, attestation: null });
}

export async function clearWorkspace(): Promise<void> {
  if (Platform.OS === 'web') webStorage().removeItem(KEY);
  else await SecureStore.deleteItemAsync(KEY);
}
