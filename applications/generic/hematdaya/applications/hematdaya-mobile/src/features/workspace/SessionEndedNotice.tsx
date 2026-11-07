import { HDNotice } from '@/components/hd/HDNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** Explains, once, that a stored workspace no longer works. Never shows a raw code. */
export function SessionEndedNotice() {
  const { ended } = useWorkspace();
  if (ended !== 'expired') {
    return null;
  }
  return (
    <HDNotice tone="attention" title="Sesi demo sudah berakhir" live>
      Data demo sebelumnya tidak dapat dibuka lagi. Mulai sesi demo baru atau ruang kerja kosong untuk melanjutkan.
    </HDNotice>
  );
}
