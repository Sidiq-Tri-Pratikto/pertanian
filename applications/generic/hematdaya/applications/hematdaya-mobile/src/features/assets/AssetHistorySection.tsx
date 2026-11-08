import { errorMessage } from '@/features/localization/error-copy';
import { useCopy, currentCopy } from '@/features/localization/messages';
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

function copyRetained(): string {
  return currentCopy("Riwayat yang tampil berasal dari pembacaan terakhir yang terkonfirmasi.", "History shows the last confirmed readings.");
}

function failureDetail(error: unknown, retained: boolean, guidance: string): string {
  const failure = ApiError.from(error);
  return [
    errorMessage(failure),
    failure.requestId ? currentCopy(`ID referensi: ${failure.requestId}.`, `Reference ID: ${failure.requestId}.`) : null,
    guidance,
    retained ? copyRetained() : null,
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
  const say = useCopy();
  const [open, setOpen] = useState(false);
  const { workspace, credential, credentialGeneration, scopeEpoch, currentScopeEpoch } = useWorkspace();
  const query = useHistory({ open, workspace, credential, credentialGeneration, scopeEpoch, currentScopeEpoch, assetId, confirmed });
  const history = useLastConfirmed(query);
  const retained = history !== undefined && (query.isFetching || query.isPaused || query.isError || query.data === undefined);

  let state: 'loading' | 'failure' | null = null;
  let label: string | undefined;
  let detail = retained ? copyRetained() : undefined;
  if (query.isError || (!confirmed && summaryError)) {
    state = 'failure';
    label = say("Riwayat belum dapat dimuat", "Could not load history");
    detail = failureDetail(
      query.error ?? summaryError,
      retained,
      query.isError ? say("Percobaan riwayat telah dihentikan. Pilih periode lain atau kembali nanti.", "Stopped trying to load history. Choose another period or come back later.") : say("Periksa periode yang dipilih.", "Check the selected period."),
    );
  } else if (query.isFetching && query.failureReason) {
    state = 'loading';
    label = say("Menunggu percobaan otomatis riwayat…", "Waiting to retry history…");
    const seconds = retryDelay(query.failureCount, query.failureReason) / 1000;
    detail = [say(`Percobaan otomatis berikutnya dalam ${seconds} detik.`, `Retrying in ${seconds} seconds.`), detail].filter(Boolean).join(' ');
  } else if (query.isPaused) {
    state = 'loading';
    label = say("Menunggu koneksi untuk riwayat…", "Waiting for a connection to load history…");
  } else if (!confirmed || query.isPending || query.isFetching) {
    state = 'loading';
    label = confirmed ? say("Memuat riwayat…", "Loading history…") : say("Menunggu periode terpilih…", "Waiting for a selected period…");
  }

  return (
    <HDDisclosure
      summary={say("Lihat riwayat", "View history")}
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
  const say = useCopy();
  const model = historyModel(history);
  const additionalOrigins = model.origins.filter((origin) => origin !== 'simulated' && origin !== 'import');

  return (
    <View style={styles.block}>
      <HDProvenanceTag origins={model.origins} />
      {additionalOrigins.length ? <HDText variant="label">{say("Asal data", "Data source")} {additionalOrigins.map(originLabel).join(', ')}</HDText> : null}
      {model.resolution ? <HDText variant="label">{say("Resolusi pengukuran", "Measurement resolution")} {model.resolution}</HDText> : null}
      {model.points.length > 0 ? (
        <>
          <HDHistoryChart
            title={say("Riwayat energi", "Energy history")}
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
            summary={say("Tabel menampilkan energi tercatat dan kelengkapan data setiap interval.", "The table shows recorded energy and data coverage for each interval.")}
            caption={say(`Riwayat ${assetName}, ${model.periodLabel}`, `History for ${assetName}, ${model.periodLabel}`)}
            columns={[
              { key: 'period', label: 'Interval' },
              { key: 'energy', label: say('Energi tercatat', 'Recorded energy') },
              { key: 'quality', label: say('Status data', 'Data status') },
              { key: 'coverage', label: say('Kelengkapan data', 'Data coverage') },
            ]}
            rows={model.rows}
          />
        </>
      ) : (
        <>
          <HDText variant="label">{model.periodLabel}</HDText>
          <HDText>{say("Riwayat belum memiliki interval untuk periode ini.", "No history intervals for this period yet.")}</HDText>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({ block: { gap: tokens.space.stackTight } });
