import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import type { ApiError } from '@/api/errors';
import type { AssetWriteState } from '@/features/assets/useAssetMutations';

function reference(error: ApiError): string | undefined {
  return error.requestId ? `ID referensi: ${error.requestId}.` : undefined;
}

export function AssetWriteFeedback({
  state, onReview, observedLabel,
}: { state: AssetWriteState | undefined; onReview?: () => void; observedLabel?: string }) {
  switch (state?.kind) {
    case 'saving':
      return <HDProgressStatus state="saving" />;
    case 'checking':
      return <HDProgressStatus state="loading" label="Memeriksa data terkini…" detail={reference(state.error)} />;
    case 'offline':
      return <HDProgressStatus state="failure" label="Perubahan belum dikirim"
        detail="Anda sedang luring. Sambungkan perangkat, lalu kirim lagi saat siap." />;
    case 'refused':
      return <HDProgressStatus state="failure" label="Perubahan ditolak" detail={[state.error.message, reference(state.error)].filter(Boolean).join(' ')} />;
    case 'unresolved':
      return <HDProgressStatus state="unknown" label="Hasil perubahan belum diketahui"
        detail={`Pemeriksaan data terkini belum berhasil. Draf tetap tersimpan. ${[state.readError.message, reference(state.readError)].filter(Boolean).join(' ')} ${
          state.error.requestId && state.error.requestId !== state.readError.requestId
            ? `ID referensi pengiriman: ${state.error.requestId}.` : ''
        }`.trim()} />;
    case 'diverged':
    case 'reviewed':
      return <HDProgressStatus state="unknown" label="Data terkini berbeda dari perubahan yang dikirim"
        detail={`Saat diperiksa: ${observedLabel ?? state.observed.name}. Permintaan awal mungkin masih diproses. ${
          state.kind === 'diverged' ? 'Tinjau data terkini sebelum mengirim perubahan baru.' : 'Periksa perubahan Anda, lalu kirim lagi jika masih diperlukan.'
        } ${reference(state.error) ?? ''}`.trim()}
        action={state.kind === 'diverged' && onReview
          ? <HDButton onPress={onReview}>Tinjau data terkini</HDButton> : null} />;
    default:
      return <HDProgressStatus state={null} />;
  }
}
