import { useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import type { Summary } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDChartDataAlternative } from '@/components/hd/HDChartDataAlternative';
import { HDContributionRanking } from '@/components/hd/HDContributionRanking';
import { HDDataQuality, freshnessRows } from '@/components/hd/HDDataQuality';
import { HDEnergyMetric } from '@/components/hd/HDEnergyMetric';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDPeriodSelector } from '@/components/hd/HDPeriodSelector';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { ReadFailure, SavedReadStatus } from '@/features/assets/ReadFailure';
import { usePreviousAssetScope } from '@/features/assets/useAssets';
import { CONTEXT_EXAMPLES, useContextPreset } from '@/features/context-preset';
import { berandaModel, shownOrigins } from '@/features/energy/beranda-model';
import { useSummary } from '@/features/energy/useSummary';
import { FeaturedInsight } from '@/features/insights/FeaturedInsight';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useScopeInvoker, useTabNavigation } from '@/features/navigation';
import { ServiceStatus } from '@/features/ServiceStatus';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDate, formatDateTime, formatPercent, localParts } from '@/lib/format';

/** S02 or S03: empty until a workspace has data, then the populated summary in UX-17 reading order. */
export default function BerandaScreen() {
  const { status, workspace, credentialGeneration } = useWorkspace();
  if (status === 'loading') {
    return (
      <HDScreen title="Beranda">
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
      </HDScreen>
    );
  }
  return workspace ? <WorkspaceBeranda key={`${workspace.siteId}:${credentialGeneration}`} /> : <EmptyBeranda />;
}

/** S02: no axes, no Rp0, no giant zero. There is simply no data yet. */
function EmptyBeranda({ expiresAt, timezone = 'Asia/Jakarta' }: { expiresAt?: string; timezone?: string }) {
  const { preset } = useContextPreset();
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  return (
    <HDScreen title="Beranda">
      <SessionEndedNotice />
      <View style={styles.section}>
        <HDText variant="section">Belum ada data energi</HDText>
        <HDText>HematDaya membaca energi dari berkas CSV atau dari sumber pengukuran yang didukung.</HDText>
        <HDText tone="secondary">{CONTEXT_EXAMPLES[preset]}</HDText>
        <View ref={demoButton}>
          <HDButton variant="primary" onPress={() => setSheetOpen(true)}>Coba demo</HDButton>
        </View>
        <HDButton onPress={openImport}>Tambah data</HDButton>
        <HDButton variant="text" onPress={() => openFeature('sumber-meter')}>
          Lihat meter yang didukung
        </HDButton>
      </View>
      {expiresAt ? (
        <HDNotice tone="info" title="Ruang kerja sementara">
          {`Ruang kerja ini tersimpan di perangkat ini sampai akun tersedia dan berakhir ${formatDate(localParts(expiresAt, timezone).date)}.`}
        </HDNotice>
      ) : null}
      <ServiceStatus />
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
      <DemoSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onOpened={() => setSheetOpen(false)}
        returnFocusTo={demoButton}
      />
    </HDScreen>
  );
}

function WorkspaceBeranda() {
  const { workspace } = useWorkspace();
  const summary = useSummary();
  const previousScope = usePreviousAssetScope();
  const kept = useLastConfirmed(summary);
  const shown = summary.offline ? summary.data : kept;
  const { period, setPeriod } = useNavigationContext();

  if (shown === undefined) {
    return (
      <HDScreen title="Beranda">
        {period ? <HDPeriodSelector value={period} activeLabel="belum terkonfirmasi" onCommit={setPeriod} /> : null}
        <SavedReadStatus offline={summary.offline} />
        {!summary.offline ? <HDProgressStatus
          state={summary.isError ? 'failure' : 'loading'}
          label={summary.isError ? 'Data belum dapat dimuat' : 'Memuat ringkasan energi…'}
          detail={summary.error?.message}
          action={
            summary.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void summary.refetch()}>
                Coba lagi
              </HDButton>
            ) : null
          }
        /> : null}
      </HDScreen>
    );
  }
  if (shown.scope.included.length === 0 && shown.scope.excluded.length === 0) {
    return <EmptyBeranda expiresAt={workspace?.expiresAt} timezone={shown.window.timezone} />;
  }
  return <PopulatedBeranda previousSelection={summary.previousSelection || shown !== summary.data || Boolean(previousScope?.summaries.has(shown))}
    data={shown} refreshing={summary.isFetching} failure={summary.error} onRefresh={summary.refresh}
    offline={summary.offline} fetchedAt={summary.confirmedAtFor(shown)} />;
}

type PopulatedProps = {
  previousSelection: boolean; data: Summary; refreshing: boolean; failure: unknown;
  onRefresh: () => void; offline: boolean; fetchedAt?: number;
};

/** S03: period and scope, recorded kWh, cost, completeness and freshness, then contributors. */
function PopulatedBeranda({ previousSelection, data, refreshing, failure, onRefresh, offline, fetchedAt }: PopulatedProps) {
  const { workspace } = useWorkspace();
  const { period, setPeriod } = useNavigationContext();
  const { openAsset, openFeature, openImport, openSettings } = useTabNavigation();
  const model = berandaModel(data);
  const scopeControl = useScopeInvoker();
  const scopeIssue = useScopeInvoker();
  const largest = model.ranking[0];

  return (
    <HDScreen title="Beranda" subtitle={model.timezone}>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
      ) : null}
      <View style={styles.section}>
        <HDText variant="labelStrong">{model.scopeLabel}</HDText>
        <HDText variant="label" tone="secondary">
          Hanya mencakup sumber yang dipilih.
          {data.scope.excluded.length ? ` Tidak termasuk: ${data.scope.excluded.map((asset) => asset.name).join(', ')}.` : ''}
        </HDText>
        <HDButton variant="text" {...scopeControl}>Atur cakupan dan sumber</HDButton>
      </View>
      {previousSelection ? (
        <HDNotice tone="info" title="Ringkasan masih memakai cakupan sebelumnya">
          {fetchedAt !== undefined && !offline
            ? `Terakhir dimuat: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. Tunggu ringkasan cakupan terkini.`
            : 'Total yang tampil berasal dari ringkasan terakhir. Tunggu ringkasan cakupan terkini.'}
        </HDNotice>
      ) : null}
      <SavedReadStatus offline={offline} failed={Boolean(failure)} fetchedAt={fetchedAt} timezone={model.timezone} />
      <HDEnergyMetric
        state={model.state}
        kwh={model.kwh}
        qualifier={model.qualifier}
        gaps={model.state === 'partial' ? model.gaps : []}
        periodLabel={model.periodLabel}
        scopeLabel={model.scopeLabel}
        origins={shownOrigins(model.origins, workspace?.scenarioId)}
        emptyDetail={model.emptyDetail}
        issues={model.issues}
        action={
          model.state === 'conflict' ? <HDButton {...scopeIssue}>Selesaikan cakupan</HDButton> : model.state === 'none' && workspace ? (
            <HDButton icon="chevronRight" onPress={() => setPeriod(workspace.initialPeriod)}>
              Lihat periode data
            </HDButton>
          ) : null
        }
      />
      {model.allocated ? (
        <HDText variant="label">Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).</HDText>
      ) : null}
      <HDNotice
        tone="neutral"
        title="Estimasi biaya segera hadir"
        action={
          <HDButton variant="text" onPress={() => openFeature('estimasi-biaya')}>
            Tentang estimasi biaya
          </HDButton>
        }>
        Biaya belum dihitung pada versi ini. Energi yang dipantau tetap tersedia.
      </HDNotice>
      <HDDataQuality
        rows={[
          ...freshnessRows(data.source_freshness, model.timezone, data.assets),
          ...(model.completeness || model.state === 'conflict'
            ? [
                {
                  term: 'Kelengkapan data',
                  value: model.state === 'conflict' ? 'Tidak dihitung untuk total gabungan' : model.completeness!,
                  detail: model.gaps.length ? model.gaps.map((gap) => `Data ${gap} belum tersedia.`).join(' ') : undefined,
                },
              ]
            : []),
          ...(model.latest
            ? [{ term: 'Pengukuran terakhir', value: `${model.latest}${model.origins.includes('simulated') ? ' (data simulasi)' : ''}` }]
            : []),
          ...(model.origins.includes('simulated')
            ? [{ term: 'Asal data', value: 'Data simulasi untuk demo', detail: 'Bukan pengukuran dari perangkat nyata.' }]
            : []),
        ]}
      />
      <View style={styles.row}>
        <HDButton variant="text" icon="refresh" loading={refreshing} loadingLabel="Memeriksa pembaruan…" onPress={onRefresh}>
          {data.source_freshness?.some((source) => source.state === 'stale') ? 'Periksa sumber' : 'Perbarui'}
        </HDButton>
      </View>
      <ReadFailure error={offline ? null : failure} label="Data belum dapat diperbarui"
        retrying={refreshing} onRetry={onRefresh} kept />
      {model.ranking.length ? (
        <View style={styles.section}>
          {largest && largest.share !== null ? (
            <HDButton variant="primary" icon="chevronRight" onPress={() => openAsset(largest.assetId)}>
              Lihat perangkat terbesar
            </HDButton>
          ) : null}
          <HDContributionRanking
            items={model.ranking}
            periodLabel={model.periodLabel}
            denominatorLabel={`${model.ranking.length} perangkat yang dipantau`}
            onOpen={openAsset}
          />
          <HDChartDataAlternative
            summary={
              largest && largest.share !== null
                ? `${largest.name} mencatat energi terbesar: ${largest.kwh} dari ${model.totalLabel} pada ${model.periodLabel}. Angka ini hanya mencakup ${model.ranking.length} perangkat yang dipilih.`
                : 'Semua perangkat mencatat 0 kWh dengan data lengkap; tidak ada persentase kontribusi.'
            }
            caption={`Energi per perangkat, ${model.periodLabel}, ${model.timezone}`}
            columns={[
              { key: 'name', label: 'Perangkat' },
              { key: 'kwh', label: 'Energi' },
              { key: 'share', label: 'Porsi' },
              { key: 'coverage', label: 'Kelengkapan data' },
            ]}
            rows={model.ranking.map((item) => ({
              name: item.name,
              kwh: item.kwh,
              share: item.share === null ? '—' : formatPercent(item.share),
              coverage: item.coverage,
            }))}
          />
        </View>
      ) : null}
      <FeaturedInsight />
      <HDButton variant="text" onPress={openImport}>Tambah data</HDButton>
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
});
