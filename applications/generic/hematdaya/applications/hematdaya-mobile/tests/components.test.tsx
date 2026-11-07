import { fireEvent, render, screen, within } from '@testing-library/react-native';
import type { ComponentProps } from 'react';
import { StyleSheet } from 'react-native';

import { HDAssetRow } from '@/components/hd/HDAssetRow';
import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDContributionRanking } from '@/components/hd/HDContributionRanking';
import { HDNotice } from '@/components/hd/HDNotice';

describe('HDButton', () => {
  it('runs its action', async () => {
    const onPress = jest.fn();

    await render(<HDButton onPress={onPress}>Simpan</HDButton>);
    await fireEvent.press(screen.getByRole('button', { name: 'Simpan' }));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('ignores presses while loading and says what is happening', async () => {
    const onPress = jest.fn();

    await render(
      <HDButton onPress={onPress} loading loadingLabel="Menyimpan…">
        Simpan
      </HDButton>,
    );
    await fireEvent.press(screen.getByRole('button', { name: 'Menyimpan…' }));

    expect(onPress).not.toHaveBeenCalled();
  });

  it('stays visible and explains itself when disabled', async () => {
    const onPress = jest.fn();

    await render(
      <HDButton onPress={onPress} disabledReason="Lengkapi pemetaan terlebih dahulu.">
        Lanjut
      </HDButton>,
    );
    await fireEvent.press(screen.getByRole('button', { name: 'Lanjut' }));

    expect(onPress).not.toHaveBeenCalled();
    expect(screen.getByText('Lengkapi pemetaan terlebih dahulu.')).toBeOnTheScreen();
  });
});

describe('HDChoiceGroup', () => {
  it('reports the chosen option', async () => {
    const onChange = jest.fn();

    await render(
      <HDChoiceGroup
        legend="Konteks"
        options={[
          { value: 'a', label: 'Satu' },
          { value: 'b', label: 'Dua' },
        ]}
        value="a"
        onChange={onChange}
      />,
    );
    await fireEvent.press(screen.getByRole('radio', { name: 'Dua' }));

    expect(onChange).toHaveBeenCalledWith('b');
    expect(screen.getByRole('radio', { name: 'Satu', checked: true })).toBeOnTheScreen();
  });
});

describe('HDNotice', () => {
  it.each([
    ['attention', 'Perhatian'],
    ['error', 'Kesalahan'],
    ['success', 'Berhasil'],
    ['info', 'Info'],
    ['neutral', 'Catatan'],
  ] as const)('names its %s tone in words', async (tone, prefix) => {
    await render(<HDNotice tone={tone} title="Judul" />);

    expect(screen.getByLabelText(`${prefix}: Judul`)).toBeOnTheScreen();
  });
});

describe('HDAssetRow', () => {
  const kulkas: ComponentProps<typeof HDAssetRow> = {
    name: 'Kulkas',
    kind: 'device',
    location: 'Dapur',
    category: 'Pendingin makanan',
    kwh: '8,400 kWh',
    quality: 'complete',
    qualityLabel: 'Kelengkapan data: 100% periode',
    sources: [],
    stale: false,
    onOpen: () => undefined,
  };

  it('is one link with a full name, and shows what it measures', async () => {
    const onOpen = jest.fn();

    await render(<HDAssetRow {...kulkas} onOpen={onOpen} />);
    const row = screen.getByRole('link', {
      name: 'Kulkas, Perangkat, Dapur, Pendingin makanan, 8,400 kWh, Kelengkapan data: 100% periode',
    });

    expect(screen.getByText('Perangkat · Dapur · Pendingin makanan')).toBeOnTheScreen();
    expect(within(row).queryByRole('button')).toBeNull();
    expect(within(row).queryByRole('switch')).toBeNull();
    await fireEvent.press(row);
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it('names a site-total meter', async () => {
    await render(<HDAssetRow {...kulkas} kind="meter" location={null} category={null} />);

    expect(screen.getByText('Meter lokasi')).toBeOnTheScreen();
  });

  it('never shows a missing value as a zero', async () => {
    await render(<HDAssetRow {...kulkas} kwh={null} quality="unavailable" qualityLabel="Data belum tersedia" />);

    expect(screen.getByText('— kWh')).toBeOnTheScreen();
    expect(
      screen.getByRole('link', { name: 'Kulkas, Perangkat, Dapur, Pendingin makanan, nilai belum tersedia, Data belum tersedia' }),
    ).toBeOnTheScreen();
    expect(screen.queryByText(/\b0[,.]?\d* kWh/)).toBeNull();
  });

  it('shows a long name whole', async () => {
    const name = 'Pompa Air Area Produksi Belakang Gedung Selatan Lantai Dua A';

    await render(<HDAssetRow {...kulkas} name={name} />);

    expect(screen.getByText(name).props.numberOfLines).toBeUndefined();
  });

  it('keeps the minimum touch target', async () => {
    await render(<HDAssetRow {...kulkas} />);

    expect(StyleSheet.flatten(screen.getByRole('link').props.style).minHeight).toBeGreaterThanOrEqual(48);
  });

  it('shows unresolved sources and staleness, and names them', async () => {
    await render(
      <HDAssetRow {...kulkas} kwh={null} quality="unavailable" qualityLabel="Lebih dari satu sumber · nilai tidak dijumlahkan" sources={['Sumber A: 1,000 kWh', 'Sumber B: 1,000 kWh']} stale />,
    );

    expect(screen.getByText('Sumber A: 1,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Sumber B: 1,000 kWh')).toBeOnTheScreen();
    expect(screen.getByText('Data belum diperbarui')).toBeOnTheScreen();
    expect(
      screen.getByRole('link', {
        name: 'Kulkas, Perangkat, Dapur, Pendingin makanan, nilai belum tersedia, Lebih dari satu sumber · nilai tidak dijumlahkan, Sumber A: 1,000 kWh, Sumber B: 1,000 kWh, Data belum diperbarui',
      }),
    ).toBeOnTheScreen();
  });
});

describe('HDContributionRanking', () => {
  const item = { assetId: 'a-1', name: 'Kulkas', kwh: '8,400 kWh', share: '57.14', width: 57.14 };

  it('makes each item one link that opens its asset', async () => {
    const onOpen = jest.fn();

    await render(<HDContributionRanking items={[item]} periodLabel="19–25 Oktober 2026" denominatorLabel="1 perangkat" onOpen={onOpen} />);
    const row = screen.getByRole('link', { name: 'Kulkas, 8,400 kWh, 57,14%' });

    expect(StyleSheet.flatten(row.props.style).minHeight).toBeGreaterThanOrEqual(48);
    await fireEvent.press(row);
    expect(onOpen).toHaveBeenCalledWith('a-1');
  });

  it('keeps two assets with one name apart', async () => {
    const onOpen = jest.fn();
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    await render(
      <HDContributionRanking
        items={[item, { ...item, assetId: 'a-2', kwh: '1,000 kWh' }]}
        periodLabel="19–25 Oktober 2026"
        denominatorLabel="2 perangkat"
        onOpen={onOpen}
      />,
    );

    expect(screen.getAllByRole('link')).toHaveLength(2);
    expect(consoleError).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByRole('link', { name: 'Kulkas, 1,000 kWh, 57,14%' }));
    expect(onOpen).toHaveBeenCalledWith('a-2');
    consoleError.mockRestore();
  });

  it('says why a zero total has no percentage', async () => {
    await render(
      <HDContributionRanking items={[{ ...item, kwh: '0,000 kWh', share: null, width: 0 }]} periodLabel="19–25 Oktober 2026" denominatorLabel="1 perangkat" onOpen={() => undefined} />,
    );

    expect(screen.getByRole('link', { name: 'Kulkas, 0,000 kWh' })).toBeOnTheScreen();
    expect(screen.getByText('Total energi nol, sehingga tidak ada persentase kontribusi.')).toBeOnTheScreen();
  });
});
