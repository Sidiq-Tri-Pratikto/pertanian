import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { Toggletip } from '@/components/tr/Toggletip';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';

describe('Toggletip (spec 055)', () => {
  it('opens on click and Enter, announces in role=status, and closes on Escape and outside click', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <div>
        <Toggletip label="TKT" id="tip-tkt">
          Skala kesiapterapan teknologi 1 sampai 9.
        </Toggletip>
        <button type="button">Luar</button>
      </div>,
    );

    const button = screen.getByRole('button', { name: 'Penjelasan: TKT' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Skala kesiapterapan teknologi 1 sampai 9.')).not.toBeInTheDocument();

    // Open via click
    await user.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    const status = screen.getByRole('status');
    expect(status).toHaveTextContent('Skala kesiapterapan teknologi 1 sampai 9.');
    expect(button).toHaveAttribute('aria-controls', status.id);
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);

    // Close via Escape
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Skala kesiapterapan teknologi 1 sampai 9.')).not.toBeInTheDocument();

    // Open via Enter
    button.focus();
    await user.keyboard('{Enter}');
    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('status')).toHaveTextContent('Skala kesiapterapan teknologi 1 sampai 9.');

    // Close via outside click
    await user.click(screen.getByRole('button', { name: 'Luar' }));
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('translates its accessible name in English', () => {
    render(
      <LocaleProvider locale="en">
        <Toggletip label="TKT">Technology readiness scale 1 to 9.</Toggletip>
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: 'Explanation: TKT' })).toBeInTheDocument();
  });
});
