import type { Persona } from '@/features/persona';

export type Route = {
  path: string;
  /** Persona of the account signed up first; `null` means a visitor who is not signed in. `:draft` and `:published` become a new invention, `:support` a support request and `:funding` a company raise. */
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
  { path: '/start', persona: null, primary: 'Kirim kode' },
  { path: '/start?masuk=1', persona: null, primary: 'Kirim kode' },
  { path: '/home', persona: 'inovator' },
  { path: '/inventions', persona: 'inovator' },
  { path: '/discover', persona: 'inovator' },
  { path: '/pitches', persona: 'inovator' },
  { path: '/settings', persona: 'inovator', primary: 'Keluar' },
  { path: '/undangan/tidak-ada', persona: 'inovator' },
  { path: '/segera-hadir/kecocokan', persona: 'inovator' },
  { path: '/inventions/:draft/edit?step=1', persona: 'inovator', primary: 'Simpan dan lanjutkan' },
  { path: '/inventions/:draft/edit?step=2', persona: 'inovator', primary: 'Simpan dan lanjutkan' },
  { path: '/inventions/:draft/edit?step=3', persona: 'inovator', primary: 'Simpan dan lanjutkan' },
  { path: '/inventions/:draft/edit?step=4', persona: 'inovator', primary: 'Terbitkan versi 1' },
  { path: '/inventions/:published', persona: 'inovator' },
  { path: '/support-requests', persona: 'inovator', primary: 'Mulai pendanaan perusahaan' },
  { path: '/support-requests/:support', persona: 'inovator', primary: 'Simpan kebutuhan' },
  { path: '/funding-requests/:funding', persona: 'inovator' },
  { path: '/funding-requests/:funding/edit', persona: 'inovator', primary: 'Simpan pendanaan' },
  { path: '/discover', persona: 'mitra' },
  { path: '/opportunities', persona: 'mitra' },
  { path: '/pitches?box=masuk', persona: 'mitra' },
  { path: '/pitches?box=diskusi', persona: 'mitra' },
  { path: '/settings', persona: 'mitra', primary: 'Keluar' },
  { path: '/segera-hadir/tidak-dikenal', persona: 'inovator' },
  { path: '/alamat-yang-tidak-ada', persona: 'inovator', status: 404 },
];

export function label(route: Route): string {
  return `${route.path} as ${route.persona ?? 'signed-out visitor'}`;
}
