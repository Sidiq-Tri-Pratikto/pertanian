import { useEffect, useRef, type ComponentRef, type ReactNode, type RefObject } from 'react';
import { Modal, Pressable, StyleSheet, View, type TextInstance } from 'react-native';

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
  /** The control that opened the sheet; focus returns to it on close. */
  returnFocusTo?: RefObject<ComponentRef<typeof View> | null>;
};

// Web only: receives programmatic focus without joining the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/** Non-destructive sheet on RN `Modal`: focus to the title on open, Escape or back closes, focus returns to the opener. */
export function HDSheetDialog({ open, title, onClose, children, footer, returnFocusTo }: HDSheetDialogProps) {
  const heading = useRef<TextInstance>(null);
  const wasOpen = useRef(open);

  useEffect(() => {
    if (wasOpen.current && !open) {
      moveFocus(returnFocusTo?.current);
    }
    wasOpen.current = open;
  }, [open, returnFocusTo]);

  return (
    <Modal visible={open} transparent animationType="slide" onRequestClose={() => onClose('escape')} onShow={() => moveFocus(heading.current)}>
      <View style={styles.root}>
        <Pressable accessibilityLabel="Tutup" style={StyleSheet.absoluteFill} onPress={() => onClose('backdrop')} />
        <View role="dialog" aria-modal aria-label={title} style={styles.sheet}>
          <View style={styles.header}>
            <HDText ref={heading} variant="section" role="heading" style={styles.title} {...FOCUSABLE_BY_SCRIPT}>
              {title}
            </HDText>
            <HDButton variant="text" onPress={() => onClose('close')}>
              Tutup
            </HDButton>
          </View>
          <View style={styles.body}>{children}</View>
          {footer ? <View style={styles.footer}>{footer}</View> : null}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: 'flex-end', alignItems: 'center', backgroundColor: tokens.color.overlayBackdrop },
  sheet: {
    width: '100%',
    maxWidth: tokens.size.sheetMaxWidth,
    backgroundColor: tokens.color.backgroundSurface,
    borderTopLeftRadius: tokens.radius.sheet,
    borderTopRightRadius: tokens.radius.sheet,
    padding: tokens.space.pageGutter,
    gap: tokens.space.stack,
  },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tokens.space.stackTight },
  title: { flexShrink: 1 },
  body: { gap: tokens.space.stack },
  footer: { gap: tokens.space.stackTight },
});
