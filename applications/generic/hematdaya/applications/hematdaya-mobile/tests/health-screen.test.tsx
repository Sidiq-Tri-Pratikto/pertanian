import { fireEvent, render, screen } from '@testing-library/react-native';

import HealthScreen from '@/app/index';

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

describe('HealthScreen', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('shows the service status', async () => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(respond(200, { status: 'ok' }));

    await render(<HealthScreen />);

    expect(await screen.findByText('Service status: ok')).toBeOnTheScreen();
  });

  it('shows the envelope message and reference without a retry when not retryable', async () => {
    jest
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        respond(500, {
          error: { code: 'INTERNAL_ERROR', message: 'Something failed.', request_id: 'ref_1', recovery: { retryable: false } },
        }),
      );

    await render(<HealthScreen />);

    expect(await screen.findByText('Something failed.')).toBeOnTheScreen();
    expect(screen.getByText('Reference: ref_1')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Try again' })).toBeNull();
  });

  it('offers a retry when the service is unreachable, and the retry recovers', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Network request failed'));

    await render(<HealthScreen />);
    const retry = await screen.findByRole('button', { name: 'Try again' });

    fetchMock.mockResolvedValue(respond(200, { status: 'ok' }));
    await fireEvent.press(retry);

    expect(await screen.findByText('Service status: ok')).toBeOnTheScreen();
  });
});
