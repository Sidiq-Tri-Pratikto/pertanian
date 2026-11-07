import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import type { HistoryResponse } from '@/api/client';
import { ApiError } from '@/api/errors';
import { retryDelay } from '@/api/query-client';
import { HDChartDataAlternative } from '@/components/hd/HDChartDataAlternative';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDHistoryChart } from '@/components/hd/HDHistoryChart';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { historyModel } from '@/features/assets/history-model';
import { originLabel } from '@/features/assets/asset-model';
import { useHistory } from '@/features/assets/useHistory';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

const COLUMNS = [
  { key: 'period', label: 'Interval' },
  { key: 'energy', label: 'Energi tercatat' },
  { key: 'quality', label: 'Status data' },
  { key: 'coverage', label: 'Kelengkapan data' },
];
const RETAINED = 'Riwayat yang tampil berasal dari pembacaan terakhir yang terkonfirmasi.';

function failureDetail(error: unknown, retained: boolean, guidance: string): string {
  const failure = ApiError.from(error);
  return [
    failure.message,
    failure.requestId ? `ID referensi: ${failure.requestId}.` : null,
    guidance,
    retained ? RETAINED : null,
  ].filter(Boolean).join(' ');
}

type AssetHistoryProps = {
  assetId: string;
  assetName: string;
  scopeLabel: string;
  confirmed: HistoryResponse['window'] | null;
  summaryError: unknown;
};

/** S06 History stays in the current detail and keeps the prior response only within that site and asset. */
export function AssetHistorySection({ assetId, assetName, scopeLabel, confirmed, summaryError }: AssetHistoryProps) {
  const [open, setOpen] = useState(false);
  const { workspace } = useWorkspace();
  const query = useHistory({ open, workspace, assetId, confirmed });
  const history = useLastConfirmed(query);
  const retained = history !== undefined && (query.isFetching || query.isPaused || query.isError || query.data === undefined);

  let state: 'loading' | 'failure' | null = null;
  let label: string | undefined;
  let detail = retained ? RETAINED : undefined;
  if (query.isError || (!confirmed && summaryError)) {
    state = 'failure';
    label = 'Riwayat belum dapat dimuat';
    detail = failureDetail(
      query.error ?? summaryError,
      retained,
      query.isError ? 'Percobaan riwayat telah dihentikan. Pilih periode lain atau kembali nanti.' : 'Periksa periode yang dipilih.',
    );
  } else if (query.isFetching && query.failureReason) {
    state = 'loading';
    label = 'Menunggu percobaan otomatis riwayat…';
    const seconds = retryDelay(query.failureCount, query.failureReason) / 1000;
    detail = [`Percobaan otomatis berikutnya dalam ${seconds} detik.`, detail].filter(Boolean).join(' ');
  } else if (query.isPaused) {
    state = 'loading';
    label = 'Menunggu koneksi untuk riwayat…';
  } else if (!confirmed || query.isPending || query.isFetching) {
    state = 'loading';
    label = confirmed ? 'Memuat riwayat…' : 'Menunggu periode terpilih…';
  }

  return (
    <HDDisclosure
      summary="Lihat riwayat"
      onToggle={setOpen}
      status={<HDProgressStatus state={open ? state : null} label={label} detail={detail} />}>
      {history ? <HistoryContent history={history} assetName={assetName} scopeLabel={scopeLabel} /> : null}
    </HDDisclosure>
  );
}

function HistoryContent({ history, assetName, scopeLabel }: {
  history: HistoryResponse;
  assetName: string;
  scopeLabel: string;
}) {
  const model = historyModel(history);
  const additionalOrigins = model.origins.filter((origin) => origin !== 'simulated' && origin !== 'import');

  return (
    <View style={styles.block}>
      <HDProvenanceTag origins={model.origins} />
      {additionalOrigins.length ? <HDText variant="label">Asal data {additionalOrigins.map(originLabel).join(', ')}</HDText> : null}
      {model.resolution ? <HDText variant="label">Resolusi pengukuran {model.resolution}</HDText> : null}
      {model.points.length > 0 ? (
        <>
          <HDHistoryChart
            title="Riwayat energi"
            points={model.points}
            periodLabel={model.periodLabel}
            scopeLabel={`${assetName} · ${scopeLabel}`}
            unit="kWh"
            summary={model.summary}
            gapNote={model.gapNote}
            dense={model.dense}
            showValues={false}
          />
          <HDChartDataAlternative
            summary="Tabel menampilkan energi tercatat dan kelengkapan data setiap interval."
            caption={`Riwayat ${assetName}, ${model.periodLabel}`}
            columns={COLUMNS}
            rows={model.rows}
          />
        </>
      ) : (
        <>
          <HDText variant="label">{model.periodLabel}</HDText>
          <HDText>Riwayat belum memiliki interval untuk periode ini.</HDText>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stackTight } });
