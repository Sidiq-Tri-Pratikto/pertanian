import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { FeedbackStatus } from '@/features/insights/FeedbackStatus';
import { useFeedback } from '@/features/insights/useFeedback';
import { useNavigationContext, type HiddenItem } from '@/features/navigation-context/NavigationContextProvider';

/** Shown where the user returns after hiding an observation, with an immediate way back. */
export function RestoreNotice({ timezone }: { timezone: string }) {
  const { recentlyHidden } = useNavigationContext();
  return recentlyHidden ? <Restore key={recentlyHidden.id} item={recentlyHidden} timezone={timezone} /> : null;
}

function Restore({ item, timezone }: { item: HiddenItem; timezone: string }) {
  const restore = useFeedback(item.id, item.revision);
  return (
    <>
      <HDNotice
        tone="success"
        live
        title="Saran disembunyikan"
        action={
          <HDButton variant="text" loading={restore.state.kind === 'pending'} loadingLabel="Memulihkan…" onPress={() => void restore.give('restore')}>
            Pulihkan
          </HDButton>
        }>
        {`${item.title} tidak lagi tampil di daftar. Data dan perangkat tidak berubah.`}
      </HDNotice>
      <FeedbackStatus state={restore.state} timezone={timezone} onRetry={() => void restore.retry()} />
    </>
  );
}
