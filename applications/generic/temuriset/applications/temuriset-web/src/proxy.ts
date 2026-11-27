import { NextResponse, type NextRequest } from 'next/server';

import { LOCALE_HEADER, toIndonesianPath } from '@/features/i18n/locale';

/**
 * English addresses (`/en/...`) are served by the Indonesian pages: the path is mapped segment by segment
 * (`/en/subscribe/manage` → `/langganan/atur`), the query string stays, and the page learns its language from a
 * request header. Indonesian addresses never pass through here (spec 050).
 */
export function proxy(request: NextRequest) {
  const url = request.nextUrl.clone();
  url.pathname = toIndonesianPath(url.pathname);
  const headers = new Headers(request.headers);
  headers.set(LOCALE_HEADER, 'en');
  return NextResponse.rewrite(url, { request: { headers } });
}

export const config = { matcher: ['/en', '/en/:path*'] };
