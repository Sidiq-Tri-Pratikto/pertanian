'use client';

import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { TextField } from '@/components/tr/TextField';
import { SECTORS } from '@/features/discovery/model';
import { STAGES } from '@/features/portfolio/model';
import { useMessages } from '@/features/i18n/LocaleProvider';
import { sectorLabel, stageLabel } from '@/features/i18n/messages';
import type { Topics } from '@/features/subscriptions/api';

type Props = { topics: Topics; keywords: string; onTopics: (topics: Topics) => void; onKeywords: (text: string) => void; error?: string };

type Stage = NonNullable<Topics['stages']>[number];

function toggle<T>(list: T[] | undefined, value: T, on: boolean): T[] {
  const current = list ?? [];
  return on ? [...current, value] : current.filter((item) => item !== value);
}

/** Sectors, stages and keywords an investor wants to hear about. */
export function TopicsFields({ topics, keywords, onTopics, onKeywords, error }: Props) {
  const messages = useMessages();
  const words = messages.topics;
  return (
    <div className="tr-stack" id="topics">
      <CheckboxGroup legend={words.sectors} hint={words.sectorsHint} error={error}>
        {SECTORS.map((sector) => (
          <Checkbox key={sector} label={sectorLabel(messages, sector)} checked={Boolean(topics.sectors?.includes(sector))} onChange={(on) => onTopics({ ...topics, sectors: toggle(topics.sectors, sector, on) })} />
        ))}
      </CheckboxGroup>
      <CheckboxGroup legend={words.stages} hint={words.stagesHint}>
        {STAGES.map((stage) => (
          <Checkbox
            key={stage.value}
            label={stageLabel(messages, stage.value) ?? stage.label}
            checked={Boolean(topics.stages?.includes(stage.value as Stage))}
            onChange={(on) => onTopics({ ...topics, stages: toggle(topics.stages, stage.value as Stage, on) })}
          />
        ))}
      </CheckboxGroup>
      <TextField label={words.keywords} hint={words.keywordsHint} value={keywords} onChange={onKeywords} id="keywords" />
    </div>
  );
}
