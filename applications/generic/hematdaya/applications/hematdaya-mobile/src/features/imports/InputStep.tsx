import { useRef, useState, type ComponentRef } from 'react';
import { Platform, StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDErrorSummary, type SummaryError } from '@/components/hd/HDErrorSummary';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { HDText } from '@/components/hd/HDText';
import { HDTextField } from '@/components/hd/HDTextField';
import { tokens } from '@/design/tokens.generated';
import { useContextPreset } from '@/features/context-preset';
import { EXAMPLES } from '@/features/imports/examples';
import { reselectText, ReselectNotice, useFilePick } from '@/features/imports/FileSource';
import { MAX_IMPORT_BYTES, useImportDraft } from '@/features/imports/ImportDraftProvider';
import { ImportFrame, useImportFrame } from '@/features/imports/ImportFrame';
import { CheckStatus, ImportLocalStatus, UnfinishedImportNotice } from '@/features/imports/ImportStatus';
import { useTabNavigation } from '@/features/navigation';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useDemoSession } from '@/features/workspace/useDemoSession';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

const REQUIREMENTS =
  'CSV UTF-8 (BOM boleh), pemisah koma atau titik koma. Maksimal 10 MiB dan 150.000 baris data. Nama perangkat paling banyak 60 karakter. Energi angka 0 atau lebih; kosong tidak dianggap 0. Zona waktu dan panjang interval dikonfirmasi di langkah berikutnya.';

type Issue = { key: string; text: string };

/** Berkas: the requirements first, then a file or a paste, the examples, and Periksa berkas. */
export function InputStep() {
  const draft = useImportDraft();
  const { status, workspace } = useWorkspace();
  const { preset } = useContextPreset();
  const demo = useDemoSession();
  const { goImportStep, showImportResult, toTabRoot } = useTabNavigation();
  const frame = useImportFrame();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [submits, setSubmits] = useState(0);
  const [pendingReplace, setPendingReplace] = useState<(() => void) | null>(null);
  const fileRef = useRef<ComponentRef<typeof View>>(null);
  const noWorkspace = status === 'ready' && !workspace;
  const file = draft.source?.kind === 'file' && !draft.needsReselect ? draft.source : null;
  const checking = draft.check.kind === 'pending';

  const refuse = (issue: Issue) => {
    setIssues([issue]);
    setSubmits((count) => count + 1);
  };

  /** A new source replaces content, answers and a preview only after the user agrees (027 D16). */
  const askFirst = (apply: () => void) => {
    if (draft.hasContent) {
      setPendingReplace(() => apply);
    } else {
      apply();
    }
  };

  const pickFile = useFilePick(refuse);
  const pick = async (mode: 'replace' | 'reselect') => {
    if (await pickFile(mode)) {
      setIssues([]);
    }
  };

  const check = async () => {
    if (checking) {
      return;
    }
    const source = draft.source;
    if (source && draft.needsReselect) {
      refuse({ key: 'source', text: reselectText(draft.sourceName ?? '') });
      return;
    }
    if (!source) {
      refuse({ key: 'source', text: 'Pilih berkas CSV atau tempel isi CSV.' });
      return;
    }
    if (source.kind === 'paste' && source.text.length > MAX_IMPORT_BYTES) {
      refuse({ key: 'size', text: 'Ukuran tempelan.csv melebihi batas 10 MiB.' });
      return;
    }
    setIssues([]);
    setSubmits((count) => count + 1);
    if (await draft.runPreview()) {
      goImportStep('pemetaan');
    }
  };

  const sourceKey = file || draft.source?.kind === 'file' ? 'file' : 'paste';
  const sourceTarget = () => frame.revealTarget(sourceKey);
  // The service's refusal of the file, one item per problem it found, each linked to the source (027 Error table).
  const refused = draft.check.kind === 'failed' && draft.check.outcome.kind === 'refused' ? draft.check.outcome.items : [];
  const summary: SummaryError[] = [...issues, ...refused].map((issue) => ({ key: issue.key, text: issue.text, target: sourceTarget }));
  const storedResult = draft.commit.kind === 'committed' && !draft.resultShown;

  if (draft.intent || draft.commit.kind === 'unknown') {
    return (
      <ImportFrame step="berkas" frame={frame}>
        <UnfinishedImportNotice />
      </ImportFrame>
    );
  }

  return (
    <ImportFrame
      step="berkas"
      frame={frame}
      footer={
        noWorkspace ? (
          <HDButton variant="primary" fullWidth loading={demo.state.kind === 'pending'} onPress={() => void demo.start('empty')}>
            Mulai ruang kerja
          </HDButton>
        ) : (
          <HDButton variant="primary" fullWidth loading={checking} loadingLabel="Memeriksa berkas…" onPress={() => void check()}>
            Periksa berkas
          </HDButton>
        )
      }>
      {noWorkspace ? (
        <View style={styles.section}>
          <SessionEndedNotice />
          <HDNotice tone="attention" title="Belum ada ruang kerja">
            Impor memerlukan ruang kerja. Mulai ruang kerja sementara untuk melanjutkan; isi yang sudah ditempel tetap ada.
          </HDNotice>
          {demo.state.kind === 'failed' || demo.state.kind === 'unknown' || demo.state.kind === 'unsent' ? (
            <HDProgressStatus state="failure" label="Belum berhasil" detail={demo.state.error.message} />
          ) : null}
        </View>
      ) : null}
      {storedResult ? (
        <HDNotice tone="success" title="Impor sebelumnya sudah tersimpan." action={<HDButton onPress={showImportResult}>Lihat hasil</HDButton>} />
      ) : null}
      <HDErrorSummary errors={summary} submitCount={submits} />
      <HDNotice tone="info" title="Syarat berkas">
        {REQUIREMENTS}
      </HDNotice>
      <ImportLocalStatus unsent={draft.unsent} failed={draft.persistenceFailed} />
      <CheckStatus check={draft.check} onRetry={() => void check()} />
      {draft.textDropped ? <HDNotice tone="attention" title="Isi tempelan terlalu besar untuk disimpan di peramban. Tempel ulang isinya." /> : null}
      <View
        ref={(node) => {
          fileRef.current = node;
          frame.refFor('file').current = node;
        }}
        style={styles.section}
        {...FOCUSABLE_BY_SCRIPT}>
        {draft.needsReselect && draft.sourceName ? (
          <ReselectNotice name={draft.sourceName} onPick={() => void pick('reselect')} />
        ) : file ? (
          <>
            <HDText variant="bodyStrong">{`Berkas: ${draft.sourceName}`}</HDText>
            {Platform.OS === 'web' ? <HDText variant="label">Setelah peramban ditutup, berkas perlu dipilih ulang.</HDText> : null}
            <View style={styles.row}>
              <HDButton onPress={() => askFirst(() => void pick('replace'))}>Ganti berkas</HDButton>
              <HDButton variant="text" onPress={draft.clearSource}>
                Hapus berkas
              </HDButton>
            </View>
          </>
        ) : (
          <HDButton icon="chevronRight" onPress={() => askFirst(() => void pick('replace'))}>
            Pilih berkas CSV
          </HDButton>
        )}
      </View>
      {file || draft.needsReselect ? null : (
        <HDTextField
          label="Atau tempel isi CSV"
          optional
          help="Untuk berkas besar, pilih berkas."
          multiline
          value={draft.source?.kind === 'paste' ? draft.source.text : ''}
          onChange={draft.setText}
          editable={!checking}
          draftNote={draft.source?.kind === 'paste' ? 'Isi tetap tersimpan bila Anda kembali.' : undefined}
          inputRef={(node) => {
            frame.refFor('paste').current = node;
          }}
        />
      )}
      <HDDisclosure summary="Contoh berkas yang dapat disalin">
        {EXAMPLES(preset).map((example) => (
          <View key={example.id} role="group" aria-label={example.label} style={styles.example}>
            <HDText variant="bodyStrong">{example.label}</HDText>
            <HDText variant="label" selectable style={styles.code}>
              {example.text}
            </HDText>
            <HDButton onPress={() => askFirst(() => draft.replaceSource({ kind: 'paste', text: example.text }))}>Gunakan contoh ini</HDButton>
          </View>
        ))}
      </HDDisclosure>
      <HDButton variant="text" onPress={toTabRoot}>
        Tutup impor (draf tetap tersimpan)
      </HDButton>
      <HDSheetDialog
        open={pendingReplace !== null}
        title="Ganti isi impor?"
        onClose={() => setPendingReplace(null)}
        returnFocusTo={fileRef}
        footer={
          <>
            <HDButton
              variant="primary"
              onPress={() => {
                const apply = pendingReplace;
                setPendingReplace(null);
                apply?.();
              }}>
              Ganti
            </HDButton>
            <HDButton onPress={() => setPendingReplace(null)}>Batal</HDButton>
          </>
        }>
        <HDText>Isi sekarang, jawaban pemetaan, dan pratinjau akan diganti. Data yang sudah tersimpan tidak berubah.</HDText>
      </HDSheetDialog>
    </ImportFrame>
  );
}

// Web only: an error summary's link can focus the file control without adding it to the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
  example: {
    gap: tokens.space.stackTight,
    padding: tokens.space['12'],
    borderRadius: tokens.radius.control,
    borderWidth: tokens.size.borderControl,
    borderColor: tokens.color.borderDecorative,
  },
  code: { fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }) },
});
