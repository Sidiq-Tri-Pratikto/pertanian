import { useState, type ComponentRef, type RefObject } from 'react';
import type { View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { HDText } from '@/components/hd/HDText';
import { useContextPreset } from '@/features/context-preset';
import { useDemoSession } from '@/features/workspace/useDemoSession';

type DemoChoice = 'h-base' | 'i-base';

const CHOICES: { value: DemoChoice; label: string; description: string }[] = [
  { value: 'h-base', label: 'Rumah tangga', description: 'Kulkas, Router, Pompa Air dan TV. Tanpa AC, jadwal atau data produksi.' },
  { value: 'i-base', label: 'Industri', description: 'Oven, Kompresor, Mesin Press dan Lampu Area. Jadwal dan output tetap opsional.' },
];

type DemoSheetProps = {
  open: boolean;
  onClose: () => void;
  onOpened: () => void;
  returnFocusTo: RefObject<ComponentRef<typeof View> | null>;
};

/** Pick a simulated workspace and open it: no text entry, failure keeps the sheet open with a retry. */
export function DemoSheet({ open, onClose, onOpened, returnFocusTo }: DemoSheetProps) {
  const { preset } = useContextPreset();
  const [choice, setChoice] = useState<DemoChoice | null>(null);
  const selected = choice ?? (preset === 'industry' || preset === 'business' ? 'i-base' : 'h-base');
  const { state, start, retry, startOver, reset } = useDemoSession();
  const pending = state.kind === 'pending';

  const close = () => {
    if (pending) {
      return;
    }
    reset();
    onClose();
  };
  const run = async (action: () => Promise<boolean>) => {
    if (await action()) {
      onOpened();
    }
  };

  return (
    <HDSheetDialog
      open={open}
      title="Pilih data demo"
      onClose={close}
      returnFocusTo={returnFocusTo}
      footer={
        <>
          <HDButton
            variant="primary"
            fullWidth
            loading={pending}
            loadingLabel="Menyiapkan data demo…"
            onPress={() => run(() => start(selected))}>
            Buka demo
          </HDButton>
          <HDButton variant="text" fullWidth onPress={close}>
            Batal
          </HDButton>
        </>
      }>
      <HDChoiceGroup legend="Data simulasi" options={CHOICES} value={selected} onChange={setChoice} />
      <HDText variant="label" tone="secondary">
        Demo · Data simulasi. Terpisah dari data Anda dan berakhir otomatis; reset hanya memengaruhi demo.
      </HDText>
      <HDProgressStatus
        state={pending ? 'loading' : (state.kind === 'failed' || state.kind === 'unsent') ? 'failure' : state.kind === 'unknown' ? 'unknown' : null}
        label={pending ? 'Menyiapkan data demo…' : state.kind === 'unknown' ? 'Hasil permintaan sebelumnya belum diketahui' : state.kind === 'unsent' ? 'Permintaan demo belum dikirim' : undefined}
        detail={state.kind === 'failed' || state.kind === 'unsent' || state.kind === 'unknown'
          ? `${state.error.message}${state.kind === 'unknown' && state.unsent ? ' Pemeriksaan belum dikirim. Sambungkan perangkat lalu coba lagi.' : ''}`
          : null}
        action={
          state.kind === 'failed' && state.canRetry ? (
            <HDButton variant="text" icon="refresh" onPress={() => run(retry)}>
              Coba lagi
            </HDButton>
          ) : state.kind === 'unknown' ? (
            <HDButton variant="text" onPress={() => run(() => startOver(selected))}>
              Mulai demo baru
            </HDButton>
          ) : null
        }
      />
    </HDSheetDialog>
  );
}
