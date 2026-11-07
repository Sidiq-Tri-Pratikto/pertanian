import type { components } from '@/api/schema.generated';

type ErrorBody = components['schemas']['ErrorBody'];
export type Recovery = components['schemas']['ErrorRecovery'];
export type ErrorDetail = components['schemas']['ErrorFieldDetail'];
export const DEFAULT_MAX_ATTEMPTS = 3;

const UNREACHABLE_MESSAGE = 'Layanan belum dapat dihubungi. Periksa koneksi Anda lalu coba lagi.';
const UNEXPECTED_MESSAGE = 'Layanan mengirim jawaban yang tidak dikenali. Coba lagi nanti.';

/** One client-side failure. Branch on `code`; show `message` and `requestId`. */
export class ApiError extends Error {
  readonly code: string;
  readonly requestId: string | null;
  readonly recovery: Recovery;
  /** The specifics a refusal carries, such as each problem in a file. Shown as sent, never parsed. */
  readonly details: ErrorDetail[];

  constructor(code: string, message: string, recovery: Recovery, requestId: string | null = null, details: ErrorDetail[] = []) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.recovery = recovery;
    this.requestId = requestId;
    this.details = details;
  }

  static unreachable(): ApiError {
    return new ApiError('NETWORK_UNREACHABLE', UNREACHABLE_MESSAGE, {
      retryable: true,
      max_attempts: DEFAULT_MAX_ATTEMPTS,
    });
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

function isErrorDetail(value: unknown): value is ErrorDetail {
  const detail = value as Partial<ErrorDetail> | null;
  return Array.isArray(detail?.loc) && typeof detail.msg === 'string' && typeof detail.type === 'string';
}

/** Keep only details of the documented shape; anything else is dropped rather than shown. */
function readDetails(value: unknown): ErrorDetail[] {
  return Array.isArray(value) ? value.filter(isErrorDetail) : [];
}

/** Read the service's failure envelope. A body that is not the envelope never leaks to the user. */
export async function readFailure(response: Response): Promise<ApiError> {
  const payload: unknown = await response.json().catch(() => null);
  const body = (payload as { error?: unknown } | null)?.error;
  if (!isErrorBody(body)) {
    return ApiError.unexpected();
  }
  return new ApiError(body.code, body.message, body.recovery ?? { retryable: false }, body.request_id, readDetails(body.details));
}
