import { act, fireEvent, render, screen, within } from '@testing-library/react-native';
import { useState, type ComponentProps } from 'react';
import { AccessibilityInfo, Platform, StyleSheet } from 'react-native';

import type { ImportPreview } from '@/api/client';

import { HDAssetRow } from '@/components/hd/HDAssetRow';
import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDContributionRanking } from '@/components/hd/HDContributionRanking';
import { HDErrorSummary } from '@/components/hd/HDErrorSummary';
import { HDImportPreview } from '@/components/hd/HDImportPreview';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProvenanceTag } from '@/components/hd/HDProvenanceTag';
import { HDTextField } from '@/components/hd/HDTextField';
import { tokens } from '@/design/tokens.generated';

import recordedImports from './fixtures/imports.json';

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

describe('HDTextField', () => {
  it('labels the input, shows help and the draft note, and marks it optional', async () => {
    const onChange = jest.fn();
    await render(
      <HDTextField label="Atau tempel isi CSV" optional help="Untuk berkas besar, pilih berkas." draftNote="Isi tetap tersimpan bila Anda kembali." value="" onChange={onChange} multiline />,
    );

    const input = screen.getByLabelText('Atau tempel isi CSV');
    expect(screen.getByText('(opsional)')).toBeOnTheScreen();
    expect(screen.getByText('Untuk berkas besar, pilih berkas.')).toBeOnTheScreen();
    expect(screen.getByText('Isi tetap tersimpan bila Anda kembali.')).toBeOnTheScreen();
    expect(input.props.multiline).toBe(true);
    expect(input.props.allowFontScaling).toBeUndefined();
    expect(StyleSheet.flatten(input.props.style).minHeight).toBeGreaterThanOrEqual(tokens.size.targetMinimum);
    await fireEvent.changeText(input, 'timestamp');
    expect(onChange).toHaveBeenCalledWith('timestamp');
  });

  it('shows an error above the input and joins it to the description', async () => {
    await render(<HDTextField label="Panjang interval (menit)" help="Angka bulat." error="Isi panjang interval dalam menit, dengan angka bulat." value="6a" onChange={() => undefined} keyboardType="number-pad" />);

    const input = screen.getByLabelText('Panjang interval (menit)');
    const error = screen.getByText('Isi panjang interval dalam menit, dengan angka bulat.');
    expect(input.props.keyboardType).toBe('number-pad');
    expect(input.props.accessibilityHint).toContain('Isi panjang interval dalam menit, dengan angka bulat.');
    expect(input.props.accessibilityHint).toContain('Angka bulat.');
    expect(StyleSheet.flatten(input.props.style).borderColor).toBe(tokens.component.fieldBorderError);
    // Above the input: the error comes first in the rendered tree.
    const tree = JSON.stringify(screen.toJSON());
    expect(error).toBeOnTheScreen();
    expect(tree.indexOf('"children":["Isi panjang interval dalam menit')).toBeGreaterThan(-1);
    expect(tree.indexOf('"children":["Isi panjang interval dalam menit')).toBeLessThan(tree.indexOf('"type":"TextInput"'));
  });
});

describe('HDChoiceGroup checkbox', () => {
  function Harness({ onChange }: { onChange: (value: string[]) => void }) {
    const [value, setValue] = useState<string[]>([]);
    return (
      <HDChoiceGroup
        type="checkbox"
        legend="Konfirmasi"
        required
        error="Centang konfirmasi."
        options={[{ value: 'ack', label: 'Saya setuju' }]}
        value={value}
        onChange={(next) => {
          setValue(next);
          onChange(next);
        }}
      />
    );
  }

  it('reports the new list of ticked options, with the state and error shown', async () => {
    const onChange = jest.fn();
    await render(<Harness onChange={onChange} />);

    expect(screen.getByText('Centang konfirmasi.')).toBeOnTheScreen();
    expect(screen.getByText('(wajib)')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Saya setuju', checked: false }));
    expect(onChange).toHaveBeenLastCalledWith(['ack']);
    expect(screen.getByRole('checkbox', { name: 'Saya setuju', checked: true })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Saya setuju' }));
    expect(onChange).toHaveBeenLastCalledWith([]);
    expect(screen.queryByRole('radio')).toBeNull();
  });

  it('checks an option with Space on the web', async () => {
    const platform = Platform.OS;
    Platform.OS = 'web';
    try {
      const onChange = jest.fn();
      const preventDefault = jest.fn();
      await render(<Harness onChange={onChange} />);
      const option = screen.getByRole('checkbox', { name: 'Saya setuju' });

      await fireEvent(option, 'keyDown', { key: ' ', repeat: false, preventDefault });
      await fireEvent(option, 'keyDown', { key: ' ', repeat: true, preventDefault });

      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(['ack']);
      expect(preventDefault).toHaveBeenCalledTimes(2);
    } finally {
      Platform.OS = platform;
    }
  });

  it('keeps the radio form for a single choice', async () => {
    await render(<HDChoiceGroup legend="Konteks" options={[{ value: 'a', label: 'Satu' }]} value="a" onChange={() => undefined} error="Pilih satu." />);

    expect(screen.getByRole('radio', { name: 'Satu', checked: true })).toBeOnTheScreen();
    expect(screen.getByText('Pilih satu.')).toBeOnTheScreen();
  });
});

describe('HDErrorSummary', () => {
  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  const target = { name: 'checkbox' };
  const errors = [
    { key: 'a', text: 'Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor.', target: () => target },
    { key: 'b', text: 'Pilih jenis nilai.', target: () => null },
  ];

  it('renders nothing with no errors', async () => {
    await render(<HDErrorSummary errors={[]} submitCount={1} />);

    expect(screen.queryByText(/Periksa/)).toBeNull();
  });

  it('is an alert with one link per error, each moving focus to its target', async () => {
    const focus = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
    focus.mockClear();
    await render(<HDErrorSummary errors={errors} submitCount={0} convention="Nomor baris data tidak menghitung header." />);

    // A plain View with a role is not an accessibility element, so React Native Testing Library finds it by label.
    expect(screen.getByLabelText('Periksa 2 hal berikut').props.role).toBe('alert');
    expect(screen.getByText('Periksa 2 hal berikut')).toBeOnTheScreen();
    expect(screen.getByText('Nomor baris data tidak menghitung header.')).toBeOnTheScreen();
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    for (const link of links) {
      expect(StyleSheet.flatten(link.props.style).minHeight).toBeGreaterThanOrEqual(tokens.size.targetMinimum);
    }
    await fireEvent.press(screen.getByRole('link', { name: errors[0].text }));
    expect(focus).toHaveBeenCalledWith(target, 'focus');
  });

  it('follows a link with Enter on the web, where a role="link" element gets no press from the keyboard', async () => {
    const realOS = Platform.OS;
    Platform.OS = 'web';
    const target = { focus: jest.fn() };
    try {
      await render(<HDErrorSummary errors={[{ key: 'a', text: 'Pilih jenis nilai.', target: () => target }]} submitCount={0} />);
      await fireEvent(screen.getByRole('link', { name: 'Pilih jenis nilai.' }), 'keyDown', { key: 'Enter', preventDefault: () => undefined });
      expect(target.focus).toHaveBeenCalledTimes(1);
    } finally {
      Platform.OS = realOS;
    }
  });

  it('uses a given title', async () => {
    await render(<HDErrorSummary errors={errors} submitCount={0} title="Baris bermasalah dalam berkas" />);

    expect(screen.getByText('Baris bermasalah dalam berkas')).toBeOnTheScreen();
  });

  it('takes focus after each submit that produced errors, and never before one', async () => {
    jest.useFakeTimers();
    const focus = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
    focus.mockClear();
    const view = await render(<HDErrorSummary errors={errors} submitCount={0} />);
    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(focus).not.toHaveBeenCalled();

    await view.rerender(<HDErrorSummary errors={errors} submitCount={1} />);
    expect(focus).not.toHaveBeenCalled();
    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(focus).toHaveBeenCalledTimes(1);

    await view.rerender(<HDErrorSummary errors={errors} submitCount={2} />);
    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(focus).toHaveBeenCalledTimes(2);
  });

  it('takes focus when it first appears with a submit behind it', async () => {
    jest.useFakeTimers();
    const focus = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
    focus.mockClear();
    await render(<HDErrorSummary errors={errors} submitCount={1} />);
    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });

    expect(focus).toHaveBeenCalledTimes(1);
  });
});

describe('HDImportPreview', () => {
  const Recorded = recordedImports as unknown as Record<string, { answered: ImportPreview }> & { reimport: { answered: ImportPreview }; streams_101: ImportPreview };

  function show(preview: ImportPreview, extra: Partial<ComponentProps<typeof HDImportPreview>> = {}) {
    return render(
      <HDImportPreview
        fileName={preview.file_name}
        period={preview.period}
        counts={preview}
        blockReasons={preview.block_reasons}
        needsAcknowledgment={preview.needs_acknowledgment}
        acknowledged={false}
        onAcknowledge={() => undefined}
        ackError={null}
        ackLocked={false}
        assumptions={preview.assumptions}
        notes={[]}
        mapping={['tempelan.csv · 10 baris data']}
        errors={preview.errors}
        loadingMore={false}
        {...extra}
      />,
    );
  }

  it('shows every count as sent, the rows to be stored, the checkbox and each row with its file line', async () => {
    const preview = Recorded.two.answered;
    await show(preview);

    for (const [label, value] of [
      ['Baris data', '10'],
      ['Diterima', '8'],
      ['Tidak valid', '2'],
      ['Duplikat (dihitung sekali)', '0'],
      ['Nilai berbeda', '0'],
    ]) {
      expect(screen.getByLabelText(`${label}: ${value}`)).toBeOnTheScreen();
    }
    expect(screen.queryByText('Menunggu pemetaan')).toBeNull();
    expect(screen.getByText('8 baris akan disimpan.')).toBeOnTheScreen();
    expect(screen.getByText('Periode data: 20 Oktober 2026 · Asia/Jakarta')).toBeOnTheScreen();
    expect(screen.getByRole('checkbox', { name: 'Saya setuju 2 baris tidak valid dilewati dan tidak diimpor.' })).toBeOnTheScreen();
    expect(screen.getByText('Baris data 4, energi_wh: "dua" bukan angka. (baris berkas 5)')).toBeOnTheScreen();
    expect(screen.getByText('Baris data 7, energi_wh: gunakan angka 0 atau lebih. (baris berkas 8)')).toBeOnTheScreen();
    expect(
      screen.getByText('Nomor baris data tidak menghitung header dan baris kosong. Baris berkas adalah nomor baris pada berkas, termasuk header.'),
    ).toBeOnTheScreen();
    for (const assumption of preview.assumptions) {
      expect(screen.getByText(assumption)).toBeOnTheScreen();
    }
    expect(screen.queryByText(/%/)).toBeNull();
  });

  it('reports a tick, shows its error and locks it on request', async () => {
    const onAcknowledge = jest.fn();
    const view = await show(Recorded.two.answered, { onAcknowledge, ackError: 'Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor.' });

    expect(screen.getByText('Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor.')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('checkbox'));
    expect(onAcknowledge).toHaveBeenCalledWith(true);

    onAcknowledge.mockClear();
    await view.rerender(
      <HDImportPreview
        fileName="x"
        period={null}
        counts={Recorded.two.answered}
        blockReasons={[]}
        needsAcknowledgment
        acknowledged
        onAcknowledge={onAcknowledge}
        ackError={null}
        ackLocked
        assumptions={[]}
        notes={[]}
        mapping={[]}
        errors={[]}
        loadingMore={false}
      />,
    );
    await fireEvent.press(screen.getByRole('checkbox'));
    expect(onAcknowledge).not.toHaveBeenCalled();
    expect(screen.getByRole('checkbox')).toBeDisabled();
  });

  it('shows the service reasons of a blocked preview verbatim', async () => {
    await show(Recorded.three.answered);

    expect(screen.getByText('Impor diblokir')).toBeOnTheScreen();
    expect(screen.getByText('Impor diblokir: 3 dari 10 baris tidak valid.')).toBeOnTheScreen();
    expect(screen.queryByText(/baris akan disimpan/)).toBeNull();
  });

  it('shows the 100-stream reason verbatim', async () => {
    await show(Recorded.streams_101);

    expect(screen.getByText(Recorded.streams_101.block_reasons[0])).toBeOnTheScreen();
  });

  it('says no row is new on a reimport, and shows pending rows only when there are some', async () => {
    const view = await show(Recorded.reimport.answered);

    expect(screen.getByText('Tidak ada baris baru; 12 baris sama dengan data tersimpan.')).toBeOnTheScreen();

    await view.rerender(<></>);
    await show({ ...Recorded.valid.answered, pending_rows: 3 });
    expect(screen.getByLabelText('Menunggu pemetaan: 3')).toBeOnTheScreen();
  });

  it('loads more rows on request', async () => {
    const onMoreErrors = jest.fn();
    const view = await show(Recorded.two.answered, { onMoreErrors });

    await fireEvent.press(screen.getByRole('button', { name: 'Muat 50 baris berikutnya' }));
    expect(onMoreErrors).toHaveBeenCalledTimes(1);

    await view.rerender(<></>);
    await show(Recorded.two.answered, { onMoreErrors, loadingMore: true });
    expect(screen.getByRole('button', { name: 'Memuat baris…' })).toBeOnTheScreen();
  });
});

describe('HDProvenanceTag', () => {
  it('names imported data, both kinds together, and nothing without origins', async () => {
    const view = await render(<HDProvenanceTag origins={['import']} />);
    expect(screen.getByText('Data historis · Impor CSV')).toBeOnTheScreen();
    expect(screen.queryByText('Demo · Data simulasi')).toBeNull();

    await view.rerender(<HDProvenanceTag origins={['import', 'simulated']} />);
    expect(screen.getByText('Data historis · Impor CSV')).toBeOnTheScreen();
    expect(screen.getByText('Demo · Data simulasi')).toBeOnTheScreen();

    await view.rerender(<HDProvenanceTag origins={[]} />);
    expect(screen.queryByText(/Data/)).toBeNull();
  });
});
