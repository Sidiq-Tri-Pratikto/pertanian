'use client';

import { Toggletip } from '@/components/tr/Toggletip';
import { t } from '@/features/i18n/t';
import { TKT_GROUPS, tktLevelOf } from '@/features/portfolio/tkt';

type TktBadgeProps = {
  level: number | null | undefined;
  /** Optional stage label such as "Prototipe"; defaults to the TKT level's own name. */
  stageLabel?: string | null;
  note?: string | null;
  hasEvidence?: boolean;
  /** Show the 9-segment readiness bar with text equivalent. */
  showBar?: boolean;
  /** Show provenance ("Dinyatakan inovator") and evidence line beneath the badge. */
  showMeta?: boolean;
  /** Use preview phrasing for attached evidence ("Bukti TKT: tersedia (dibagikan saat pitching)"). */
  preview?: boolean;
  /** Explicit locale override for signed-out public pages (TeaserView). */
  locale?: 'id' | 'en';
};

/** Nine-segment progress bar with a text equivalent; colours never carry meaning alone. */
export function TktBar({ level, locale }: { level: number; locale?: 'id' | 'en' }) {
  const text = locale === 'en' ? `TKT ${level} of 9` : locale === 'id' ? `TKT ${level} dari 9` : t('TKT {n} dari 9', { n: level });
  return (
    <div className="tr-tkt-bar">
      <div className="tr-tkt-bar__track" aria-hidden="true">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((step) => (
          <span key={step} className={step <= level ? 'tr-tkt-bar__seg is-filled' : 'tr-tkt-bar__seg'} />
        ))}
      </div>
      <span className="tr-muted tr-sys-type-support">{text}</span>
    </div>
  );
}

/**
 * Compact TKT badge ("TKT 6 · Prototipe") with an accessible Toggletip explaining the level and group (spec 056).
 * Renders nothing when no TKT level is stated; never renders "TKT 0".
 */
export function TktBadge({ level, stageLabel, note, hasEvidence, showBar = false, showMeta = false, preview = false, locale }: TktBadgeProps) {
  const entry = tktLevelOf(level);
  if (!entry) return null;
  const group = TKT_GROUPS.find((item) => item.id === entry.group);
  const tr = (idText: string, enText: string) => (locale === 'en' ? enText : locale === 'id' ? idText : t(idText));
  const detail = stageLabel?.trim() || tr(entry.name, entry.nameEn);
  const groupText = group ? tr(group.label, group.labelEn) : '';
  const meaningText = tr(entry.meaning, entry.meaningEn);
  const provenance = tr('Dinyatakan inovator', 'Stated by inventor');
  const evidenceText = preview
    ? tr('Bukti TKT: tersedia (dibagikan saat pitching)', 'TKT evidence: available (shared when pitching)')
    : tr('Bukti terlampir saat pitching', 'Evidence attached when pitching');

  return (
    <div className="tr-tkt-badge tr-stack">
      <div className="tr-row">
        <span className="tr-tag tr-sys-type-support-strong">{`TKT ${entry.level} · ${detail}`}</span>
        <Toggletip label={`TKT ${entry.level}`}>
          <span>{`${meaningText}${groupText ? ` (${groupText})` : ''}`}</span>
        </Toggletip>
      </div>
      {showBar ? <TktBar level={entry.level} locale={locale} /> : null}
      {showMeta ? (
        <p className="tr-muted tr-sys-type-support">
          {provenance}
          {hasEvidence ? ` · ${evidenceText}` : ''}
        </p>
      ) : null}
      {showMeta && note?.trim() ? <p className="tr-sys-type-support">{note}</p> : null}
    </div>
  );
}
