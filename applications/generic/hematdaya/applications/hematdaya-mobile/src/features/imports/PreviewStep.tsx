import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDErrorSummary, type SummaryError } from '@/components/hd/HDErrorSummary';
import { HDImportPreview, ROW_CONVENTION, rowKey } from '@/components/hd/HDImportPreview';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { counterNotes, mappingLine, mappingOf, rowErrorText, streamRow } from '@/features/imports/import-model';
import { ReadFailure } from '@/features/assets/ReadFailure';
import { uploadable, useImportDraft } from '@/features/imports/ImportDraftProvider';
import { ImportFrame, useImportFrame } from '@/features/imports/ImportFrame';
import { CheckStatus, CommitStatus } from '@/features/imports/ImportStatus';
import { useTabNavigation } from '@/features/navigation';

const OPERATION_SENTENCE = 'Konfirmasi impor membuat satu operasi. Mencoba lagi memakai permintaan yang sama, sehingga data tidak tersimpan dua kali.';
const BLOCKED_REASON = 'Impor diblokir. Selesaikan alasan di atas lalu periksa lagi.';
const SUMMARY_ROWS = 5;

/** Pratinjau: the service's preview, the acknowledgment and Konfirmasi impor, with one commit intent (027 D5). */
export function PreviewStep() {
  const draft = useImportDraft();
  const { back, goImportStep, replaceImportStep, showImportResult } = useTabNavigation();
  const frame = useImportFrame();
  const [ackMissing, setAckMissing] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const { preview, reloadPreview, commit } = draft;

  useEffect(() => {
    if (!preview && commit.kind === 'idle') {
      void reloadPreview();
    }
  }, [commit.kind, preview, reloadPreview]);

  // Only the focused step moves on: a Pratinjau left under another tab must not navigate that tab.
  const resultShown = draft.resultShown;
  useFocusEffect(
    useCallback(() => {
      if (commit.kind === 'committed' && !resultShown) {
        showImportResult();
      }
      // Navigation helpers change identity on every render; the commit state alone decides.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [commit.kind, resultShown]),
  );

  /** A stale or gone preview: the same source and answers again, or the file first after a reload (027 D12). */
  const newPreview = async () => {
    if (!uploadable(draft.source)) {
      replaceImportStep('berkas');
      return;
    }
    const next = await draft.runPreview();
    if (next && next.questions.length > 0) {
      goImportStep('pemetaan');
    }
  };

  const recovery = (() => {
    switch (commit.kind) {
      case 'unknown':
      case 'checking':
        return (
          <HDButton variant="primary" fullWidth loading={commit.kind === 'checking'} loadingLabel="Memeriksa status…" onPress={() => void draft.checkStatus()}>
            Periksa status
          </HDButton>
        );
      case 'notYet':
        return (
          <HDButton variant="primary" fullWidth onPress={() => void draft.resend()}>
            Kirim lagi
          </HDButton>
        );
      case 'refused':
        if (commit.outcome.kind === 'stale' || commit.outcome.kind === 'gone') {
          return (
            <HDButton variant="primary" fullWidth loading={draft.check.kind === 'pending'} onPress={() => void newPreview()}>
              Buat pratinjau baru
            </HDButton>
          );
        }
        break;
      default:
        break;
    }
    return null;
  })();

  if (!preview) {
    return (
      <ImportFrame step="pratinjau" frame={frame} footer={recovery}>
        <CommitStatus commit={commit} />
        {draft.check.kind === 'failed' ? (
          <CheckStatus check={draft.check} onRetry={() => void (recovery ? newPreview() : reloadPreview())} />
        ) : null}
        {!recovery && draft.check.kind !== 'failed' ? <HDProgressStatus state="loading" /> : null}
      </ImportFrame>
    );
  }

  const ackText = `Centang konfirmasi bahwa ${preview.invalid_rows} baris tidak valid tidak akan diimpor.`;
  const pending = commit.kind === 'pending';
  const locked = draft.intent !== null;
  const ackRefused = commit.kind === 'refused' && commit.outcome.reason === 'ack';
  const showAck = (ackMissing && !draft.acknowledged) || ackRefused;

  const confirm = async () => {
    if (pending) {
      return;
    }
    setAttempts((count) => count + 1);
    if (preview.needs_acknowledgment && !draft.acknowledged) {
      // Checked before any request: nothing is sent without the acknowledgment (027 D20).
      setAckMissing(true);
      return;
    }
    setAckMissing(false);
    await draft.confirm();
  };

  const footer = recovery ?? (
    <HDButton
      variant="primary"
      fullWidth
      loading={pending}
      loadingLabel="Menyimpan impor…"
      disabledReason={preview.blocked ? BLOCKED_REASON : null}
      onPress={() => void confirm()}>
      Konfirmasi impor
    </HDButton>
  );

  const rowItems: SummaryError[] = draft.errors.length
    ? [
        ...draft.errors.slice(0, SUMMARY_ROWS).map((error) => ({
          key: rowKey(error),
          text: rowErrorText(error),
          target: () => frame.revealTarget(rowKey(error)),
        })),
        { key: 'all-rows', text: 'Lihat semua baris bermasalah', target: () => frame.revealTarget('list') },
      ]
    : [];
  const summary: SummaryError[] = showAck ? [{ key: 'ack', text: ackText, target: () => frame.revealTarget('ack') }] : rowItems;
  const { streams } = mappingOf(preview);

  return (
    <ImportFrame
      step="pratinjau"
      frame={frame}
      footer={footer}>
      <HDErrorSummary
        errors={summary}
        submitCount={(rowItems.length ? draft.previews : 0) + attempts}
        title={showAck ? undefined : 'Baris bermasalah dalam berkas'}
        convention={showAck ? undefined : ROW_CONVENTION}
      />
      <HDImportPreview
        fileName={preview.file_name}
        period={preview.period}
        counts={preview}
        blockReasons={preview.blocked ? preview.block_reasons : []}
        needsAcknowledgment={preview.needs_acknowledgment}
        acknowledged={draft.acknowledged}
        onAcknowledge={draft.setAcknowledged}
        ackError={showAck ? ackText : null}
        ackLocked={locked}
        assumptions={preview.assumptions}
        notes={counterNotes(preview)}
        mapping={[mappingLine(preview), ...streams.map(streamRow)]}
        errors={draft.errors}
        onMoreErrors={draft.nextCursor ? () => void draft.loadMoreErrors() : undefined}
        loadingMore={draft.more.kind === 'pending'}
        rowTarget={(key) => (node) => {
          frame.refFor(key).current = node;
        }}
        ackTarget={(node) => {
          frame.refFor('ack').current = node;
        }}
        listTarget={(node) => {
          frame.refFor('list').current = node;
        }}
      />
      <View style={styles.section}>
        <HDText variant="label">{OPERATION_SENTENCE}</HDText>
        <CommitStatus commit={commit} />
        <CheckStatus check={draft.check} onRetry={() => void newPreview()} />
      </View>
      {draft.more.kind === 'failed' ? (
        <ReadFailure error={draft.more.error} label="Baris berikutnya belum dapat dimuat" retrying={false} onRetry={() => void draft.loadMoreErrors()} />
      ) : null}
      {locked ? null : (
        <HDButton variant="text" onPress={back}>
          Ubah pemetaan
        </HDButton>
      )}
    </ImportFrame>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
});
