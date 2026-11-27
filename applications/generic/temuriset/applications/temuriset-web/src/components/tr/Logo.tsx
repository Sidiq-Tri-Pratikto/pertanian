import Link from 'next/link';

/**
 * Port of TR.Logo: two paths meeting at one node, the inventor and the investor who meet ("temu"). The mark is
 * decorative; the visible word names the link.
 */
export function Logo({ href }: { href?: string }) {
  const mark = (
    <svg className="tr-logo__mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect width="32" height="32" rx="7" fill="var(--tr-sys-color-action-primary-background)" />
      <path
        d="M7 24c5 0 7-3 8.4-6.6M25 8c-5 0-7 3-8.4 6.6"
        fill="none"
        stroke="var(--tr-sys-color-action-primary-foreground)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="16" cy="16" r="3.2" fill="var(--tr-sys-color-selected-surface)" />
    </svg>
  );
  if (!href) {
    return (
      <span className="tr-logo">
        {mark}
        <span>TemuRiset</span>
      </span>
    );
  }
  return (
    <Link className="tr-logo" href={href}>
      {mark}
      <span>TemuRiset</span>
    </Link>
  );
}
