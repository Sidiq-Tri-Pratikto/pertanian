import { HDNotice } from '@/components/hd/HDNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Explains, once, that a stored workspace no longer works. Never shows a raw code. */
export function SessionEndedNotice() {
  const { ended, storageError } = useWorkspace();
  return (
    <>
      {ended === 'expired' ? (
        <HDNotice tone="attention" title="Sesi demo sudah berakhir" live>
          Pilih Coba demo untuk membuka sesi baru, atau lanjutkan dari Beranda.
        </HDNotice>
      ) : null}
      {storageError ? (
        <HDNotice tone="attention" title="Penyimpanan perangkat belum dapat diperbarui" live>
          Penyimpanan atau penghapusan data belum terkonfirmasi. Periksa penyimpanan perangkat lalu coba lagi.
        </HDNotice>
      ) : null}
    </>
  );
}
