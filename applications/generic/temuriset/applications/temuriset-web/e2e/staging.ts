import { readFileSync } from 'node:fs';
import type { Persona } from '@/features/persona';

/** The widths every route must hold without horizontal scroll (PRD section 13). */
export const VIEWPORTS = [320, 360, 768, 1280] as const;

export const STAGING_SUITES = ['axe', 'keyboard', 'overflow'] as const;
export const STAGING_JOURNEYS = [
  {
    name: 'J01', file: 'matching.spec.ts', project: 'chromium-1280',
    title: 'J01: from Beranda through the range repair and the match to a submitted pitch Mitra J01 receives (S03, S10, S11)',
  },
  {
    name: 'J02', file: 'j02-company-raise.spec.ts', project: 'chromium-1280',
    title: 'J02: Bima pitches one company raise to an equity mandate, and the second link opens the same pitch (S10, S11)',
  },
  {
    name: 'J03', file: 'j03-revision.spec.ts', project: 'chromium-1280',
    title: 'J03: revision with an honest answer, a new file version, resubmission, item review and approval (S12, S13)',
  },
  {
    name: 'J04', file: 'j04-schedule.spec.ts', project: 'chromium-1280',
    title: 'J04: propose, conflict, counter, conflict, confirm 10:00 UTC, then a replacement (S14, UX-13, UX-14)',
  },
  {
    name: 'J05', file: 'j05-relationship.spec.ts', project: 'chromium-1280',
    title: 'J05: both parties correct and confirm one version, then narrow its public projection',
  },
] as const;

export function stagingOrigin(): string | undefined {
  const value = process.env.E2E_STAGING_URL;
  if (value === undefined) return;
  const url = URL.parse(value);
  if (!url || url.protocol !== 'https:' || value !== url.origin) {
    throw new Error('E2E_STAGING_URL must be an HTTPS origin.');
  }
  return url.origin;
}

type Fixture = { email: string; session: string };
const DNS_LABEL = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;

function isSyntheticDomain(value: unknown): value is string {
  if (typeof value !== 'string' || value.length > 253 || /[^a-z0-9.-]/.test(value)) return false;
  const labels = value.split('.');
  return labels.length >= 2 && labels.every((label) => DNS_LABEL.test(label)) && /[a-z]/.test(labels.at(-1)!);
}

/** A private operator-supplied file, with a fresh authorized account for each test and persona. */
export function loadStagingFixtures(origin: string): Record<string, Partial<Record<Persona, Fixture[]>>> {
  const file = process.env.E2E_STAGING_FIXTURES_FILE;
  if (!file) throw new Error('Set E2E_STAGING_FIXTURES_FILE to approved synthetic staging sessions.');
  const invalid = 'Staging sessions must be valid JSON for this approved synthetic environment.';
  let data;
  try {
    data = JSON.parse(readFileSync(file, 'utf8'));
  } catch {
    throw new Error(invalid);
  }
  if (!data || data.origin !== origin || data.synthetic !== true || !isSyntheticDomain(data.syntheticEmailDomain) ||
    !data.sessions || Array.isArray(data.sessions) ||
    typeof data.sessions !== 'object' || Object.keys(data.sessions).length === 0) {
    throw new Error(invalid);
  }
  const seen = new Set<string>();
  for (const personas of Object.values(data.sessions)) {
    if (!personas || typeof personas !== 'object' || Array.isArray(personas)) throw new Error(invalid);
    for (const accounts of Object.values(personas)) {
      if (!Array.isArray(accounts) || accounts.length === 0) throw new Error(invalid);
      for (const account of accounts) {
        if (!account || typeof account.email !== 'string' || typeof account.session !== 'string' ||
          account.session.length < 40 || /[^A-Za-z0-9_-]/.test(account.session) || seen.has(account.email)) {
          throw new Error(invalid);
        }
        const [local, domain, extra] = account.email.split('@');
        if (!local || extra !== undefined || /\s/.test(account.email) || domain !== data.syntheticEmailDomain ||
          account.email !== account.email.toLowerCase()) {
          throw new Error(invalid);
        }
        seen.add(account.email);
      }
    }
  }
  return data.sessions;
}
