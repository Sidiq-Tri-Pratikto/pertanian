import type { Persona } from '@/features/persona';

export type Route = {
  path: string;
  /** Persona of the account signed up first; `null` means a visitor who is not signed in. `:draft` and `:published` become a new invention, `:support` a support request (also inside `?source=SUPPORT_REQUEST::support`) and `:funding` a company raise. */
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
  { path: '/inventions/import', persona: 'inovator' },
  { path: '/discover', persona: 'inovator' },
  { path: '/pitches', persona: 'inovator' },
  { path: '/pitches/00000000-0000-4000-8000-000000000000', persona: 'inovator' },
  { path: '/settings', persona: 'inovator', primary: 'Keluar' },
  { path: '/undangan/tidak-ada', persona: 'inovator' },
  { path: '/segera-hadir/pemberitahuan-email', persona: 'inovator' },
  { path: '/partnerships/new', persona: 'inovator' },
  { path: '/partnerships/00000000-0000-4000-8000-000000000000', persona: 'inovator' },
  { path: '/profiles/00000000-0000-4000-8000-000000000000', persona: null },
  { path: '/discover?type=inventions&q=air', persona: 'inovator' },
  { path: '/matches', persona: 'inovator' },
  { path: '/matches?source=SUPPORT_REQUEST::support', persona: 'inovator' },
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
  { path: '/discover?type=funding', persona: 'mitra' },
  { path: '/discover?type=partners&sector=Energi&stage=IDEA', persona: 'mitra' },
  { path: '/opportunities', persona: 'mitra', primary: 'Buat mandat' },
  { path: '/partners/:no-profile', persona: 'mitra', primary: 'Simpan profil' },
  { path: '/partners/:partner', persona: 'mitra', primary: 'Buat mandat' },
  { path: '/opportunities/:mandate/edit', persona: 'mitra', primary: 'Tinjau mandat' },
  { path: '/pitches?box=masuk', persona: 'mitra' },
  { path: '/pitches?box=diskusi', persona: 'mitra' },
  { path: '/settings', persona: 'mitra', primary: 'Keluar' },
  { path: '/segera-hadir/tidak-dikenal', persona: 'inovator' },
  { path: '/alamat-yang-tidak-ada', persona: 'inovator', status: 404 },
];

export function label(route: Route): string {
  return `${route.path} as ${route.persona ?? 'signed-out visitor'}`;
}
