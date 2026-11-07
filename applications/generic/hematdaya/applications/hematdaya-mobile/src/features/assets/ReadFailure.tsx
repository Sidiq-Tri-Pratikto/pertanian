import { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';

type ReadFailureProps = {
  error: unknown;
  label: string;
  retrying: boolean;
  onRetry: () => void;
  /** Older numbers are still on screen, so the status says they are the last confirmed ones. */
  kept?: boolean;
};

const KEPT_SENTENCE = 'Angka yang tampil adalah data terakhir yang terkonfirmasi.';

/** A failed read: the service's message and reference, and Coba lagi only when the service allows a retry. */
export function ReadFailure({ error, label, retrying, onRetry, kept = false }: ReadFailureProps) {
  if (error === null || error === undefined) {
    return <HDProgressStatus state={null} />;
  }
  const failure = ApiError.from(error);
  const reference = failure.requestId ? `ID referensi: ${failure.requestId}.` : null;
  return (
    <HDProgressStatus
      state="failure"
      label={label}
      detail={[failure.message, reference, kept ? KEPT_SENTENCE : null].filter(Boolean).join(' ')}
      action={
        failure.recovery.retryable === true ? (
          <HDButton variant="text" icon="refresh" loading={retrying} onPress={onRetry}>
            Coba lagi
          </HDButton>
        ) : null
      }
    />
  );
}
