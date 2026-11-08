import { errorMessage } from '@/features/localization/error-copy';
import { useLocale } from '@/features/localization/locale';
import { useCopy } from '@/features/localization/messages';
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
import { isKnownOffline, useConnectivity } from '@/features/offline/useConnectivity';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDateRange } from '@/lib/format';

/** S07: observations that met the rule, data notices apart from them, and honest empty states. */
export function SaranScreen() {
  const say = useCopy();
  const { workspace } = useWorkspace();
  const { openSettings } = useTabNavigation();
  const insights = useInsights();
  useConnectivity();
  const offline = isKnownOffline();

  const settings = <HDButton variant="text" onPress={openSettings}>{say("Pengaturan", "Settings")}</HDButton>;
  const supporting = insights.data ? <><DataNotices data={insights.data} />{settings}</> : null;
  return (
    <HDScreen title={say("Saran", "Insights")} subtitle={say("Pengamatan berbasis bukti, bukan diagnosis", "Observations from your readings")} supporting={supporting}>
      {workspace === null ? (
        <NoData />
      ) : insights.data === undefined ? (
        <HDProgressStatus
          state={insights.isError ? 'failure' : 'loading'}
          label={offline ? say("Menunggu koneksi untuk saran…", "Waiting for a connection to load insights…") : insights.isError ? say("Saran belum dapat dimuat", "Could not load insights") : say("Memuat saran…", "Loading insights…")}
          detail={errorMessage(insights.error)}
          action={
            insights.isError && !offline ? (
              <HDButton variant="text" icon="refresh" onPress={() => void insights.refetch()}>{say("Coba lagi", "Try again")}</HDButton>
            ) : null
          }
        />
      ) : (
        <SaranList data={insights.data} />
      )}
      {supporting === null ? settings : null}
    </HDScreen>
  );
}

function NoData() {
  const say = useCopy();
  const { openImport } = useTabNavigation();
  return (
    <View style={styles.section}>
      <HDText variant="section">{say("Belum ada saran", "No insights yet")}</HDText>
      <HDText>{say("Saran hanya muncul dari data yang tercatat. Ini bukan penilaian efisiensi atau keamanan.", "Insights use recorded data and show changes worth a closer look.")}</HDText>
      <HDButton variant="text" onPress={() => openImport()}>{say("Tentang impor data", "About importing data")}</HDButton>
    </View>
  );
}

function SaranList({ data }: { data: InsightList }) {
  const say = useCopy();
  const { openEvidence, openAssetHistoryChooser, openHidden } = useTabNavigation();
  const learningOnly = data.comparable_count === 0 && data.learning_count > 0;

  return (
    <>
      <HDText variant="labelStrong">
        {formatDateRange(data.window.start_date, data.window.end_date)} · {data.window.timezone}
      </HDText>
      <RestoreNotice timezone={data.window.timezone} />
      <View role="list" aria-label={say("Pengamatan", "Observations")} style={styles.section}>
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
        <HDText>{say("Semua pengamatan pada periode ini sedang disembunyikan atau ditunda.", "All observations for this period are hidden or snoozed.")}</HDText>
      ) : data.observations.length === 0 ? (
        learningOnly ? (
          <View style={styles.section}>
            <HDText variant="section">{say("Belum cukup periode pembanding", "Not enough comparable history")}</HDText>
            <HDText>{say("Perubahan hanya dihitung bila ada sedikitnya dua minggu sebelumnya dengan data yang cukup pada hari dan jam yang sama. Saran akan muncul setelah riwayatnya cukup.", "Insights compare the same days and hours across at least two earlier weeks with enough data.")}</HDText>
            <HDButton variant="text" onPress={openAssetHistoryChooser}>{say("Tentang riwayat perangkat", "About device history")}</HDButton>
          </View>
        ) : data.comparable_count === 0 ? (
          <NoData />
        ) : (
          <View style={styles.section}>
            <HDText variant="section">{say("Belum ada perubahan yang memenuhi kriteria pada periode ini", "No significant changes in this period")}</HDText>
            <HDText>{say("Ini bukan penilaian efisiensi atau keamanan, hanya berarti tidak ada perubahan yang cukup besar.", "The readings did not change enough to trigger an insight.")}</HDText>
          </View>
        )
      ) : null}
      {data.learning_count > 0 && !learningOnly ? (
        <HDText variant="label" tone="secondary">
          {say(`${data.learning_count} perangkat belum punya cukup periode pembanding.`, `Devices without enough comparable history: ${data.learning_count}.`)}
        </HDText>
      ) : null}
      {(data.hidden_count ?? 0) > 0 ? (
        <View style={styles.row}>
          <HDButton variant="text" icon="chevronRight" onPress={openHidden}>
            {say(`Saran tersembunyi (${data.hidden_count})`, `Hidden insights (${data.hidden_count})`)}
          </HDButton>
        </View>
      ) : null}
    </>
  );
}

function DataNotices({ data }: { data: InsightList }) {
  const say = useCopy();
  const locale = useLocale();
  return data.notices.length ? (
    <View style={styles.section}>
      <HDText variant="section" role="heading">{say("Catatan data", "Data notes")}</HDText>
      <HDText variant="label" tone="secondary">{say("Catatan ini tentang kualitas data, bukan pengamatan pemakaian.", "These notes explain the quality of your readings.")}</HDText>
      {data.notices.map((notice) => (
        <HDNotice key={notice.id} tone="attention" title={notice.copy_by_locale?.[locale].title ?? notice.title}>
          {notice.copy_by_locale?.[locale].body ?? notice.body}
        </HDNotice>
      ))}
    </View>
  ) : null;
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
});
