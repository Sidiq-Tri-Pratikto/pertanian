import { useCopy } from '@/features/localization/messages';
import { HDNotice } from '@/components/hd/HDNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Explains, once, that a stored workspace no longer works. Never shows a raw code. */
export function SessionEndedNotice() {
  const say = useCopy();
  const { ended, storageError } = useWorkspace();
  return (
    <>
      {ended === 'expired' ? (
        <HDNotice tone="attention" title={say("Sesi demo sudah berakhir", "Demo session ended")} live>{say("Pilih Coba demo untuk membuka sesi baru, atau lanjutkan dari Beranda.", "Open another demo or keep exploring from Home.")}</HDNotice>
      ) : null}
      {storageError ? (
        <HDNotice tone="attention" title={say("Penyimpanan perangkat belum dapat diperbarui", "Device storage could not be updated")} live>{say("Penyimpanan atau penghapusan data belum terkonfirmasi. Periksa penyimpanan perangkat lalu coba lagi.", "Check your device storage and try again.")}</HDNotice>
      ) : null}
    </>
  );
}
