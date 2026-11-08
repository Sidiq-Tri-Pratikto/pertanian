import { useCallback, useLayoutEffect, useRef, useState, type ComponentRef, type ReactNode, type Ref } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';

import { HDIcon, type HDIconName } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDButtonProps = {
  children: ReactNode;
  ref?: Ref<ComponentRef<typeof View>>;
  variant?: 'primary' | 'secondary' | 'text' | 'destructive';
  onPress?: () => void;
  icon?: HDIconName;
  /** Shows progress and ignores presses, so a submit cannot be duplicated. Never announces success. */
  loading?: boolean;
  loadingLabel?: string;
  /** Non-empty means disabled. The control stays focusable and the reason stays visible. */
  disabledReason?: string | null;
  fullWidth?: boolean;
  expanded?: boolean;
};

const { color, component } = tokens;

const FOREGROUND = {
  primary: component.buttonPrimaryForeground,
  secondary: color.actionSecondaryForeground,
  text: color.actionSecondaryForeground,
  destructive: color.actionDestructiveForeground,
};

function background(variant: NonNullable<HDButtonProps['variant']>, pressed: boolean, disabled: boolean) {
  if (disabled) {
    return color.disabledBackground;
  }
  switch (variant) {
    case 'primary':
      return pressed ? color.actionPrimaryPressed : component.buttonPrimaryBackground;
    case 'destructive':
      return pressed ? color.actionDestructiveHover : color.actionDestructiveBackground;
    case 'secondary':
      return pressed ? color.actionSecondaryHover : color.actionSecondaryBackground;
    default:
      return pressed ? color.actionSecondaryHover : 'transparent';
  }
}

/** One labelled action. At most one primary per task step. */
export function HDButton({
  children,
  ref,
  variant = 'secondary',
  onPress,
  icon,
  loading = false,
  loadingLabel = 'Memproses…',
  disabledReason,
  fullWidth = false,
  expanded,
}: HDButtonProps) {
  const [focused, setFocused] = useState(false);
  const disabled = Boolean(disabledReason);
  const foreground = disabled ? color.disabledForeground : FOREGROUND[variant];
  const action = useRef({ disabled, loading, onPress });
  // The web Pressable installs callbacks after paint. Use the committed action as soon as the button is enabled.
  useLayoutEffect(() => { action.current = { disabled, loading, onPress }; }, [disabled, loading, onPress]);
  const press = useCallback(() => {
    const current = action.current;
    if (!current.disabled && !current.loading) current.onPress?.();
  }, []);

  return (
    <View style={[styles.wrapper, fullWidth && styles.fullWidth]}>
      <Pressable
        ref={ref}
        role="button"
        aria-disabled={disabled}
        aria-busy={loading}
        aria-expanded={expanded}
        accessibilityHint={disabledReason ?? undefined}
        onPress={press}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: background(variant, pressed, disabled) },
          variant === 'secondary' && styles.outlined,
          disabled && styles.disabled,
          fullWidth && styles.fullWidth,
          focused && styles.focused,
        ]}>
        {loading ? (
          <ActivityIndicator color={foreground} />
        ) : (
          icon && <HDIcon name={icon} size="small" color={foreground} />
        )}
        <HDText variant="bodyStrong" style={[styles.label, { color: foreground }]}>
          {loading ? loadingLabel : children}
        </HDText>
      </Pressable>
      {disabledReason ? (
        <HDText variant="label" tone="secondary">
          {disabledReason}
        </HDText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { alignSelf: 'flex-start', gap: tokens.space.stackTight, maxWidth: '100%' },
  fullWidth: { alignSelf: 'stretch' },
  button: {
    minHeight: tokens.size.targetMinimum,
    minWidth: tokens.size.targetMinimum,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: tokens.space.inlineGap,
    paddingHorizontal: tokens.space.controlPaddingX,
    paddingVertical: tokens.space.controlPaddingY,
    borderRadius: tokens.radius.control,
  },
  outlined: { borderWidth: tokens.size.borderControl, borderColor: color.borderControl },
  disabled: { borderWidth: tokens.size.borderControl, borderColor: color.borderControl, borderStyle: 'dashed' },
  focused: {
    outlineColor: color.focusRing,
    outlineStyle: 'solid',
    outlineWidth: tokens.size.focusRingWidth,
    outlineOffset: tokens.size.focusGapWidth,
  },
  label: { flexShrink: 1, textAlign: 'center' },
});
