import { useCopy } from '@/features/localization/messages';
import { useContext, useEffect, useRef, type ComponentRef, type ReactNode, type RefObject } from 'react';
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, View, type TextInstance } from 'react-native';
import { SafeAreaInsetsContext } from 'react-native-safe-area-context';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { moveFocus } from '@/lib/focus';

type CloseReason = 'close' | 'escape' | 'backdrop';

type HDSheetDialogProps = {
  open: boolean;
  title: string;
  onClose: (reason: CloseReason) => void;
  children: ReactNode;
  footer?: ReactNode;
  scrollable?: boolean;
  /** The control that opened the sheet; focus returns to it on close. */
  returnFocusTo?: RefObject<ComponentRef<typeof View> | null>;
};

// Web only: receives programmatic focus without joining the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/** Non-destructive sheet on RN `Modal`: focus to the title on open, Escape or back closes, focus returns to the opener. */
export function HDSheetDialog({ open, title, onClose, children, footer, returnFocusTo, scrollable = false }: HDSheetDialogProps) {
  const say = useCopy();
  const heading = useRef<TextInstance>(null);
  const wasOpen = useRef(open);
  const web = Platform.OS === 'web';
  const insets = useContext(SafeAreaInsetsContext);
  // Android's edge-to-edge Modal can extend beneath the system navigation buttons.
  const bottomInset = Platform.OS === 'android' ? (insets?.bottom ?? 0) : 0;
  const sheetStyle = bottomInset ? [styles.sheet, { paddingBottom: tokens.space.pageGutter + bottomInset }] : styles.sheet;
  const modalLabel = web ? { 'aria-label': title } : {};
  const nativeDialog = web ? {} : { role: 'dialog' as const, 'aria-modal': true, 'aria-label': title };

  useEffect(() => {
    if (!web && wasOpen.current && !open) {
      moveFocus(returnFocusTo?.current);
    }
    wasOpen.current = open;
  }, [open, returnFocusTo, web]);

  const returnWebFocus = web ? () => {
    requestAnimationFrame(() => {
      if (!wasOpen.current) moveFocus(returnFocusTo?.current);
    });
  } : undefined;

  return (
    <Modal {...modalLabel} visible={open} transparent animationType="slide" onDismiss={returnWebFocus} onRequestClose={() => onClose('escape')} onShow={() => moveFocus(heading.current)}>
      <KeyboardAvoidingView style={styles.root} behavior={scrollable && Platform.OS === 'ios' ? 'padding' : undefined}>
        <Pressable accessibilityLabel={say("Tutup", "Close")} style={StyleSheet.absoluteFill} onPress={() => onClose('backdrop')} />
        <View {...nativeDialog} style={sheetStyle}>
          <View style={styles.header}>
            <HDText ref={heading} variant="section" role="heading" style={styles.title} {...FOCUSABLE_BY_SCRIPT}>
              {title}
            </HDText>
            <HDButton variant="text" onPress={() => onClose('close')}>{say("Tutup", "Close")}</HDButton>
          </View>
          {scrollable ? (
            <ScrollView style={styles.scrollBody} contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
              {children}
            </ScrollView>
          ) : <View style={styles.body}>{children}</View>}
          {footer ? <View style={styles.footer}>{footer}</View> : null}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: 'flex-end', alignItems: 'center', backgroundColor: tokens.color.overlayBackdrop },
  sheet: {
    width: '100%',
    maxHeight: '100%',
    maxWidth: tokens.size.sheetMaxWidth,
    backgroundColor: tokens.color.backgroundSurface,
    borderTopLeftRadius: tokens.radius.sheet,
    borderTopRightRadius: tokens.radius.sheet,
    padding: tokens.space.pageGutter,
    gap: tokens.space.stack,
  },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tokens.space.stackTight },
  title: { flexShrink: 1 },
  scrollBody: { flexGrow: 0, flexShrink: 1 },
  body: { gap: tokens.space.stack },
  footer: { gap: tokens.space.stackTight },
});
