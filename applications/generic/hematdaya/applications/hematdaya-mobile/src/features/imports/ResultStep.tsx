import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { mappingOf, resultModel } from '@/features/imports/import-model';
import { useImportDraft } from '@/features/imports/ImportDraftProvider';
import { ImportFrame, useImportFrame } from '@/features/imports/ImportFrame';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';

const SCOPE_NOTE =
  'Jawaban cakupan hanya berlaku antar perangkat dalam berkas ini. Bila ruang kerja sudah berisi perangkat lain, total gabungan menunggu konfirmasi cakupan; nilai per perangkat tetap tampil.';
const UNKNOWN_OVERLAP_NOTE = 'Anda memilih “Belum tahu”: nilai tampil per perangkat dan total gabungan tidak dihitung.';

/** Hasil: what the service stored, stated plainly, and where to see it, or that it is not visible yet (027 D21). */
export function ResultStep() {
  const draft = useImportDraft();
  const router = useRouter();
  const { setPeriod } = useNavigationContext();
  const { toTabRoot, replaceImportStep } = useTabNavigation();
  const frame = useImportFrame();
  const { commit, markResultShown } = draft;

  useEffect(() => {
    markResultShown();
  }, [markResultShown]);

  if (commit.kind !== 'committed') {
    return null;
  }
  const timezone = commit.result.period?.timezone ?? (draft.preview ? mappingOf(draft.preview).timezone : 'Asia/Jakarta');
  const model = resultModel(commit.result, { found: commit.found, timezone });
  const scope = (draft.sentAnswers ?? draft.answers).scope;

  const leave = (landing: boolean) => {
    if (landing && model.landing) {
      const { preset, start_date, end_date } = model.landing;
      setPeriod({ preset, start_date, end_date });
    }
    toTabRoot();
    router.navigate('/beranda');
    draft.finish();
  };

  return (
    <ImportFrame
      step="hasil"
      frame={frame}
      footer={
        model.primary === 'landing' ? (
          <HDButton variant="primary" fullWidth icon="chevronRight" onPress={() => leave(true)}>
            Lihat periode data
          </HDButton>
        ) : (
          <HDButton variant="primary" fullWidth onPress={() => leave(false)}>
            Kembali ke Beranda
          </HDButton>
        )
      }>
      <HDNotice tone="success" title={model.title} live>
        {model.note ?? undefined}
      </HDNotice>
      {model.clockNotice ? <HDNotice tone={model.clockNotice.tone} title={model.clockNotice.text} /> : null}
      {model.nothingNew ? <HDNotice tone="info" title={model.nothingNew} /> : null}
      {model.longRange ? <HDNotice tone="info" title={model.longRange} /> : null}
      <View style={styles.section}>
        <HDText variant="label">{model.confirmedAt}</HDText>
        {model.rows.map((row) => (
          <View key={row.term} accessible accessibilityLabel={`${row.term}: ${row.value}`} style={styles.row}>
            <HDText variant="label" tone="secondary">
              {row.term}
            </HDText>
            <HDText variant="bodyStrong">{row.value}</HDText>
          </View>
        ))}
        <HDText variant="label">Asal data: Data historis · Impor CSV</HDText>
      </View>
      {scope ? (
        <HDNotice tone="neutral" title={SCOPE_NOTE}>
          {scope === 'unknown_overlap' ? UNKNOWN_OVERLAP_NOTE : undefined}
        </HDNotice>
      ) : null}
      <HDButton
        variant="text"
        onPress={() => {
          replaceImportStep('berkas');
          draft.finish();
        }}>
        Impor berkas lain
      </HDButton>
    </ImportFrame>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  row: { gap: tokens.space['4'] },
});
