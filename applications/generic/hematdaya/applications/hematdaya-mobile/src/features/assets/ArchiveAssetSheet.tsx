import type { ComponentRef, RefObject } from 'react';
import type { View } from 'react-native';

import type { Asset, AssetChanges } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { HDText } from '@/components/hd/HDText';
import { assetScopeLabel } from '@/features/assets/asset-model';
import { AssetWriteFeedback } from '@/features/assets/AssetWriteFeedback';
import type { AssetWriteState } from '@/features/assets/useAssetMutations';

type ArchiveProps = {
  open: boolean;
  asset: Asset;
  archive: boolean;
  state: AssetWriteState | undefined;
  blocked: boolean;
  onSubmit: (changes: AssetChanges) => void;
  onReview: () => void;
  onCheck?: () => void;
  onClose: () => void;
  returnFocusTo: RefObject<ComponentRef<typeof View> | null>;
};

export function ArchiveAssetSheet({
  open, asset, archive, state, blocked, onSubmit, onReview, onCheck, onClose, returnFocusTo,
}: ArchiveProps) {
  const action = archive ? 'Arsipkan' : 'Pulihkan';
  const busy = state?.kind === 'saving' || state?.kind === 'checking';
  const archiveWrite = state?.changes.archived !== undefined;
  const observedLabel = state?.kind === 'diverged' || state?.kind === 'reviewed'
    ? `${state.observed.name} ${state.observed.archived ? 'diarsipkan' : 'aktif'}` : undefined;
  return (
    <HDSheetDialog open={open} title={`${action} ${asset.name}?`} onClose={onClose} returnFocusTo={returnFocusTo} scrollable
      footer={
        <>
          <HDButton variant="primary" loading={busy} loadingLabel={archive ? 'Mengarsipkan…' : 'Memulihkan…'}
            disabledReason={blocked && !busy ? 'Periksa hasil perubahan sebelumnya.' : undefined}
            onPress={() => onSubmit({ archived: archive })}>{action}</HDButton>
          <HDButton variant="text" onPress={onClose}>Batal</HDButton>
        </>
      }>
      <HDText>{assetScopeLabel(asset.scope_kind)}.</HDText>
      {archive ? (
        <HDText>
          {asset.name} akan keluar dari daftar aktif dan cakupan ringkasan yang menyertakannya. Riwayat pengukuran dan
          sumber data tetap tersimpan. Anda dapat memulihkannya dari Perangkat, di bagian Diarsipkan.
        </HDText>
      ) : (
        <HDText>
          {asset.name} akan kembali ke daftar aktif. Riwayat pengukuran dan sumber data tetap tersimpan. Ringkasan
          lokasi mengikuti cakupan yang berlaku.
        </HDText>
      )}
      <AssetWriteFeedback state={archiveWrite || blocked ? state : undefined} onReview={archiveWrite ? onReview : undefined}
        onCheck={onCheck} observedLabel={observedLabel} />
    </HDSheetDialog>
  );
}
