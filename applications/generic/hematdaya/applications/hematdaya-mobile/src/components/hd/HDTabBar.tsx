import type { ReactNode, Ref } from 'react';
import { Pressable, StyleSheet, View, type GestureResponderEvent, type ViewInstance } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { HDIcon, type HDIconName } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useLabels } from '@/features/localization/messages';

/** The bar. Exactly three destinations are composed in the tabs layout, and no badge implies urgency. */
export function HDTabBar({ children, ...props }: { children?: ReactNode }) {
  const insets = useSafeAreaInsets();
  const { navigation } = useLabels();
  return (
    <View {...props} role="tablist" aria-label={navigation} style={[styles.bar, { paddingBottom: insets.bottom }]}>
      {children}
    </View>
  );
}

type HDTabItemProps = {
  icon: HDIconName;
  label: string;
  /** Injected by `TabTrigger`. */
  isFocused?: boolean;
  onPress?: (event: GestureResponderEvent) => void;
  ref?: Ref<ViewInstance>;
};

/** One destination. Selection shows as a bar, a filled background and a semibold label, not by colour alone. */
export function HDTabItem({ icon, label, isFocused = false, onPress, ref }: HDTabItemProps) {
  const foreground = isFocused ? tokens.color.selectionForeground : tokens.color.textSecondary;
  return (
    <Pressable
      ref={ref}
      role="tab"
      aria-label={label}
      aria-selected={isFocused}
      onPress={onPress}
      style={[styles.item, isFocused && styles.selected]}>
      <HDIcon name={icon} color={foreground} />
      <HDText variant={isFocused ? 'labelStrong' : 'label'} style={[styles.label, { color: foreground }]}>
        {label}
      </HDText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: tokens.color.backgroundSurface,
    borderTopWidth: tokens.size.borderControl,
    borderTopColor: tokens.color.borderDecorative,
  },
  item: {
    flexGrow: 1,
    flexShrink: 1,
    minWidth: tokens.size.targetMinimum,
    minHeight: tokens.size.targetMinimum,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: tokens.space['4'],
    borderTopWidth: tokens.size.borderSelected,
    borderTopColor: 'transparent',
  },
  label: { textAlign: 'center' },
  selected: {
    backgroundColor: tokens.component.tabSelectedBackground,
    borderTopColor: tokens.component.tabSelectedIndicator,
  },
});
