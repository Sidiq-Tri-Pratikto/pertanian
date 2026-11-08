import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import { ApiError } from '@/api/errors';
import type { AssetDetail as AssetDetailData, Summary } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDDataQuality, freshnessRows } from '@/components/hd/HDDataQuality';
import { HDEnergyMetric } from '@/components/hd/HDEnergyMetric';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDPeriodSelector } from '@/components/hd/HDPeriodSelector';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { assetDetailModel, assetSourceRows, originLabel, type AssetDetailModel, type SourceRow } from '@/features/assets/asset-model';
import { ArchiveAssetSheet } from '@/features/assets/ArchiveAssetSheet';
import { AssetWriteFeedback } from '@/features/assets/AssetWriteFeedback';
import { createAssetDraft, EditAssetSheet, reviewedDraft } from '@/features/assets/EditAssetSheet';
import { useAssetMutations } from '@/features/assets/useAssetMutations';
import { AssetHistorySection } from '@/features/assets/AssetHistorySection';
import { ReadFailure, SavedReadStatus } from '@/features/assets/ReadFailure';
import { useAsset } from '@/features/assets/useAssets';
import { useAssetSummary } from '@/features/assets/useAssetSummary';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { shownOrigins } from '@/features/energy/beranda-model';
import { useAssetDraft } from '@/features/offline/persist-drafts';
import { periodQuery, useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useScopeInvoker, useTabNavigation } from '@/features/navigation';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import type { Period } from '@/features/workspace/workspace-store';

const TITLE = 'Perangkat';
const LOADING = 'Memuat perangkat…';

/** S06: one asset for the shared period, with its quality and where its data comes from. */
export function AssetDetailScreen({ assetId }: { assetId: string | undefined }) {
  const { status, workspace, credentialGeneration } = useWorkspace();
  const { back } = useTabNavigation();
  if (status === 'loading') {
    return (
      <HDScreen title={TITLE} onBack={back}>
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
      </HDScreen>
    );
  }
  // A disabled query stays pending, so with nothing to ask this must not wait on one.
  if (workspace === null || assetId === undefined) {
    return <NotAvailable />;
  }
  return <AssetDetail key={`${workspace.siteId}:${credentialGeneration}:${assetId}`} assetId={assetId} />;
}

function NotAvailable({ requestId = null }: { requestId?: string | null }) {
  const { back } = useTabNavigation();
  return (
    <HDScreen title="Perangkat tidak ditemukan" onBack={back}>
      <HDNotice tone="attention" title="Perangkat tidak ditemukan">
        <HDText>Perangkat ini tidak ada di ruang kerja aktif.</HDText>
        {requestId ? <HDText>ID referensi: {requestId}.</HDText> : null}
      </HDNotice>
      <SessionEndedNotice />
    </HDScreen>
  );
}

function notFoundIn(...errors: unknown[]): ApiError | undefined {
  return errors.flatMap((error) => (error ? [ApiError.from(error)] : [])).find((failure) => failure.code === 'NOT_FOUND');
}

function AssetDetail({ assetId }: { assetId: string }) {
  const { back } = useTabNavigation();
  const { period } = useNavigationContext();
  const summaryQuery = useAssetSummary(assetId);
  const assetQuery = useAsset(assetId);
  const keptSummary = useLastConfirmed(summaryQuery);
  const summary = summaryQuery.offline ? summaryQuery.data : keptSummary;
  const savedDraft = useAssetDraft(assetId);
  const asset = useLastConfirmed(assetQuery);
  const retrySummary = summaryQuery.refresh;
  const retryAsset = () => void assetQuery.refetch();

  const notFound = notFoundIn(summaryQuery.error, assetQuery.error);
  if (notFound && !savedDraft.draft) {
    return <NotAvailable requestId={notFound.requestId} />;
  }

  const sourceSection = (timezone: string | null) => (
    <SourceSection
      rows={assetSourceRows(asset, timezone)}
      known={asset !== undefined}
      failure={assetQuery.error}
      retrying={assetQuery.isFetching}
      onRetry={retryAsset}
    />
  );

  const selected = period && periodQuery(period);
  const window = summaryQuery.isPlaceholderData ? undefined : summaryQuery.data?.window;
  const confirmedWindow = window && selected && (selected.preset ||
    (selected.start_date === window.start_date && selected.end_date === window.end_date)) ? window : null;
  const historyWindowError = window && !confirmedWindow ? ApiError.unexpected() : summaryQuery.error;
  const model = summary ? assetDetailModel(summary, asset) : undefined;
  return (
    <HDScreen title={model?.name || asset?.name || savedDraft.draft?.baseline.name || TITLE} subtitle={model?.meta} onBack={back}>
      {asset || savedDraft.draft ? <AssetActions assetId={assetId} asset={asset} saved={savedDraft} /> : null}
      {summary && model ? (
        <PopulatedDetail assetId={assetId} summary={summary} model={model}
          confirmedWindow={confirmedWindow} historyWindowError={historyWindowError}
          failure={summaryQuery.error} retrying={summaryQuery.isFetching} onRetry={retrySummary}
          offline={summaryQuery.offline} fetchedAt={summaryQuery.confirmedAtFor(summary)}
          previousSelection={summaryQuery.previousSelection || summary !== summaryQuery.data} />
      ) : (
        <>
          <SavedReadStatus offline={summaryQuery.offline} />
          <HDProgressStatus state={summaryQuery.isError || summaryQuery.offline ? null : 'loading'} label={LOADING} />
          <ReadFailure error={summaryQuery.error} label="Perangkat belum dapat dimuat"
            retrying={summaryQuery.isFetching} onRetry={retrySummary} />
        </>
      )}
      {asset || summary ? sourceSection(summary?.window.timezone ?? null) : null}
    </HDScreen>
  );
}

function AssetActions({ assetId, asset, saved }: {
  assetId: string; asset?: AssetDetailData; saved: ReturnType<typeof useAssetDraft>;
}) {
  const [sheet, setSheet] = useState<'edit' | 'archive' | null>(null);
  const { draft, change: setDraft, restored, reconciled, failed } = saved;
  const [archive, setArchive] = useState(false);
  const editButton = useRef<ComponentRef<typeof View>>(null);
  const archiveButton = useRef<ComponentRef<typeof View>>(null);
  const { state, submit, reconcileDraft, checkOutcome, review, dismiss, blocked } = useAssetMutations(assetId);
  const close = () => setSheet(null);
  const edit = state?.changes.archived === undefined;
  const pendingReview = state?.kind === 'diverged';

  const [handled, setHandled] = useState(state);
  useEffect(() => {
    if (state?.kind === 'draft-ready' && restored && draft) {
      reconciled();
      setDraft(reviewedDraft(draft, state.observed, state.changes));
    }
  }, [draft, reconciled, restored, setDraft, state]);
  useEffect(() => {
    if ((state?.kind !== 'acknowledged' && state?.kind !== 'observed') || state === handled) return;
    // Mutation state comes from the external query cache. Clear the form after its confirmed transition.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHandled(state);
    if (edit) setDraft(null);
    if (sheet === (edit ? 'edit' : 'archive')) setSheet(null);
  }, [edit, handled, setDraft, sheet, state]);

  function discardDraft() {
    if (edit) dismiss();
    setDraft(null);
    close();
  }

  let announcement = asset?.archived ? 'Diarsipkan. Pulihkan dari Perangkat, di bagian Diarsipkan.' : null;
  if (state?.kind === 'observed') {
    announcement = edit ? 'Data saat diperiksa sesuai dengan draf.' : `Status saat diperiksa: ${announcement ?? 'aktif.'}`;
  } else if (state?.kind === 'acknowledged') {
    announcement = edit ? 'Detail perangkat disimpan.' : (announcement ?? 'Perangkat dipulihkan ke daftar aktif.');
  }

  const editable = draft ?? (asset ? createAssetDraft(asset) : null);
  if (!asset && !editable && !announcement) return null;
  return (
    <View style={styles.section}>
      {!asset && draft ? <HDText>Detail perangkat terkini belum tersedia. Anda masih dapat membuka draf tersimpan.</HDText> : null}
      <View role="status" accessibilityLiveRegion="polite">{announcement ? <HDText>{announcement}</HDText> : null}</View>
      <View style={styles.actions}>
        <HDButton ref={editButton} disabledReason={pendingReview && !edit ? 'Tinjau status arsip dahulu.' : undefined}
          onPress={() => { if (!draft && asset) setDraft(createAssetDraft(asset)); setSheet('edit'); }}>
          {restored ? 'Buka draf detail' : 'Ubah detail'}</HDButton>
        {asset ? <HDButton ref={archiveButton} disabledReason={pendingReview && edit ? 'Tinjau draf detail dahulu.' : undefined}
          onPress={() => { setArchive(!asset.archived); setSheet('archive'); }}>{asset.archived ? 'Pulihkan' : 'Arsipkan'}</HDButton> : null}
      </View>
      {sheet === null && blocked ? <AssetWriteFeedback state={state} onCheck={() => void checkOutcome()} /> : null}
      {editable ? <EditAssetSheet open={sheet === 'edit'} draft={editable} onDraft={setDraft}
        onSubmit={(changes) => { void (restored ? reconcileDraft(changes, editable.baseline) : submit(changes)); }}
        onReview={review} onCheck={() => void checkOutcome()} state={state} blocked={blocked} storageFailed={failed}
        onClose={close} onDiscard={discardDraft} returnFocusTo={editButton} /> : null}
      {asset ? <ArchiveAssetSheet open={sheet === 'archive'} asset={asset} archive={archive} state={state} blocked={blocked}
        onSubmit={(changes) => void submit(changes)} onReview={review} onCheck={() => void checkOutcome()} onClose={close} returnFocusTo={archiveButton} /> : null}
    </View>
  );
}

function samePeriod(one: Period, other: Period) {
  return JSON.stringify(periodQuery(one)) === JSON.stringify(periodQuery(other));
}

type PopulatedProps = {
  assetId: string;
  summary: Summary;
  confirmedWindow: Summary['window'] | null;
  historyWindowError: ApiError | Error | null;
  model: AssetDetailModel;
  failure: unknown;
  retrying: boolean;
  onRetry: () => void;
  offline: boolean;
  fetchedAt?: number;
  previousSelection: boolean;
};

function PopulatedDetail({ assetId, summary, confirmedWindow, historyWindowError, model, failure, retrying, onRetry, offline, fetchedAt, previousSelection }: PopulatedProps) {
  const { workspace } = useWorkspace();
  const scopeIssue = useScopeInvoker();
  const { period, setPeriod } = useNavigationContext();
  // A summary's origins are empty on a no-data period and on a conflict, so sources speak first.
  const origins = model.origins.length ? model.origins : shownOrigins(summary.origins, workspace?.scenarioId);
  const simulated = origins.includes('simulated');
  // The service has no per-asset data range. A button that changes nothing would be a dead end.
  const canShowDataPeriod = model.state === 'none' && workspace && period && !samePeriod(period, workspace.initialPeriod);

  return (
    <>
      {period ? (
        <HDPeriodSelector value={period} activeLabel={model.periodLabel} timezone={model.timezone} onCommit={setPeriod} />
      ) : null}
      <SavedReadStatus offline={offline} failed={Boolean(failure)} fetchedAt={fetchedAt} timezone={model.timezone} />
      {previousSelection ? <HDNotice tone="info" title="Ringkasan masih memakai pilihan sebelumnya">
        Periode dan cakupan berikut mengikuti ringkasan terakhir.
      </HDNotice> : null}
      {model.state === 'conflict' ? (
        <View style={styles.section}>
          <HDProvenanceTag origins={origins} />
          <HDText variant="label">{model.scopeLabel}</HDText>
          <HDNotice tone="attention" title="Lebih dari satu sumber untuk beban yang sama"
            action={<HDButton {...scopeIssue}>Selesaikan cakupan</HDButton>}>
            <View style={styles.tight}>
              {model.sources.map((line, index) => (
                <HDText key={`${index}-${line}`}>{line}</HDText>
              ))}
              {model.issues.map((issue) => (
                <HDText key={issue}>{issue}</HDText>
              ))}
            </View>
          </HDNotice>
        </View>
      ) : (
        <HDEnergyMetric
          state={model.state}
          kwh={model.kwh}
          qualifier={model.qualifier}
          gaps={model.gaps}
          periodLabel={model.periodLabel}
          scopeLabel={model.scopeLabel}
          origins={origins}
          emptyDetail={model.emptyDetail}
          issues={[]}
          action={
            canShowDataPeriod ? (
              <HDButton icon="chevronRight" onPress={() => setPeriod(workspace.initialPeriod)}>
                Lihat periode data
              </HDButton>
            ) : null
          }
        />
      )}
      {model.allocated ? (
        <HDText variant="label">Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).</HDText>
      ) : null}
      <ReadFailure error={failure} label="Data perangkat belum dapat diperbarui" retrying={retrying} onRetry={onRetry} kept />
      {summary.source_freshness?.some((source) => source.state === 'stale') ? (
        <HDButton variant="text" icon="refresh" loading={retrying} onPress={onRetry}>Periksa sumber</HDButton>
      ) : null}
      <HDDataQuality
        rows={[
          ...freshnessRows(summary.source_freshness, model.timezone, summary.assets),
          ...(model.completeness ? [{ term: 'Kelengkapan data', value: model.completeness }] : []),
          ...(model.latest ? [{ term: 'Pengukuran terakhir', value: `${model.latest}${simulated ? ' (data simulasi)' : ''}` }] : []),
          ...(simulated
            ? [{ term: 'Asal data', value: 'Data simulasi untuk demo', detail: 'Bukan pengukuran dari perangkat nyata.' }]
            : origins.length
              ? [{ term: 'Asal data', value: origins.map(originLabel).join(', ') }]
              : []),
        ]}
      />
      <AssetHistorySection
        assetId={assetId}
        assetName={model.name}
        scopeLabel={model.scopeLabel}
        confirmed={confirmedWindow}
        summaryError={historyWindowError}
      />
    </>
  );
}

type SourceSectionProps = { rows: SourceRow[]; known: boolean; failure: unknown; retrying: boolean; onRetry: () => void };

/** Where this asset's data comes from, one entry per binding. Null cadence or resolution says it is unknown. */
function SourceSection({ rows, known, failure, retrying, onRetry }: SourceSectionProps) {
  return (
    <View style={styles.section}>
      <HDText variant="section">Sumber data</HDText>
      {known ? (
        rows.length ? (
          <View role="list" aria-label="Sumber data" style={styles.section}>
            {rows.map((row) => (
              <View key={row.id} role="listitem" style={styles.tight}>
                <SourceTerm term="Sumber" value={row.label} />
                <SourceTerm term="Asal" value={row.origin} />
                <SourceTerm term="Interval dan resolusi" value={row.interval} />
                {row.effective ? <SourceTerm term="Berlaku" value={row.effective} /> : null}
                <SourceTerm term="Peran" value={row.role} />
              </View>
            ))}
          </View>
        ) : (
          <HDText>Belum ada sumber untuk perangkat ini.</HDText>
        )
      ) : failure ? null : (
        <HDProgressStatus state="loading" label={LOADING} />
      )}
      <ReadFailure error={failure} label="Sumber data belum dapat dimuat" retrying={retrying} onRetry={onRetry} />
    </View>
  );
}

function SourceTerm({ term, value }: { term: string; value: string }) {
  return (
    <View>
      <HDText variant="labelStrong">{term}</HDText>
      <HDText>{value}</HDText>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: tokens.space.stack },
  tight: { gap: tokens.space.stackTight },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.stackTight },
});
