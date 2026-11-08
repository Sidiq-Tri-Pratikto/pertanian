import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { setLocale, useLocale, type Locale } from '@/features/localization/locale';
import { message } from '@/features/localization/messages';

const LANGUAGES: { value: Locale; label: string }[] = [
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'en', label: 'English' },
];

export function LanguageSetting() {
  const language = useLocale();
  return <HDChoiceGroup legend={message(language, 'language')} value={language} options={LANGUAGES} onChange={setLocale} />;
}
