import { StyleSheet, View } from 'react-native';

import { selectionScopePair, summaryScopePair, type ScopePreview, type Summary } from '@/api/client';
import type { ApiError } from '@/api/errors';
import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDScopeSummary, scopeEnergy } from '@/components/hd/HDScopeSummary';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useLastConfirmed } from '@/features/assets/useLastConfirmed';
import { SavedReadStatus } from '@/features/assets/ReadFailure';
import { shownOrigins } from '@/features/energy/beranda-model';
import { useSummary } from '@/features/energy/useSummary';
import { useNavigationContext } from '@/features/navigation-context/NavigationContextProvider';
import { useTabNavigation } from '@/features/navigation';
import { candidateCutover, useScopeDraft } from '@/features/scope/useScopeDraft';
import { useScopeSave, useSelection } from '@/features/scope/useSelection';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDateRange, formatDateTime, formatKwh } from '@/lib/format';

const TITLE = 'Cakupan dan sumber';

function Evidence({ error }: { error: ApiError }) {
  return (
    <View style={styles.group}>
      <HDText>{error.message}</HDText>
      {error.details.map((row, index) => <HDText key={`${row.type}-${index}`}>{row.msg}</HDText>)}
      {error.requestId ? <HDText variant="label">{`ID referensi: ${error.requestId}.`}</HDText> : null}
    </View>
  );
}

function WindowLabel({ data, title }: { data: Summary; title: string }) {
  const { window } = data;
  return (
    <View style={styles.group}>
      <HDText variant="labelStrong">{title}</HDText>
      <HDText>{`${formatDateRange(window.start_date, window.end_date)} · ${window.timezone}`}</HDText>
      <HDText variant="label">{`Data hingga ${formatDateTime(window.effective_end, window.timezone)}.`}</HDText>
    </View>
  );
}

function optionEnergy(result: ScopePreview | undefined): string {
  if (!result) return 'Nilai belum tersedia';
  const { scope, energy_kwh, energy_unavailable_reason } = result.summary;
  return scopeEnergy(scope.valid ? energy_kwh : null, energy_unavailable_reason);
}

function optionContext(result: ScopePreview | undefined, confirmed: Summary['window']) {
  if (!result) return undefined;
  const { window } = result.summary;
  if (window.is_current) return `Data hingga ${formatDateTime(window.effective_end, window.timezone)} (${window.timezone}).`;
  if (window.start !== confirmed.start || window.end !== confirmed.end || window.timezone !== confirmed.timezone) {
    return `${formatDateRange(window.start_date, window.end_date)} · ${window.timezone}`;
  }
  return undefined;
}

export function ScopeScreen() {
  const { workspace, credentialGeneration, status } = useWorkspace();
  const { scopeBack } = useTabNavigation();
  if (!workspace) {
    return (
      <HDScreen title={TITLE} onBack={scopeBack}>
        <SessionEndedNotice />
        {status === 'loading' ? <HDProgressStatus state="loading" label="Memuat ruang kerja…" /> : (
          <HDNotice title="Belum ada ruang kerja aktif">Buka ruang kerja untuk meninjau cakupan pengukuran.</HDNotice>
        )}
      </HDScreen>
    );
  }
  return <OwnedScope key={`${workspace.siteId}:${credentialGeneration}`} onBack={scopeBack} />;
}

function OwnedScope({ onBack }: { onBack: () => void }) {
  const { workspace, scopeEpoch, isScopeCurrent, scopeWriting, scopeAttempt } = useWorkspace();
  const { period } = useNavigationContext();
  const summary = useSummary();
  const selection = useSelection();
  const save = useScopeSave(selection, summary);
  const kept = useLastConfirmed(summary);
  const data = summary.data;
  const pair = data && summaryScopePair(data);
  const selected = selection.data && selectionScopePair(selection.data);
  const confirmed = data && !summary.previousSelection && pair && selected &&
    isScopeCurrent(scopeEpoch, pair) && isScopeCurrent(scopeEpoch, selected) ? data : undefined;
  const draft = useScopeDraft(confirmed ? selection.data : undefined, confirmed, period);
  const previous = kept && kept !== confirmed ? kept : undefined;
  const displayed = confirmed ?? previous;
  const fetchedAt = displayed && summary.confirmedAtFor(displayed);
  const status = save.status;
  const busy = scopeWriting || status?.kind === 'saving' || status?.kind === 'checking';
  const sent = status?.kind === 'saving' && status.dispatched;
  const checked = draft.reviewed?.response.summary;
  const members = draft.proposal?.selected_asset_ids ?? [];
  const cannotPreview = summary.offline ? 'Sambungkan perangkat untuk memuat pratinjau.' :
    !confirmed ? 'Tunggu ringkasan dan pilihan cakupan terkonfirmasi.' :
    members.length === 0 ? 'Pilih setidaknya satu perangkat.' :
    members.length > 100 ? 'Pilih paling banyak 100 perangkat.' : null;
  const cannotConfirm = cannotPreview ?? (draft.previewing ? 'Tunggu pratinjau selesai.' :
    !checked ? 'Tinjau pratinjau cakupan sebelum menyimpan.' :
    !checked.scope.valid ? 'Selesaikan tumpang tindih atau pilih sumber acuan pada pratinjau.' : null);

  function leave() {
    draft.discard();
    onBack();
  }

  function verify() {
    if (period) void save.check(period);
  }

  const errors = [selection.error, summary.error].filter((error): error is ApiError => error !== null);
  const confirm = (
    <HDButton variant="primary" fullWidth loading={busy} loadingLabel="Memproses cakupan…" disabledReason={cannotConfirm}
      onPress={() => {
        const review = draft.reviewed;
        if (review) void save.save(review, draft.reviewIsCurrent, draft.wasDiscarded).then((acknowledged) => {
          if (acknowledged !== undefined) draft.finishReview(review, acknowledged);
        });
      }}>Konfirmasi cakupan</HDButton>
  );
  return (
    <HDScreen title={TITLE} onBack={leave} footer={confirm}>
      <HDProgressStatus state={busy ? status?.kind === 'checking' ? 'loading' : 'saving' :
        draft.previewing || (!displayed && !summary.offline && errors.length === 0) ? 'loading' : null}
        label={status?.kind === 'checking' ? 'Memeriksa cakupan terkonfirmasi…' :
          busy ? 'Menyimpan cakupan…' : draft.previewing ? 'Menghitung pratinjau cakupan…' : 'Memuat cakupan pengukuran…'} />
      <SavedReadStatus offline={summary.offline} failed={errors.length > 0} fetchedAt={fetchedAt} timezone={displayed?.window.timezone} />
      <ScopeSaveNotice status={status} pending={save.pending} offline={summary.offline} onCheck={verify} />
      {errors.length ? <HDNotice tone="error" title="Cakupan terkonfirmasi belum dapat dimuat" live
        action={<HDButton variant="text" onPress={verify} disabledReason={summary.offline ? 'Sambungkan perangkat untuk memeriksa cakupan.' : null}>Periksa cakupan</HDButton>}>
        {errors.map((error, index) => <Evidence key={index} error={error} />)}
      </HDNotice> : null}
      {previous ? (
        <View style={styles.group}>
          <HDNotice tone="info" title="Ringkasan masih memakai cakupan sebelumnya">
            {fetchedAt ? `Terakhir dimuat: ${formatDateTime(new Date(fetchedAt).toISOString(), previous.window.timezone)}.` :
              'Tunggu ringkasan untuk cakupan terkini.'}
          </HDNotice>
          <WindowLabel data={previous} title="Periode ringkasan sebelumnya" />
          <HDProvenanceTag origins={shownOrigins(previous.origins, workspace?.scenarioId)} />
          <HDScopeSummary summary={previous} />
        </View>
      ) : null}
      {confirmed && selection.data ? (
        <>
          <View style={styles.group}>
            <HDText variant="section">Cakupan terkonfirmasi</HDText>
            <WindowLabel data={confirmed} title="Periode pengukuran" />
            <HDProvenanceTag origins={shownOrigins(confirmed.origins, workspace?.scenarioId)} />
            <HDScopeSummary summary={confirmed} />
            {confirmed.scope.excluded.filter((row) => row.reason === 'archived' && selection.data?.selected_asset_ids.includes(row.asset_id))
              .map((row) => <HDText key={row.asset_id} variant="label">{`${row.name} masih tercatat dalam pilihan tersimpan dan dikecualikan karena diarsipkan.`}</HDText>)}
          </View>
          <DraftControls confirmed={confirmed} selection={selection.data} draft={draft} disabled={busy || summary.offline} />
        </>
      ) : null}
      {draft.error ? <HDNotice tone="error" title="Pratinjau belum dapat digunakan" live
        action={draft.error.code === 'SCOPE_STALE' ? <HDButton variant="text" onPress={verify}>Periksa cakupan</HDButton> : null}>
        <Evidence error={draft.error} />
      </HDNotice> : null}
      {checked ? (
        <View style={styles.group}>
          <HDText variant="section">Pratinjau cakupan</HDText>
          <WindowLabel data={checked} title="Periode yang ditinjau" />
          <HDProvenanceTag origins={shownOrigins(checked.origins, workspace?.scenarioId)} />
          <HDScopeSummary summary={checked} />
        </View>
      ) : null}
      <View style={styles.group}>
        <HDButton onPress={() => void draft.preview()} loading={draft.previewing}
          disabledReason={cannotPreview ?? (busy ? 'Tunggu pemeriksaan cakupan selesai.' : null)}>Pratinjau cakupan</HDButton>
        {sent ? <HDText variant="label">Permintaan sudah dikirim. Penyimpanan dapat selesai setelah halaman ditutup.</HDText> : null}
        <HDButton variant="text" onPress={leave}>{sent ? 'Tutup' : 'Batal'}</HDButton>
      </View>
      {scopeAttempt && !save.pending && !busy && !status ? (
        <HDNotice tone="info" title="Cakupan terbaru tersedia">
          Pemeriksaan menemukan revisi yang lebih baru. Periksa kembali cakupan sebelum membuat perubahan.
        </HDNotice>
      ) : null}
    </HDScreen>
  );
}

function DraftControls({ confirmed, selection, draft, disabled }: {
  confirmed: Summary;
  selection: NonNullable<ReturnType<typeof useSelection>['data']>;
  draft: ReturnType<typeof useScopeDraft>;
  disabled: boolean;
}) {
  const members = draft.proposal?.selected_asset_ids ?? [];
  const all = [...confirmed.scope.included, ...confirmed.scope.excluded];
  const names = new Map(all.map((row) => [row.asset_id, row.name]));
  const assets = all.filter((row) => !('reason' in row) || row.reason !== 'archived');
  const contained = selection.relations.filter((row) => row.kind === 'contains' && names.has(row.from_asset_id) && names.has(row.to_asset_id));
  const parent = draft.groups?.parent;
  const children = draft.groups?.children ?? [];
  const unknown = draft.groups?.disjoint ?? [];
  const parentPreview = draft.options.get('parent');
  const childrenPreview = draft.options.get('children');
  const choice = draft.options.get('candidates');
  return (
    <>
      {contained.length > 0 ? <View style={styles.group}>
        <HDText variant="section">Hubungan pengukuran</HDText>
        {contained.map((row) => (
          <HDText key={`${row.from_asset_id}:${row.to_asset_id}`}>{`${names.get(row.from_asset_id)} mencakup ${names.get(row.to_asset_id)}.`}</HDText>
        ))}
      </View> : null}
      {parent && children.length > 0 ? (
        <HDChoiceGroup
          legend="Pilih tampilan pengukuran"
          help="Pilih nilai meter atau perangkat yang dicakupnya."
          disabled={disabled}
          value={draft.variant}
          onChange={(value) => draft.selectMembers(value === 'parent' ? [parent] : children)}
          options={[
            { value: 'parent', testID: 'scope-view-parent', label: `${names.get(parent)} · ${optionEnergy(parentPreview)}`,
              description: optionContext(parentPreview, confirmed.window) },
            { value: 'children', label: `Perangkat dalam ${names.get(parent)} · ${optionEnergy(childrenPreview)}`,
              description: [children.map((id) => names.get(id)).join(', '), optionContext(childrenPreview, confirmed.window)].filter(Boolean).join(' · ') },
          ]} />
      ) : null}
      <HDChoiceGroup type="checkbox" legend="Perangkat dalam draf" value={members} disabled={disabled}
        onChange={draft.selectMembers} options={assets.map((asset) => ({ value: asset.asset_id, label: asset.name }))} />
      {unknown.length > 0 ? (
        <View style={styles.group}>
          <HDText variant="section">Nilai masing-masing perangkat</HDText>
          <HDText>Periksa apakah kedua alat ukur mencatat beban yang terpisah.</HDText>
          {[...new Set(unknown.flatMap((row) => [row.first_asset_id, row.second_asset_id]))].map((id) => {
            const individual = draft.options.get(id);
            const row = confirmed.assets.find((item) => item.asset_id === id);
            const changedAuthority = draft.proposal?.authority_actions?.some((action) => action.action === 'choose' && action.asset_id === id);
            const energy = !individual && row && !changedAuthority ? scopeEnergy(row.energy_kwh, row.energy_unavailable_reason) : optionEnergy(individual);
            const context = optionContext(individual, confirmed.window);
            return names.has(id) ? <View key={id} style={styles.group}>
              <HDText>{`${names.get(id)} · ${energy}`}</HDText>
              {context ? <HDText variant="label" tone="secondary">{context}</HDText> : null}
            </View> : null;
          })}
          {unknown.filter((row) => members.includes(row.first_asset_id) && members.includes(row.second_asset_id) &&
            assets.some((asset) => asset.asset_id === row.first_asset_id) && assets.some((asset) => asset.asset_id === row.second_asset_id))
            .map((row) => {
              const value = `${row.first_asset_id}:${row.second_asset_id}`;
              const checked = draft.proposal?.disjoint_confirmations?.some((pair) =>
                pair.first_asset_id === row.first_asset_id && pair.second_asset_id === row.second_asset_id);
              return <HDChoiceGroup key={value} type="checkbox" legend="Konfirmasi beban terpisah" disabled={disabled}
                value={checked ? [value] : []} onChange={(chosen) => draft.changeDisjoint(row, chosen.length > 0)}
                options={[{ value, label: `Saya memastikan ${names.get(row.first_asset_id)} dan ${names.get(row.second_asset_id)} mengukur beban terpisah` }]} />;
            })}
        </View>
      ) : null}
      {choice ? assets.filter((asset) => members.includes(asset.asset_id)).map((asset) => {
        const candidates = choice.candidates.filter((row) => row.asset_id === asset.asset_id);
        const readings = choice.summary.assets.find((row) => row.asset_id === asset.asset_id)?.conflict_sources ?? [];
        if (candidates.length < 2 && readings.length < 2 && !draft.chosen[asset.asset_id]) return null;
        const { window } = choice.summary;
        return (
          <HDChoiceGroup key={asset.asset_id} legend={`Sumber acuan · ${asset.name}`}
            disabled={disabled}
            help={`Pilih sumber untuk ${formatDateRange(window.start_date, window.end_date)}.`}
            value={draft.chosen[asset.asset_id] ?? null} onChange={(id) => draft.chooseAuthority(asset.asset_id, id)}
            options={[
              ...candidates.map((candidate) => {
                const action = candidateCutover(candidate.binding_id, candidates, window);
                const reading = readings.find((row) => row.source_id === candidate.source_id);
                return {
                  value: candidate.binding_id,
                  label: reading ? `${candidate.label} · ${formatKwh(reading.energy_kwh)}` : candidate.label,
                  description: action ? `Berlaku mulai ${formatDateTime(action.effective_from, window.timezone)} (${window.timezone}) · ${action.effective_from}` : undefined,
                  disabledReason: action ? undefined : 'Waktu mulai sumber ini belum dapat dipastikan untuk periode ini.',
                };
              }),
              { value: 'skip', label: 'Lewati perubahan sumber' },
            ]} />
        );
      }) : null}
    </>
  );
}

function ScopeSaveNotice({ status, pending, offline, onCheck }: {
  status: ReturnType<typeof useScopeSave>['status'];
  pending: boolean;
  offline: boolean;
  onCheck: () => void;
}) {
  const check = <HDButton variant="text" onPress={onCheck} disabledReason={offline ? 'Sambungkan perangkat untuk memeriksa cakupan.' : null}>Periksa status simpan</HDButton>;
  const error = status && 'error' in status ? status.error : null;
  const title = status?.kind === 'unsent' ? 'Perubahan belum dikirim' :
    status?.kind === 'refused' ? 'Perubahan ditolak layanan' :
    status?.kind === 'stale' ? 'Pratinjau perlu diperbarui' :
    status?.kind === 'check-failed' ? 'Cakupan belum dapat diperiksa' : null;
  return (
    <>
      {title && error ? <HDNotice tone="error" title={title} live><Evidence error={error} /></HDNotice> : null}
      {pending && status?.kind !== 'saving' && status?.kind !== 'checking' ? (
        <HDNotice tone="attention" title="Hasil penyimpanan belum diketahui" live action={check}>
          <HDText>Periksa cakupan terkonfirmasi. Jika ingin menyimpan lagi, buat pratinjau baru dan konfirmasi secara terpisah.</HDText>
          {status?.kind === 'uncertain' ? <Evidence error={status.error} /> : null}
        </HDNotice>
      ) : null}
      {(status?.kind === 'observed' || status?.kind === 'uncertain') && !pending ? (
        <HDNotice tone="info" title="Cakupan terkini telah diperiksa" live>
          Ringkasan memakai hasil pembacaan cakupan terkonfirmasi dari layanan.
        </HDNotice>
      ) : null}
      {status?.kind === 'acknowledged' ? <HDNotice tone="success" title="Cakupan tersimpan di layanan" live /> : null}
      {status?.kind === 'refresh-failed' ? (
        <HDNotice tone="attention" title="Cakupan tersimpan · ringkasan belum dapat diperbarui" live action={check}>
          <Evidence error={status.error} />
        </HDNotice>
      ) : null}
      {status?.kind === 'local-failed' ? (
        <HDNotice tone="attention" title="Cakupan tersimpan · penyimpanan perangkat belum diperbarui" live action={check}>
          <HDText>Periksa cakupan kembali saat terhubung untuk memuat ringkasan terbaru.</HDText>
          {status.refreshError ? <Evidence error={status.refreshError} /> : null}
        </HDNotice>
      ) : null}
    </>
  );
}

const styles = StyleSheet.create({
  group: { gap: tokens.space.stackTight },
});
