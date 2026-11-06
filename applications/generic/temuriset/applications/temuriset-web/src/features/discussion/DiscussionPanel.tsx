'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';

import { newIdempotencyKey, send } from '@/api/client';
import { ApiError } from '@/api/errors';
import type { components } from '@/api/schema.generated';
import { Button } from '@/components/tr/Button';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { formatDateTime } from '@/features/organizations';

export type Message = components['schemas']['MessageResponse'];
export type Task = components['schemas']['TaskResponse'];

/** R1 polls; no realtime transport (spec 027). */
export const POLL_MS = 30_000;

type Party = { id: string; name: string };
type Props = { pitchId: string; open: boolean; messages: Message[]; tasks: Task[]; parties: Party[]; actingPartyId: string; zone: string };

/** The Diskusi tab: threaded messages with polling, and tasks with an owner and due date. A failed send keeps the text. */
export function DiscussionPanel({ pitchId, open, messages: initial, tasks, parties, actingPartyId, zone }: Props) {
  const [messages, setMessages] = useState<Message[]>(initial);
  const [draft, setDraft] = useState('');
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  const poll = useCallback(async () => {
    const last = messages[messages.length - 1]?.created_at;
    const query = last ? `?since=${encodeURIComponent(last)}` : '';
    try {
      const response = await fetch(`/api/v1/pitches/${pitchId}/messages${query}`, { cache: 'no-store' });
      if (!response.ok) return;
      const newer = (await response.json()) as Message[];
      if (newer.length) setMessages((current) => [...current, ...newer.filter((item) => !current.some((known) => known.id === item.id))]);
    } catch {
      // The next poll tries again; the thread on screen stays.
    }
  }, [messages, pitchId]);

  useEffect(() => {
    const timer = setInterval(() => void poll(), POLL_MS);
    return () => clearInterval(timer);
  }, [poll]);

  async function sendMessage() {
    if (!draft.trim()) {
      setFailure('Tulis pesan terlebih dahulu.');
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      const sent = await send<Message>('POST', `/api/v1/pitches/${pitchId}/messages`, { acting_party_id: actingPartyId, text: draft }, { idempotencyKey: key.current });
      key.current = newIdempotencyKey();
      setMessages((current) => [...current, sent]);
      setDraft('');
    } catch (error) {
      const failed = ApiError.from(error);
      if (!failed.recovery.retryable) key.current = newIdempotencyKey();
      setFailure(`${failed.message} Pesan Anda masih ada di kotak isian.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="tr-stack">
      <h2 className="tr-sys-type-heading-sm">Diskusi</h2>
      <section className="tr-stack" aria-labelledby="pesan">
        <h3 id="pesan" className="tr-sys-type-label">
          Pesan
        </h3>
        {messages.length ? (
          <ol className="tr-stack" aria-live="polite">
            {messages.map((message) => (
              <li key={message.id} className="tr-panel tr-stack">
                <p className="tr-muted tr-sys-type-support">{`${message.mine ? 'Anda' : message.author_name} · ${formatDateTime(message.created_at, zone)}`}</p>
                <p>{message.text}</p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="tr-muted">Belum ada pesan.</p>
        )}
        {open ? (
          <>
            {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
            <TextArea label="Pesan baru" rows={3} value={draft} onChange={setDraft} limit={4000} id="message" />
            <div className="tr-row">
              <Button intent="primary" busy={busy} busyLabel="Mengirim…" onClick={() => void sendMessage()}>
                Kirim pesan
              </Button>
            </div>
          </>
        ) : null}
      </section>
      <TaskList pitchId={pitchId} open={open} tasks={tasks} parties={parties} actingPartyId={actingPartyId} />
    </div>
  );
}

function TaskList({ pitchId, open, tasks, parties, actingPartyId }: { pitchId: string; open: boolean; tasks: Task[]; parties: Party[]; actingPartyId: string }) {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [owner, setOwner] = useState(parties[0]?.id ?? '');
  const [due, setDue] = useState('');
  const [reference, setReference] = useState('');
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  async function run(action: () => Promise<unknown>, reset = false) {
    setBusy(true);
    setFailure(null);
    try {
      await action();
      key.current = newIdempotencyKey();
      if (reset) {
        setTitle('');
        setDue('');
        setReference('');
      }
      router.refresh();
    } catch (error) {
      key.current = newIdempotencyKey();
      const failed = ApiError.from(error);
      setFailure(failed.details[0]?.msg ?? failed.message);
    } finally {
      setBusy(false);
    }
  }

  function add() {
    if (!title.trim()) {
      setFailure('Tuliskan tugasnya.');
      return;
    }
    void run(
      () =>
        send('POST', `/api/v1/pitches/${pitchId}/tasks`, { acting_party_id: actingPartyId, title, owner_party_id: owner, due_date: due || null, reference }, { idempotencyKey: key.current }),
      true,
    );
  }

  return (
    <section className="tr-stack" aria-labelledby="tugas">
      <h3 id="tugas" className="tr-sys-type-label">
        Tugas
      </h3>
      {tasks.length ? (
        <ul className="tr-stack">
          {tasks.map((task) => (
            <li key={task.id} className="tr-panel tr-stack">
              <p className="tr-sys-type-body-strong">{task.title}</p>
              <p className="tr-muted tr-sys-type-support">{[`Untuk ${task.owner_name}`, task.due_date ? `batas ${task.due_date}` : null, task.reference || null].filter(Boolean).join(' · ')}</p>
              <p className="tr-row">
                <Status tone={task.status === 'DONE' ? 'success' : 'neutral'} label={task.status === 'DONE' ? 'Selesai' : 'Terbuka'} />
                {open && task.status === 'OPEN' ? (
                  <Button onClick={() => void run(() => send('POST', `/api/v1/tasks/${task.id}/complete`, { acting_party_id: actingPartyId, expected_version: task.version }, { idempotencyKey: key.current }))}>
                    {`Tandai selesai: ${task.title}`}
                  </Button>
                ) : null}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="tr-muted">Belum ada tugas.</p>
      )}
      {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
      {open ? (
        <div className="tr-panel tr-stack">
          <TextField label="Tugas baru" value={title} onChange={setTitle} id="task-title" />
          <Select label="Penanggung jawab" value={owner} onChange={setOwner} options={parties.map((party) => ({ value: party.id, label: party.name }))} emptyLabel={null} id="task-owner" />
          <TextField label="Batas waktu" type="date" value={due} onChange={setDue} hint="Boleh dikosongkan." id="task-due" />
          <TextField label="Terkait" value={reference} onChange={setReference} hint="Misalnya butir revisi atau bukti yang kurang." id="task-reference" />
          <div className="tr-row">
            <Button busy={busy} busyLabel="Menyimpan…" onClick={add}>
              Tambah tugas
            </Button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
