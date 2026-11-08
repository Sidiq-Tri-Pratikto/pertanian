import { errorMessage } from '@/features/localization/error-copy';
import { useCopy, currentCopy } from '@/features/localization/messages';
import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import type { ApiError } from '@/api/errors';
import type { AssetWriteState } from '@/features/assets/useAssetMutations';

function reference(error: ApiError): string | undefined {
  return error.requestId ? currentCopy(`ID referensi: ${error.requestId}.`, `Reference ID: ${error.requestId}.`) : undefined;
}

export function AssetWriteFeedback({
  state, onReview, onCheck, observedLabel,
}: { state: AssetWriteState | undefined; onReview?: () => void; onCheck?: () => void; observedLabel?: string }) {
  const say = useCopy();
  switch (state?.kind) {
    case 'saving':
      return <HDProgressStatus state="saving" />;
    case 'draft-checking':
      return <HDProgressStatus state="loading" label={say("Memeriksa detail perangkat terkini…", "Checking current device details…")} />;
    case 'draft-blocked':
      return <HDProgressStatus state="failure" label={say("Draf belum dapat diperiksa", "Could not check the draft")}
        detail={[errorMessage(state.error), reference(state.error)].filter(Boolean).join(' ')} />;
    case 'draft-ready':
      return <HDProgressStatus state="unknown" label={say("Detail terkini sudah diperiksa", "Current details checked")}
        detail={say("Periksa draf Anda, lalu pilih Simpan untuk mengirim perubahan yang masih diperlukan.", "Review your draft and choose Save to send any changes you still want.")} />;
    case 'draft-review':
      return <HDProgressStatus state="unknown" label={say("Detail perangkat berubah sejak draf disimpan", "Device details changed since this draft")}
        detail={say(`Saat diperiksa: ${observedLabel ?? state.observed.name}. Tinjau data terkini sebelum menyimpan.`, `When checked: ${observedLabel ?? state.observed.name}. Review the current details before saving.`)}
        action={onReview ? <HDButton onPress={onReview}>{say("Tinjau data terkini", "Review current details")}</HDButton> : null} />;
    case 'checking':
      return <HDProgressStatus state="loading" label={say("Memeriksa data terkini…", "Checking current details…")} detail={reference(state.error)} />;
    case 'offline':
      return <HDProgressStatus state="failure" label={say("Perubahan belum dikirim", "Changes not sent")}
        detail={say("Anda sedang luring. Sambungkan perangkat, lalu kirim lagi saat siap.", "You are offline. Reconnect and send again when ready.")} />;
    case 'refused':
      return <HDProgressStatus state="failure" label={say("Perubahan ditolak", "Changes refused")} detail={[errorMessage(state.error), reference(state.error)].filter(Boolean).join(' ')} />;
    case 'unresolved':
      return <HDProgressStatus state="unknown" label={say("Hasil perubahan belum diketahui", "Save status unknown")}
        detail={`Pemeriksaan data terkini belum berhasil. Draf tetap tersimpan. ${[errorMessage(state.readError), reference(state.readError)].filter(Boolean).join(' ')} ${
          state.error.requestId && state.error.requestId !== state.readError.requestId
            ? say(`ID referensi pengiriman: ${state.error.requestId}.`, `Request reference ID: ${state.error.requestId}.`) : ''
        }`.trim()}
        action={onCheck ? <HDButton onPress={onCheck}>{say("Periksa data terkini", "Check current details")}</HDButton> : null} />;
    case 'diverged':
    case 'reviewed':
      return <HDProgressStatus state="unknown" label={say("Data terkini berbeda dari perubahan yang dikirim", "Current details differ from the changes sent")}
        detail={`Saat diperiksa: ${observedLabel ?? state.observed.name}. Permintaan awal mungkin masih diproses. ${
          state.kind === 'diverged' ? say("Tinjau data terkini sebelum mengirim perubahan baru.", "Review the current details before sending new changes.") : say("Periksa perubahan Anda, lalu kirim lagi jika masih diperlukan.", "Review your changes and send them again if needed.")
        } ${reference(state.error) ?? ''}`.trim()}
        action={state.kind === 'diverged' && onReview
          ? <HDButton onPress={onReview}>{say("Tinjau data terkini", "Review current details")}</HDButton> : null} />;
    default:
      return <HDProgressStatus state={null} />;
  }
}
