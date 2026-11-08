import { errorMessage } from '@/features/localization/error-copy';
import { useCopy } from '@/features/localization/messages';
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
import { contextExample, useContextPreset } from '@/features/context-preset';
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
  const say = useCopy();
  const { status, workspace, credentialGeneration } = useWorkspace();
  if (status === 'loading') {
    return (
      <HDScreen title={say("Beranda", "Home")}>
        <HDProgressStatus state="loading" label={say("Memuat ruang kerja…", "Loading workspace…")} />
      </HDScreen>
    );
  }
  return workspace ? <WorkspaceBeranda key={`${workspace.siteId}:${credentialGeneration}`} /> : <EmptyBeranda />;
}

/** S02: no axes, no Rp0, no giant zero. There is simply no data yet. */
function EmptyBeranda({ expiresAt, timezone = 'Asia/Jakarta' }: { expiresAt?: string; timezone?: string }) {
  const say = useCopy();
  const { preset } = useContextPreset();
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  return (
    <HDScreen title={say("Beranda", "Home")}>
      <SessionEndedNotice />
      <View style={styles.section}>
        <HDText variant="section">{say("Belum ada data energi", "No energy data yet")}</HDText>
        <HDText>{say("HematDaya membaca energi dari berkas CSV atau dari sumber pengukuran yang didukung.", "Add a CSV file to see your own readings.")}</HDText>
        <HDText tone="secondary">{contextExample(preset)}</HDText>
        <View ref={demoButton}>
          <HDButton variant="primary" onPress={() => setSheetOpen(true)}>{say("Coba demo", "Try demo")}</HDButton>
        </View>
        <HDButton onPress={openImport}>{say("Tambah data", "Add data")}</HDButton>
        <HDButton variant="text" onPress={() => openFeature('sumber-meter')}>{say("Lihat meter yang didukung", "View supported meters")}</HDButton>
      </View>
      {expiresAt ? (
        <HDNotice tone="info" title={say("Ruang kerja sementara", "Temporary workspace")}>
          {say(`Ruang kerja ini tersimpan di perangkat ini sampai akun tersedia dan berakhir ${formatDate(localParts(expiresAt, timezone).date)}.`, `This workspace is stored on this device until ${formatDate(localParts(expiresAt, timezone).date)}.`)}
        </HDNotice>
      ) : null}
      <ServiceStatus />
      <HDButton variant="text" onPress={openSettings}>{say("Pengaturan", "Settings")}</HDButton>
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
  const say = useCopy();
  const { workspace } = useWorkspace();
  const summary = useSummary();
  const previousScope = usePreviousAssetScope();
  const kept = useLastConfirmed(summary);
  const shown = summary.offline ? summary.data : kept;
  const { period, setPeriod } = useNavigationContext();

  if (shown === undefined) {
    return (
      <HDScreen title={say("Beranda", "Home")}>
        {period ? <HDPeriodSelector value={period} activeLabel={say("belum terkonfirmasi", "not confirmed")} onCommit={setPeriod} /> : null}
        <SavedReadStatus offline={summary.offline} />
        {!summary.offline ? <HDProgressStatus
          state={summary.isError ? 'failure' : 'loading'}
          label={summary.isError ? say("Data belum dapat dimuat", "Could not load data") : say("Memuat ringkasan energi…", "Loading energy summary…")}
          detail={errorMessage(summary.error)}
          action={
            summary.isError ? (
              <HDButton variant="text" icon="refresh" onPress={() => void summary.refetch()}>{say("Coba lagi", "Try again")}</HDButton>
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
  const say = useCopy();
  const { workspace } = useWorkspace();
  const { period, setPeriod } = useNavigationContext();
  const { openAsset, openFeature, openImport, openSettings } = useTabNavigation();
  const model = berandaModel(data);
  const scopeControl = useScopeInvoker();
  const scopeIssue = useScopeInvoker();
  const largest = model.ranking[0];

  const supporting = (
    <>
      {model.ranking.length ? (
        <View style={styles.section}>
          {largest && largest.share !== null ? (
            <HDButton variant="primary" icon="chevronRight" onPress={() => openAsset(largest.assetId)}>{say("Lihat perangkat terbesar", "View largest contributors")}</HDButton>
          ) : null}
          <HDContributionRanking
            items={model.ranking}
            periodLabel={model.periodLabel}
            denominatorLabel={say(`${model.ranking.length} perangkat yang dipantau`, `Monitored devices: ${model.ranking.length}`)}
            onOpen={openAsset}
          />
          <HDChartDataAlternative
            summary={
              largest && largest.share !== null
                ? say(`${largest.name} mencatat energi terbesar: ${largest.kwh} dari ${model.totalLabel} pada ${model.periodLabel}. Angka ini hanya mencakup ${model.ranking.length} perangkat yang dipilih.`, `${largest.name} used the most recorded energy: ${largest.kwh} of ${model.totalLabel} for ${model.periodLabel}. The total covers only the ${model.ranking.length} selected devices.`)
                : say("Semua perangkat mencatat 0 kWh dengan data lengkap; tidak ada persentase kontribusi.", "All devices recorded 0 kWh with complete data. There are no percentage shares.")
            }
            caption={say(`Energi per perangkat, ${model.periodLabel}, ${model.timezone}`, `Energy by device, ${model.periodLabel}, ${model.timezone}`)}
            columns={[
              { key: 'name', label: say("Perangkat", "Devices") },
              { key: 'kwh', label: say("Energi", "Energy") },
              { key: 'share', label: say("Porsi", "Share") },
              { key: 'coverage', label: say("Kelengkapan data", "Data coverage") },
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
      <HDButton variant="text" onPress={openImport}>{say("Tambah data", "Add data")}</HDButton>
      <HDButton variant="text" onPress={openSettings}>{say("Pengaturan", "Settings")}</HDButton>
    </>
  );

  return (
    <HDScreen title={say("Beranda", "Home")} subtitle={model.timezone} supporting={supporting}>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
      ) : null}
      <View style={styles.section}>
        <HDText variant="label" tone="secondary">{say("Hanya mencakup sumber yang dipilih.", "Includes only the selected sources.")}{data.scope.excluded.length ? say(` Tidak termasuk: ${data.scope.excluded.map((asset) => asset.name).join(', ')}.`, ` Excludes: ${data.scope.excluded.map((asset) => asset.name).join(', ')}.`) : ''}
        </HDText>
        <HDButton variant="text" {...scopeControl}>{say("Atur cakupan dan sumber", "Manage scope and sources")}</HDButton>
      </View>
      {previousSelection ? (
        <HDNotice tone="info" title={say("Ringkasan masih memakai cakupan sebelumnya", "Summary still uses the previous scope")}>
          {fetchedAt !== undefined && !offline
            ? say(`Terakhir dimuat: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. Tunggu ringkasan cakupan terkini.`, `Last loaded: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. Waiting for the new scope summary.`)
            : say("Total yang tampil berasal dari ringkasan terakhir. Tunggu ringkasan cakupan terkini.", "The total comes from the last summary. Waiting for the new scope summary.")}
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
          model.state === 'conflict' ? <HDButton {...scopeIssue}>{say("Selesaikan cakupan", "Resolve scope")}</HDButton> : model.state === 'none' && workspace ? (
            <HDButton icon="chevronRight" onPress={() => setPeriod(workspace.initialPeriod)}>{say("Lihat periode data", "View data period")}</HDButton>
          ) : null
        }
      />
      {model.allocated ? (
        <HDText variant="label">{say("Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).", "Readings crossing the period boundary are split evenly over their intervals (estimated).")}</HDText>
      ) : null}
      <View style={styles.row}>
        <HDText variant="label" tone="secondary">{say("Estimasi biaya segera hadir", "Cost estimates are coming soon")}</HDText>
        <HDButton variant="text" onPress={() => openFeature('estimasi-biaya')}>{say("Tentang estimasi biaya", "About cost estimates")}</HDButton>
      </View>
      <HDDataQuality
        rows={[
          ...freshnessRows(data.source_freshness, model.timezone, data.assets),
          ...(model.completeness || model.state === 'conflict'
            ? [
                {
                  term: say("Kelengkapan data", "Data coverage"),
                  value: model.state === 'conflict' ? say("Tidak dihitung untuk total gabungan", "Combined total unavailable") : model.completeness!,
                  detail: model.gaps.length ? model.gaps.map((gap) => say(`Data ${gap} belum tersedia.`, `Data unavailable for ${gap}.`)).join(' ') : undefined,
                },
              ]
            : []),
          ...(model.latest
            ? [{ term: say("Pengukuran terakhir", "Last reading"), value: `${model.latest}${model.origins.includes('simulated') ? say(" (data simulasi)", " (simulated data)") : ''}` }]
            : []),
          ...(model.origins.includes('simulated')
            ? [{ term: say("Asal data", "Data source"), value: say("Data simulasi untuk demo", "Simulated demo data"), detail: say("Bukan pengukuran dari perangkat nyata.", "These readings are simulated.") }]
            : []),
        ]}
      />
      <View style={styles.row}>
        <HDButton variant="text" icon="refresh" loading={refreshing} loadingLabel={say("Memeriksa pembaruan…", "Checking for updates…")} onPress={onRefresh}>
          {data.source_freshness?.some((source) => source.state === 'stale') ? say("Periksa sumber", "Check sources") : say("Perbarui", "Refresh")}
        </HDButton>
      </View>
      <ReadFailure error={offline ? null : failure} label={say("Data belum dapat diperbarui", "Could not refresh data")}
        retrying={refreshing} onRetry={onRefresh} kept />
    </HDScreen>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
});
