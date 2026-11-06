'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { Disclosure } from '@/components/tr/Disclosure';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { ScheduleSlotList } from '@/components/tr/ScheduleSlotList';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { VersionConflict } from '@/components/tr/VersionConflict';
import { acceptSlot, calendarHref, cancelMeeting, EXPIRED_REASON, proposeSlots, recordOutcome, type Meeting, type Proposal, type Schedule } from '@/features/scheduling/api';
import { clock, fromLocalInput, longDate, slotTime, toLocalInput, zoneLabel } from '@/features/scheduling/time';

type Props = { pitchId: string; approved: boolean; schedule: Schedule; actingPartyId: string; zone: string };

const OUTCOME: Record<string, string> = { COMPLETED: 'Pertemuan selesai', NO_SHOW: 'Tidak terlaksana' };

/** S14 inside the room: propose in the reader's zone, choose, confirm explicitly, replace, record the outcome (UX-13, UX-14). */
export function SchedulePanel({ pitchId, approved, schedule, actingPartyId, zone }: Props) {
  const router = useRouter();
  const open = schedule.proposals.find((proposal) => proposal.state === 'OPEN') ?? null;
  const latest = schedule.proposals[0] ?? null;
  const active = schedule.meetings.find((meeting) => meeting.state === 'CONFIRMED') ?? null;
  const completed = schedule.meetings.find((meeting) => meeting.state === 'COMPLETED') ?? null;
  const [form, setForm] = useState<{ slots: string[]; replaces: string | null } | null>(null);

  if (!approved) {
    return (
      <div className="tr-stack">
        <h2 className="tr-sys-type-heading-sm">Jadwal</h2>
        <p className="tr-muted">Jadwal tersedia setelah pitching disetujui untuk diskusi.</p>
      </div>
    );
  }

  function proposeFrom(proposal: Proposal | null, replaces: string | null, skip: string[] = []) {
    const slots = (proposal?.slots ?? []).filter((slot) => !skip.includes(slot.id)).map((slot) => toLocalInput(slot.starts_at, zone));
    setForm({ slots: slots.length >= 2 ? slots : [...slots, '', ''].slice(0, Math.max(2, slots.length)), replaces });
  }

  return (
    <div className="tr-stack">
      <h2 className="tr-sys-type-heading-sm">Jadwal</h2>
      <p className="tr-muted tr-sys-type-support">Ketersediaan di kalender luar tidak diketahui; TemuRiset hanya memeriksa jadwal yang tercatat di sini.</p>
      {!schedule.can_schedule ? <Status tone="neutral" label="Akun Anda hanya dapat melihat jadwal ini" /> : null}
      {completed ? (
        <section className="tr-panel tr-stack" aria-labelledby="pertemuan-selesai">
          <h3 id="pertemuan-selesai" className="tr-sys-type-label">Pertemuan selesai dicatat kedua pihak</h3>
          <p>{`${longDate(completed.starts_at, zone)}, ${slotTime(completed.starts_at, completed.ends_at, zone)}`}</p>
        </section>
      ) : null}
      {active ? (
        <MeetingPanel
          meeting={active}
          zone={zone}
          actingPartyId={actingPartyId}
          canSchedule={schedule.can_schedule}
          onReplace={() => proposeFrom(null, active.id)}
          replacing={Boolean(open?.replaces_meeting_id)}
        />
      ) : null}
      {open ? (
        <OpenProposal
          key={`${open.id}-${open.version}`}
          proposal={open}
          zone={zone}
          actingPartyId={actingPartyId}
          canSchedule={schedule.can_schedule}
          onPropose={(skip) => proposeFrom(open, open.replaces_meeting_id, skip)}
        />
      ) : latest && latest.state === 'EXPIRED' && !active ? (
        <Status tone="neutral" label="Usulan waktu sudah kedaluwarsa">
          <p>{`${EXPIRED_REASON[latest.expired_reason ?? 'AGE']} Pitching tetap disetujui untuk diskusi.`}</p>
        </Status>
      ) : null}
      {schedule.can_schedule && !completed && (form || (!open && !active)) ? (
        <ProposeForm
          key={form ? form.slots.join('|') + (form.replaces ?? '') : 'new'}
          pitchId={pitchId}
          zone={zone}
          actingPartyId={actingPartyId}
          initial={form?.slots ?? ['', '', '']}
          replaces={form?.replaces ?? null}
          onDone={() => {
            setForm(null);
            router.refresh();
          }}
          onCancel={form ? () => setForm(null) : undefined}
        />
      ) : null}
    </div>
  );
}

function OpenProposal({ proposal, zone, actingPartyId, canSchedule, onPropose }: { proposal: Proposal; zone: string; actingPartyId: string; canSchedule: boolean; onPropose: (skip: string[]) => void }) {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  async function confirm() {
    if (!selected) return;
    setBusy(true);
    setFailure(null);
    try {
      await acceptSlot(proposal, selected, actingPartyId, key.current);
      router.refresh();
    } catch (error) {
      const failed = ApiError.from(error);
      key.current = newIdempotencyKey();
      if (failed.code === 'BOOKING_CONFLICT') {
        setConflicts((current) => [...current, failed.field('slot_id') ?? selected]);
        setSelected(null);
      }
      setFailure(failed);
    } finally {
      setBusy(false);
    }
  }

  const error =
    failure?.code === 'STALE_VERSION' ? (
      <VersionConflict what="Usulan ini baru saja berubah. Muat usulan terbaru." onRefresh={() => router.refresh()} refreshLabel="Muat versi terbaru" />
    ) : failure ? (
      <Status tone="danger" icon="alert" label={failure.code === 'BOOKING_CONFLICT' ? 'Waktu ini bentrok' : 'Belum dikonfirmasi'} live="alert">
        <p>{failure.field('reason') ?? failure.message}</p>
        {failure.code === 'BOOKING_CONFLICT' ? <p>Agenda dan waktu lain tetap ada. Pilih waktu lain atau usulkan waktu baru.</p> : null}
      </Status>
    ) : null;

  return (
    <section className="tr-panel tr-stack" aria-labelledby="usulan-terbuka">
      <h3 id="usulan-terbuka" className="tr-sys-type-label">
        {proposal.replaces_meeting_id ? 'Usulan jadwal pengganti' : proposal.mine ? 'Usulan Anda, menunggu pihak lain memilih' : `Usulan dari ${proposal.proposed_by_name}`}
      </h3>
      <p className="tr-muted tr-sys-type-support">{`Berlaku sampai ${longDate(proposal.expires_at, zone)}, ${clock(proposal.expires_at, zone)} ${zoneLabel(zone)}.`}</p>
      {proposal.link ? (
        <p>
          <span className="tr-muted">Tautan: </span>
          {proposal.link}
        </p>
      ) : null}
      <ScheduleSlotList
        slots={proposal.slots.map((slot) => ({ id: slot.id, start: slot.starts_at, end: slot.ends_at, minutes: proposal.minutes, conflict: conflicts.includes(slot.id) }))}
        zone={zone}
        otherZone={proposal.mine ? undefined : proposal.time_zone}
        selectedId={selected}
        onSelect={setSelected}
        state="open"
        canConfirm={canSchedule && !proposal.mine}
        onConfirm={() => void confirm()}
        onPropose={() => onPropose(conflicts)}
        busy={busy}
        agenda={proposal.agenda}
        error={error}
      />
      {proposal.mine && canSchedule ? <Button onClick={() => onPropose([])}>Ubah usulan</Button> : null}
    </section>
  );
}

function MeetingPanel({ meeting, zone, actingPartyId, canSchedule, onReplace, replacing }: { meeting: Meeting; zone: string; actingPartyId: string; canSchedule: boolean; onReplace: () => void; replacing: boolean }) {
  const router = useRouter();
  const [ics, setIcs] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());
  const mine = meeting.outcomes.find((outcome) => outcome.party_id === actingPartyId);

  useEffect(() => {
    let live = true;
    fetch(calendarHref(meeting), { cache: 'no-store' })
      .then((response) => (response.ok ? response.text() : null))
      .then((text) => live && setIcs(text))
      .catch(() => live && setIcs(null));
    return () => {
      live = false;
    };
  }, [meeting]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setFailure(null);
    try {
      await action();
      key.current = newIdempotencyKey();
      setCancelling(false);
      router.refresh();
    } catch (error) {
      key.current = newIdempotencyKey();
      setFailure(ApiError.from(error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="pertemuan">
      <h3 id="pertemuan" className="tr-sys-type-label">
        Pertemuan dikonfirmasi
      </h3>
      <p className="tr-sys-type-body-strong">{longDate(meeting.starts_at, zone)}</p>
      <p className="tr-num">{slotTime(meeting.starts_at, meeting.ends_at, zone)}</p>
      {meeting.time_zone !== zone ? <p className="tr-muted tr-sys-type-support">{`Pihak lain: ${slotTime(meeting.starts_at, meeting.ends_at, meeting.time_zone)}`}</p> : null}
      <p>
        <span className="tr-muted">Agenda: </span>
        {meeting.agenda}
      </p>
      {replacing ? <Status tone="neutral" label="Jadwal pengganti diusulkan; pertemuan ini tetap berlaku sampai penggantinya dikonfirmasi" /> : null}
      {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
      <p>
        <a className="tr-link" href={calendarHref(meeting)} download="pertemuan-temuriset.ics">
          Unduh ICS
        </a>
      </p>
      {ics ? (
        <Disclosure label="Lihat isi berkas ICS">
          <pre className="tr-sys-type-support">{ics}</pre>
        </Disclosure>
      ) : null}
      {meeting.started ? (
        <div className="tr-stack">
          <p className="tr-muted">Waktu yang berlalu tidak otomatis berarti pertemuan selesai. Catat hasilnya.</p>
          {meeting.outcomes.map((outcome) => (
            <p key={outcome.party_id}>{`${outcome.party_name}: ${OUTCOME[outcome.result]}`}</p>
          ))}
          {meeting.disagreement ? <Status tone="warning" icon="alert" label="Catatan kedua pihak berbeda" /> : null}
          {canSchedule ? (
            <div className="tr-row">
              <Button intent={mine ? 'secondary' : 'primary'} busy={busy} busyLabel="Menyimpan…" onClick={() => void run(() => recordOutcome(meeting, actingPartyId, 'COMPLETED', key.current))}>
                Pertemuan selesai
              </Button>
              <Button onClick={() => void run(() => recordOutcome(meeting, actingPartyId, 'NO_SHOW', key.current))}>Tidak terlaksana</Button>
            </div>
          ) : null}
        </div>
      ) : canSchedule && !replacing ? (
        <div className="tr-row">
          <Button onClick={onReplace}>Usulkan jadwal pengganti</Button>
          <Button intent="danger" id="cancel-meeting" onClick={() => setCancelling(true)}>
            Batalkan pertemuan
          </Button>
        </div>
      ) : null}
      <Dialog
        open={cancelling}
        onClose={() => setCancelling(false)}
        title="Batalkan pertemuan"
        returnFocusId="cancel-meeting"
        primary={{ label: 'Batalkan pertemuan', intent: 'danger', busy, busyLabel: 'Membatalkan…', onClick: () => void run(() => cancelMeeting(meeting, actingPartyId, key.current)) }}
        secondary={{ label: 'Kembali', onClick: () => setCancelling(false) }}>
        <p>Waktu kedua pihak dibebaskan. Pitching tetap disetujui untuk diskusi.</p>
      </Dialog>
    </section>
  );
}

function ProposeForm({ pitchId, zone, actingPartyId, initial, replaces, onDone, onCancel }: { pitchId: string; zone: string; actingPartyId: string; initial: string[]; replaces: string | null; onDone: () => void; onCancel?: () => void }) {
  const [slots, setSlots] = useState<string[]>(initial.length >= 2 ? initial : [...initial, ''].slice(0, 2));
  const [minutes, setMinutes] = useState('60');
  const [agenda, setAgenda] = useState('');
  const [link, setLink] = useState('');
  const [errors, setErrors] = useState<{ fieldId: string; message: string }[]>([]);
  const [failure, setFailure] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  async function send() {
    const filled = slots.filter(Boolean);
    const found = [
      ...(filled.length < 2 ? [{ fieldId: 'slot-0', message: 'Usulkan setidaknya 2 waktu.' }] : []),
      ...(agenda.trim() ? [] : [{ fieldId: 'agenda', message: 'Tuliskan agenda singkat.' }]),
      ...(link && !link.startsWith('https://') ? [{ fieldId: 'link', message: 'Tautan pertemuan harus memakai https.' }] : []),
    ];
    setErrors(found);
    setFailure(null);
    if (found.length) {
      setAttempt((value) => value + 1);
      return;
    }
    setBusy(true);
    try {
      await proposeSlots(
        pitchId,
        { acting_party_id: actingPartyId, slots: filled.map((value) => fromLocalInput(value, zone)), minutes: minutes === '30' ? 30 : 60, time_zone: zone, agenda: agenda.trim(), link: link.trim() || null, replaces_meeting_id: replaces },
        key.current,
      );
      key.current = newIdempotencyKey();
      onDone();
    } catch (error) {
      const failed = ApiError.from(error);
      if (!failed.recovery.retryable) key.current = newIdempotencyKey();
      setFailure(failed.details[0]?.msg ?? failed.message);
      setAttempt((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="usulkan-waktu">
      <h3 id="usulkan-waktu" className="tr-sys-type-label">
        {replaces ? 'Usulkan jadwal pengganti' : 'Usulkan waktu pertemuan'}
      </h3>
      <p className="tr-muted tr-sys-type-support">{`Isi 2 sampai 5 waktu dalam ${zoneLabel(zone)}. Pihak lain melihatnya dalam zona waktu mereka.`}</p>
      {errors.length ? <ErrorSummary errors={errors} focusKey={attempt} id="propose-errors" /> : null}
      {failure ? (
        <Status tone="danger" icon="alert" label="Usulan belum terkirim" live="alert">
          <p>{failure}</p>
        </Status>
      ) : null}
      {slots.map((value, index) => (
        <TextField key={index} label={`Waktu ${index + 1}`} type="datetime-local" value={value} onChange={(next) => setSlots((current) => current.map((item, at) => (at === index ? next : item)))} id={`slot-${index}`} />
      ))}
      {slots.length < 5 ? <Button onClick={() => setSlots((current) => [...current, ''])}>Tambah waktu</Button> : null}
      <Select label="Durasi" value={minutes} onChange={setMinutes} options={[{ value: '30', label: '30 menit' }, { value: '60', label: '60 menit' }]} emptyLabel={null} id="minutes" />
      <TextArea label="Agenda" required rows={2} value={agenda} onChange={setAgenda} id="agenda" />
      <TextField label="Tautan pertemuan" hint="Opsional, harus https." value={link} onChange={setLink} id="link" />
      <div className="tr-row">
        <Button intent="primary" busy={busy} busyLabel="Mengirim…" onClick={() => void send()}>
          {replaces ? 'Kirim usulan pengganti' : 'Kirim usulan waktu'}
        </Button>
        {onCancel ? <Button onClick={onCancel}>Batal</Button> : null}
      </div>
    </section>
  );
}
