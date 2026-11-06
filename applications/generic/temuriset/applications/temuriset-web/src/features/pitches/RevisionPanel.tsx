'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { RevisionItem, type RevisionValue } from '@/components/tr/RevisionItem';
import { SaveState, type SaveStatus } from '@/components/tr/SaveState';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { TextField } from '@/components/tr/TextField';
import { VersionConflict } from '@/components/tr/VersionConflict';
import type { Pitch } from '@/features/pitches/model';
import {
  ITEM_REVIEW,
  RESPONSE_LABEL,
  requestRevision,
  resubmit,
  reviewItem,
  saveAnswer,
  type ChosenFile,
  type ItemDraft,
  type RevisionItemView,
  type RevisionRound,
} from '@/features/pitches/workspace';

export type OwnFile = ChosenFile & { title: string };

type Draft = RevisionValue & { files: string[]; version: number | null; save: SaveStatus; message?: string };

const fileKey = (file: ChosenFile) => `${file.document_id}:${file.version}`;
/** Element ids start with a letter, so links and selectors to them stay valid. */
const fieldOf = (itemId: string) => `item-${itemId}`;
const fileId = (file: ChosenFile) => `${file.document_id}-v${file.version}`;

function fromKey(key: string): ChosenFile {
  const [document_id, version] = key.split(':');
  return { document_id, version: Number(version) };
}

function drafts(round: RevisionRound | undefined): Record<string, Draft> {
  return Object.fromEntries(
    (round?.items ?? []).map((item) => [
      item.id,
      item.answer
        ? { response: item.answer.response, text: item.answer.text, files: item.answer.files.map(fileKey), version: item.answer.version, save: 'saved' as SaveStatus }
        : { files: [], version: null, save: 'local' as SaveStatus },
    ]),
  );
}

type Props = { pitch: Pitch; actingPartyId: string; files: OwnFile[] };

/** The Revisi tab: rounds stay visible; the requester answers the open one honestly, the recipient reviews each answer. */
export function RevisionPanel({ pitch, actingPartyId, files }: Props) {
  const allowed = pitch.allowed_actions;
  const open = pitch.rounds.find((round) => round.open);
  return (
    <div className="tr-stack">
      <h2 className="tr-sys-type-heading-sm">Revisi</h2>
      {allowed.includes('request_revision') ? <RequestForm pitch={pitch} actingPartyId={actingPartyId} /> : null}
      {open && allowed.includes('answer') ? <AnswerRound pitch={pitch} round={open} actingPartyId={actingPartyId} files={files} /> : null}
      {pitch.rounds
        .filter((round) => !(round.open && allowed.includes('answer')))
        .map((round) => (
          <PastRound key={round.number} pitch={pitch} round={round} actingPartyId={actingPartyId} canReview={allowed.includes('review_items')} />
        ))}
      {!pitch.rounds.length && !allowed.includes('request_revision') ? <p className="tr-muted">Belum ada permintaan revisi.</p> : null}
    </div>
  );
}

function AnswerRound({ pitch, round, actingPartyId, files }: { pitch: Pitch; round: RevisionRound; actingPartyId: string; files: OwnFile[] }) {
  const router = useRouter();
  const [values, setValues] = useState<Record<string, Draft>>(() => drafts(round));
  const [shared, setShared] = useState<string[]>([]);
  const [missing, setMissing] = useState<{ fieldId: string; message: string }[]>([]);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  function change(itemId: string, next: Partial<Draft>) {
    setValues((current) => ({ ...current, [itemId]: { ...current[itemId], ...next, save: 'local' } }));
  }

  async function save(item: RevisionItemView) {
    const draft = values[item.id];
    if (!draft.response) {
      setValues((current) => ({ ...current, [item.id]: { ...draft, save: 'failed', message: 'Pilih tanggapan terlebih dahulu.' } }));
      return;
    }
    setValues((current) => ({ ...current, [item.id]: { ...draft, save: 'saving', message: undefined } }));
    try {
      const saved = await saveAnswer(pitch.id, item.id, {
        acting_party_id: actingPartyId,
        expected_version: draft.version,
        response: draft.response,
        text: draft.text ?? '',
        files: draft.files.map(fromKey),
      });
      setValues((current) => ({ ...current, [item.id]: { ...current[item.id], version: saved.version, save: 'saved', message: undefined } }));
    } catch (error) {
      const failed = ApiError.from(error);
      // A failed attachment or a conflict keeps every answer on the page (UX-11).
      const save: SaveStatus = failed.code === 'STALE_VERSION' ? 'conflict' : 'failed';
      const message = failed.details[0]?.msg ?? failed.message;
      setValues((current) => ({ ...current, [item.id]: { ...current[item.id], save, message } }));
    }
  }

  async function send() {
    const unanswered = round.items.filter((item) => item.required && values[item.id].save !== 'saved');
    if (unanswered.length) {
      setMissing(unanswered.map((item) => ({ fieldId: `${fieldOf(item.id)}-response-CAN`, message: `Simpan jawaban untuk “${item.question}”.` })));
      setAttempt((value) => value + 1);
      return;
    }
    setMissing([]);
    setBusy(true);
    setFailure(null);
    try {
      await resubmit(pitch, actingPartyId, shared.map(fromKey), key.current);
      key.current = newIdempotencyKey();
      router.refresh();
    } catch (error) {
      const failed = ApiError.from(error);
      if (!failed.recovery.retryable) key.current = newIdempotencyKey();
      const items = failed.fields.items;
      if (failed.code === 'REQUIRED_ANSWERS_MISSING' && Array.isArray(items)) {
        setMissing(round.items.filter((item) => items.includes(item.id)).map((item) => ({ fieldId: `${fieldOf(item.id)}-response-CAN`, message: `Jawab “${item.question}”.` })));
      } else {
        setFailure(failed);
      }
      setAttempt((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-stack" aria-labelledby={`putaran-${round.number}`}>
      <h3 id={`putaran-${round.number}`} className="tr-sys-type-label">{`Putaran ${round.number} · menunggu jawaban Anda`}</h3>
      {missing.length ? <ErrorSummary errors={missing} focusKey={attempt} title="Jawaban wajib belum tersimpan" id="revision-errors" /> : null}
      {round.items.map((item) => {
        const draft = values[item.id];
        return (
          <div key={item.id} className="tr-stack">
            <RevisionItem
              id={fieldOf(item.id)}
              round={round.number}
              index={item.position}
              question={item.question}
              reason={item.reason}
              required={item.required}
              due={item.due_date}
              value={draft}
              onChange={(next) => change(item.id, next)}
              attachments={
                files.length ? (
                  <CheckboxGroup legend="Lampiran" hint="Berkas dibagikan kepada penerima saat Anda mengirim ulang.">
                    {files.map((file) => (
                      <Checkbox
                        key={fileKey(file)}
                        id={`${fieldOf(item.id)}-file-${fileId(file)}`}
                        label={`${file.title}, versi ${file.version}`}
                        checked={draft.files.includes(fileKey(file))}
                        onChange={(on) => change(item.id, { files: on ? [...draft.files, fileKey(file)] : draft.files.filter((key) => key !== fileKey(file)) })}
                      />
                    ))}
                  </CheckboxGroup>
                ) : null
              }
            />
            {draft.message ? <p className="tr-sys-type-support">{draft.message}</p> : null}
            {draft.save === 'conflict' ? (
              <VersionConflict what="Jawaban ini sudah diubah di tempat lain. Jawaban Anda tetap ada di halaman ini." onRefresh={() => router.refresh()} refreshLabel="Muat versi terbaru" />
            ) : null}
            <div className="tr-row">
              <Button busy={draft.save === 'saving'} busyLabel="Menyimpan…" onClick={() => void save(item)}>
                {`Simpan jawaban ${item.position}`}
              </Button>
              <SaveState state={draft.save} onRetry={() => void save(item)} />
            </div>
          </div>
        );
      })}
      <section className="tr-panel tr-stack" aria-labelledby="kirim-ulang">
        <h3 id="kirim-ulang" className="tr-sys-type-label">Kirim ulang</h3>
        <p>{`Kiriman ${pitch.submissions.length + 1} membekukan kebutuhan dan inovasi seperti sekarang. Kiriman dan jawaban sebelumnya tetap tersimpan.`}</p>
        {files.length ? (
          <CheckboxGroup legend="Berkas untuk kiriman ini" hint="Pilih versi berkas yang ingin Anda bagikan. Lampiran jawaban ikut dibagikan.">
            {files.map((file) => (
              <Checkbox
                key={fileKey(file)}
                id={`share-${fileId(file)}`}
                label={`${file.title}, versi ${file.version}`}
                checked={shared.includes(fileKey(file))}
                onChange={(on) => setShared((current) => (on ? [...current, fileKey(file)] : current.filter((key) => key !== fileKey(file))))}
              />
            ))}
          </CheckboxGroup>
        ) : null}
        {failure?.code === 'STALE_VERSION' ? (
          <VersionConflict what="Pitching ini baru saja berubah. Jawaban Anda tetap ada." onRefresh={() => router.refresh()} refreshLabel="Muat versi terbaru" />
        ) : failure ? (
          <Status tone="danger" icon="alert" label="Belum terkirim ulang" live="alert">
            <p>{failure.message}</p>
            {failure.requestId ? <p className="tr-sys-type-support">{`ID referensi: ${failure.requestId}`}</p> : null}
          </Status>
        ) : null}
        <Button intent="primary" busy={busy} busyLabel="Mengirim ulang…" onClick={() => void send()}>
          {`Kirim ulang kepada ${pitch.recipient_name}`}
        </Button>
      </section>
    </section>
  );
}

function PastRound({ pitch, round, actingPartyId, canReview }: { pitch: Pitch; round: RevisionRound; actingPartyId: string; canReview: boolean }) {
  const router = useRouter();
  const [failure, setFailure] = useState<string | null>(null);
  const hidden = round.open;
  async function mark(item: RevisionItemView, result: 'ACCEPTED' | 'NEEDS_DETAIL') {
    setFailure(null);
    try {
      await reviewItem(pitch.id, item, actingPartyId, result);
      router.refresh();
    } catch (error) {
      setFailure(ApiError.from(error).message);
    }
  }
  return (
    <section className="tr-stack" aria-labelledby={`putaran-${round.number}`}>
      <h3 id={`putaran-${round.number}`} className="tr-sys-type-label">{`Putaran ${round.number} · untuk kiriman ${round.submission_number}`}</h3>
      {hidden ? <p className="tr-muted">Jawaban terlihat setelah pengirim mengirim ulang.</p> : null}
      {failure ? <Status tone="danger" icon="alert" label={failure} live="alert" /> : null}
      {round.items.map((item) => (
        <article key={item.id} className="tr-revision">
          <div className="tr-req__head">
            <h4 className="tr-sys-type-label">{`Pertanyaan ${item.position} · ${item.category}`}</h4>
            <Status tone={item.required ? 'action' : 'neutral'} icon={null} label={item.required ? 'Wajib dijawab' : 'Opsional'} />
          </div>
          <p className="tr-sys-type-body-strong">{item.question}</p>
          <p>
            <span className="tr-muted">Alasan: </span>
            {item.reason}
          </p>
          {item.answer ? (
            <>
              <p>
                <Status tone="neutral" icon={null} label={RESPONSE_LABEL[item.answer.response]} />
              </p>
              {item.answer.text ? <p>{item.answer.text}</p> : null}
              {item.answer.files.length ? <p className="tr-sys-type-support">{`Lampiran: ${item.answer.files.map((file) => `${file.title}, versi ${file.version}`).join('; ')}`}</p> : null}
            </>
          ) : hidden ? null : (
            <p className="tr-muted">Tidak dijawab.</p>
          )}
          {item.review ? <Status tone="neutral" label={`Tinjauan: ${ITEM_REVIEW[item.review]}`} /> : null}
          {canReview && item.answer ? (
            <div className="tr-row">
              <Button onClick={() => void mark(item, 'ACCEPTED')}>{`Terima jawaban ${item.position}`}</Button>
              <Button onClick={() => void mark(item, 'NEEDS_DETAIL')}>{`Perlu detail ${item.position}`}</Button>
            </div>
          ) : null}
        </article>
      ))}
    </section>
  );
}

const EMPTY_ITEM: ItemDraft = { category: '', question: '', reason: '', required: true, due_date: null, expected_evidence: '' };

function RequestForm({ pitch, actingPartyId }: { pitch: Pitch; actingPartyId: string }) {
  const router = useRouter();
  const [items, setItems] = useState<ItemDraft[]>([{ ...EMPTY_ITEM }]);
  const [errors, setErrors] = useState<{ fieldId: string; message: string }[]>([]);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const key = useRef(newIdempotencyKey());

  function edit(index: number, next: Partial<ItemDraft>) {
    setItems((current) => current.map((item, at) => (at === index ? { ...item, ...next } : item)));
  }

  async function send() {
    const found = items.flatMap((item, index) => [
      ...(item.category.trim() ? [] : [{ fieldId: `item-${index}-category`, message: `Butir ${index + 1}: isi kategori.` }]),
      ...(item.question.trim() ? [] : [{ fieldId: `item-${index}-question`, message: `Butir ${index + 1}: tulis pertanyaan.` }]),
      ...(item.reason.trim() ? [] : [{ fieldId: `item-${index}-reason`, message: `Butir ${index + 1}: tulis alasan.` }]),
    ]);
    setErrors(found);
    setFailure(null);
    if (found.length) {
      setAttempt((value) => value + 1);
      return;
    }
    setBusy(true);
    try {
      await requestRevision(pitch, actingPartyId, items.map((item) => ({ ...item, due_date: item.due_date || null })), key.current);
      key.current = newIdempotencyKey();
      router.refresh();
    } catch (error) {
      const failed = ApiError.from(error);
      if (!failed.recovery.retryable) key.current = newIdempotencyKey();
      setFailure(failed);
      setAttempt((value) => value + 1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="minta-revisi">
      <h3 id="minta-revisi" className="tr-sys-type-label">Minta revisi per butir</h3>
      <p className="tr-muted tr-sys-type-support">Setiap butir perlu kategori, pertanyaan, dan alasan. Jawaban jujur bahwa sesuatu belum dapat dipenuhi tetap sah.</p>
      {errors.length ? <ErrorSummary errors={errors} focusKey={attempt} id="request-errors" /> : null}
      {failure?.code === 'STALE_VERSION' ? (
        <VersionConflict what="Pitching ini baru saja berubah. Butir yang Anda tulis tetap ada." onRefresh={() => router.refresh()} refreshLabel="Muat versi terbaru" />
      ) : failure ? (
        <Status tone="danger" icon="alert" label="Permintaan belum terkirim" live="alert">
          <p>{failure.message}</p>
        </Status>
      ) : null}
      {items.map((item, index) => (
        <fieldset key={index} className="tr-fieldset tr-stack">
          <legend className="tr-field__label tr-sys-type-label">{`Butir ${index + 1}`}</legend>
          <TextField label="Kategori" required value={item.category} onChange={(category) => edit(index, { category })} id={`item-${index}-category`} hint="Misalnya Anggaran atau Fitur." />
          <TextArea label="Pertanyaan" required rows={2} value={item.question} onChange={(question) => edit(index, { question })} id={`item-${index}-question`} />
          <TextArea label="Alasan" required rows={2} value={item.reason} onChange={(reason) => edit(index, { reason })} id={`item-${index}-reason`} />
          <TextField label="Bukti yang diharapkan" value={item.expected_evidence} onChange={(expected_evidence) => edit(index, { expected_evidence })} id={`item-${index}-evidence`} />
          <TextField label="Batas waktu" type="date" value={item.due_date ?? ''} onChange={(due_date) => edit(index, { due_date })} id={`item-${index}-due`} hint="Boleh dikosongkan." />
          <Checkbox label="Wajib dijawab" checked={item.required} onChange={(required) => edit(index, { required })} id={`item-${index}-required`} />
        </fieldset>
      ))}
      <div className="tr-row">
        <Button onClick={() => setItems((current) => [...current, { ...EMPTY_ITEM, required: false }])}>
          Tambah butir
        </Button>
        <Button intent="primary" busy={busy} busyLabel="Mengirim…" onClick={() => void send()}>
          {`Kirim permintaan revisi kepada ${pitch.requester_name}`}
        </Button>
      </div>
    </section>
  );
}
