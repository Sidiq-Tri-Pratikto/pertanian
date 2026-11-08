import { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDNotice } from '@/components/hd/HDNotice';
import { useLocale } from '@/features/localization/locale';
import { formatDateTime } from '@/lib/format';

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

/** Announce the original successful fetch or explain that the selected data has no saved copy. */
export function SavedReadStatus({ offline, fetchedAt, timezone, failed = false }: {
  offline: boolean; fetchedAt?: number; timezone?: string; failed?: boolean;
}) {
  const locale = useLocale();
  if (!offline && !failed) return null;
  if (fetchedAt === undefined || timezone === undefined) {
    return offline ? (
      <HDNotice tone="info" title={locale === 'en' ? 'Offline · no saved data' : 'Offline · belum ada data tersimpan'} live>
        {locale === 'en' ? 'There is no saved data for this selection. Reconnect to load it.'
          : 'Data untuk pilihan ini belum tersimpan. Sambungkan perangkat untuk memuatnya.'}
      </HDNotice>
    ) : null;
  }
  const title = locale === 'en'
    ? (offline ? 'Offline · showing saved data' : 'Showing the last confirmed data')
    : (offline ? 'Offline · menampilkan data tersimpan' : 'Menampilkan data terakhir yang terkonfirmasi');
  const label = locale === 'en' ? 'Last loaded' : 'Terakhir dimuat';
  return (
    <HDNotice tone="info" title={title} live>
      {`${label}: ${formatDateTime(new Date(fetchedAt).toISOString(), timezone, locale)} (${timezone}).`}
    </HDNotice>
  );
}
