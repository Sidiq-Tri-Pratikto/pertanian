import { useCallback, useEffect, useRef, useState } from 'react';

import { normalizeAssetText, type Asset } from '@/api/client';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

export const EDITABLE_FIELDS = ['name', 'category', 'location'] as const;
export type AssetField = typeof EDITABLE_FIELDS[number];
export type AssetValues = Record<AssetField, string>;
export type AssetDraft = { baseline: AssetValues; values: AssetValues; touched: Partial<Record<AssetField, true>> };
type DraftEntry = AssetDraft & { assetId: string };

const MAX_FIELDS_LENGTH = 256;
const MAX_DRAFTS = 12;

export function assetValues(asset: Asset): AssetValues {
  return { name: asset.name, category: asset.category ?? '', location: asset.location ?? '' };
}

function projectValues(value: unknown, bounded: boolean): AssetValues | null {
  const values = value as Partial<AssetValues> | null;
  if (values == null || EDITABLE_FIELDS.some((field) =>
    typeof values[field] !== 'string' || (bounded && values[field]!.length > MAX_FIELDS_LENGTH))) return null;
  return { name: values.name!, category: values.category!, location: values.location! };
}

function projectDraft(value: unknown): DraftEntry | null {
  const row = value as Partial<DraftEntry> | null;
  if (typeof row?.assetId !== 'string' || row.assetId.length === 0 || row.assetId.length > 100 ||
    row.touched === null || typeof row.touched !== 'object') return null;
  const baseline = projectValues(row.baseline, true);
  const values = projectValues(row.values, true);
  if (!baseline || !normalizeAssetText(baseline.name) || !values) return null;
  const touched: AssetDraft['touched'] = {};
  for (const field of EDITABLE_FIELDS) {
    if (row.touched[field] === true) touched[field] = true;
  }
  return Object.keys(touched).length ? { assetId: row.assetId, baseline, values, touched } : null;
}

function decode(raw: string | null): DraftEntry[] {
  if (!raw || raw.length > 65_536) return [];
  try {
    const data = JSON.parse(raw);
    return data?.version === 1 && Array.isArray(data.items)
      ? data.items.slice(0, MAX_DRAFTS).flatMap((row: unknown) => projectDraft(row) ?? [])
      : [];
  } catch {
    return [];
  }
}

/** Editable fields only. An operation, archive status or server response never enters this record. */
export function useAssetDraft(assetId: string) {
  const { storage, credential } = useWorkspace();
  const [draft, setDraft] = useState<AssetDraft | null>(null);
  const [restored, setRestored] = useState(false);
  const [failed, setFailed] = useState(false);
  const edited = useRef(false);

  useEffect(() => {
    if (!storage) return;
    let live = true;
    void storage.read('asset-drafts').then((raw) => {
      if (!live || edited.current || !credential?.current()) return;
      const saved = decode(raw).find((row) => row.assetId === assetId);
      if (saved) {
        const { baseline, values, touched } = saved;
        setDraft({ baseline, values, touched });
        setRestored(true);
      }
    });
    return () => { live = false; };
  }, [assetId, credential, storage]);

  const change = useCallback((next: AssetDraft | null) => {
    if (!credential?.current()) return;
    edited.current = true;
    setDraft(next);
    if (!next) setRestored(false);
    const projected = next ? projectDraft({ ...next, assetId }) : null;
    if (!storage) {
      if (next && Object.keys(next.touched).length) setFailed(true);
      return;
    }
    void storage.update('asset-drafts', (before) => {
      const others = decode(before).filter((row) => row.assetId !== assetId);
      const items = (projected ? [projected, ...others] : others).slice(0, MAX_DRAFTS);
      return JSON.stringify({ version: 1, items });
    }).then((written) => {
      if (credential.current()) setFailed(!written || (next !== null && !projected && Object.keys(next.touched).length > 0));
    });
  }, [assetId, credential, storage]);

  return { draft, change, restored, reconciled: () => setRestored(false), failed };
}
