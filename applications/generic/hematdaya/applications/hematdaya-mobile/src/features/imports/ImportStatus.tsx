import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import type { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDText } from '@/components/hd/HDText';
import { HDNotice } from '@/components/hd/HDNotice';
import { tokens } from '@/design/tokens.generated';
import type { CheckState, CommitState } from '@/features/imports/ImportDraftProvider';
import { useTabNavigation } from '@/features/navigation';

const UNKNOWN_DETAIL = 'Jawaban layanan tidak diterima. Periksa status sebelum mencoba lagi; impor tidak akan tersimpan dua kali.';
const NOT_YET_DETAIL =
  'Saat diperiksa, impor ini belum tersimpan. Data tersimpan sebelumnya tidak berubah. Kirim lagi memakai permintaan yang sama.';
const UNCHANGED = 'Data yang tersimpan tidak berubah.';

/** The service's message, then the details it sent where they carry specifics, then the reference. */
export function failureLines(error: ApiError | null, { details = false }: { details?: boolean } = {}): string[] {
  if (!error) {
    return [];
  }
  return [
    error.message,
    ...(details ? error.details.map((detail) => detail.msg) : []),
    ...(error.requestId ? [`ID referensi: ${error.requestId}.`] : []),
  ];
}

function Lines({ lines, action }: { lines: string[]; action?: ReactNode }) {
  if (!lines.length && !action) {
    return null;
  }
  return (
    <View style={styles.lines}>
      {lines.map((line) => (
        <HDText key={line}>{line}</HDText>
      ))}
      {action}
    </View>
  );
}

/**
 * A preview's state in the always-mounted status region (027 Error table). A refusal keeps the source and
 * answers; a lost preview saved nothing and may be sent again when the service allows it (027 D4).
 */
export function CheckStatus({ check, onRetry }: { check: CheckState; onRetry: () => void }) {
  if (check.kind !== 'failed' || check.outcome.kind === 'ended') {
    return <HDProgressStatus state={null} />;
  }
  const { error, outcome } = check;
  const label =
    outcome.kind === 'notFinished'
      ? 'Berkas belum selesai diperiksa'
      : outcome.kind === 'assetGone'
        ? 'Perangkat yang dipilih tidak ditemukan lagi. Pilih ulang perangkatnya.'
        : 'Berkas belum dapat diperiksa';
  const lines = [...failureLines(error), ...(outcome.kind === 'notFinished' ? [UNCHANGED] : [])];
  return (
    <HDProgressStatus
      state="failure"
      label={label}
      action={
        <Lines
          lines={lines}
          action={
            outcome.canRetry ? (
              <HDButton variant="text" icon="refresh" onPress={onRetry}>
                Coba lagi
              </HDButton>
            ) : null
          }
        />
      }
    />
  );
}

export function UnfinishedImportNotice() {
  const { goImportStep } = useTabNavigation();
  return (
    <HDNotice
      tone="attention"
      title="Ada impor yang belum selesai."
      action={<HDButton onPress={() => goImportStep('pratinjau')}>Buka pratinjau</HDButton>}
    />
  );
}

/** A commit's state: pending, unknown until checked, not yet recorded, or a definite refusal (027 D5, D6). */
export function CommitStatus({ commit }: { commit: CommitState }) {
  switch (commit.kind) {
    case 'pending':
      return <HDProgressStatus state="saving" label="Menyimpan impor…" detail="Berkas besar dapat memerlukan waktu hingga satu menit." />;
    case 'checking':
      return <HDProgressStatus state="loading" label="Memeriksa status…" />;
    case 'unknown':
      return (
        <HDProgressStatus
          state="unknown"
          label="Status impor belum diketahui"
          detail={UNKNOWN_DETAIL}
          action={
            <Lines lines={Array.from(new Set([
              ...failureLines(commit.error),
              ...(commit.checkError ? ['Status impor belum dapat diperiksa', ...failureLines(commit.checkError)] : []),
            ]))} />
          }
        />
      );
    case 'notYet':
      return <HDProgressStatus state="unknown" label="Impor belum tercatat" detail={NOT_YET_DETAIL} />;
    case 'refused': {
      const { outcome, error } = commit;
      const label =
        outcome.kind === 'stale' ? 'Pratinjau sudah tidak berlaku' : outcome.kind === 'gone' ? 'Pratinjau sudah tidak tersedia' : 'Impor belum disimpan';
      return <HDProgressStatus state="failure" label={label} action={<Lines lines={failureLines(error, { details: outcome.kind !== 'gone' })} />} />;
    }
    default:
      return <HDProgressStatus state={null} />;
  }
}

const styles = StyleSheet.create({
  lines: { gap: tokens.space.stackTight },
});
