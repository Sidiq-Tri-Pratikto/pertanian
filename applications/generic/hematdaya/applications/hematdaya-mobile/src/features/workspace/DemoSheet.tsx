import { errorMessage } from '@/features/localization/error-copy';
import { useCopy } from '@/features/localization/messages';
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

type DemoSheetProps = {
  open: boolean;
  onClose: () => void;
  onOpened: () => void;
  returnFocusTo: RefObject<ComponentRef<typeof View> | null>;
};

/** Pick a simulated workspace and open it: no text entry, failure keeps the sheet open with a retry. */
export function DemoSheet({ open, onClose, onOpened, returnFocusTo }: DemoSheetProps) {
  const say = useCopy();
  const choices = [
    { value: 'h-base' as const, label: say('Rumah tangga', 'Household'),
      description: say('Kulkas, Router, Pompa Air dan TV. Tanpa AC, jadwal atau data produksi.',
        'Explore readings from Kulkas, Router, Pompa Air and TV.') },
    { value: 'i-base' as const, label: say('Industri', 'Industrial'),
      description: say('Oven, Kompresor, Mesin Press dan Lampu Area. Jadwal dan output tetap opsional.',
        'Explore readings from Oven, Kompresor, Mesin Press and Lampu Area.') },
  ];
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
      title={say("Pilih data demo", "Choose demo data")}
      onClose={close}
      returnFocusTo={returnFocusTo}
      footer={
        <>
          <HDButton
            variant="primary"
            fullWidth
            loading={pending}
            loadingLabel={say("Menyiapkan data demo…", "Setting up demo data…")}
            onPress={() => run(() => start(selected))}>{say("Buka demo", "Open demo")}</HDButton>
          <HDButton variant="text" fullWidth onPress={close}>{say("Batal", "Cancel")}</HDButton>
        </>
      }>
      <HDChoiceGroup legend={say("Data simulasi", "Simulated data")} options={choices} value={selected} onChange={setChoice} />
      <HDText variant="label" tone="secondary">{say("Demo · Data simulasi. Terpisah dari data Anda dan berakhir otomatis; reset hanya memengaruhi demo.", "The demo uses sample data. It expires automatically and keeps your data separate.")}</HDText>
      <HDProgressStatus
        state={pending ? 'loading' : (state.kind === 'failed' || state.kind === 'unsent') ? 'failure' : state.kind === 'unknown' ? 'unknown' : null}
        label={pending ? say("Menyiapkan data demo…", "Setting up demo data…") : state.kind === 'unknown' ? say("Hasil permintaan sebelumnya belum diketahui", "Previous request status unknown") : state.kind === 'unsent' ? say("Permintaan demo belum dikirim", "Demo request not sent") : undefined}
        detail={state.kind === 'failed' || state.kind === 'unsent' || state.kind === 'unknown'
          ? `${errorMessage(state.error)}${state.kind === 'unknown' && state.unsent ? say(" Pemeriksaan belum dikirim. Sambungkan perangkat lalu coba lagi.", " Reconnect and try checking again.") : ''}`
          : null}
        action={
          state.kind === 'failed' && state.canRetry ? (
            <HDButton variant="text" icon="refresh" onPress={() => run(retry)}>{say("Coba lagi", "Try again")}</HDButton>
          ) : state.kind === 'unknown' ? (
            <HDButton variant="text" onPress={() => run(() => startOver(selected))}>{say("Mulai demo baru", "Start a new demo")}</HDButton>
          ) : null
        }
      />
    </HDSheetDialog>
  );
}
