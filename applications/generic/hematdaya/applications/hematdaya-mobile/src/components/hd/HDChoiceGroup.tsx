import { useCopy } from '@/features/localization/messages';
import type { ComponentRef, Ref } from 'react';
import { Platform, Pressable, StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type Option<Value extends string> = {
  value: Value;
  label: string;
  description?: string;
  disabledReason?: string;
  testID?: string;
  ref?: Ref<ComponentRef<typeof View>>;
};

type Common<Value extends string> = {
  legend: string;
  help?: string;
  optional?: boolean;
  /** Shows "(wajib)" beside the legend. */
  required?: boolean;
  /** Shown above the options, in the same words as the error summary. */
  error?: string | null;
  /** Locks every option, for example while a request that depends on the choice is in flight. */
  disabled?: boolean;
  options: Option<Value>[];
  /** The group, so an error summary can move focus to it. */
  groupRef?: Ref<ComponentRef<typeof View>>;
};

type RadioProps<Value extends string> = Common<Value> & {
  type?: 'radio';
  value: Value | null;
  onChange: (value: Value) => void;
};

type CheckboxProps<Value extends string> = Common<Value> & {
  type: 'checkbox';
  value: Value[];
  onChange: (value: Value[]) => void;
};

type HDChoiceGroupProps<Value extends string> = RadioProps<Value> | CheckboxProps<Value>;

const { color } = tokens;

/**
 * Single choice (radio) or independent ticks (checkbox). Selection shows beyond colour: thicker border, semibold
 * label and a filled mark, round for a radio and square for a checkbox.
 */
export function HDChoiceGroup<Value extends string>(props: HDChoiceGroupProps<Value>) {
  const say = useCopy();
  const { legend, help, optional = false, required = false, error, disabled = false, options, groupRef } = props;
  const checkbox = props.type === 'checkbox';
  const isSelected = (value: Value) => (props.type === 'checkbox' ? props.value.includes(value) : props.value === value);
  const choose = (value: Value) => {
    if (disabled) {
      return;
    }
    if (props.type === 'checkbox') {
      props.onChange(props.value.includes(value) ? props.value.filter((item) => item !== value) : [...props.value, value]);
    } else {
      props.onChange(value);
    }
  };

  return (
    <View ref={groupRef} role={checkbox ? 'group' : 'radiogroup'} aria-label={legend} style={styles.group} {...FOCUSABLE_BY_SCRIPT}>
      <HDText variant="labelStrong">
        {legend}
        {optional ? <HDText variant="label"> {say("(opsional)", "(optional)")}</HDText> : null}
        {required ? <HDText variant="label"> {say("(wajib)", "(required)")}</HDText> : null}
      </HDText>
      {help ? (
        <HDText variant="label" tone="secondary">
          {help}
        </HDText>
      ) : null}
      {error ? <HDText tone="error">{error}</HDText> : null}
      {options.map((option) => {
        const selected = isSelected(option.value);
        const unavailable = disabled || Boolean(option.disabledReason);
        const onSelect = () => { if (!unavailable) choose(option.value); };
        return (
          <Pressable
            key={option.value}
            ref={option.ref}
            testID={option.testID}
            role={checkbox ? 'checkbox' : 'radio'}
            aria-checked={selected}
            aria-disabled={unavailable || undefined}
            aria-label={option.label}
            accessibilityHint={option.disabledReason ?? error ?? undefined}
            disabled={unavailable}
            onPress={onSelect}
            {...spaceSelect(onSelect)}
            style={[styles.option, selected && styles.selected, unavailable && styles.disabled]}>
            <View style={[styles.mark, checkbox && styles.square, selected && styles.markSelected]}>
              {selected ? <View style={[styles.markFill, checkbox && styles.squareFill]} /> : null}
            </View>
            <View style={styles.optionText}>
              <HDText variant={selected ? 'bodyStrong' : 'body'}>{option.label}</HDText>
              {option.description || option.disabledReason ? (
                <HDText variant="label" tone="secondary">
                  {[option.description, option.disabledReason].filter(Boolean).join(' ')}
                </HDText>
              ) : null}
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

// React Native Web handles Enter for Pressable, but handles Space only for button roles.
function spaceSelect(select: () => void): object {
  if (Platform.OS !== 'web') {
    return {};
  }
  return {
    onKeyDown: (event: { key: string; repeat: boolean; preventDefault: () => void }) => {
      if (event.key === ' ') {
        event.preventDefault();
        if (!event.repeat) {
          select();
        }
      }
    },
  };
}

// Web only: an error summary can move focus to the group without adding it to the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;
const MARK = tokens.size.iconSmall;

const styles = StyleSheet.create({
  group: { gap: tokens.space.stackTight },
  optionText: { flexShrink: 1, gap: tokens.space['4'] },
  option: {
    minHeight: tokens.size.targetMinimum,
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.space.stack,
    paddingHorizontal: tokens.space.controlPaddingX,
    paddingVertical: tokens.space.controlPaddingY,
    borderRadius: tokens.radius.control,
    borderWidth: tokens.size.borderControl,
    borderColor: color.borderControl,
    backgroundColor: color.backgroundSurface,
  },
  selected: {
    borderWidth: tokens.size.borderSelected,
    borderColor: color.selectionIndicator,
    backgroundColor: color.selectionBackground,
  },
  disabled: { borderStyle: 'dashed' },
  mark: {
    width: MARK,
    height: MARK,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: MARK / 2,
    borderWidth: tokens.size.strokeChart,
    borderColor: color.borderControl,
  },
  square: { borderRadius: tokens.radius['0'] },
  markSelected: { borderColor: color.selectionIndicator },
  markFill: { width: MARK / 2, height: MARK / 2, borderRadius: MARK / 4, backgroundColor: color.selectionIndicator },
  squareFill: { borderRadius: tokens.radius['0'] },
});
