import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import type { ReactElement } from 'react';

import { ScoreBreakdown } from '@/components/tr/ScoreBreakdown';
import { Toggletip } from '@/components/tr/Toggletip';
import { dimensionSentence, type Dimension } from '@/features/discovery/breakdown';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { setAppLocale } from '@/features/i18n/t';
import { WorkspaceView, type Room } from '@/views/pitches/WorkspaceView';

import { makeMe, PERSONAL } from './fixtures';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }));

const FULL_BREAKDOWN: Dimension[] = [
  { id: 'sector', score: 100, status: 'MATCH', weight: '0.15', values: { source: 'Energi', target: ['Energi'] } },
  { id: 'topic', score: 50, status: 'PARTIAL', weight: '0.45', values: { matched: ['surya'], missing: ['baterai'] } },
  { id: 'readiness', score: 25, status: 'MISMATCH', weight: '0.15', values: { stage: 'PROTOTYPE', accepted_stages: ['PILOT'], tkt: 4, min_tkt: 6 } },
  { id: 'money', score: null, status: 'UNKNOWN', weight: '0.15', values: { source: null, target: null, accepts_partial: false, reason: 'Kisaran biaya pilot untuk kebutuhan ini belum diisi.' } },
  { id: 'form', score: 100, status: 'MATCH', weight: '0.30', values: { source: 'PROJECT', target: ['PROJECT'] } },
  { id: 'requirements', score: null, status: 'NOT_APPLICABLE', weight: null, values: { passed: 0, failed: [], unknown: [], total: 0 } },
  { id: 'evidence', score: 75, status: 'PARTIAL', weight: null, values: { provided: 3, reviewed: 0, applicable: 4 } },
  { id: 'availability', score: 100, status: 'MATCH', weight: '0.15', values: { available: true, reason: null } },
];

async function axeViolations(element: ReactElement): Promise<string[]> {
  const { container } = render(element);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
  });
  return result!.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`);
}

afterEach(() => setAppLocale('id'));

describe('Toggletip', () => {
  it('opens on click and closes on Escape and outside click', async () => {
    const user = userEvent.setup();
    render(
      <div>
        <Toggletip label="Bidang">Penjelasan bidang.</Toggletip>
        <button type="button">Luar</button>
      </div>,
    );
    const btn = screen.getByRole('button', { name: 'Penjelasan: Bidang' });
    expect(btn).toHaveAttribute('aria-expanded', 'false');
    await user.click(btn);
    expect(btn).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('status')).toHaveTextContent('Penjelasan bidang.');

    await user.keyboard('{Escape}');
    expect(btn).toHaveAttribute('aria-expanded', 'false');

    await user.click(btn);
    expect(btn).toHaveAttribute('aria-expanded', 'true');
    await user.click(screen.getByRole('button', { name: 'Luar' }));
    expect(btn).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('ScoreBreakdown (spec 057)', () => {
  it('renders all eight dimensions, never shows 0% for unknown, and formats sentences in ID and EN', () => {
    const { rerender } = render(<ScoreBreakdown dimensions={FULL_BREAKDOWN} deltas={{ topic: { before: 25, after: 50 } }} />);

    expect(screen.getByRole('heading', { name: 'Rincian kecocokan' })).toBeInTheDocument();
    const rows = screen.getAllByRole('listitem');
    expect(rows).toHaveLength(8);
    expect(screen.getByText('Mandat mencari TKT 6 ke atas; produk ini TKT 4.', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Topik dan detail produk 25 → 50')).toBeInTheDocument();
    const moneyRow = rows[3];
    expect(within(moneyRow).getAllByText('Belum diketahui').length).toBeGreaterThanOrEqual(1);
    expect(within(moneyRow).queryByText('0%')).toBeNull();

    rerender(
      <LocaleProvider locale="en">
        <ScoreBreakdown dimensions={FULL_BREAKDOWN} />
      </LocaleProvider>,
    );
    expect(screen.getByRole('heading', { name: 'Match breakdown' })).toBeInTheDocument();
    expect(screen.getByText(/This mandate looks for TKT 6 or above; this product states TKT 4\./)).toBeInTheDocument();
  });

  it('shows recalculate prompt when an old run has no breakdown', async () => {
    const user = userEvent.setup();
    const onRecalculate = vi.fn();
    render(<ScoreBreakdown dimensions={[]} onRecalculate={onRecalculate} />);

    expect(screen.getByText('Hitung ulang untuk melihat rincian')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Hitung ulang' }));
    expect(onRecalculate).toHaveBeenCalledTimes(1);
  });

  it('formats mismatch, overlap, partial, and failure sentences cleanly', () => {
    expect(
      dimensionSentence({ id: 'sector', score: 0, status: 'MISMATCH', weight: '0.15', values: { source: 'Air dan sanitasi', target: ['Pertanian'] } }),
    ).toContain('Pertanian');
    expect(
      dimensionSentence({
        id: 'money',
        score: 100,
        status: 'MATCH',
        weight: '0.15',
        values: {
          source: { low: '20000', high: '30000', currency: 'USD' },
          target: { low: '15000', high: '40000', currency: 'USD' },
          accepts_partial: true,
        },
      }),
    ).toContain('beririsan');
    expect(
      dimensionSentence({
        id: 'money',
        score: 50,
        status: 'PARTIAL',
        weight: '0.15',
        values: {
          source: { low: '50000', high: '60000', currency: 'USD' },
          target: { low: '15000', high: '40000', currency: 'USD' },
          accepts_partial: true,
        },
      }),
    ).toContain('dukungan sebagian');
    expect(
      dimensionSentence({
        id: 'requirements',
        score: 67,
        status: 'MISMATCH',
        weight: null,
        values: { passed: 2, failed: ['SSO yang sudah berjalan'], unknown: [], total: 3 },
      }),
    ).toContain('SSO yang sudah berjalan');
    expect(
      dimensionSentence({ id: 'availability', score: 0, status: 'MISMATCH', weight: '0.15', values: { available: false, reason: 'TARGET_NOT_ACTIVE' } }),
    ).toContain('tidak menerima pitching');
  });

  it('shows the frozen breakdown to the pitch recipient in WorkspaceView (AC79)', () => {
    const room: Room = {
      next: { who: 'you', title: 'Tinjau pitching', text: 'Mulai tinjau.', tab: 'ringkasan', action: 'begin_review' },
      schedule: { proposals: [], meetings: [], can_schedule: false },
      messages: [],
      tasks: [],
      relationship: null,
    };
    const pitch = {
      id: 'p1',
      status: 'SUBMITTED',
      subject_type: 'SUPPORT_REQUEST' as const,
      subject_id: 's1',
      subject_title: 'SolarBox Desa',
      opportunity_id: 'o1',
      opportunity_title: 'Pendanaan energi surya desa',
      requester_party_id: 'other-party',
      requester_name: 'Inovator A',
      recipient_party_id: PERSONAL,
      recipient_name: 'Investor B',
      purpose: 'PROJECT',
      submitted_at: '2026-11-28T00:00:00Z',
      updated_at: '2026-11-28T00:00:00Z',
      waiting_on_party_id: PERSONAL,
      version: 1,
      submissions: [
        {
          number: 1,
          brief: 'Ringkasan singkat.',
          snapshot: {
            opportunity: { version: 1 },
            inventions: [{ title: 'SolarBox Desa', number: 1 }],
            match: { label: 'Kecocokan kuat', fit: { lower: '88.11', upper: '94.04', coverage: '0.95' }, breakdown: FULL_BREAKDOWN },
          },
          files: [],
          submitted_at: '2026-11-28T00:00:00Z',
        },
      ],
      decisions: [],
      rounds: [],
      allowed_actions: [],
    };
    render(<WorkspaceView me={makeMe({ persona: 'mitra' })} pitch={pitch} tab="ringkasan" files={[]} justSent={false} room={room} />);
    expect(screen.getByRole('heading', { name: 'Kecocokan dengan mandat Anda' })).toBeInTheDocument();
    expect(screen.getByText('Kecocokan kuat')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Rincian kecocokan' })).toBeInTheDocument();
  });

  it('is axe clean', async () => {
    expect(await axeViolations(<ScoreBreakdown dimensions={FULL_BREAKDOWN} />)).toEqual([]);
  });
});
