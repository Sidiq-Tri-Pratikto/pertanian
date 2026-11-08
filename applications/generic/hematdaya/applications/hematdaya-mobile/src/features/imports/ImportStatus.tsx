import { errorMessage } from '@/features/localization/error-copy';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import type { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDText } from '@/components/hd/HDText';
import { HDNotice } from '@/components/hd/HDNotice';
import { tokens } from '@/design/tokens.generated';
import type { CheckState, CommitState } from '@/features/imports/ImportDraftProvider';
import { getLocale, useLocale, type Locale } from '@/features/localization/locale';
import { currentCopy, useCopy, message } from '@/features/localization/messages';
import { useTabNavigation } from '@/features/navigation';

const UNKNOWN_DETAIL = 'Jawaban layanan tidak diterima. Periksa status sebelum mencoba lagi; impor tidak akan tersimpan dua kali.';
function copyNotYetDetail(): string {
  return currentCopy("Saat diperiksa, impor ini belum tersimpan. Data tersimpan sebelumnya tidak berubah. Kirim lagi memakai permintaan yang sama.", "The service has no saved import yet. You can send the same request again.");
}
function copyUnchanged(): string {
  return currentCopy("Data yang tersimpan tidak berubah.", "Your saved data is unchanged.");
}

/** The service's message, then the details it sent where they carry specifics, then the reference. */
export function failureLines(error: ApiError | null, {
  details = false, locale,
}: { details?: boolean; locale?: Locale } = {}): string[] {
  if (!error) {
    return [];
  }
  const language = locale ?? getLocale();
  const useMessage = language === error.language;
  const reference = language === 'en' ? 'Reference ID' : 'ID referensi';
  return [
    ...(errorMessage(error) ? [errorMessage(error)!] : []),
    ...(useMessage && details ? error.details.map((detail) => detail.msg) : []),
    ...(error.requestId ? [`${reference}: ${error.requestId}.`] : []),
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
  const say = useCopy();
  if (check.kind !== 'failed' || check.outcome.kind === 'ended') {
    return <HDProgressStatus state={null} />;
  }
  const { error, outcome } = check;
  const label =
    outcome.kind === 'notFinished'
      ? say("Berkas belum selesai diperiksa", "File check incomplete")
      : outcome.kind === 'assetGone'
        ? say("Perangkat yang dipilih tidak ditemukan lagi. Pilih ulang perangkatnya.", "The device is no longer available. Choose a device again.")
        : say("Berkas belum dapat diperiksa", "Could not check the file");
  const lines = [...failureLines(error), ...(outcome.kind === 'notFinished' ? [copyUnchanged()] : [])];
  return (
    <HDProgressStatus
      state="failure"
      label={label}
      action={
        <Lines
          lines={lines}
          action={
            outcome.canRetry ? (
              <HDButton variant="text" icon="refresh" onPress={onRetry}>{say("Coba lagi", "Try again")}</HDButton>
            ) : null
          }
        />
      }
    />
  );
}

export function UnfinishedImportNotice() {
  const say = useCopy();
  const { goImportStep } = useTabNavigation();
  return (
    <HDNotice
      tone="attention"
      title={say("Ada impor yang belum selesai.", "You have an unfinished import.")}
      action={<HDButton onPress={() => goImportStep('pratinjau')}>{say("Buka pratinjau", "Open preview")}</HDButton>}
    />
  );
}

/** A commit's state: pending, unknown until checked, not yet recorded, or a definite refusal (027 D5, D6). */
export function CommitStatus({ commit }: { commit: CommitState }) {
  const say = useCopy();
  const locale = useLocale();
  switch (commit.kind) {
    case 'pending':
      return <HDProgressStatus state="saving" label={say("Menyimpan impor…", "Saving import…")} detail={say("Berkas besar dapat memerlukan waktu hingga satu menit.", "Large files can take up to one minute.")} />;
    case 'checking':
      return <HDProgressStatus state="loading" label={say("Memeriksa status…", "Checking status…")} />;
    case 'unknown':
      return (
        <HDProgressStatus
          state="unknown"
          label={message(locale, 'importUnknown')}
          detail={locale === 'en'
            ? 'The service did not confirm the import. Check its status before trying again.'
            : UNKNOWN_DETAIL}
          action={
            <Lines lines={Array.from(new Set([
              ...failureLines(commit.error, { locale }),
              ...(commit.checkError ? [
                locale === 'en' ? 'Could not check the import status' : 'Status impor belum dapat diperiksa',
                ...failureLines(commit.checkError, { locale }),
              ] : []),
            ]))} />
          }
        />
      );
    case 'notYet':
      return <HDProgressStatus state="unknown" label={say("Impor belum tercatat", "Import has not been saved")} detail={copyNotYetDetail()} />;
    case 'refused': {
      const { outcome, error } = commit;
      const label =
        outcome.kind === 'stale' ? say("Pratinjau sudah tidak berlaku", "Preview expired") : outcome.kind === 'gone' ? say("Pratinjau sudah tidak tersedia", "Preview no longer available") : say("Impor belum disimpan", "Import was not saved");
      return <HDProgressStatus state="failure" label={label} action={<Lines lines={failureLines(error, { details: outcome.kind !== 'gone' })} />} />;
    }
    default:
      return <HDProgressStatus state={null} />;
  }
}

const styles = StyleSheet.create({
  lines: { gap: tokens.space.stackTight },
});

export function ImportLocalStatus({ unsent, failed }: { unsent: ApiError | null; failed: boolean }) {
  const say = useCopy();
  return (
    <>
      {unsent ? <HDProgressStatus state="failure" label={say("Impor belum dikirim", "Import not sent")} detail={unsent.message} /> : null}
      {failed ? (
        <HDNotice tone="attention" title={say("Pemulihan draf belum terkonfirmasi", "Draft recovery unconfirmed")} live>{say("Isian masih tersedia selama aplikasi terbuka. Periksa penyimpanan perangkat sebelum memulai ulang.", "Your entries are available while the app is open. Check device storage before restarting.")}</HDNotice>
      ) : null}
    </>
  );
}
