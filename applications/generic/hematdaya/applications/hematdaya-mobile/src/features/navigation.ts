import { useFocusEffect, useRouter, useSegments, type Href } from 'expo-router';

import { useCallback, useRef, type ComponentRef } from 'react';
import type { View } from 'react-native';

import { useOptionalImportDraft } from '@/features/imports/ImportDraftProvider';
import { moveFocus } from '@/lib/focus';

export type ImportStep = 'berkas' | 'pemetaan' | 'pratinjau' | 'hasil';

/** Link helpers that keep a detail screen inside the current tab, so back returns to where the user was. */
export function useTabNavigation() {
  const router = useRouter();
  const segments = useSegments() as string[];
  const group = segments.find((segment) => /^\((beranda|perangkat|saran)\)$/.test(segment)) ?? '(beranda)';
  const inTab = (path: string) => `/(tabs)/${group}/${path}` as Href;
  const draft = useOptionalImportDraft();
  const toTabRoot = () => {
    if (router.canDismiss()) {
      router.dismissAll();
    }
  };

  return {
    openFeature: (id: string) => router.push(inTab(id === 'cakupan-sumber' ? 'cakupan' : `segera-hadir/${id}`)),
    openScope: () => router.push(inTab('cakupan')),
    scopeHref: inTab('cakupan'),
    scopeBack: () => router.canGoBack() ? router.back() : router.replace(inTab(group.slice(1, -1))),
    openSettings: () => router.push(inTab('pengaturan')),
    openHidden: () => router.push(inTab('saran/tersembunyi')),
    openEvidence: (id: string, revision: number) =>
      router.push(inTab(`saran/${encodeURIComponent(id)}?revision=${revision}`)),
    openAssetHistoryChooser: () => router.push(inTab('perangkat/riwayat')),
    openAsset: (id: string) => router.push(inTab(`asset/${encodeURIComponent(id)}`)),
    back: () => (router.canGoBack() ? router.back() : router.replace('/beranda')),
    /** S10 from any entry point. A draft whose result was already shown is done, so a new import starts empty. */
    openImport: () => {
      if (draft?.resultShown) {
        draft.finish();
      }
      router.push(inTab('impor/berkas'));
    },
    importHref: (step: ImportStep) => inTab(`impor/${step}`),
    goImportStep: (step: ImportStep) => router.push(inTab(`impor/${step}`)),
    replaceImportStep: (step: ImportStep) => router.replace(inTab(`impor/${step}`)),
    /** The result replaces the import stack, so back from it never returns to a committed preview (027 D10). */
    showImportResult: () => {
      toTabRoot();
      router.push(inTab('impor/hasil'));
    },
    toTabRoot,
  };
}

/** A returning screen focuses the opener after the shared screen heading has taken focus. */
export function useScopeInvoker() {
  const { openScope } = useTabNavigation();
  const ref = useRef<ComponentRef<typeof View>>(null);
  const returning = useRef(false);
  useFocusEffect(useCallback(() => {
    if (!returning.current) return;
    returning.current = false;
    let focused = true;
    // The heading focuses in the same route event. Restore the opener once those listeners have run.
    void Promise.resolve().then(() => {
      const opener = ref.current;
      if (focused && opener) moveFocus(opener);
    });
    return () => { focused = false; };
  }, []));
  return { ref, onPress: () => { returning.current = true; openScope(); } };
}
