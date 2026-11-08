import { currentCopy, useCopy } from '@/features/localization/messages';
import { useRef, useState, type ComponentRef, type RefObject } from 'react';
import { StyleSheet, View, type TextInput } from 'react-native';

import { normalizeAssetText, type Asset, type AssetChanges } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDErrorSummary } from '@/components/hd/HDErrorSummary';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { HDText } from '@/components/hd/HDText';
import { HDTextField } from '@/components/hd/HDTextField';
import { tokens } from '@/design/tokens.generated';
import { AssetWriteFeedback } from '@/features/assets/AssetWriteFeedback';
import { assetValues, EDITABLE_FIELDS, type AssetDraft, type AssetField, type AssetValues } from '@/features/offline/persist-drafts';
import type { AssetWriteState } from '@/features/assets/useAssetMutations';

const FIELDS = EDITABLE_FIELDS;
function fieldLabel(field: keyof AssetValues): string {
  return {
    name: currentCopy('Nama perangkat', 'Device name'),
    category: currentCopy('Kategori', 'Category'),
    location: currentCopy('Lokasi', 'Location'),
  }[field];
}
type FieldErrors = Partial<AssetValues>;
export type { AssetDraft };

export function createAssetDraft(asset: Asset): AssetDraft {
  const values = assetValues(asset);
  return { baseline: values, values, touched: {} };
}

export function reviewedDraft(draft: AssetDraft, observed: Asset, changes: AssetChanges): AssetDraft {
  const next = createAssetDraft(observed);
  for (const field of FIELDS) {
    if (changes[field] !== undefined) {
      next.values = { ...next.values, [field]: draft.values[field] };
      next.touched[field] = true;
    }
  }
  return next;
}

type EditProps = {
  open: boolean;
  draft: AssetDraft;
  state: AssetWriteState | undefined;
  blocked: boolean;
  storageFailed?: boolean;
  onDraft: (draft: AssetDraft) => void;
  onSubmit: (changes: AssetChanges) => void;
  onReview: () => void;
  onCheck?: () => void;
  onClose: () => void;
  onDiscard: () => void;
  returnFocusTo?: RefObject<ComponentRef<typeof View> | null>;
};

export function EditAssetSheet({
  open, draft, state, blocked, storageFailed = false, onDraft, onSubmit, onReview, onCheck, onClose, onDiscard, returnFocusTo,
}: EditProps) {
  const say = useCopy();
  const name = useRef<ComponentRef<typeof TextInput>>(null);
  const category = useRef<ComponentRef<typeof TextInput>>(null);
  const location = useRef<ComponentRef<typeof TextInput>>(null);
  const inputs = { name, category, location };
  const [validation, setValidation] = useState<FieldErrors>({});
  const [submits, setSubmits] = useState(0);
  const [noChanges, setNoChanges] = useState(false);
  const edited = state?.changes.archived === undefined;
  const busy = state?.kind === 'saving' || state?.kind === 'checking' || state?.kind === 'draft-checking';
  const refused = edited && state?.kind === 'refused' && state.error.code === 'VALIDATION_FAILED' ? state : null;
  const errors: FieldErrors = { ...validation };
  for (const detail of refused?.error.details ?? []) {
    const field = FIELDS.find((key) => detail.loc.length === 2 && detail.loc[0] === 'body' && detail.loc[1] === key);
    if (field && normalizeAssetText(draft.values[field]) === refused?.changes[field]) {
      errors[field] ??= detail.msg;
    }
  }
  const links = FIELDS.flatMap((field) => errors[field]
    ? [{ key: field, text: `${fieldLabel(field)}. ${errors[field]}`, target: () => inputs[field].current }] : []);

  function change(field: AssetField, value: string) {
    onDraft({ ...draft, values: { ...draft.values, [field]: value }, touched: { ...draft.touched, [field]: true } });
    setValidation({ ...validation, [field]: undefined });
    setNoChanges(false);
  }

  function submit() {
    const errors: FieldErrors = {};
    const changes: AssetChanges = {};
    for (const field of FIELDS) {
      const value = normalizeAssetText(draft.values[field]);
      if (field === 'name' && !value) errors[field] = say("Isi nama perangkat.", "Enter a device name.");
      else if ([...value].length > 60) errors[field] = say(`${fieldLabel(field)} paling banyak 60 karakter.`, `${fieldLabel(field)} must be 60 characters or fewer.`);
      if (draft.touched[field] && value !== normalizeAssetText(draft.baseline[field])) changes[field] = value;
    }
    setValidation(errors);
    setSubmits(submits + 1);
    if (Object.keys(errors).length > 0) return;
    const changed = Object.keys(changes).length > 0;
    setNoChanges(!changed);
    if (changed) onSubmit(changes);
  }

  function review() {
    if ((state?.kind !== 'diverged' && state?.kind !== 'draft-review') || !edited) return;
    onDraft(reviewedDraft(draft, state.observed, state.changes));
    onReview();
  }

  const observedLabel = state?.kind === 'diverged' || state?.kind === 'reviewed' || state?.kind === 'draft-review'
    ? [state.observed.name, say(`kategori ${state.observed.category || 'kosong'}`, `category ${state.observed.category || 'kosong'}`), say(`lokasi ${state.observed.location || 'kosong'}`, `location ${state.observed.location || 'kosong'}`)].join(', ')
    : undefined;

  return (
    <HDSheetDialog open={open} title={say("Ubah detail perangkat", "Edit device details")} onClose={onClose} returnFocusTo={returnFocusTo} scrollable
      footer={
        <View style={styles.actions}>
          <HDButton variant="primary" loading={busy} loadingLabel={say("Menyimpan…", "Saving…")} onPress={submit}
            disabledReason={blocked && !busy ? say("Periksa hasil perubahan sebelumnya.", "Check the status of the earlier change.") : undefined}>{say("Simpan", "Save")}</HDButton>
          <HDButton variant="text" onPress={onClose}>{say("Batal", "Cancel")}</HDButton>
          {Object.keys(draft.touched).length ? (
            <HDButton variant="text" onPress={onDiscard}
              disabledReason={busy ? say("Perubahan sedang diproses.", "Changes are in progress.") : undefined}>{say("Buang draf", "Discard draft")}</HDButton>
          ) : null}
        </View>
      }>
      {open ? (
        <>
          <HDErrorSummary errors={links} submitCount={submits + (refused ? 1 : 0)} />
          {FIELDS.map((field) => (
            <HDTextField key={field} inputRef={inputs[field]} label={fieldLabel(field)} value={draft.values[field]}
              required={field === 'name'} optional={field !== 'name'} editable={!blocked}
              error={errors[field]} onChange={(value) => change(field, value)} />
          ))}
          {storageFailed ? <HDText role="status">{say("Draf tersedia selama halaman ini terbuka. Pemulihan setelah aplikasi dimulai ulang belum terkonfirmasi.", "The draft is available while this screen is open. It may be unavailable after restarting.")}</HDText> : null}
          {noChanges ? <HDText role="status">{say("Belum ada perubahan untuk disimpan.", "No changes to save.")}</HDText> : null}
          <AssetWriteFeedback state={edited || blocked ? state : undefined} onReview={edited ? review : undefined}
            onCheck={onCheck} observedLabel={observedLabel} />
        </>
      ) : null}
    </HDSheetDialog>
  );
}

const styles = StyleSheet.create({
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.stackTight },
});
