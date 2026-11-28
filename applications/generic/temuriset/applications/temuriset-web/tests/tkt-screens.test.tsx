import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import axe from 'axe-core';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TktBadge } from '@/components/tr/TktBadge';
import { TktSteps, type ReadinessDraft } from '@/features/portfolio/TktSteps';
import { expectedRange, mismatch } from '@/features/portfolio/tkt';
import { draftRequest, valuesFrom } from '@/features/portfolio/editor-state';
import { MandateCard } from '@/views/intake/MandateCard';
import type { Mandate } from '@/features/intake/model';
import { PreflightView } from '@/views/pitches/PreflightView';
import type { Me } from '@/api/client';
import type { Preflight } from '@/features/pitches/model';

const { pushMock, runPreflightMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  runPreflightMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock, refresh: vi.fn() }),
}));

vi.mock('@/features/pitches/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/pitches/api')>();
  return {
    ...actual,
    runPreflight: runPreflightMock,
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const ME: Me = {
  account: { id: 'acc-1', email: 'in@example.test', display_name: 'Rina', persona: 'inovator', time_zone: 'Asia/Jakarta' },
  active_party_id: 'party-1',
  parties: [{ id: 'party-1', name: 'Lab Rina', kind: 'INDIVIDUAL', role: 'OWNER' }],
  capabilities: [],
} as unknown as Me;

describe('TKT helpers (spec 056)', () => {
  it('computes expected ranges and stage mismatch notes cleanly', () => {
    expect(expectedRange('IDEA')).toEqual([1, 3]);
    expect(expectedRange('PROTOTYPE')).toEqual([3, 6]);
    expect(expectedRange('MARKET')).toEqual([8, 9]);
    expect(mismatch('IDEA', 6)).toBe('above');
    expect(mismatch('MARKET', 3)).toBe('below');
    expect(mismatch('PROTOTYPE', 4)).toBeNull();
    expect(mismatch('PROTOTYPE', 7)).toBeNull(); // within ±1 tolerance
    expect(mismatch('IDEA', null)).toBeNull();
  });
});

describe('TktBadge (spec 056)', () => {
  it('renders nothing when level is null or undefined (never TKT 0)', () => {
    const { container } = render(<TktBadge level={null} showBar showMeta />);
    expect(container.textContent).toBe('');
  });

  it('shows badge, 9-segment bar text equivalent, provenance, note, and Toggletip', () => {
    render(<TktBadge level={4} stageLabel="Prototipe" note="Diuji di lab." hasEvidence showBar showMeta />);
    expect(screen.getByText('TKT 4 · Prototipe')).toBeTruthy();
    expect(screen.getByText('TKT 4 dari 9')).toBeTruthy();
    expect(screen.getByText(/Dinyatakan inovator/)).toBeTruthy();
    expect(screen.getByText(/Bukti terlampir saat pitching/)).toBeTruthy();
    expect(screen.getByText('Diuji di lab.')).toBeTruthy();

    const tipBtn = screen.getByRole('button', { name: /TKT 4/ });
    fireEvent.click(tipBtn);
    expect(screen.getByText(/divalidasi di laboratorium/i)).toBeTruthy();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(tipBtn.getAttribute('aria-expanded')).toBe('false');
  });
});

describe('TktSteps (spec 056)', () => {
  it('defaults to Belum mengisi TKT, allows choosing TKT 6, shows mismatch note for IDEA, and passes axe', async () => {
    let current: ReadinessDraft | null = null;
    const onChange = vi.fn((next: ReadinessDraft | null) => {
      current = next;
    });
    const { container, rerender } = render(
      <TktSteps value={current} onChange={onChange} stage="IDEA" actingPartyId="party-1" documents={[]} />,
    );

    const noneRadio = screen.getByRole('radio', { name: 'Belum mengisi TKT' }) as HTMLInputElement;
    expect(noneRadio.checked).toBe(true);

    const tkt6 = screen.getByRole('radio', { name: /TKT 6/ });
    fireEvent.click(tkt6);
    expect(onChange).toHaveBeenCalledWith({ tkt_level: 6, note: '', evidence: null });

    rerender(<TktSteps value={{ tkt_level: 6, note: '', evidence: null }} onChange={onChange} stage="IDEA" actingPartyId="party-1" documents={[]} />);
    expect(screen.getByText('TKT 6 dari 9')).toBeTruthy();
    expect(screen.getByText(/TKT 6 biasanya sudah melewati tahap Ide/)).toBeTruthy();

    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });

  it('includes readiness in draftRequest when set and omits/nulls it when unset', () => {
    const base = valuesFrom(null);
    expect(draftRequest(base, 1, 'party-1').readiness).toBeNull();
    const withTkt = { ...base, readiness: { tkt_level: 5, note: ' Uji lapangan ', evidence: null } };
    expect(draftRequest(withTkt, 1, 'party-1').readiness).toEqual({ tkt_level: 5, note: 'Uji lapangan', evidence: null });
  });
});

describe('MandateCard min_tkt (spec 056)', () => {
  it('renders Mencari TKT {n} ke atas with Toggletip when min_tkt is set', () => {
    const mandate = {
      id: 'opp-1',
      title: 'Mandat Agritech',
      status: 'ACTIVE',
      number: 1,
      outcome: 'Pilot',
      support: '',
      timing: '',
      min_tkt: 6,
      financial: null,
      requirements: [],
      target_availability: { available: true, reason: null },
      general_intake_label: null,
    } as unknown as Mandate;

    render(<MandateCard mandate={mandate} />);
    expect(screen.getByText('Mencari TKT 6 ke atas')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Apa itu TKT/ })).toBeTruthy();
  });
});

describe('PreflightView TKT evidence pre-tick (spec 056)', () => {
  it('pre-ticks kind=tkt files by default with Dokumentasi TKT hint and allows unticking', async () => {
    const preflight: Preflight = {
      token: 'tok-1',
      readiness: 'READY_TO_SUBMIT',
      availability: { available: true, reason: null },
      duplicate_pitch_id: null,
      gap: null,
      sender: { id: 'party-1', name: 'Lab Rina' },
      recipient: { id: 'party-2', name: 'Investor A' },
      source: { type: 'INVENTION', id: 'inv-1', title: 'Sensor Irigasi', version: 1 },
      opportunity: { id: 'opp-1', title: 'Mandat A', version: 1 },
      inventions: [{ id: 'inv-1', title: 'Sensor Irigasi', version: 1 }],
      brief: { id: 'br-1', text: 'Ringkasan singkat.' },
      rows: [],
      shareable_files: [
        { document_id: 'doc-tkt', version_id: 'ver-tkt', version: 1, title: 'Laporan Uji TKT 4', review_state: 'PROVIDED_UNREVIEWED', kind: 'tkt', selected: true },
        { document_id: 'doc-reg', version_id: 'ver-reg', version: 1, title: 'Pitch Deck', review_state: 'PROVIDED_UNREVIEWED', kind: 'document', selected: false },
      ],
    } as unknown as Preflight;

    runPreflightMock.mockResolvedValueOnce(preflight);
    render(<PreflightView me={ME} source={{ type: 'SUPPORT_REQUEST', id: 'sr-1' }} targetId="opp-1" />);

    await waitFor(() => expect(screen.getByText(/Dokumentasi TKT ·/)).toBeTruthy());
    const tktCheckbox = screen.getByRole('checkbox', { name: /Laporan Uji TKT 4/ }) as HTMLInputElement;
    const regCheckbox = screen.getByRole('checkbox', { name: /Pitch Deck/ }) as HTMLInputElement;
    expect(tktCheckbox.checked).toBe(true);
    expect(regCheckbox.checked).toBe(false);

    // Unticking must stay allowed
    fireEvent.click(tktCheckbox);
    expect(tktCheckbox.checked).toBe(false);
  });
});
