import type { Ref } from 'react';
import { Text, type TextInstance, type TextProps } from 'react-native';

import { tokens } from '@/design/tokens.generated';

export type HDTextProps = TextProps & {
  variant?: keyof typeof tokens.type;
  tone?: 'primary' | 'secondary' | 'link' | 'attention' | 'error';
  ref?: Ref<TextInstance>;
};

const TONES = {
  primary: tokens.color.textPrimary,
  secondary: tokens.color.textSecondary,
  link: tokens.color.textLink,
  attention: tokens.color.statusAttentionForeground,
  error: tokens.color.statusErrorForeground,
};

/** Design-system text. Sizes scale with the user's font setting. */
export function HDText({ variant = 'body', tone = 'primary', style, ...props }: HDTextProps) {
  return <Text {...props} style={[tokens.type[variant], { color: TONES[tone] }, style]} />;
}
