import { StyleSheet, View } from 'react-native';

import type { InsightList } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDInsightSummary } from '@/components/hd/HDInsightSummary';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { evidenceModel } from '@/features/insights/evidence-model';
import { useInsights } from '@/features/insights/useInsights';
import { useTabNavigation } from '@/features/navigation';
import { RestoreNotice } from '@/features/insights/RestoreNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDateRange } from '@/lib/format';

/** S07: observations that met the rule, data notices apart from them, and honest empty states. */
export function SaranScreen() {
  const { workspace } = useWorkspace();
  const { openSettings } = useTabNavigation();
  const insights = useInsights();

  return (
    <HDScreen title="Saran" subtitle="Pengamatan berbasis bukti, bukan diagnosis">
      {workspace === null ? (
        <NoData />
      ) : insights.data === undefined ? (
        <HDProgressStatus
          state={insights.isError ? 'failure' : 'loading'}
          label={insights.isError ? 'Saran belum dapat dimuat' : 'Memuat saran…'}
          detail={insights.error?.message}
          action={
            insights.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void insights.refetch()}>
                Coba lagi
              </HDButton>
            ) : null
          }
        />
      ) : (
        <SaranList data={insights.data} />
      )}
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

function NoData() {
  const { openImport } = useTabNavigation();
  return (
    <View style={styles.section}>
      <HDText variant="section">Belum ada saran</HDText>
      <HDText>Saran hanya muncul dari data yang tercatat. Ini bukan penilaian efisiensi atau keamanan.</HDText>
      <HDButton variant="text" onPress={() => openImport()}>
        Tentang impor data
      </HDButton>
    </View>
  );
}

function SaranList({ data }: { data: InsightList }) {
  const { openEvidence, openAssetHistoryChooser, openHidden } = useTabNavigation();
  const learningOnly = data.comparable_count === 0 && data.learning_count > 0;

  return (
    <>
      <HDText variant="labelStrong">
        {formatDateRange(data.window.start_date, data.window.end_date)} · {data.window.timezone}
      </HDText>
      <RestoreNotice timezone={data.window.timezone} />
      <View role="list" aria-label="Pengamatan" style={styles.section}>
        {data.observations.map((insight) => {
          const model = evidenceModel(insight);
          return (
            <View key={insight.id} role="listitem">
              <HDInsightSummary
                title={model.title}
                periodLabel={model.periodLabel}
                comparison={model.comparisonLabel}
                qualification={model.qualification}
                onOpenEvidence={() => openEvidence(insight.id, insight.revision)}
              />
            </View>
          );
        })}
      </View>
      {data.observations.length === 0 && (data.hidden_count ?? 0) > 0 ? (
        <HDText>Semua pengamatan pada periode ini sedang disembunyikan atau ditunda.</HDText>
      ) : data.observations.length === 0 ? (
        learningOnly ? (
          <View style={styles.section}>
            <HDText variant="section">Belum cukup periode pembanding</HDText>
            <HDText>
              Perubahan hanya dihitung bila ada sedikitnya dua minggu sebelumnya dengan data yang cukup pada hari dan
              jam yang sama. Saran akan muncul setelah riwayatnya cukup.
            </HDText>
            <HDButton variant="text" onPress={openAssetHistoryChooser}>
              Tentang riwayat perangkat
            </HDButton>
          </View>
        ) : data.comparable_count === 0 ? (
          <NoData />
        ) : (
          <View style={styles.section}>
            <HDText variant="section">Belum ada perubahan yang memenuhi kriteria pada periode ini</HDText>
            <HDText>
              Ini bukan penilaian efisiensi atau keamanan, hanya berarti tidak ada perubahan yang cukup besar.
            </HDText>
          </View>
        )
      ) : null}
      {data.learning_count > 0 && !learningOnly ? (
        <HDText variant="label" tone="secondary">
          {`${data.learning_count} perangkat belum punya cukup periode pembanding.`}
        </HDText>
      ) : null}
      {(data.hidden_count ?? 0) > 0 ? (
        <View style={styles.row}>
          <HDButton variant="text" icon="chevronRight" onPress={openHidden}>
            {`Saran tersembunyi (${data.hidden_count})`}
          </HDButton>
        </View>
      ) : null}
      {data.notices.length ? (
        <View style={styles.section}>
          <HDText variant="section" role="heading">
            Catatan data
          </HDText>
          <HDText variant="label" tone="secondary">
            Catatan ini tentang kualitas data, bukan pengamatan pemakaian.
          </HDText>
          {data.notices.map((notice) => (
            <HDNotice key={notice.id} tone="attention" title={notice.title}>
              {notice.body}
            </HDNotice>
          ))}
        </View>
      ) : null}
    </>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
});
