import type { IconName } from '@/components/tr/Icon';

/**
 * The two public personas. A persona picks language and navigation only; it never grants access (PRD section 3).
 * Until accounts arrive (spec 008) the choice lives in a cookie.
 */
export type Persona = 'inovator' | 'mitra';

export const PERSONA_COOKIE = 'tr_persona';

export const PERSONA_LABEL: Record<Persona, string> = { inovator: 'Inovator', mitra: 'Investor/Mitra' };

export type NavItem = { id: string; label: string; short?: string; icon: IconName; href: string };

/** Primary destinations per persona (handoff section 5). The tab bar shows the first four plus Lainnya. */
export const NAV: Record<Persona, NavItem[]> = {
  inovator: [
    { id: 'beranda', label: 'Beranda', icon: 'home', href: '/home' },
    { id: 'inovasi', label: 'Inovasi Saya', icon: 'bulb', href: '/inventions' },
    { id: 'temukan', label: 'Temukan Investor/Mitra', short: 'Temukan', icon: 'search', href: '/discover' },
    { id: 'pitching', label: 'Pitching dan Diskusi', short: 'Pitching', icon: 'chat', href: '/pitches' },
    { id: 'profil', label: 'Profil', icon: 'user', href: '/settings' },
  ],
  mitra: [
    { id: 'jelajahi', label: 'Jelajahi', icon: 'search', href: '/discover' },
    { id: 'mandat', label: 'Kebutuhan/Mandat', short: 'Mandat', icon: 'file', href: '/opportunities' },
    { id: 'masuk', label: 'Pitching Masuk', short: 'Masuk', icon: 'inbox', href: '/pitches?box=masuk' },
    { id: 'diskusi', label: 'Diskusi dan Jadwal', short: 'Diskusi', icon: 'calendar', href: '/pitches?box=diskusi' },
    { id: 'profil', label: 'Profil', icon: 'user', href: '/settings' },
  ],
};

export function readPersona(value: string | undefined | null): Persona | null {
  return value === 'inovator' || value === 'mitra' ? value : null;
}

/** Where each persona starts. Partners begin at Jelajahi. */
export function homeFor(persona: Persona): string {
  return NAV[persona][0].href;
}
