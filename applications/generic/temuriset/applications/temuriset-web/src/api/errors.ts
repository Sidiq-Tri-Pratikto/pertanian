import type { components } from '@/api/schema.generated';

type ErrorBody = components['schemas']['ErrorBody'];
export type Recovery = components['schemas']['ErrorRecovery'];

const UNREACHABLE_MESSAGE = 'Layanan belum dapat dihubungi. Periksa koneksi Anda lalu coba lagi.';
const UNEXPECTED_MESSAGE = 'Layanan mengirim jawaban yang tidak dikenali. Coba lagi nanti.';

/** One client-side failure. Branch on `code`; show `message` and `requestId`. */
export class ApiError extends Error {
  readonly code: string;
  readonly requestId: string | null;
  readonly recovery: Recovery;
  /** Guesses left for a sign-in code (`CODE_INVALID`). */
  readonly attemptsLeft: number | null;

  constructor(code: string, message: string, recovery: Recovery, requestId: string | null = null, attemptsLeft: number | null = null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.recovery = recovery;
    this.requestId = requestId;
    this.attemptsLeft = attemptsLeft;
  }

  static unreachable(): ApiError {
    return new ApiError('NETWORK_UNREACHABLE', UNREACHABLE_MESSAGE, { retryable: true, max_attempts: 3 });
  }

  static unexpected(): ApiError {
    return new ApiError('UNEXPECTED_RESPONSE', UNEXPECTED_MESSAGE, { retryable: false });
  }

  /** Normalize anything caught at a call site. */
  static from(error: unknown): ApiError {
    return error instanceof ApiError ? error : ApiError.unexpected();
  }
}

function isErrorBody(value: unknown): value is ErrorBody {
  const body = value as Partial<ErrorBody> | null;
  return typeof body?.code === 'string' && typeof body.message === 'string' && typeof body.recovery === 'object';
}

/** Read the service's failure envelope. A body that is not the envelope never leaks to the user. */
export async function readFailure(response: Response): Promise<ApiError> {
  const payload: unknown = await response.json().catch(() => null);
  const body = (payload as { error?: unknown } | null)?.error;
  if (!isErrorBody(body)) {
    return ApiError.unexpected();
  }
  return new ApiError(body.code, body.message, body.recovery ?? { retryable: false }, body.request_id, body.attempts_left ?? null);
}
