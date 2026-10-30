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
