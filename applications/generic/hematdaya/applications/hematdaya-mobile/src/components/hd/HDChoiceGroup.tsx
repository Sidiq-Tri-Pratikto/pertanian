import { Pressable, StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type Option<Value extends string> = { value: Value; label: string; description?: string };

type HDChoiceGroupProps<Value extends string> = {
  legend: string;
  help?: string;
  optional?: boolean;
  options: Option<Value>[];
  value: Value;
  onChange: (value: Value) => void;
};

const { color } = tokens;

/** Single-choice setting. Selection shows beyond colour: thicker border, semibold label and a filled mark. */
export function HDChoiceGroup<Value extends string>({
  legend,
  help,
  optional = false,
  options,
  value,
  onChange,
}: HDChoiceGroupProps<Value>) {
  return (
    <View role="radiogroup" aria-label={legend} style={styles.group}>
      <HDText variant="labelStrong">
        {legend}
        {optional ? <HDText variant="label"> (opsional)</HDText> : null}
      </HDText>
      {help ? (
        <HDText variant="label" tone="secondary">
          {help}
        </HDText>
      ) : null}
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            role="radio"
            aria-checked={selected}
            aria-label={option.label}
            onPress={() => onChange(option.value)}
            style={[styles.option, selected && styles.selected]}>
            <View style={[styles.mark, selected && styles.markSelected]}>
              {selected ? <View style={styles.markFill} /> : null}
            </View>
            <View style={styles.optionText}>
              <HDText variant={selected ? 'bodyStrong' : 'body'}>{option.label}</HDText>
              {option.description ? (
                <HDText variant="label" tone="secondary">
                  {option.description}
                </HDText>
              ) : null}
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

const MARK = tokens.size.iconSmall;


const styles = StyleSheet.create({
  group: { gap: tokens.space.stackTight },
  optionText: { flexShrink: 1, gap: tokens.space["4"] },
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
  mark: {
    width: MARK,
    height: MARK,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: MARK / 2,
    borderWidth: tokens.size.strokeChart,
    borderColor: color.borderControl,
  },
  markSelected: { borderColor: color.selectionIndicator },
  markFill: { width: MARK / 2, height: MARK / 2, borderRadius: MARK / 4, backgroundColor: color.selectionIndicator },
});
