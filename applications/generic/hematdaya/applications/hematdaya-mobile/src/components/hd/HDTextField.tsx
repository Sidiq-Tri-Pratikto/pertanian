import { useCopy } from '@/features/localization/messages';
import type { ComponentRef, Ref } from 'react';
import { StyleSheet, TextInput, View, type KeyboardTypeOptions } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDTextFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  help?: string;
  /** Shown above the input and read with it, so it is never only a colour or a placeholder. */
  error?: string | null;
  optional?: boolean;
  required?: boolean;
  multiline?: boolean;
  keyboardType?: KeyboardTypeOptions;
  secureTextEntry?: boolean;
  maxLength?: number;
  /** Says the typed text is kept, for example when the user leaves and comes back. */
  draftNote?: string;
  editable?: boolean;
  inputRef?: Ref<ComponentRef<typeof TextInput>>;
};

const MULTILINE_HEIGHT = 160;

/** Labelled text input with help, error, required or optional marker and a draft note. */
export function HDTextField({
  label,
  value,
  onChange,
  help,
  error,
  optional = false,
  required = false,
  multiline = false,
  keyboardType,
  secureTextEntry,
  maxLength,
  draftNote,
  editable = true,
  inputRef,
}: HDTextFieldProps) {
  const say = useCopy();
  const description = [error, help, draftNote].filter(Boolean).join(' ');
  return (
    <View style={styles.field}>
      <HDText variant="labelStrong">
        {label}
        {optional ? <HDText variant="label"> {say("(opsional)", "(optional)")}</HDText> : null}
        {required ? <HDText variant="label"> {say("(wajib)", "(required)")}</HDText> : null}
      </HDText>
      {help ? (
        <HDText variant="label" tone="secondary">
          {help}
        </HDText>
      ) : null}
      {error ? <HDText tone="error">{error}</HDText> : null}
      <TextInput
        ref={inputRef}
        accessibilityLabel={label}
        accessibilityHint={description || undefined}
        aria-invalid={error ? true : undefined}
        aria-required={required || undefined}
        value={value}
        onChangeText={onChange}
        multiline={multiline}
        keyboardType={keyboardType}
        secureTextEntry={secureTextEntry}
        maxLength={maxLength}
        autoCapitalize={secureTextEntry ? 'none' : undefined}
        autoCorrect={secureTextEntry ? false : undefined}
        editable={editable}
        readOnly={!editable}
        textAlignVertical={multiline ? 'top' : 'center'}
        style={[styles.input, multiline && styles.multiline, error ? styles.invalid : null, !editable && styles.readOnly]}
      />
      {draftNote ? (
        <HDText variant="label" tone="secondary">
          {draftNote}
        </HDText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: tokens.space.stackTight },
  input: {
    minHeight: tokens.size.targetMinimum,
    paddingHorizontal: tokens.space.controlPaddingX,
    paddingVertical: tokens.space.controlPaddingY,
    borderRadius: tokens.radius.control,
    borderWidth: tokens.size.borderControl,
    borderColor: tokens.component.fieldBorder,
    backgroundColor: tokens.color.backgroundSurface,
    color: tokens.color.textPrimary,
    ...tokens.type.body,
  },
  multiline: { minHeight: MULTILINE_HEIGHT },
  invalid: { borderWidth: tokens.size.focusRingWidth, borderColor: tokens.component.fieldBorderError },
  readOnly: { borderStyle: 'dashed' },
});
