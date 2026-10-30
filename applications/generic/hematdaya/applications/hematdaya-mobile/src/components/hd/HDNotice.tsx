import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDIcon, type HDIconName } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type Tone = 'info' | 'attention' | 'error' | 'success' | 'neutral';

type HDNoticeProps = {
  tone?: Tone;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  /** Announce on appearance, for notices that respond to an action. Off for persistent explanations. */
  live?: boolean;
};

const { color } = tokens;

const TONES: Record<Tone, { icon: HDIconName; background: string; foreground: string; prefix: string }> = {
  info: { icon: 'info', background: color.statusInfoBackground, foreground: color.statusInfoForeground, prefix: 'Info' },
  attention: {
    icon: 'attention',
    background: color.statusAttentionBackground,
    foreground: color.statusAttentionForeground,
    prefix: 'Perhatian',
  },
  error: {
    icon: 'error',
    background: color.statusErrorBackground,
    foreground: color.statusErrorForeground,
    prefix: 'Kesalahan',
  },
  success: {
    icon: 'success',
    background: color.statusSuccessBackground,
    foreground: color.statusSuccessForeground,
    prefix: 'Berhasil',
  },
  neutral: {
    icon: 'info',
    background: color.statusNeutralBackground,
    foreground: color.textSecondary,
    prefix: 'Catatan',
  },
};

/** Persistent explanation with a tone word, so meaning never rests on colour alone. */
export function HDNotice({ tone = 'neutral', title, children, action, live = false }: HDNoticeProps) {
  const style = TONES[tone];
  return (
    <View
      accessibilityLiveRegion={live ? 'polite' : 'none'}
      role={live ? 'status' : undefined}
      style={[styles.notice, { backgroundColor: style.background }]}>
      <HDIcon name={style.icon} size="small" color={style.foreground} />
      <View style={styles.content}>
        <HDText variant="bodyStrong" accessibilityLabel={`${style.prefix}: ${title}`}>
          {title}
        </HDText>
        {typeof children === 'string' ? <HDText>{children}</HDText> : children}
        {action}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: {
    flexDirection: 'row',
    gap: tokens.space.stackTight,
    padding: tokens.space['16'],
    borderRadius: tokens.radius.surface,
  },
  content: { flex: 1, gap: tokens.space.stackTight },
});
