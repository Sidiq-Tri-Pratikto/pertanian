import { serverLocale } from '@/features/i18n/server';
import { TeaserView } from '@/views/subscriptions/TeaserView';

/** An invention that is not public answers 404 with a way back, in the page's language. */
export default async function PublicInventionNotFound() {
  return <TeaserView teaser={null} locale={await serverLocale()} />;
}
