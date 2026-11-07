import { useRouter, useSegments, type Href } from 'expo-router';

/** Link helpers that keep a detail screen inside the current tab, so back returns to where the user was. */
export function useTabNavigation() {
  const router = useRouter();
  const segments = useSegments() as string[];
  const group = segments.find((segment) => /^\((beranda|perangkat|saran)\)$/.test(segment)) ?? '(beranda)';
  const inTab = (path: string) => `/(tabs)/${group}/${path}` as Href;

  return {
    openFeature: (id: string) => router.push(inTab(`segera-hadir/${id}`)),
    openSettings: () => router.push(inTab('pengaturan')),
    openHidden: () => router.push(inTab('saran/tersembunyi')),
    openEvidence: (id: string, revision: number) =>
      router.push(inTab(`saran/${encodeURIComponent(id)}?revision=${revision}`)),
    openAsset: (id: string) => router.push(inTab(`asset/${encodeURIComponent(id)}`)),
    back: () => (router.canGoBack() ? router.back() : router.replace('/beranda')),
  };
}
