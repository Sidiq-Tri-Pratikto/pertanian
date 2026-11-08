import { errorMessage } from '@/features/localization/error-copy';
import { useCopy } from '@/features/localization/messages';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChartDataAlternative } from '@/components/hd/HDChartDataAlternative';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDEvidencePanel } from '@/components/hd/HDEvidencePanel';
import { HDHistoryChart } from '@/components/hd/HDHistoryChart';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { evidenceModel, insightCopy } from '@/features/insights/evidence-model';
import { FeedbackControls } from '@/features/insights/FeedbackControls';
import { useInsight } from '@/features/insights/useInsights';
import { useTabNavigation } from '@/features/navigation';
import { formatKwh } from '@/lib/format';

/** S08: the exact evidence revision the card showed, read in order. No apply, shutdown or diagnosis action. */
export function EvidenceScreen({ insightId, revision }: { insightId: string | undefined; revision: number | undefined }) {
  const say = useCopy();
  const { back, openEvidence } = useTabNavigation();
  const insight = useInsight(insightId, revision);

  if (insightId === undefined || revision === undefined) {
    return (
      <HDScreen title={say("Dasar saran", "Insight evidence")} onBack={back}>
        <HDNotice tone="neutral" title={say("Bukti tidak ditemukan", "Evidence not found")}>{say("Tautan ini tidak menyebut versi bukti. Buka saran dari daftar Saran.", "Open the insight from the Insights list to see its evidence.")}</HDNotice>
      </HDScreen>
    );
  }
  if (insight.data === undefined) {
    return (
      <HDScreen title={say("Dasar saran", "Insight evidence")} onBack={back}>
        <HDProgressStatus
          state={insight.isError ? 'failure' : 'loading'}
          label={insight.isError ? say("Bukti belum dapat dimuat", "Could not load evidence") : say("Memuat dasar saran…", "Loading evidence…")}
          detail={errorMessage(insight.error)}
          action={
            insight.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void insight.refetch()}>{say("Coba lagi", "Try again")}</HDButton>
            ) : null
          }
        />
      </HDScreen>
    );
  }

  const data = insight.data;
  const model = evidenceModel(data);
  const copy = insightCopy(data);
  return (
    <HDScreen title={model.title} subtitle={`${model.periodLabel} · ${model.timezone}`} onBack={back}>
      <View style={styles.row}>
        <HDProvenanceTag origins={model.origins} />
      </View>
      {data.superseded ? (
        <HDNotice
          tone="info"
          title={say("Bukti ini sudah diperbarui", "Newer evidence is available")}
          action={
            <HDButton variant="text" onPress={() => openEvidence(data.id, data.current_revision)}>{say("Lihat bukti terbaru", "View latest evidence")}</HDButton>
          }>
          {say(`Anda melihat versi ${data.revision} seperti saat saran ditampilkan. Data kemudian berubah dan versi ${data.current_revision} tersedia.`, `You’re viewing the original evidence (version ${data.revision}). The data has changed and version ${data.current_revision} is available.`)}
        </HDNotice>
      ) : null}
      {!data.active ? (
        <HDNotice tone="neutral" title={say("Tidak lagi memenuhi kriteria", "No longer meets the rule")}>{say("Dengan data terbaru, perubahan ini tidak lagi memenuhi kriteria. Bukti di bawah tetap seperti saat ditampilkan.", "The latest data no longer meets the rule. The original evidence is below.")}</HDNotice>
      ) : null}
      <HDText variant="label" tone="secondary">
        {model.comparisonLabel}
      </HDText>
      <HDEvidencePanel
        observed={[copy.observed, copy.pct_note].filter(Boolean).join(' ')}
        comparison={copy.comparison}
        qualityScope={model.qualityScope}
        unknown={copy.unknown}
        guidance={copy.step}
        metadata={model.calculation}
        feedback={<FeedbackControls insight={data} timezone={model.timezone} />}
      />
      <HDDisclosure summary={say("Lihat data pembanding", "View comparison data")}>
        <HDHistoryChart
          title={say(`${model.assetName}: periode ini dan pembanding`, `${model.assetName}: this period and comparison`)}
          points={model.points}
          periodLabel={model.periodLabel}
          scopeLabel={model.assetName}
          unit="kWh"
          summary={model.chartSummary}
          gapNote={model.points.some((point) => point.current === null) ? say("Kolom bergaris titik berarti data belum tersedia, bukan 0 kWh.", "Dotted columns mark missing readings.") : undefined}
        />
        <HDChartDataAlternative
          summary={say("Tabel berisi angka yang sama dengan grafik, dari versi bukti ini.", "The table lists the same figures as the chart for this evidence version.")}
          caption={say(`Energi harian ${model.assetName}, ${model.periodLabel}, ${model.timezone}`, `Daily energy for ${model.assetName}, ${model.periodLabel}, ${model.timezone}`)}
          columns={[
            { key: 'date', label: say("Tanggal", "Date") },
            { key: 'current', label: say("Periode ini", "This period") },
            { key: 'reference', label: say("Pembanding (median)", "Comparison (median)") },
          ]}
          rows={model.points.map((point) => ({
            date: point.date,
            current: point.current === null ? '' : formatKwh(point.current),
            reference: point.reference === null ? '' : formatKwh(point.reference),
          }))}
        />
      </HDDisclosure>
    </HDScreen>
  );
}

const styles = StyleSheet.create({ row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap } });
