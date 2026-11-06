import { View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { tokens } from '@/design/tokens.generated';

// Path data copied from HD.Icon in HematDaya Design System 1.0.0-draft. There is deliberately no power symbol.
const PATHS = {
  home: 'M4 11 12 4l8 7M6 9.5V20h12V9.5M10 20v-5h4v5',
  devices:
    'M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM8 8h8M12 17.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  saran: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.8.6 1.1 1.4 1.1 2.2v.5h5V16c0-.8.3-1.6 1.1-2.2A6 6 0 0 0 12 3z',
  chevronRight: 'M9 6l6 6-6 6',
  chevronLeft: 'M15 6l-6 6 6 6',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01',
  attention: 'M12 4l9 15.5H3L12 4zM12 10v4M12 16.8h.01',
  error: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9 9l6 6M15 9l-6 6',
  success: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8 12.5l2.7 2.6L16 9.6',
  refresh: 'M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
};

export type HDIconName = keyof typeof PATHS;

type HDIconProps = { name: HDIconName; size?: 'default' | 'small'; color?: string };

/** Decorative stroke icon. Meaning always comes from adjacent text or the control's label. */
export function HDIcon({ name, size = 'default', color = tokens.color.textPrimary }: HDIconProps) {
  const dimension = size === 'small' ? tokens.size.iconSmall : tokens.size.iconDefault;
  return (
    <View aria-hidden>
      <Svg width={dimension} height={dimension} viewBox="0 0 24 24">
        <Path d={PATHS[name]} stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" fill="none" />
      </Svg>
    </View>
  );
}
