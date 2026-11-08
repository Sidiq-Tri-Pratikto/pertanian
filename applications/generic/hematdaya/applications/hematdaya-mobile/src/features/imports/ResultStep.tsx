import { currentCopy, useCopy } from '@/features/localization/messages';
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

function copyScopeNote(): string {
  return currentCopy("Jawaban cakupan hanya berlaku antar perangkat dalam berkas ini. Bila ruang kerja sudah berisi perangkat lain, total gabungan menunggu konfirmasi cakupan; nilai per perangkat tetap tampil.", "Your scope answer applies to the devices in this file. Review scope before combining them with other devices. Individual readings are available.");
}
function copyUnknownOverlapNote(): string {
  return currentCopy("Anda memilih “Belum tahu”: nilai tampil per perangkat dan total gabungan tidak dihitung.", "You selected “Not sure”. You can view individual readings while the combined total is unavailable.");
}

/** Hasil: what the service stored, stated plainly, and where to see it, or that it is not visible yet (027 D21). */
export function ResultStep() {
  const say = useCopy();
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
          <HDButton variant="primary" fullWidth icon="chevronRight" onPress={() => leave(true)}>{say("Lihat periode data", "View data period")}</HDButton>
        ) : (
          <HDButton variant="primary" fullWidth onPress={() => leave(false)}>{say("Kembali ke Beranda", "Back to Home")}</HDButton>
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
        <HDText variant="label">{say("Asal data: Data historis · Impor CSV", "Source: Historical data · CSV import")}</HDText>
      </View>
      {scope ? (
        <HDNotice tone="neutral" title={copyScopeNote()}>
          {scope === 'unknown_overlap' ? copyUnknownOverlapNote() : undefined}
        </HDNotice>
      ) : null}
      <HDButton
        variant="text"
        onPress={() => {
          replaceImportStep('berkas');
          draft.finish();
        }}>{say("Impor berkas lain", "Import another file")}</HDButton>
    </ImportFrame>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stackTight },
  row: { gap: tokens.space['4'] },
});
