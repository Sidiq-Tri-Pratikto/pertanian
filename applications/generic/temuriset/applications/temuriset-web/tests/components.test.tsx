import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Button } from '@/components/tr/Button';
import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { EmptyState } from '@/components/tr/EmptyState';
import { NextStep } from '@/components/tr/NextStep';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';

describe('TR component ports', () => {
  it('Status carries meaning in words and announces when live', () => {
    render(<Status tone="warning" label="Belum diketahui" live="alert" />);

    expect(screen.getByRole('alert')).toHaveTextContent('Belum diketahui');
  });

  it('Status with a body renders a notice', () => {
    render(
      <Status tone="success" label="Tersimpan" icon={null}>
        <p>Isian Anda aman.</p>
      </Status>,
    );

    expect(screen.getByText('Isian Anda aman.')).toBeInTheDocument();
    expect(document.querySelector('.tr-notice--success svg')).toBeNull();
  });

  it('NextStep names whose turn it is', () => {
    render(<NextStep who="other" title="Menunggu keputusan mitra" />);

    expect(screen.getByRole('region', { name: 'Menunggu keputusan mitra' })).toHaveTextContent('Menunggu pihak lain');
  });

  it('EmptyState offers the next step', () => {
    render(
      <EmptyState icon="bulb" title="Belum ada inovasi" action={<a href="/x">Tambah</a>}>
        Mulai dari sini.
      </EmptyState>,
    );

    expect(screen.getByRole('heading', { name: 'Belum ada inovasi' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Tambah' })).toBeInTheDocument();
  });

  it('Button keeps a blocked control focusable, explains why, and ignores the click', async () => {
    const onClick = vi.fn();
    render(
      <Button intent="primary" disabledReason="Pilih satu waktu terlebih dahulu." onClick={onClick}>
        Konfirmasi waktu
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Konfirmasi waktu' });
    await userEvent.click(button);

    expect(onClick).not.toHaveBeenCalled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(button).toHaveAccessibleDescription('Pilih satu waktu terlebih dahulu.');
  });

  it('Button shows the busy label and ignores repeat clicks', async () => {
    const onClick = vi.fn();
    render(
      <Button busy busyLabel="Mengirim…" onClick={onClick}>
        Kirim pitching
      </Button>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Mengirim…' }));

    expect(onClick).not.toHaveBeenCalled();
  });

  it('Button runs its action when allowed', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Coba lagi</Button>);

    await userEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(onClick).toHaveBeenCalledOnce();
  });

  it('ChoiceGroup labels every option and keeps the hint linked', () => {
    render(
      <ChoiceGroup
        legend="Pilih"
        name="persona"
        hint="Hanya mengatur menu."
        required
        defaultValue="mitra"
        options={[
          { value: 'inovator', label: 'Inovator' },
          { value: 'mitra', label: 'Investor/Mitra', hint: 'Memberi dukungan' },
        ]}
      />,
    );

    expect(screen.getByRole('radio', { name: /Investor\/Mitra/ })).toBeChecked();
    // jsdom drops the space before "(wajib)" when computing the name; browsers keep it.
    expect(screen.getByRole('group', { name: /^Pilih/ })).toHaveAccessibleDescription('Hanya mengatur menu.');
  });

  it('Screen marks the current destination and opens Lainnya', async () => {
    render(
      <Screen persona="inovator" current="pitching" title="Pitching dan Diskusi" provenance="Versi awal">
        <p>Isi</p>
      </Screen>,
    );

    const current = screen.getAllByRole('link', { current: 'page' });
    expect(current.map((link) => link.getAttribute('href'))).toEqual(['/pitches', '/pitches']);
    expect(screen.getByRole('heading', { level: 1, name: 'Pitching dan Diskusi' })).toBeInTheDocument();

    const more = screen.getByRole('button', { name: 'Lainnya' });
    await userEvent.click(more);

    expect(more).toHaveAttribute('aria-expanded', 'true');
    expect(document.querySelector('.tr-tabbar__more a')).toHaveAttribute('href', '/settings');
  });

  it('Screen skip link moves focus to the main region', async () => {
    render(<Screen persona="mitra" title="Jelajahi" />);

    await userEvent.click(screen.getByRole('link', { name: 'Langsung ke isi utama' }));

    expect(document.activeElement).toBe(screen.getByRole('main'));
  });
});
