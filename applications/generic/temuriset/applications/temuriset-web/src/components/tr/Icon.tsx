// Port of TR.Icon from TemuRiset Design System 1.0.0-draft: same names, paths and classes.
const ICONS = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  cross: 'M6 6l12 12M18 6L6 18',
  question: 'M9 9.2a3 3 0 1 1 4.6 2.5c-1 .7-1.6 1.3-1.6 2.5M12 17.6v.1',
  minus: 'M6 12h12',
  alert: 'M12 4l9 16H3L12 4zM12 10v4.5M12 17.2v.1',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7.5V12l3 2',
  lock: 'M7 11V8a5 5 0 0 1 10 0v3M6 11h12v9H6z',
  file: 'M7 3h7l4 4v14H7zM14 3v4h4',
  right: 'M9 6l6 6-6 6',
  left: 'M15 6l-6 6 6 6',
  arrow: 'M5 12h14M13 6l6 6-6 6',
  close: 'M6 6l12 12M18 6L6 18',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4.5 20.5c1-4 4-6 7.5-6s6.5 2 7.5 6',
  building: 'M5 21V4h10v17M15 10h4v11M3 21h18M8.5 8h3M8.5 12h3M8.5 16h3',
  search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM16.2 16.2L21 21',
  home: 'M4 11l8-7 8 7M6 9.5V20h12V9.5',
  bulb: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1 1.2 1.1 2.2h5c.1-1 .4-1.6 1.1-2.2A6 6 0 0 0 12 3z',
  chat: 'M4 5h16v11H9l-5 4V5z',
  inbox: 'M4 13l2.5-8h11L20 13v6H4zM4 13h5l1 2.5h4l1-2.5h5',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
  more: 'M5 12h.1M12 12h.1M19 12h.1',
  refresh:
    'M20 11a8 8 0 0 0-14.3-4.5L4 8.5M4 4v4.5h4.5M4 13a8 8 0 0 0 14.3 4.5L20 15.5M20 20v-4.5h-4.5',
  edit: 'M4 20l1-4L16 5l3 3L8 19l-4 1z',
  upload: 'M12 16V5M8 9l4-4 4 4M5 19h14',
  shield: 'M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6l8-3z',
  partner: 'M3 9.5L8 7l4 2 4-2 5 2.5M3 9.5V16l3 1M21 9.5V16l-3 1M12 9l-4 4 2 2 3-2 3 3 2-2',
} as const;

export type IconName = keyof typeof ICONS;

type IconProps = { name: IconName; size?: 'small'; className?: string };

/** Decorative stroke icon. It always sits beside a word, so it is hidden from assistive technology. */
export function Icon({ name, size, className }: IconProps) {
  const classes = ['tr-icon', size === 'small' && 'tr-icon--small', className].filter(Boolean).join(' ');
  return (
    <svg className={classes} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d={ICONS[name]} />
    </svg>
  );
}
