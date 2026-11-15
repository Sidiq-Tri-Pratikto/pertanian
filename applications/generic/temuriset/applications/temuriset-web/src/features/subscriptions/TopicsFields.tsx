'use client';

import { Checkbox, CheckboxGroup } from '@/components/tr/Checkbox';
import { TextField } from '@/components/tr/TextField';
import { SECTORS } from '@/features/discovery/model';
import { STAGES } from '@/features/portfolio/model';
import type { Topics } from '@/features/subscriptions/api';

type Props = { topics: Topics; keywords: string; onTopics: (topics: Topics) => void; onKeywords: (text: string) => void; error?: string };

type Stage = NonNullable<Topics['stages']>[number];

function toggle<T>(list: T[] | undefined, value: T, on: boolean): T[] {
  const current = list ?? [];
  return on ? [...current, value] : current.filter((item) => item !== value);
}

/** Sectors, stages and keywords an investor wants to hear about. */
export function TopicsFields({ topics, keywords, onTopics, onKeywords, error }: Props) {
  return (
    <div className="tr-stack" id="topics">
      <CheckboxGroup legend="Sektor" hint="Pilih satu atau lebih." error={error}>
        {SECTORS.map((sector) => (
          <Checkbox key={sector} label={sector} checked={Boolean(topics.sectors?.includes(sector))} onChange={(on) => onTopics({ ...topics, sectors: toggle(topics.sectors, sector, on) })} />
        ))}
      </CheckboxGroup>
      <CheckboxGroup legend="Tahap inovasi" hint="Kosongkan bila tahap mana pun boleh.">
        {STAGES.map((stage) => (
          <Checkbox
            key={stage.value}
            label={stage.label}
            checked={Boolean(topics.stages?.includes(stage.value as Stage))}
            onChange={(on) => onTopics({ ...topics, stages: toggle(topics.stages, stage.value as Stage, on) })}
          />
        ))}
      </CheckboxGroup>
      <TextField label="Kata kunci" hint="Opsional, pisahkan dengan koma. Paling banyak lima, misalnya: filter air, surya." value={keywords} onChange={onKeywords} id="keywords" />
    </div>
  );
}
