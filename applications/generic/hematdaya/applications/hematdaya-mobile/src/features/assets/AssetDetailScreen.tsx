import { useIsFocused } from 'expo-router';
import { useCopy } from '@/features/localization/messages';
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


/** S06: one asset for the shared period, with its quality and where its data comes from. */
export function AssetDetailScreen({ assetId }: { assetId: string | undefined }) {
  const say = useCopy();
  const { status, workspace, credentialGeneration } = useWorkspace();
  const { back } = useTabNavigation();
  if (status === 'loading') {
    return (
      <HDScreen title={say('Perangkat', 'Devices')} onBack={back}>
        <HDProgressStatus state="loading" label={say("Memuat ruang kerja…", "Loading workspace…")} />
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
  const say = useCopy();
  const { back } = useTabNavigation();
  return (
    <HDScreen title={say("Perangkat tidak ditemukan", "Device not found")} onBack={back}>
      <HDNotice tone="attention" title={say("Perangkat tidak ditemukan", "Device not found")}>
        <HDText>{say("Perangkat ini tidak ada di ruang kerja aktif.", "This device is outside the active workspace.")}</HDText>
        {requestId ? <HDText>{say("ID referensi:", "Reference ID:")} {requestId}.</HDText> : null}
      </HDNotice>
      <SessionEndedNotice />
    </HDScreen>
  );
}

function notFoundIn(...errors: unknown[]): ApiError | undefined {
  return errors.flatMap((error) => (error ? [ApiError.from(error)] : [])).find((failure) => failure.code === 'NOT_FOUND');
}

function AssetDetail({ assetId }: { assetId: string }) {
  const say = useCopy();
  const { back } = useTabNavigation();
  const { period } = useNavigationContext();
  const summaryQuery = useAssetSummary(assetId, useIsFocused());
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
    <HDScreen title={model?.name || asset?.name || savedDraft.draft?.baseline.name || say('Perangkat', 'Devices')} subtitle={model?.meta} onBack={back}>
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
          <HDProgressStatus state={summaryQuery.isError || summaryQuery.offline ? null : 'loading'} label={say('Memuat perangkat…', 'Loading device…')} />
          <ReadFailure error={summaryQuery.error} label={say("Perangkat belum dapat dimuat", "Could not load the device")}
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
  const say = useCopy();
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

  let announcement = asset?.archived ? say("Diarsipkan. Pulihkan dari Perangkat, di bagian Diarsipkan.", "Archived. You can restore it under Archived in Devices.") : null;
  if (state?.kind === 'observed') {
    announcement = edit ? say("Data saat diperiksa sesuai dengan draf.", "The current details match your draft.") : say(`Status saat diperiksa: ${announcement ?? 'aktif.'}`, `Status when checked: ${announcement ?? 'aktif.'}`);
  } else if (state?.kind === 'acknowledged') {
    announcement = edit ? say("Detail perangkat disimpan.", "Device details saved.") : (announcement ?? say("Perangkat dipulihkan ke daftar aktif.", "Device restored to the active list."));
  }

  const editable = draft ?? (asset ? createAssetDraft(asset) : null);
  if (!asset && !editable && !announcement) return null;
  return (
    <View style={styles.section}>
      {!asset && draft ? <HDText>{say("Detail perangkat terkini belum tersedia. Anda masih dapat membuka draf tersimpan.", "Current device details are unavailable. You can still open your saved draft.")}</HDText> : null}
      <View role="status" accessibilityLiveRegion="polite">{announcement ? <HDText>{announcement}</HDText> : null}</View>
      <View style={styles.actions}>
        <HDButton ref={editButton} disabledReason={pendingReview && !edit ? say("Tinjau status arsip dahulu.", "Check the archive status first.") : undefined}
          onPress={() => { if (!draft && asset) setDraft(createAssetDraft(asset)); setSheet('edit'); }}>
          {restored ? say("Buka draf detail", "Open detail draft") : say("Ubah detail", "Edit details")}</HDButton>
        {asset ? <HDButton ref={archiveButton} disabledReason={pendingReview && edit ? say("Tinjau draf detail dahulu.", "Review the details draft first.") : undefined}
          onPress={() => { setArchive(!asset.archived); setSheet('archive'); }}>{asset.archived ? say("Pulihkan", "Restore") : say("Arsipkan", "Archive")}</HDButton> : null}
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
  const say = useCopy();
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
      {previousSelection ? <HDNotice tone="info" title={say("Ringkasan masih memakai pilihan sebelumnya", "Summary still uses the previous selection")}>{say("Periode dan cakupan berikut mengikuti ringkasan terakhir.", "The period and scope below are from the last confirmed summary.")}</HDNotice> : null}
      {model.state === 'conflict' ? (
        <View style={styles.section}>
          <HDProvenanceTag origins={origins} />
          <HDText variant="label">{model.scopeLabel}</HDText>
          <HDNotice tone="attention" title={say("Lebih dari satu sumber untuk beban yang sama", "Multiple sources measure the same load")}
            action={<HDButton {...scopeIssue}>{say("Selesaikan cakupan", "Resolve scope")}</HDButton>}>
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
              <HDButton icon="chevronRight" onPress={() => setPeriod(workspace.initialPeriod)}>{say("Lihat periode data", "View data period")}</HDButton>
            ) : null
          }
        />
      )}
      {model.allocated ? (
        <HDText variant="label">{say("Sebagian interval melewati batas periode dan dibagi rata dalam intervalnya (estimasi).", "Readings crossing the period boundary are split evenly over their intervals (estimated).")}</HDText>
      ) : null}
      <ReadFailure error={failure} label={say("Data perangkat belum dapat diperbarui", "Could not refresh device data")} retrying={retrying} onRetry={onRetry} kept />
      {summary.source_freshness?.some((source) => source.state === 'stale') ? (
        <HDButton variant="text" icon="refresh" loading={retrying} onPress={onRetry}>{say("Periksa sumber", "Check sources")}</HDButton>
      ) : null}
      <HDDataQuality
        rows={[
          ...freshnessRows(summary.source_freshness, model.timezone, summary.assets),
          ...(model.completeness ? [{ term: say("Kelengkapan data", "Data coverage"), value: model.completeness }] : []),
          ...(model.latest ? [{ term: say("Pengukuran terakhir", "Last reading"), value: `${model.latest}${simulated ? say(" (data simulasi)", " (simulated data)") : ''}` }] : []),
          ...(simulated
            ? [{ term: say("Asal data", "Data source"), value: say("Data simulasi untuk demo", "Simulated demo data"), detail: say("Bukan pengukuran dari perangkat nyata.", "These readings are simulated.") }]
            : origins.length
              ? [{ term: say("Asal data", "Data source"), value: origins.map(originLabel).join(', ') }]
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
  const say = useCopy();
  return (
    <View style={styles.section}>
      <HDText variant="section">{say("Sumber data", "Data sources")}</HDText>
      {known ? (
        rows.length ? (
          <View role="list" aria-label={say("Sumber data", "Data sources")} style={styles.section}>
            {rows.map((row) => (
              <View key={row.id} role="listitem" style={styles.tight}>
                <SourceTerm term={say("Sumber", "Source")} value={row.label} />
                <SourceTerm term={say("Asal", "Origin")} value={row.origin} />
                <SourceTerm term={say("Interval dan resolusi", "Interval and resolution")} value={row.interval} />
                {row.effective ? <SourceTerm term={say("Berlaku", "Effective")} value={row.effective} /> : null}
                <SourceTerm term={say("Peran", "Role")} value={row.role} />
              </View>
            ))}
          </View>
        ) : (
          <HDText>{say("Belum ada sumber untuk perangkat ini.", "This device has no sources yet.")}</HDText>
        )
      ) : failure ? null : (
        <HDProgressStatus state="loading" label={say('Memuat perangkat…', 'Loading device…')} />
      )}
      <ReadFailure error={failure} label={say("Sumber data belum dapat dimuat", "Could not load data sources")} retrying={retrying} onRetry={onRetry} />
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
