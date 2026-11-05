import type { Persona } from '@/features/persona';

export type Route = {
  path: string;
  /** Persona cookie to set first; `null` means a first visit. */
  persona: Persona | null;
  /** Expected document status. */
  status?: number;
  /** Accessible name of the route's primary action, checked at 200% text. */
  primary?: string;
};

/**
 * Every route the web app serves, with the persona that reaches it. One list feeds every browser check, so a new
 * screen is checked everywhere by adding one line here (spec 003 FR-005).
 */
export const ROUTES: Route[] = [
  { path: '/start', persona: null, primary: 'Lanjutkan' },
  { path: '/home', persona: 'inovator' },
  { path: '/inventions', persona: 'inovator' },
  { path: '/discover', persona: 'inovator' },
  { path: '/pitches', persona: 'inovator' },
  { path: '/settings', persona: 'inovator', primary: 'Simpan tampilan' },
  { path: '/segera-hadir/inovasi', persona: 'inovator' },
  { path: '/discover', persona: 'mitra' },
  { path: '/opportunities', persona: 'mitra' },
  { path: '/pitches?box=masuk', persona: 'mitra' },
  { path: '/pitches?box=diskusi', persona: 'mitra' },
  { path: '/settings', persona: 'mitra', primary: 'Simpan tampilan' },
  { path: '/segera-hadir/tidak-dikenal', persona: 'inovator' },
  { path: '/alamat-yang-tidak-ada', persona: 'inovator', status: 404 },
];

export function label(route: Route): string {
  return `${route.path} as ${route.persona ?? 'first visit'}`;
}
