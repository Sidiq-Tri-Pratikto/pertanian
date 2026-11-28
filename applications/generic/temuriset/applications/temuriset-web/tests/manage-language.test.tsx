import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { ManageView } from '@/views/subscriptions/ManageView';

const { readSubscriptionMock, updateTopicsMock, unsubscribeMock } = vi.hoisted(() => ({
  readSubscriptionMock: vi.fn(),
  updateTopicsMock: vi.fn(),
  unsubscribeMock: vi.fn(),
}));

vi.mock('@/features/subscriptions/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/subscriptions/api')>();
  return {
    ...actual,
    readSubscription: readSubscriptionMock,
    updateTopics: updateTopicsMock,
    unsubscribe: unsubscribeMock,
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('ManageView email language selector (spec 060)', () => {
  it('loads the subscription locale and sends the updated locale on save', async () => {
    const initial = {
      email: 'in***@example.test',
      topics: { sectors: ['Air dan sanitasi'], stages: [], keywords: [] },
      status: 'ACTIVE' as const,
      locale: 'id' as const,
      confirmed_at: '2026-04-01T02:00:00Z',
      manage_token: null,
    };
    readSubscriptionMock.mockResolvedValueOnce(initial);
    updateTopicsMock.mockResolvedValueOnce({ ...initial, locale: 'en' });

    render(
      <LocaleProvider locale="id">
        <ManageView token="manage-token-12345678901234567890" />
      </LocaleProvider>,
    );

    const select = (await screen.findByLabelText('Bahasa email')) as HTMLSelectElement;
    expect(select.value).toBe('id');

    fireEvent.change(select, { target: { value: 'en' } });
    fireEvent.click(screen.getByRole('button', { name: 'Simpan perubahan' }));

    await waitFor(() =>
      expect(updateTopicsMock).toHaveBeenCalledWith(
        'manage-token-12345678901234567890',
        { sectors: ['Air dan sanitasi'], stages: [], keywords: [] },
        'en',
      ),
    );
  });
});
