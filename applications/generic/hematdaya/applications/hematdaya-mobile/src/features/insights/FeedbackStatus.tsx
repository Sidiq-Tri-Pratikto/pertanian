import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { ACTION_LABELS, confirmedText } from '@/features/insights/feedback-copy';
import type { FeedbackState } from '@/features/insights/useFeedback';

/** Pending, failure with retry, unknown with a safe check, or confirmation after the service acknowledged. */
export function FeedbackStatus({ state, timezone, onRetry }: { state: FeedbackState; timezone: string; onRetry: () => void }) {
  if (state.kind === 'confirmed') {
    return <HDNotice tone="success" live title="Umpan balik diterima">{confirmedText(state.result, timezone)}</HDNotice>;
  }
  return (
    <HDProgressStatus
      state={state.kind === 'pending' ? 'saving' : state.kind === 'failed' ? 'failure' : state.kind === 'unknown' ? 'unknown' : null}
      label={
        state.kind === 'pending'
          ? `Mengirim: ${ACTION_LABELS[state.action]}…`
          : state.kind === 'failed'
            ? 'Umpan balik belum tersimpan'
            : 'Status umpan balik belum diketahui'
      }
      detail={
        state.kind === 'failed'
          ? `${state.error.message}${state.error.requestId ? ` ID referensi: ${state.error.requestId}.` : ''} Tidak ada yang berubah.`
          : state.kind === 'unknown'
            ? 'Jawaban layanan tidak diterima. Memeriksa lagi tidak akan mengirim umpan balik dua kali.'
            : null
      }
      action={
        (state.kind === 'failed' && state.canRetry) || state.kind === 'unknown' ? (
          <HDButton variant="text" icon="refresh" onPress={onRetry}>
            {state.kind === 'unknown' ? 'Periksa lagi' : 'Coba lagi'}
          </HDButton>
        ) : null
      }
    />
  );
}
