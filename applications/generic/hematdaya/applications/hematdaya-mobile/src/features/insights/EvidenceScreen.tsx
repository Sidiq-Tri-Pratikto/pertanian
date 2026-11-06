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
import { evidenceModel } from '@/features/insights/evidence-model';
import { FeedbackControls } from '@/features/insights/FeedbackControls';
import { useInsight } from '@/features/insights/useInsights';
import { useTabNavigation } from '@/features/navigation';
import { formatKwh } from '@/lib/format';

/** S08: the exact evidence revision the card showed, read in order. No apply, shutdown or diagnosis action. */
export function EvidenceScreen({ insightId, revision }: { insightId: string | undefined; revision: number | undefined }) {
  const { back, openEvidence } = useTabNavigation();
  const insight = useInsight(insightId, revision);

  if (insightId === undefined || revision === undefined) {
    return (
      <HDScreen title="Dasar saran" onBack={back}>
        <HDNotice tone="neutral" title="Bukti tidak ditemukan">
          Tautan ini tidak menyebut versi bukti. Buka saran dari daftar Saran.
        </HDNotice>
      </HDScreen>
    );
  }
  if (insight.data === undefined) {
    return (
      <HDScreen title="Dasar saran" onBack={back}>
        <HDProgressStatus
          state={insight.isError ? 'failure' : 'loading'}
          label={insight.isError ? 'Bukti belum dapat dimuat' : 'Memuat dasar saran…'}
          detail={insight.error?.message}
          action={
            insight.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void insight.refetch()}>
                Coba lagi
              </HDButton>
            ) : null
          }
        />
      </HDScreen>
    );
  }

  const data = insight.data;
  const model = evidenceModel(data);
  return (
    <HDScreen title={model.title} subtitle={`${model.periodLabel} · ${model.timezone}`} onBack={back}>
      <View style={styles.row}>
        <HDProvenanceTag origins={model.origins} />
      </View>
      {data.superseded ? (
        <HDNotice
          tone="info"
          title="Bukti ini sudah diperbarui"
          action={
            <HDButton variant="text" onPress={() => openEvidence(data.id, data.current_revision)}>
              Lihat bukti terbaru
            </HDButton>
          }>
          {`Anda melihat versi ${data.revision} seperti saat saran ditampilkan. Data kemudian berubah dan versi ${data.current_revision} tersedia.`}
        </HDNotice>
      ) : null}
      {!data.active ? (
        <HDNotice tone="neutral" title="Tidak lagi memenuhi kriteria">
          Dengan data terbaru, perubahan ini tidak lagi memenuhi kriteria. Bukti di bawah tetap seperti saat ditampilkan.
        </HDNotice>
      ) : null}
      <HDText variant="label" tone="secondary">
        {model.comparisonLabel}
      </HDText>
      <HDEvidencePanel
        observed={[data.text.observed, data.text.pct_note].filter(Boolean).join(' ')}
        comparison={data.text.comparison}
        qualityScope={model.qualityScope}
        unknown={data.text.unknown}
        guidance={data.text.step}
        metadata={model.calculation}
        feedback={<FeedbackControls insight={data} timezone={model.timezone} />}
      />
      <HDDisclosure summary="Lihat data pembanding">
        <HDHistoryChart
          title={`${model.assetName}: periode ini dan pembanding`}
          points={model.points}
          periodLabel={model.periodLabel}
          scopeLabel={model.assetName}
          unit="kWh"
          summary={model.chartSummary}
          gapNote={model.points.some((point) => point.current === null) ? 'Kolom bergaris titik berarti data belum tersedia, bukan 0 kWh.' : undefined}
        />
        <HDChartDataAlternative
          summary="Tabel berisi angka yang sama dengan grafik, dari versi bukti ini."
          caption={`Energi harian ${model.assetName}, ${model.periodLabel}, ${model.timezone}`}
          columns={[
            { key: 'date', label: 'Tanggal' },
            { key: 'current', label: 'Periode ini' },
            { key: 'reference', label: 'Pembanding (median)' },
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
