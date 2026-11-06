'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import type { Me } from '@/api/client';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { Disclosure } from '@/components/tr/Disclosure';
import { EmptyState } from '@/components/tr/EmptyState';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { PartnershipConsent } from '@/components/tr/PartnershipConsent';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { SummaryList } from '@/components/tr/SummaryList';
import { TextArea } from '@/components/tr/TextArea';
import { VersionConflict } from '@/components/tr/VersionConflict';
import { ContextBar } from '@/features/ContextBar';
import { money } from '@/features/money';
import { readPersona } from '@/features/persona';
import { FIELDS, publicRows, toggleField, valuesOf, type Partnership, type PublicField, type Values } from '@/features/relationships/model';
import { RelationshipError } from '@/features/relationships/RelationshipError';
import { CeilingFields, RelationshipFields } from '@/features/relationships/RelationshipFields';
import { useRelationshipAction } from '@/features/relationships/useRelationshipAction';
import { PROVENANCE } from '@/views/parts';

export function RelationshipUnavailable({ me, message, pitchId }: { me: Me; message?: string; pitchId?: string }) {
  return (
    <Screen persona={readPersona(me.account.persona) ?? 'inovator'} title="Kerja Sama" provenance={PROVENANCE} context={<ContextBar me={me} />}>
      <EmptyState icon="lock" title="Ringkasan Kerja Sama belum tersedia"
        action={<Link className="tr-link" href={pitchId ? `/pitches/${pitchId}` : '/pitches'}>Kembali ke pitching</Link>}>
        {message ?? 'Ringkasan hanya dapat dibuka oleh pihak yang terlibat. Periksa konteks yang aktif.'}
      </EmptyState>
    </Screen>
  );
}

type DialogState =
  | { kind: 'correct'; version: number; values: Values; ceiling: PublicField[]; note: string }
  | { kind: 'restrict'; field: PublicField }
  | { kind: 'decline'; version: number }
  | { kind: 'review'; note: string };

export function PartnershipView({ me, initial }: { me: Me; initial: Partnership }) {
  const router = useRouter();
  const [update, setUpdate] = useState<{ source: Partnership; result: Partnership } | null>(null);
  const record = update?.source === initial ? update.result : initial;
  const { current } = record;
  const [choices, setChoices] = useState<{ checksum: string; fields: PublicField[] }>({ checksum: current.checksum, fields: [] });
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [notice, setNotice] = useState('');
  const [invalid, setInvalid] = useState(0);
  const action = useRelationshipAction();
  const selected = choices.checksum === current.checksum ? choices.fields : [];
  const allows = (name: string) => record.allowed_actions.includes(name);
  const values = valuesOf(current.values);
  const actor = record.parties.find((party) => party.party_id === me.active_party_id)?.name;
  const preview = publicRows(record.effective.values);

  async function mutate(path: string, payload: object, message: string) {
    const result = await action.run(`/api/v1/partnerships/${record.id}/${path}`, {
      ...payload, acting_party_id: me.active_party_id,
    });
    if (result) {
      setUpdate({ source: initial, result });
      setNotice(message);
      setDialog(null);
    }
  }

  function open(next: DialogState) {
    action.clearError();
    setInvalid(0);
    setDialog(next);
  }

  function execute() {
    if (dialog?.kind === 'correct') {
      if (!dialog.values.name.trim() || !dialog.values.scope.trim() || !dialog.values.start_date || !dialog.ceiling.length) {
        setInvalid((count) => count + 1);
        return;
      }
      setInvalid(0);
      void mutate('corrections', {
        version: dialog.version, values: dialog.values, ceiling: dialog.ceiling, note: dialog.note,
      }, 'Versi baru dibuat. Konfirmasi lama tidak berlaku lagi untuk versi ini.');
    } else if (dialog?.kind === 'restrict') {
      void mutate('restrictions', { field: dialog.field }, 'Data disembunyikan dari tampilan publik.');
    } else if (dialog?.kind === 'decline') {
      void mutate('decline', { version: dialog.version }, 'Ringkasan ditolak.');
    } else if (dialog?.kind === 'review') {
      void mutate('request-review', { reason: dialog.note }, 'Klaim disembunyikan selama ditinjau.');
    }
  }

  const dialogTitle = dialog?.kind === 'correct' ? 'Minta perubahan' :
    dialog?.kind === 'restrict' ? 'Sembunyikan data publik' :
    dialog?.kind === 'decline' ? 'Tolak ringkasan' : 'Minta tinjauan klaim publik';

  function failure(prefix: string) {
    if (!action.error) return null;
    return action.error.failure.code === 'STALE_VERSION' ? (
      <VersionConflict what={action.error.failure.message} currentVersion={action.error.failure.currentVersion?.toString()}
        onRefresh={() => { action.clearError(); router.refresh(); }} />
    ) : <RelationshipError error={action.error} prefix={prefix} />;
  }

  return (
    <Screen persona={readPersona(me.account.persona) ?? 'inovator'} title="Kerja Sama" provenance={PROVENANCE}
      subtitle={actor ? `Bertindak sebagai ${actor}` : undefined}
      context={<ContextBar me={me} />} back={<Link className="tr-link" href={`/pitches/${record.pitch_id}`}>Kembali ke ruang pitching</Link>}>
      {notice ? <Status label={notice} tone="success" live /> : null}
      {record.contested ? <Status label="Klaim sedang ditinjau" tone="warning">Riwayat tetap dapat dibaca kedua pihak.</Status> : null}
      {current.number > 1 ? <p>Konfirmasi lama tidak berlaku lagi untuk versi ini.</p> : null}
      {!dialog ? failure('ringkasan') : null}
      <section className="tr-panel tr-stack" aria-label="Isi ringkasan privat">
        <h2 className="tr-sys-type-heading-sm">{values.name || 'Isi ringkasan'}</h2>
        <SummaryList rows={[
          { id: 'cakupan', label: 'Cakupan', value: values.scope },
          { id: 'mulai', label: 'Tanggal mulai', value: values.start_date },
          ...(values.amount ? [{ id: 'dana', label: 'Jumlah dana', value: money(values.currency, values.amount) }] : []),
          ...(record.type === 'EQUITY' && values.percent ? [{ id: 'saham', label: 'Persentase saham', value: `${values.percent}% · ${values.percent_date ?? ''}` }] : []),
          ...(values.evidence ? [{ id: 'bukti', label: 'Catatan bukti (privat)', value: values.evidence }] : []),
        ]} />
        {current.note ? <p>{current.note}</p> : null}
      </section>
      <div className="tr-panel tr-stack">
        <PartnershipConsent record={record} actingPartyId={me.active_party_id} selected={selected}
          onToggle={(field, checked) => setChoices({ checksum: current.checksum, fields: toggleField(selected, field, checked) })}
          onRestrict={allows('restrict') ? (field) => open({ kind: 'restrict', field }) : undefined} />
        <div className="tr-row">
          {allows('confirm') ? <Button intent="primary" busy={action.busy} onClick={() => void mutate('confirmations', {
            version: current.number, checksum: current.checksum, subset: selected,
          }, `Konfirmasi versi ${current.number} disimpan.`)}>Konfirmasi versi {current.number}</Button> : null}
          {allows('correct') ? <Button onClick={() => open({ kind: 'correct', version: current.number, values,
            ceiling: FIELDS.filter((field) => current.ceiling.includes(field)), note: '' })}>Minta perubahan</Button> : null}
          {allows('decline') ? <Button onClick={() => open({ kind: 'decline', version: current.number })}>Tolak ringkasan</Button> : null}
        </div>
      </div>
      <section className="tr-panel tr-stack" aria-labelledby="publik-sekarang">
        <h2 id="publik-sekarang" className="tr-sys-type-heading-sm">Tampilan publik saat ini</h2>
        {preview.length ? <SummaryList rows={preview} /> : <p>Belum ada data Kerja Sama yang tampil di publik.</p>}
        {record.effective.version !== null && record.effective.version !== current.number && allows('restrict') ? (
          <ul className="tr-stack">
            {preview.map(({ id, label }) => <li key={id}><Button onClick={() => open({ kind: 'restrict', field: id })}>Sembunyikan {label.toLowerCase()}</Button></li>)}
          </ul>
        ) : null}
        <div className="tr-row">
          <Link className="tr-link" href={`/profiles/${me.active_party_id}`}>Lihat profil publik</Link>
          {allows('request_review') && !record.contested ? <Button onClick={() => open({ kind: 'review', note: '' })}>Minta tinjauan klaim publik</Button> : null}
        </div>
      </section>
      {record.versions.length > 1 ? <Disclosure label="Versi sebelumnya"><ul className="tr-stack">
        {record.versions.filter((version) => version.number !== current.number).map((version) => (
          <li key={version.number}><strong>Versi {version.number}</strong><p>{valuesOf(version.values).scope}</p></li>
        ))}
      </ul></Disclosure> : null}
      <Dialog open={Boolean(dialog)} title={dialogTitle} onClose={() => { if (!action.busy) setDialog(null); }}
        primary={{ label: dialog?.kind === 'correct' ? `Buat versi ${dialog.version + 1}` :
          dialog?.kind === 'restrict' ? 'Sembunyikan sekarang' : dialog?.kind === 'decline' ? 'Tolak ringkasan' : 'Kirim permintaan',
          onClick: execute, busy: action.busy }}>
        {dialog ? failure('ubah') : null}
        {dialog?.kind === 'correct' ? <>
          <p>Versi baru perlu dikonfirmasi ulang oleh kedua pihak.</p>
          {dialog.version !== current.number ? <Button onClick={() => setDialog({ ...dialog, version: current.number })}>Gunakan versi terbaru untuk perubahan ini</Button> : null}
          {invalid ? <ErrorSummary focusKey={invalid} errors={[
            ...(!dialog.values.name.trim() ? [{ fieldId: 'ubah-name', message: 'Isi nama Kerja Sama.' }] : []),
            ...(!dialog.values.scope.trim() ? [{ fieldId: 'ubah-scope', message: 'Isi cakupan.' }] : []),
            ...(!dialog.values.start_date ? [{ fieldId: 'ubah-start_date', message: 'Pilih tanggal mulai.' }] : []),
            ...(!dialog.ceiling.length ? [{ fieldId: 'ubah-ceiling', message: 'Pilih setidaknya satu batas data publik.' }] : []),
          ]} /> : null}
          <RelationshipFields kind={record.type} values={dialog.values} onChange={(next) => setDialog({ ...dialog, values: next })} prefix="ubah" />
          <CeilingFields id="ubah-ceiling" kind={record.type} fields={dialog.ceiling}
            onToggle={(field, checked) => setDialog({ ...dialog, ceiling: toggleField(dialog.ceiling, field, checked) })} />
          <TextArea id="ubah-note" label="Alasan perubahan" rows={2} limit={1000} value={dialog.note} onChange={(note) => setDialog({ ...dialog, note })} />
        </> : dialog?.kind === 'restrict' ? <p>Data langsung hilang dari tampilan publik. Salinan yang sudah diunduh tidak dapat ditarik.</p> :
          dialog?.kind === 'decline' ? <p>Ringkasan versi {dialog.version} akan ditandai ditolak.</p> :
            dialog?.kind === 'review' ? <TextArea id="ubah-reason" label="Alasan peninjauan" value={dialog.note} rows={3} limit={500} onChange={(note) => setDialog({ ...dialog, note })} /> : null}
      </Dialog>
    </Screen>
  );
}
