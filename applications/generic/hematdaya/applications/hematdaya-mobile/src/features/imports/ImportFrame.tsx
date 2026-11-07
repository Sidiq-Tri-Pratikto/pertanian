import { useRouter } from 'expo-router';
import { useCallback, useRef, type ComponentRef, type ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';

import { HDScreen } from '@/components/hd/HDScreen';
import { tokens } from '@/design/tokens.generated';
import { useTabNavigation, type ImportStep } from '@/features/navigation';

export const IMPORT_TITLE = 'Impor data CSV';

const SUBTITLES: Record<ImportStep, string> = {
  berkas: 'Langkah 1 dari 4 · Berkas',
  pemetaan: 'Langkah 2 dari 4 · Arti kolom dan pemetaan',
  pratinjau: 'Langkah 3 dari 4 · Pratinjau',
  hasil: 'Langkah 4 dari 4 · Hasil',
};

const PREVIOUS: Record<ImportStep, ImportStep | null> = { berkas: null, pemetaan: 'berkas', pratinjau: 'pemetaan', hasil: null };

/** Scroll and content refs for one step, and `reveal`, which brings a focus target into view on native. */
export function useImportFrame() {
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const contentRef = useRef<ComponentRef<typeof View>>(null);
  const reveal = useCallback((node: unknown) => {
    const target = node as { measureLayout?: (relativeTo: unknown, onSuccess: (x: number, y: number) => void, onFail: () => void) => void } | null;
    if (Platform.OS !== 'web' && target?.measureLayout && contentRef.current) {
      // The web scrolls a focused element into view itself; native needs the scroll view moved first.
      target.measureLayout(
        contentRef.current,
        (_x, y) => scrollRef.current?.scrollTo({ y: Math.max(y - tokens.space.pageGutter, 0), animated: false }),
        () => undefined,
      );
    }
    return node;
  }, []);
  // Focus targets by key, for error summary links. Plain holders, so a step never reads a ref while rendering.
  const targets = useRef(new Map<string, { current: unknown }>());
  const refFor = useCallback((key: string) => {
    let holder = targets.current.get(key);
    if (!holder) {
      holder = { current: null };
      targets.current.set(key, holder);
    }
    return holder;
  }, []);
  /** Brings a registered target into view and returns it, for `moveFocus`. */
  const revealTarget = useCallback((key: string) => reveal(targets.current.get(key)?.current ?? null), [reveal]);
  return { scrollRef, contentRef, reveal, refFor, revealTarget };
}

type ImportFrameProps = {
  step: ImportStep;
  footer?: ReactNode;
  children: ReactNode;
  frame: ReturnType<typeof useImportFrame>;
};

/**
 * One import step: the same heading on every step, the step as its subtitle, and back as one step back. The
 * primary action sits in the footer, outside the scroll view, and the screen avoids the keyboard (027 D34).
 */
export function ImportFrame({ step, footer, children, frame }: ImportFrameProps) {
  const router = useRouter();
  const { back, replaceImportStep } = useTabNavigation();
  const previous = PREVIOUS[step];
  const onBack = () => {
    if (step === 'hasil' || step === 'berkas' || router.canGoBack()) {
      back();
    } else if (previous) {
      replaceImportStep(previous);
    }
  };
  return (
    <KeyboardAvoidingView testID="import-keyboard-avoiding" behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.fill}>
      <HDScreen title={IMPORT_TITLE} subtitle={SUBTITLES[step]} onBack={onBack} footer={footer} scrollRef={frame.scrollRef} contentRef={frame.contentRef}>
        {children}
      </HDScreen>
    </KeyboardAvoidingView>
  );
}


const styles = StyleSheet.create({ fill: { flex: 1 } });
