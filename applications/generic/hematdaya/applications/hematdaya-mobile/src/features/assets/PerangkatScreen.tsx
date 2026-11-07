import { useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import type { Asset, Summary } from '@/api/client';
import { HDAssetRow } from '@/components/hd/HDAssetRow';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDPeriodSelector } from '@/components/hd/HDPeriodSelector';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { assetRowModel, staleAssetIds } from '@/features/assets/asset-model';
import { ReadFailure } from '@/features/assets/ReadFailure';
import { useAssets } from '@/features/assets/useAssets';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { berandaModel, shownOrigins } from '@/features/energy/beranda-model';
import { useSummary } from '@/features/energy/useSummary';
import { useInsights } from '@/features/insights/useInsights';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

const TITLE = 'Perangkat';
const SUBTITLE = 'Perangkat, grup, sirkuit, dan meter lokasi';

/** S04: every measured thing with its scope kind and quality, in the service's order. */
export function PerangkatScreen() {
  const { status, workspace } = useWorkspace();
  if (status === 'loading') {
    return (
      <HDScreen title={TITLE} subtitle={SUBTITLE}>
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
      </HDScreen>
    );
  }
  // The key drops confirmed data and query observers, so nothing crosses workspaces.
  return workspace ? <WorkspacePerangkat key={workspace.siteId} /> : <EmptyPerangkat />;
}

/** No workspace or no asset: no number and no date, and every way data will arrive. */
function EmptyPerangkat() {
  const { openFeature, openSettings } = useTabNavigation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  return (
    <HDScreen title={TITLE} subtitle={SUBTITLE}>
      <SessionEndedNotice />
      <View style={styles.section}>
        <HDText variant="section">Belum ada perangkat</HDText>
        <HDText>Perangkat muncul di sini setelah ada data energi. HematDaya tidak mengendalikan perangkat.</HDText>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>
          Tambah sumber
        </HDButton>
        <HDButton onPress={() => openFeature('impor-data')}>Impor data</HDButton>
        <View ref={demoButton}>
          <HDButton onPress={() => setSheetOpen(true)}>Coba demo</HDButton>
        </View>
      </View>
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

function WorkspacePerangkat() {
  const summaryQuery = useSummary();
  const assetsQuery = useAssets();
  const insightsQuery = useInsights();
  const summary = useLastConfirmed(summaryQuery);
  const assets = useLastConfirmed(assetsQuery);
  const insights = useLastConfirmed(insightsQuery);
  const retry = () => void summaryQuery.refetch();

  if (summary === undefined) {
    return (
      <HDScreen title={TITLE} subtitle={SUBTITLE}>
        <HDProgressStatus state={summaryQuery.isError ? null : 'loading'} label="Memuat data perangkat…" />
        <ReadFailure error={summaryQuery.error} label="Data perangkat belum dapat dimuat" retrying={summaryQuery.isFetching} onRetry={retry} />
      </HDScreen>
    );
  }
  if (summary.assets.length === 0) {
    return <EmptyPerangkat />;
  }
  return (
    <PopulatedPerangkat
      summary={summary}
      assets={assets ?? []}
      staleIds={staleAssetIds(insights?.notices ?? [])}
      failure={summaryQuery.error}
      retrying={summaryQuery.isFetching}
      onRetry={retry}
      assetsFailed={assetsQuery.isError}
      staleCheckFailed={insightsQuery.isError}
    />
  );
}

type PopulatedProps = {
  summary: Summary;
  assets: Asset[];
  staleIds: ReadonlySet<string>;
  failure: unknown;
  retrying: boolean;
  onRetry: () => void;
  assetsFailed: boolean;
  staleCheckFailed: boolean;
};

function PopulatedPerangkat({ summary, assets, staleIds, failure, retrying, onRetry, assetsFailed, staleCheckFailed }: PopulatedProps) {
  const { workspace } = useWorkspace();
  const { period, setPeriod } = useNavigationContext();
  const { openAsset, openFeature, openSettings } = useTabNavigation();
  const model = berandaModel(summary);
  const { excluded, issues, valid } = summary.scope;

  return (
    <HDScreen title={TITLE} subtitle={SUBTITLE}>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
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
        <HDNotice tone="attention" title="Total gabungan belum dapat dihitung">
          {`${issues.map((issue) => issue.message).join(' ')} Nilai masing-masing tetap ditampilkan.`}
        </HDNotice>
      )}
      <ReadFailure error={failure} label="Data perangkat belum dapat diperbarui" retrying={retrying} onRetry={onRetry} kept />
      <View style={styles.section}>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>
          Tambah sumber
        </HDButton>
        <HDButton onPress={() => openFeature('impor-data')}>Impor data</HDButton>
      </View>
      {assetsFailed ? <HDText variant="label">Lokasi dan kategori belum dapat dimuat.</HDText> : null}
      {staleCheckFailed ? <HDText variant="label">Status pembaruan sumber belum dapat diperiksa.</HDText> : null}
      <View role="list" aria-label="Daftar perangkat, urut energi tercatat">
        {summary.assets.map((row) => {
          const item = assetRowModel(row, assets.find((asset) => asset.id === row.asset_id), staleIds);
          return (
            <View key={item.assetId} role="listitem">
              <HDAssetRow
                name={item.name}
                kind={item.kind}
                location={item.location}
                category={item.category}
                kwh={item.kwh}
                quality={item.quality}
                qualityLabel={item.qualityLabel}
                sources={item.sources}
                stale={item.stale}
                onOpen={() => openAsset(item.assetId)}
              />
            </View>
          );
        })}
      </View>
      <HDText variant="label" tone="secondary">
        Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat.
      </HDText>
      {model.allocated ? (
        <HDText variant="label">Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).</HDText>
      ) : null}
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });
