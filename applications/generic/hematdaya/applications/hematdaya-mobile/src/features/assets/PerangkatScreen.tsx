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

const TITLE = 'Perangkat';
const LIST = 'Daftar perangkat, urut energi tercatat';
const SUBTITLE = 'Perangkat, grup, sirkuit, dan meter lokasi';

/** S04: every measured thing with its scope kind and quality, in the service's order. */
export function PerangkatScreen({ historyChooser = false }: { historyChooser?: boolean }) {
  const { status, workspace, credentialGeneration } = useWorkspace();
  const { back } = useTabNavigation();
  const onBack = historyChooser ? back : undefined;
  const title = historyChooser ? 'Riwayat perangkat' : TITLE;
  if (status === 'loading') {
    return (
      <HDScreen title={title} subtitle={SUBTITLE} onBack={onBack}>
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
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
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  return (
    <HDScreen title={title} subtitle={SUBTITLE} onBack={onBack}>
      <SessionEndedNotice />
      <View style={styles.section}>
        <HDText variant="section">Belum ada perangkat</HDText>
        <HDText>Perangkat muncul di sini setelah ada data energi. HematDaya tidak mengendalikan perangkat.</HDText>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>
          Tambah sumber
        </HDButton>
        <HDButton onPress={() => openImport()}>Impor data</HDButton>
        <View ref={demoButton}>
          <HDButton onPress={() => setSheetOpen(true)}>Coba demo</HDButton>
        </View>
      </View>
      {children}
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

function WorkspacePerangkat({ title, onBack }: { title: string; onBack?: () => void }) {
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
      <HDScreen title={title} subtitle={SUBTITLE} onBack={onBack}>
        <SavedReadStatus offline={summaryQuery.offline} />
        <HDProgressStatus state={summaryQuery.isError || summaryQuery.offline ? null : 'loading'} label="Memuat data perangkat…" />
        <ReadFailure error={summaryQuery.error} label="Data perangkat belum dapat dimuat" retrying={summaryQuery.isFetching} onRetry={retry} />
        {restored.length > 0 ? <AssetList label="Perangkat aktif tanpa ringkasan" rows={restored} /> : null}
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
  const { workspace } = useWorkspace();
  const { period, setPeriod } = useNavigationContext();
  const { openFeature, openImport, openSettings } = useTabNavigation();
  const model = berandaModel(summary);
  const scopeIssue = useScopeInvoker();
  const { excluded, issues, valid } = summary.scope;

  return (
    <HDScreen title={title} subtitle={SUBTITLE} onBack={onBack}>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
      ) : null}
      <SavedReadStatus offline={offline} failed={Boolean(failure)} fetchedAt={fetchedAt} timezone={model.timezone} />
      {previousSelection ? (
        <HDNotice tone="info" title="Ringkasan masih memakai cakupan sebelumnya">
          {fetchedAt !== undefined && !offline
            ? `Terakhir dimuat: ${formatDateTime(new Date(fetchedAt).toISOString(), model.timezone)}. Angka berikut mengikuti cakupan sebelumnya.`
            : 'Angka dan cakupan berikut berasal dari ringkasan terakhir.'}
        </HDNotice>
      ) : null}
      <View style={styles.section}>
        <HDText variant="labelStrong">{model.scopeLabel}</HDText>
        <HDText variant="label" tone="secondary">
          Hanya mencakup sumber yang dipilih.
          {excluded.length ? ` Tidak termasuk: ${excluded.map((asset) => asset.name).join(', ')}.` : ''}
        </HDText>
        <HDProvenanceTag origins={shownOrigins(model.origins, workspace?.scenarioId)} />
      </View>
      {valid ? null : (
        <HDNotice tone="attention" title="Total gabungan belum dapat dihitung"
          action={<HDButton {...scopeIssue}>Selesaikan cakupan</HDButton>}>
          {`${issues.map((issue) => issue.message).join(' ')} Nilai masing-masing tetap ditampilkan.`}
        </HDNotice>
      )}
      <ReadFailure error={failure} label="Data perangkat belum dapat diperbarui" retrying={retrying} onRetry={onRetry} kept />
      <View style={styles.section}>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>
          Tambah sumber
        </HDButton>
        <HDButton onPress={() => openImport()}>Impor data</HDButton>
      </View>
      {assetsFailed ? <HDText variant="label">Lokasi dan kategori belum dapat dimuat.</HDText> : null}
      {summary.source_freshness === undefined ? <HDText variant="label">Kesegaran sumber belum diketahui.</HDText> : null}
      <AssetList rows={ranked} />
      <HDText variant="label" tone="secondary">
        Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat.
      </HDText>
      {unranked.length > 0 ? (
        <AssetList label="Perangkat aktif tanpa ringkasan" rows={unranked.map((asset) => unrankedAssetRow(asset, false))} />
      ) : null}
      {model.allocated ? (
        <HDText variant="label">Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).</HDText>
      ) : null}
      {archiveSection}
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

function AssetList({ rows, label = LIST }: { rows: AssetRowModel[]; label?: string }) {
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
  return (
    <View style={styles.section}>
      <HDButton onPress={toggle} expanded={open}>Diarsipkan</HDButton>
      {open ? (
        <>
          <HDProgressStatus state={loading ? 'loading' : error ? 'failure' : null}
            label={loading ? 'Memuat daftar arsip…' : 'Daftar arsip belum dapat dimuat'}
            detail={error ? [error.message, error.requestId ? `ID referensi: ${error.requestId}.` : null].filter(Boolean).join(' ') : null} />
          {assets.length ? <AssetList label="Perangkat diarsipkan" rows={assets.map((asset) => unrankedAssetRow(asset, true))} /> : null}
          {incomplete ? <HDText role="status">Daftar arsip yang tampil belum lengkap.</HDText> : null}
          {loaded && !incomplete && assets.length === 0 ? <HDText>Belum ada perangkat yang diarsipkan.</HDText> : null}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });
