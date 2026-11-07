import { ApiError, readFailure } from '@/api/errors';

const envelope = {
  error: {
    code: 'DATABASE_UNAVAILABLE',
    message: 'The database is temporarily unavailable. Please try again in a few minutes.',
    request_id: 'ref_abc',
    recovery: { retryable: true, retry_after_seconds: 30, max_attempts: 3 },
  },
};

describe('readFailure', () => {
  it('reads code, message, reference and recovery from the envelope', async () => {
    const error = await readFailure(new Response(JSON.stringify(envelope), { status: 503 }));

    expect(error.code).toBe('DATABASE_UNAVAILABLE');
    expect(error.requestId).toBe('ref_abc');
    expect(error.recovery.retry_after_seconds).toBe(30);
  });

  it.each([
    ['html', '<html>bad gateway</html>'],
    ['another shape', JSON.stringify({ detail: 'secret stack trace' })],
    ['partial envelope', JSON.stringify({ error: { code: 'X' } })],
  ])('never surfaces a body that is %s', async (_, body) => {
    const error = await readFailure(new Response(body, { status: 502 }));

    expect(error.code).toBe('UNEXPECTED_RESPONSE');
    expect(error.message).not.toContain('secret');
    expect(error.recovery.retryable).toBe(false);
  });
});

describe('ApiError.from', () => {
  it('keeps a typed error', () => {
    const error = ApiError.unreachable();

    expect(ApiError.from(error)).toBe(error);
  });

  it('normalizes anything else', () => {
    expect(ApiError.from(new TypeError('raw')).code).toBe('UNEXPECTED_RESPONSE');
  });
});

describe('readFailure details', () => {
  const recorded = jest.requireActual<Record<string, { error: Record<string, unknown> }>>('../../tests/fixtures/imports.json');

  function withDetails(details: unknown) {
    return new Response(JSON.stringify({ error: { ...envelope.error, code: 'IMPORT_INVALID', details } }), { status: 400 });
  }

  it('keeps every detail of an import refusal, as sent', async () => {
    const error = await readFailure(new Response(JSON.stringify(recorded.invalid_header), { status: 400 }));
    const sent = recorded.invalid_header.error.details as { msg: string; type: string }[];

    expect(error.details).toHaveLength(3);
    expect(error.details.map((detail) => [detail.msg, detail.type])).toEqual(sent.map((detail) => [detail.msg, detail.type]));
  });

  it('keeps a line location as given', async () => {
    const error = await readFailure(withDetails([{ loc: ['file', 'line', 3], msg: 'Baris 3 rusak.', type: 'column_count' }]));

    expect(error.details).toEqual([{ loc: ['file', 'line', 3], msg: 'Baris 3 rusak.', type: 'column_count' }]);
  });

  it('drops a detail that is not the documented shape', async () => {
    const error = await readFailure(
      withDetails([
        { loc: ['file'], msg: 'Benar.', type: 'x' },
        { loc: ['file'], msg: 42, type: 'x' },
        { loc: 'file', msg: 'Tanpa daftar.', type: 'x' },
        { loc: ['file'], msg: 'Tanpa jenis.' },
        'teks',
      ]),
    );

    expect(error.details).toEqual([{ loc: ['file'], msg: 'Benar.', type: 'x' }]);
  });

  it.each([
    ['absent', undefined],
    ['null', null],
    ['not a list', { msg: 'x' }],
  ])('gives no details when they are %s', async (_name, details) => {
    const error = await readFailure(withDetails(details));

    expect(error.code).toBe('IMPORT_INVALID');
    expect(error.details).toEqual([]);
  });

  it('never surfaces details from a body that is not the envelope', async () => {
    const error = await readFailure(new Response(JSON.stringify({ details: [{ loc: [], msg: 'secret', type: 'x' }] }), { status: 400 }));

    expect(error.code).toBe('UNEXPECTED_RESPONSE');
    expect(error.details).toEqual([]);
  });

  it('gives client-side failures no details', () => {
    expect(ApiError.unreachable().details).toEqual([]);
    expect(ApiError.unexpected().details).toEqual([]);
  });
});
