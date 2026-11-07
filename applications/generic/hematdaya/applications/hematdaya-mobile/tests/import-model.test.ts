// Recorded on 2026-11-07 from the merged hematdaya-api at 42aeebc (Alembic head 0009), by real demo sessions.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import type { ImportCommit, ImportPreview } from '@/api/client';
import { ApiError } from '@/api/errors';
import { EXAMPLES } from '@/features/imports/examples';
import {
  answerFor,
  answersChanged,
  askedAgain,
  assetOptionLabel,
  commitOutcome,
  counterNotes,
  landingPeriod,
  mappingLine,
  previewOutcome,
  questionControls,
  resultModel,
  streamRow,
  unanswered,
} from '@/features/imports/import-model';

import recorded from './fixtures/imports.json';

type Entry = { first: ImportPreview; answered: ImportPreview; commit: ImportCommit };
const Recorded = recorded as unknown as Record<string, Entry> & {
  same_name: { first: ImportPreview; second: ImportPreview };
  value_kind: ImportPreview;
  instant: ImportPreview;
  counter_append: ImportPreview;
  reimport: { answered: ImportPreview; commit: ImportCommit };
  streams_101: ImportPreview;
} & Record<string, unknown>;

type Envelope = { error: { code: string; message: string; recovery: ApiError['recovery']; request_id: string; details?: ApiError['details'] } };

function envelope(name: string, key?: string): ApiError {
  const value = Recorded[name] as unknown as Envelope & Record<string, Envelope>;
  const { error } = key ? value[key] : value;
  return new ApiError(error.code, error.message, error.recovery, error.request_id, error.details ?? []);
}

const failure = (code: string, retryable = false) => new ApiError(code, 'Pesan layanan.', { retryable }, 'ref_1');

describe('questionControls', () => {
  it.each([
    ['valid', ['timezone', 'scope']],
    ['one', ['timezone', 'interval_duration', 'scope']],
    ['power', ['power_meaning', 'scope']],
  ])('gives one control per question of %s', (name, kinds) => {
    expect(questionControls(Recorded[name].first).map((control) => control.kind)).toEqual(kinds);
  });

  it('names the timezone and the stream of an interval question', () => {
    const controls = questionControls(Recorded.one.first);

    expect(controls[0]).toMatchObject({ kind: 'timezone', timezone: 'Asia/Jakarta' });
    expect(controls[1]).toMatchObject({ kind: 'interval_duration', streamKey: 'pemanas air', assetName: 'Pemanas Air' });
  });

  it('offers the three value kinds', () => {
    const control = questionControls(Recorded.value_kind).find((item) => item.kind === 'value_kind');

    expect(control).toBeDefined();
  });

  it('offers only a new asset for another source', () => {
    expect(questionControls(Recorded.same_name.first)).toEqual([
      expect.objectContaining({ kind: 'other_source', assetName: 'Kulkas', streamKey: 'kulkas' }),
    ]);
  });

  it('offers every candidate of a shared name, and a new asset', () => {
    const [control] = questionControls(Recorded.same_name.second);
    const candidates = Recorded.same_name.second.questions[0].candidates ?? [];
    const lower = candidates.find((candidate) => candidate.name === 'kulkas')!;
    const upper = candidates.find((candidate) => candidate.name === 'Kulkas')!;

    expect(control.kind).toBe('asset_choice');
    expect(control.kind === 'asset_choice' && control.options).toEqual(
      expect.arrayContaining([
        { value: lower.id, label: `kulkas · Perangkat · ID …${lower.id.slice(-6)}` },
        { value: upper.id, label: `Kulkas · Perangkat · Dapur · Pendingin makanan · ID …${upper.id.slice(-6)}` },
        { value: 'new', label: 'Buat perangkat baru' },
      ]),
    );
    expect(assetOptionLabel(upper)).toBe(`Kulkas · Perangkat · Dapur · Pendingin makanan · ID …${upper.id.slice(-6)}`);
  });

  it('makes names that only the file can change unanswerable', () => {
    const preview = { ...Recorded.valid.first, questions: [{ kind: 'stream_assets' as const, message: 'Satu sumber memakai dua nama.' }] };

    expect(questionControls(preview)).toEqual([expect.objectContaining({ kind: 'unanswerable', message: 'Satu sumber memakai dua nama.' })]);
  });
});

describe('answerFor', () => {
  it('keys another source by the name the file writes, and by the stored name', () => {
    const [control] = questionControls(Recorded.same_name.first);

    expect(answerFor(Recorded.same_name.first, control, 'new', {}).asset_map).toEqual({ kulkas: 'new', Kulkas: 'new' });
  });

  it('keys an asset choice by the question name', () => {
    const [control] = questionControls(Recorded.same_name.second);

    expect(answerFor(Recorded.same_name.second, control, 'abc', {}).asset_map).toEqual({ Kulkas: 'abc' });
  });

  it('sets each other answer on its field, keeping the rest', () => {
    const [timezone, interval, scope] = questionControls(Recorded.one.first);
    let answers = answerFor(Recorded.one.first, timezone, true, {});
    answers = answerFor(Recorded.one.first, interval, 60, answers);
    answers = answerFor(Recorded.one.first, scope, 'disjoint', answers);

    expect(answers).toEqual({ timezone_confirmed: true, interval_minutes: { 'pemanas air': 60 }, scope: 'disjoint' });
  });
});

describe('unanswered', () => {
  it('lists each control with no answer, in the copy of the step', () => {
    expect(unanswered(Recorded.one.first, {}).map((item) => item.text)).toEqual([
      'Konfirmasi zona waktu Asia/Jakarta.',
      'Isi panjang interval untuk Pemanas Air.',
      'Pilih apakah beban perangkat terukur terpisah.',
    ]);
    expect(unanswered(Recorded.power.first, { scope: 'disjoint' }).map((item) => item.text)).toEqual(['Pilih arti kolom daya.']);
    expect(unanswered(Recorded.value_kind, { timezone_confirmed: true, scope: 'disjoint' }).map((item) => item.text)).toEqual([
      'Pilih jenis nilai.',
    ]);
    expect(unanswered(Recorded.same_name.first, {}).map((item) => item.text)).toEqual(['Pilih cara mengimpor Kulkas.']);
    expect(unanswered(Recorded.same_name.second, {}).map((item) => item.text)).toEqual(['Pilih perangkat untuk “Kulkas”.']);
  });

  it('lists nothing once every control has an answer', () => {
    expect(unanswered(Recorded.one.first, { timezone_confirmed: true, scope: 'disjoint', interval_minutes: { 'pemanas air': 60 } })).toEqual([]);
  });

  it('treats names only the file can change as unanswerable', () => {
    const preview = { ...Recorded.valid.first, questions: [{ kind: 'asset_streams' as const, message: 'Dua sumber memakai satu nama.' }] };

    expect(unanswered(preview, {})).toEqual([expect.objectContaining({ text: 'Dua sumber memakai satu nama.', unanswerable: true })]);
  });

  it('repeats the service message for a question asked again', () => {
    expect(askedAgain(Recorded.instant, { power_meaning: 'instantaneous', timezone_confirmed: true, scope: 'disjoint' }).map((item) => item.text)).toEqual([
      Recorded.instant.questions[0].message,
    ]);
    expect(askedAgain(Recorded.value_kind, { value_kind: 'counter' }).map((item) => item.text)).toEqual([
      `Jenis nilai ini tidak ada di berkas. Pilih jenis lain. ${Recorded.value_kind.questions[0].message}`,
    ]);
  });
});

describe('answersChanged', () => {
  it('ignores key order and compares values', () => {
    expect(answersChanged({ scope: 'disjoint', timezone_confirmed: true }, { timezone_confirmed: true, scope: 'disjoint' })).toBe(false);
    expect(answersChanged({ interval_minutes: { a: 1, b: 2 } }, { interval_minutes: { b: 2, a: 1 } })).toBe(false);
    expect(answersChanged({ scope: 'disjoint' }, { scope: 'unknown_overlap' })).toBe(true);
    expect(answersChanged({}, { scope: 'disjoint' })).toBe(true);
    expect(answersChanged(null, {})).toBe(true);
  });
});

describe('landingPeriod', () => {
  it('lands on the imported range', () => {
    expect(landingPeriod(Recorded.valid.commit.period ?? null)).toEqual({ preset: 'range', start_date: '2026-10-20', end_date: '2026-10-20', clamped: false });
  });

  it.each([
    ['366 inclusive days stay whole', '2025-10-21', '2026-10-21', '2025-10-21', false],
    ['367 days keep the last 366', '2025-10-20', '2026-10-21', '2025-10-21', true],
    ['a leap day is one of the days', '2023-03-01', '2024-03-01', '2023-03-02', true],
  ])('%s', (_name, start, end, landed, clamped) => {
    expect(landingPeriod({ start_date: start, end_date: end, timezone: 'Asia/Jakarta' })).toEqual({ preset: 'range', start_date: landed, end_date: end, clamped });
  });

  it('keeps the last 366 days of a long file, and has no landing without a period', () => {
    expect(landingPeriod((Recorded.long as unknown as Entry).commit.period ?? null)).toEqual({
      preset: 'range',
      start_date: '2025-10-20',
      end_date: '2026-10-20',
      clamped: true,
    });
    expect(landingPeriod(null)).toBeNull();
  });
});

describe('resultModel', () => {
  it('shows stored, visible rows with the landing', () => {
    const model = resultModel(Recorded.valid.commit, { found: false, timezone: 'Asia/Jakarta' });

    expect(model).toMatchObject({ title: 'Impor tersimpan', note: null, primary: 'landing', clockNotice: null, nothingNew: null, longRange: null });
    expect(model.rows).toEqual([
      { term: 'Baris disimpan', value: '12' },
      { term: 'Baris tidak valid dilewati', value: '0' },
      { term: 'Duplikat (dihitung sekali)', value: '0' },
      { term: 'Perangkat baru', value: 'Lampu Teras, Dispenser' },
      { term: 'Perangkat yang dipakai', value: 'Tidak ada' },
      { term: 'Periode data', value: '20 Oktober 2026' },
    ]);
    expect(model.confirmedAt).toMatch(/^Dikonfirmasi layanan 7 November 2026 \d{2}\.\d{2}$/);
  });

  it('says how many rows are after the clock, and still lands', () => {
    expect(resultModel((Recorded.straddle as unknown as Entry).commit, { found: false, timezone: 'Asia/Jakarta' })).toMatchObject({
      primary: 'landing',
      clockNotice: { tone: 'attention', text: '2 dari 4 baris tersimpan berada setelah waktu ruang kerja ini, sehingga belum dihitung pada ringkasan.' },
    });
  });

  it('never offers the data period when every row is after the clock', () => {
    expect(resultModel((Recorded.after_clock as unknown as Entry).commit, { found: false, timezone: 'Asia/Jakarta' })).toMatchObject({
      primary: 'home',
      clockNotice: { tone: 'attention', text: 'Semua 2 baris tersimpan, tetapi berada setelah waktu ruang kerja ini, sehingga belum tampil di Beranda atau Perangkat.' },
    });
  });

  it('says nothing is new on a reimport', () => {
    const model = resultModel(Recorded.reimport.commit, { found: false, timezone: 'Asia/Jakarta' });

    expect(model).toMatchObject({
      primary: 'home',
      nothingNew: 'Tidak ada baris baru. 12 baris sama dengan data tersimpan dan dihitung sekali.',
    });
    expect(model.rows).toContainEqual({ term: 'Periode data', value: 'Tidak ada periode baru' });
    expect(model.rows).toContainEqual({ term: 'Perangkat yang dipakai', value: 'Lampu Teras, Dispenser' });
  });

  it('names a result found again, and a long range', () => {
    expect(resultModel({ ...Recorded.valid.commit, replayed: true }, { found: false, timezone: 'Asia/Jakarta' })).toMatchObject({
      title: 'Impor sudah dikonfirmasi sebelumnya',
      note: 'Permintaan yang sama ditemukan; data tidak diimpor dua kali.',
    });
    expect(resultModel(Recorded.valid.commit, { found: true, timezone: 'Asia/Jakarta' }).title).toBe('Impor sudah dikonfirmasi sebelumnya');
    expect(resultModel((Recorded.long as unknown as Entry).commit, { found: false, timezone: 'Asia/Jakarta' }).longRange).toBe(
      'Rentang data lebih dari 366 hari, sehingga Beranda menampilkan 366 hari terakhirnya.',
    );
  });
});

describe('commitOutcome', () => {
  it.each([
    ['two', 'ack_required', 'refused'],
    ['three', 'blocked_commit', 'refused'],
  ])('refuses %s', (name, key, kind) => {
    expect(commitOutcome(envelope(name, key)).kind).toBe(kind);
  });

  it.each([
    ['stale', 'stale'],
    ['key_conflict', 'refused'],
    ['commit_not_found', 'gone'],
    ['bad_key', 'refused'],
  ])('maps the recorded %s', (name, kind) => {
    expect(commitOutcome(envelope(name)).kind).toBe(kind);
  });

  it.each([
    ['IMPORT_ACK_REQUIRED', 'refused', 'ack'],
    ['IMPORT_BLOCKED', 'refused', 'blocked'],
    ['CONFLICT', 'refused', 'conflict'],
    ['VALIDATION_FAILED', 'refused', 'other'],
    ['IMPORT_STALE', 'stale', 'other'],
    ['NOT_FOUND', 'gone', 'other'],
    ['SESSION_EXPIRED', 'ended', 'other'],
    ['UNAUTHORIZED', 'ended', 'other'],
    ['NETWORK_UNREACHABLE', 'unknown', 'other'],
    ['UNEXPECTED_RESPONSE', 'unknown', 'other'],
    ['INTERNAL_ERROR', 'unknown', 'other'],
    ['DATABASE_UNAVAILABLE', 'unknown', 'other'],
  ])('maps %s on code alone', (code, kind, reason) => {
    expect(commitOutcome(failure(code))).toEqual({ kind, reason });
  });
});

describe('previewOutcome', () => {
  it('lists every detail of a refusal, linked to the source', () => {
    const outcome = previewOutcome(envelope('invalid_header'));
    const details = (Recorded.invalid_header as unknown as { error: { details: { msg: string }[] } }).error.details;

    expect(outcome).toMatchObject({ kind: 'refused', canRetry: false });
    expect(outcome.items).toEqual(details.map((detail, index) => ({ key: `detail-${index}`, text: detail.msg, target: 'source' })));
  });

  it('adds the file line when a detail names one', () => {
    const error = new ApiError('IMPORT_INVALID', 'x', { retryable: false }, 'r', [{ loc: ['file', 'line', 7], msg: 'Kolom kurang.', type: 'column_count' }]);

    expect(previewOutcome(error).items).toEqual([{ key: 'detail-0', text: 'Kolom kurang. (baris berkas 7)', target: 'source' }]);
  });

  it('links a minutes detail to its field', () => {
    expect(previewOutcome(envelope('bad_minutes')).items).toEqual([
      { key: 'detail-0', text: 'Nilai isian ini belum valid. Periksa lalu coba lagi.', target: 'interval:pemanas air' },
    ]);
  });

  it.each([
    ['too_large', 'refused'],
    ['too_many_rows', 'refused'],
    ['not_utf8', 'refused'],
    ['invalid_empty', 'refused'],
    ['asset_gone', 'assetGone'],
  ])('maps the recorded %s', (name, kind) => {
    expect(previewOutcome(envelope(name)).kind).toBe(kind);
  });

  it.each([
    ['BAD_REQUEST', 'refused', false],
    ['SESSION_EXPIRED', 'ended', false],
    ['UNAUTHORIZED', 'ended', false],
    ['NETWORK_UNREACHABLE', 'notFinished', true],
    ['INTERNAL_ERROR', 'notFinished', false],
    ['UNEXPECTED_RESPONSE', 'notFinished', false],
  ])('maps %s on code alone', (code, kind, retryable) => {
    const outcome = previewOutcome(failure(code, retryable));
    expect(outcome.kind).toBe(kind);
    expect(outcome.canRetry).toBe(retryable);
  });
});

describe('preview lines', () => {
  it('adds a note only for a counter that continues a stored one', () => {
    expect(counterNotes(Recorded.counter.answered)).toEqual([]);
    expect(counterNotes(Recorded.counter_append)).toEqual([
      'Mesin Cuci melanjutkan penghitung yang sudah tersimpan. Energi dihitung dari selisih dengan pembacaan tersimpan; catatan “pembacaan pertama” hanya menggambarkan isi berkas ini.',
    ]);
  });

  it('describes each stream from its fields', () => {
    const streams = (preview: ImportPreview) => (preview.mapping as { streams: Parameters<typeof streamRow>[0][] }).streams;

    expect(streamRow(streams(Recorded.valid.answered)[0])).toBe('Lampu Teras: interval 1 jam (disimpulkan)');
    expect(streamRow(streams(Recorded.power.answered)[0])).toBe('Pompa Air: interval belum diketahui (dari kolom awal dan akhir)');
    expect(streamRow(streams(Recorded.one.answered)[0])).toBe('Pemanas Air: interval 1 jam (diisi)');
  });

  it('states the file and its columns', () => {
    expect(mappingLine(Recorded.valid.first)).toBe('tempelan.csv · 12 baris data · kolom waktu timestamp · kolom nilai energi_wh (Wh)');
    expect(mappingLine(Recorded.power.answered)).toBe(
      'tempelan.csv · 2 baris data · kolom waktu interval_start dan interval_end · kolom nilai power_w (W)',
    );
    expect(mappingLine(Recorded.value_kind)).toBe('tempelan.csv · 2 baris data · kolom waktu timestamp · kolom nilai belum dipilih');
  });
});

describe('examples', () => {
  // The prototype is the oracle: its EXAMPLES function runs here, so the ported data must match it byte for byte.
  const source = readFileSync(join(__dirname, '../../../docs/reference/prototype/hematdaya-app.js'), 'utf8');
  const start = source.indexOf('var EXAMPLES = function (ctx) {');
  const end = source.indexOf('\n  };\n', start);
  // eslint-disable-next-line no-new-func -- evaluates the prototype's own data function as the oracle
  const oracle = new Function(`${source.slice(start, end)}\n  }; return EXAMPLES;`)() as (ctx: string) => { id: string; label: string; file: string; text: string }[];

  it.each(['household', 'business', 'industry', 'unspecified'] as const)('matches the prototype for %s', (preset) => {
    expect(EXAMPLES(preset)).toEqual(oracle(preset === 'unspecified' ? 'household' : preset));
  });

  it('names the industrial assets', () => {
    expect(EXAMPLES('industry')[0].text).toContain('Mesin Jahit');
    expect(EXAMPLES('industry')[0].text).toContain('Lampu Gudang');
    expect(EXAMPLES('household').map((example) => example.id)).toEqual(['valid', 'two', 'three', 'conflict', 'semi', 'power', 'counter', 'one']);
  });
});
