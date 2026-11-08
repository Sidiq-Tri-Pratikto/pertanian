import { errorMessage } from '@/features/localization/error-copy';
import { useCopy } from '@/features/localization/messages';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { actionLabel, confirmedText } from '@/features/insights/feedback-copy';
import type { FeedbackState } from '@/features/insights/useFeedback';

/** Pending, failure with retry, unknown with a safe check, or confirmation after the service acknowledged. */
export function FeedbackStatus({ state, timezone, onRetry }: { state: FeedbackState; timezone: string; onRetry: () => void }) {
  const say = useCopy();
  if (state.kind === 'unsent') {
    return <HDProgressStatus state="failure" label={say("Umpan balik belum dikirim", "Feedback not sent")} detail={errorMessage(state.error)} />;
  }
  if (state.kind === 'confirmed') {
    return <HDNotice tone="success" live title={say("Umpan balik diterima", "Feedback received")}>{confirmedText(state.result, timezone)}</HDNotice>;
  }
  return (
    <HDProgressStatus
      state={state.kind === 'pending' ? 'saving' : state.kind === 'failed' ? 'failure' : state.kind === 'unknown' ? 'unknown' : null}
      label={
        state.kind === 'pending'
          ? say(`Mengirim: ${actionLabel(state.action)}…`, `Sending: ${actionLabel(state.action)}…`)
          : state.kind === 'failed'
            ? say("Umpan balik belum tersimpan", "Feedback could not be saved")
            : say("Status umpan balik belum diketahui", "Feedback status unknown")
      }
      detail={
        state.kind === 'failed'
          ? `${errorMessage(state.error)}${state.error.requestId ? say(` ID referensi: ${state.error.requestId}.`, ` Reference ID: ${state.error.requestId}.`) : ''}${say(' Tidak ada yang berubah.', ' No changes were made.')}`
          : state.kind === 'unknown'
            ? [state.unsent ? say("Pemeriksaan belum dikirim. Sambungkan perangkat lalu coba lagi.", "Reconnect before checking again.") : null,
                say("Jawaban layanan tidak diterima. Memeriksa lagi tidak akan mengirim umpan balik dua kali.", "We didn’t receive a response. Checking again is safe.")].filter(Boolean).join(' ')
            : null
      }
      action={
        (state.kind === 'failed' && state.canRetry) || state.kind === 'unknown' ? (
          <HDButton variant="text" icon="refresh" onPress={onRetry}>
            {state.kind === 'unknown' ? say("Periksa lagi", "Check again") : say("Coba lagi", "Try again")}
          </HDButton>
        ) : null
      }
    />
  );
}
