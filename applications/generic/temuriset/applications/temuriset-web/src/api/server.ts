import { cookies } from 'next/headers';

import { ApiError, readFailure } from '@/api/errors';
import { API_LOCALE_HEADER } from '@/features/i18n/locale';
import { serverLocale } from '@/features/i18n/server';

// Server Components read the service directly and forward the visitor's cookies, so the service authorizes each
// read as that visitor. Browsers never call this; they use the same-origin proxy (`src/api/client.ts`).
const TIMEOUT_MS = 5_000;

export async function serverGet<Body>(path: `/${string}`): Promise<Body> {
  const apiUrl = process.env.API_URL ?? 'http://localhost:8020';
  const cookie = (await cookies()).toString();
  // The service answers in the page's language, so its messages match the English pages.
  const locale = await serverLocale();
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      headers: { ...(cookie ? { cookie } : {}), [API_LOCALE_HEADER]: locale },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });
  } catch {
    throw ApiError.unreachable();
  }
  if (!response.ok) {
    throw await readFailure(response);
  }
  return (await response.json()) as Body;
}
