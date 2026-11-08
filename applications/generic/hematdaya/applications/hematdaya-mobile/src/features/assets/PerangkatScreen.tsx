import { scopeIssueCopy } from '@/features/scope/scope-copy';
import { errorMessage } from '@/features/localization/error-copy';
import { currentCopy, useCopy } from '@/features/localization/messages';
import { useRef, useState, type ComponentRef, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import type { Asset, Summary } from '@/api/client';
import { HDAssetRow } from '@/components/hd/HDAssetRow';
import { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDPeriodSelector } from '@/components/hd/HDPeriodSelector';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { assetRowModel, staleAssetIds, unrankedAssetRow, type AssetRowModel } from '@/features/assets/asset-model';
import { ReadFailure, SavedReadStatus } from '@/features/assets/ReadFailure';
import { useArchivedAssets, useAssets, usePreviousAssetScope } from '@/features/assets/useAssets';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { berandaModel, shownOrigins } from '@/features/energy/beranda-model';
import { useSummary } from '@/features/energy/useSummary';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useScopeInvoker, useTabNavigation } from '@/features/navigation';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { formatDateTime } from '@/lib/format';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

function copyTitle(): string {
  return currentCopy("Perangkat", "Devices");
}
function copyList(): string {
  return currentCopy("Daftar perangkat, urut energi tercatat", "Devices by recorded energy");
}
function copySubtitle(): string {
  return currentCopy("Perangkat, grup, sirkuit, dan meter lokasi", "Devices, groups, circuits and site meters");
}

/** S04: every measured thing with its scope kind and quality, in the service's order. */
export function PerangkatScreen({ historyChooser = false }: { historyChooser?: boolean }) {
  const say = useCopy();
  const { status, workspace, credentialGeneration } = useWorkspace();
  const { back } = useTabNavigation();
  const onBack = historyChooser ? back : undefined;
  const title = historyChooser ? say("Riwayat perangkat", "Device history") : copyTitle();
  if (status === 'loading') {
    return (
      <HDScreen title={title} subtitle={copySubtitle()} onBack={onBack}>
        <HDProgressStatus state="loading" label={say("Memuat ruang kerja…", "Loading workspace…")} />
      </HDScreen>
    );
  }
  // The key drops confirmed data and query observers, so nothing crosses workspaces.
  return workspace
    ? <WorkspacePerangkat key={`${workspace.siteId}:${credentialGeneration}`} title={title} onBack={onBack} />
    : <EmptyPerangkat title={title} onBack={onBack} />;
}

/** No workspace or no asset: no number and no date, and every way data will arrive. */
function EmptyPerangkat({ title, onBack, children }: { title: string; onBack?: () => void; children?: ReactNode }) {
  const say = useCopy();
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  return (
    <HDScreen title={title} subtitle={copySubtitle()} onBack={onBack}>
      <SessionEndedNotice />
      <View style={styles.section}>
        <HDText variant="section">{say("Belum ada perangkat", "No devices yet")}</HDText>
        <HDText>{say("Perangkat muncul di sini setelah ada data energi. HematDaya tidak mengendalikan perangkat.", "Devices appear here once you have energy readings.")}</HDText>
        <View ref={demoButton}>
          <HDButton variant="primary" onPress={() => setSheetOpen(true)}>{say("Coba demo", "Try demo")}</HDButton>
        </View>
        <HDButton onPress={openImport}>{say("Tambah data", "Add data")}</HDButton>
        <HDButton variant="text" onPress={() => openFeature('sumber-meter')}>{say("Tambah sumber", "Add source")}</HDButton>
      </View>
      {children}
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

function WorkspacePerangkat({ title, onBack }: { title: string; onBack?: () => void }) {
  const say = useCopy();
  const summaryQuery = useSummary();
  const assetsQuery = useAssets();
  const [archiveOpen, setArchiveOpen] = useState(false);
  const archive = useArchivedAssets(archiveOpen);
  const keptSummary = useLastConfirmed(summaryQuery);
  const summary = summaryQuery.offline ? summaryQuery.data : keptSummary;
  const assets = useLastConfirmed(assetsQuery);
  const previousScope = usePreviousAssetScope();
  const retry = summaryQuery.refresh;
  const archiveItems = archive.data?.items ?? [];
  const recent = archive.dataUpdatedAt >= assetsQuery.dataUpdatedAt
    ? [...(assets ?? []), ...archiveItems] : [...archiveItems, ...(assets ?? [])];
  const metadata = new Map(recent.map((asset) => [asset.id, asset]));
  const archived = [...metadata.values()].filter((asset) => asset.archived);
  const archivedIds = new Set(archived.map((asset) => asset.id));
  const active = new Map([...metadata].filter(([, asset]) => !asset.archived));
  const listed = new Set(summary?.assets.map((asset) => asset.asset_id));
  const unranked = [...active.values()].filter((asset) => !listed.has(asset.id));
  const previousSelection = summaryQuery.previousSelection || summary !== summaryQuery.data ||
    Boolean(summary && previousScope?.summaries.has(summary));
  const archiveSection = (
    <ArchiveSection open={archiveOpen} toggle={() => setArchiveOpen((wasOpen) => !wasOpen)}
      assets={archived} error={archive.error} loading={archive.isFetching} loaded={archive.data !== undefined}
      incomplete={Boolean(archive.data?.incomplete || archive.data?.next_cursor)} />
  );

  if (summary === undefined) {
    const restored = unranked.filter((asset) => previousScope?.restored.has(asset.id))
      .map((asset) => unrankedAssetRow(asset, false));
    return (
      <HDScreen title={title} subtitle={copySubtitle()} onBack={onBack}>
        <SavedReadStatus offline={summaryQuery.offline} />
        <HDProgressStatus state={summaryQuery.isError || summaryQuery.offline ? null : 'loading'} label={say("Memuat data perangkat…", "Loading device data…")} />
        <ReadFailure error={summaryQuery.error} label={say("Data perangkat belum dapat dimuat", "Could not load device data")} retrying={summaryQuery.isFetching} onRetry={retry} />
        {restored.length > 0 ? <AssetList label={say("Perangkat aktif tanpa ringkasan", "Active devices without a summary")} rows={restored} /> : null}
        {archiveSection}
      </HDScreen>
    );
  }
  if (summary.assets.length === 0 && !unranked.length && !previousSelection) {
    return <EmptyPerangkat title={title} onBack={onBack}>{archiveSection}</EmptyPerangkat>;
  }
  const staleIds = staleAssetIds(summary.source_freshness);
  const ranked = summary.assets
    .filter((row) => !archivedIds.has(row.asset_id))
    .map((row) => assetRowModel(row, active.get(row.asset_id), staleIds));
  return (
    <PopulatedPerangkat title={title} onBack={onBack} summary={summary}
      ranked={ranked} unranked={unranked} archiveSection={archiveSection} previousSelection={previousSelection}
      offline={summaryQuery.offline} fetchedAt={summaryQuery.confirmedAtFor(summary)}
      failure={summaryQuery.error} retrying={summaryQuery.isFetching} onRetry={retry}
      assetsFailed={assetsQuery.isError} />
  );
}

type PopulatedProps = {
  title: string;
  onBack?: () => void;
  summary: Summary;
  ranked: AssetRowModel[];
  unranked: Asset[];
  archiveSection: ReactNode;
  previousSelection: boolean;
  offline: boolean;
  fetchedAt?: number;
  failure: unknown;
  retrying: boolean;
  onRetry: () => void;
  assetsFailed: boolean;
};

function PopulatedPerangkat({
  title, onBack, summary, ranked, unranked, archiveSection, previousSelection,
  failure, retrying, onRetry, assetsFailed, offline, fetchedAt,
}: PopulatedProps) {
  const say = useCopy();
  const { workspace } = useWorkspace();
  const { period, setPeriod } = useNavigationContext();
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const model = berandaModel(summary);
  const scopeIssue = useScopeInvoker();
  const { excluded, issues, valid } = summary.scope;
  const issueAssets = [...summary.scope.included, ...excluded];
  const issueText = issues.map((issue) => scopeIssueCopy(issue, issueAssets)).join(' ');

  const supporting = (
    <>
      {archiveSection}
      <HDButton variant="text" onPress={openSettings}>{say("Pengaturan", "Settings")}</HDButton>
    </>
  );

  return (
    <HDScreen title={title} subtitle={copySubtitle()} onBack={onBack} supporting={supporting}>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
      ) : null}
      <SavedReadStatus offline={offline} failed={Boolean(failure)} fetchedAt={fetchedAt} timezone={model.timezone} />
      {previousSelection ? (
        <HDNotice tone="info" title={say("Ringkasan masih memakai cakupan sebelumnya", "Summary still uses the previous scope")}>
          {fetchedAt !== undefined && !offline
            ? say(`Terakhir dimuat: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. Angka berikut mengikuti cakupan sebelumnya.`, `Last loaded: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. The figures use the previous scope.`)
            : say("Angka dan cakupan berikut berasal dari ringkasan terakhir.", "The figures and scope below are from the last confirmed summary.")}
        </HDNotice>
      ) : null}
      <View style={styles.section}>
        <HDText variant="labelStrong">{model.scopeLabel}</HDText>
        <HDText variant="label" tone="secondary">{say("Hanya mencakup sumber yang dipilih.", "Includes only the selected sources.")}{excluded.length ? say(` Tidak termasuk: ${excluded.map((asset) => asset.name).join(', ')}.`, ` Excludes: ${excluded.map((asset) => asset.name).join(', ')}.`) : ''}
        </HDText>
        <HDProvenanceTag origins={shownOrigins(model.origins, workspace?.scenarioId)} />
      </View>
      {valid ? null : (
        <HDNotice tone="attention" title={say("Total gabungan belum dapat dihitung", "Combined total unavailable")}
          action={<HDButton {...scopeIssue}>{say("Selesaikan cakupan", "Resolve scope")}</HDButton>}>
          {say(`${issueText} Nilai masing-masing tetap ditampilkan.`, `${issueText} Individual readings are still available.`)}
        </HDNotice>
      )}
      <ReadFailure error={failure} label={say("Data perangkat belum dapat diperbarui", "Could not refresh device data")} retrying={retrying} onRetry={onRetry} kept />
      <View style={styles.section}>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>{say("Tambah sumber", "Add source")}</HDButton>
        <HDButton onPress={() => openImport()}>{say("Tambah data", "Add data")}</HDButton>
      </View>
      {assetsFailed ? <HDText variant="label">{say("Lokasi dan kategori belum dapat dimuat.", "Could not load location and category.")}</HDText> : null}
      {summary.source_freshness === undefined ? <HDText variant="label">{say("Kesegaran sumber belum diketahui.", "Source update status is unknown.")}</HDText> : null}
      <AssetList rows={ranked} />
      <HDText variant="label" tone="secondary">{say("Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat.", "Ranked by energy recorded in this period.")}</HDText>
      {unranked.length > 0 ? (
        <AssetList label={say("Perangkat aktif tanpa ringkasan", "Active devices without a summary")} rows={unranked.map((asset) => unrankedAssetRow(asset, false))} />
      ) : null}
      {model.allocated ? (
        <HDText variant="label">{say("Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).", "Readings crossing the period boundary are split evenly over their intervals (estimated).")}</HDText>
      ) : null}
    </HDScreen>
  );
}

function AssetList({ rows, label = copyList() }: { rows: AssetRowModel[]; label?: string }) {
  const { openAsset } = useTabNavigation();
  return (
    <View role="list" aria-label={label}>
      {rows.map((item) => (
        <View key={item.assetId} role="listitem">
          <HDAssetRow name={item.name} kind={item.kind} location={item.location} category={item.category} kwh={item.kwh}
            quality={item.quality} qualityLabel={item.qualityLabel} sources={item.sources} stale={item.stale}
            onOpen={() => openAsset(item.assetId)} />
        </View>
      ))}
    </View>
  );
}

function ArchiveSection({ open, toggle, assets, error, loading, loaded, incomplete }: {
  open: boolean;
  toggle: () => void;
  assets: Asset[];
  error: ApiError | null;
  loading: boolean;
  loaded: boolean;
  incomplete: boolean;
}) {
  const say = useCopy();
  return (
    <View style={styles.section}>
      <HDButton onPress={toggle} expanded={open}>{say("Diarsipkan", "Archived")}</HDButton>
      {open ? (
        <>
          <HDProgressStatus state={loading ? 'loading' : error ? 'failure' : null}
            label={loading ? say("Memuat daftar arsip…", "Loading archived devices…") : say("Daftar arsip belum dapat dimuat", "Could not load archived devices")}
            detail={error ? [errorMessage(error), error.requestId ? say(`ID referensi: ${error.requestId}.`, `Reference ID: ${error.requestId}.`) : null].filter(Boolean).join(' ') : null} />
          {assets.length ? <AssetList label={say("Perangkat diarsipkan", "Archived devices")} rows={assets.map((asset) => unrankedAssetRow(asset, true))} /> : null}
          {incomplete ? <HDText role="status">{say("Daftar arsip yang tampil belum lengkap.", "The archived list is incomplete.")}</HDText> : null}
          {loaded && !incomplete && assets.length === 0 ? <HDText>{say("Belum ada perangkat yang diarsipkan.", "No archived devices yet.")}</HDText> : null}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });
