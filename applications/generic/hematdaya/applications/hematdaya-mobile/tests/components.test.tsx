import { fireEvent, render, screen } from '@testing-library/react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
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
