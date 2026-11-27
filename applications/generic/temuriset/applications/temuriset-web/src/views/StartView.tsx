'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, useSyncExternalStore, type FormEvent, type ReactNode } from 'react';

import { send } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { Disclosure } from '@/components/tr/Disclosure';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Select } from '@/components/tr/Select';
import { TextField } from '@/components/tr/TextField';
import { carriedEmail, forgetEmail } from '@/features/i18n/carry';
import { useLocale, useMessages } from '@/features/i18n/LocaleProvider';
import { localHref } from '@/features/i18n/locale';
import type { Messages } from '@/features/i18n/messages';
import type { Persona } from '@/features/persona';
import { codeRequest, EMAIL_PATTERN, LOCALES, savePending, TIME_ZONES, type PendingSignIn } from '@/features/signIn';
import { AuthShell } from '@/views/AuthShell';

const DEFAULT_ZONE = 'Asia/Jakarta';

function subscribeNever(): () => void {
  return () => undefined;
}

function supportedBrowserZone(): string {
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return TIME_ZONES.some((option) => option.value === zone) ? zone : DEFAULT_ZONE;
}

function labelOf(options: { value: string; label: string }[], value: string): string {
  return options.find((option) => option.value === value)?.label ?? value;
}

function personaChoices(words: Messages['start']) {
  return [
    { value: 'inovator', label: words.personaInventor, hint: words.personaInventorHint },
    { value: 'mitra', label: words.personaPartner, hint: words.personaPartnerHint },
  ];
}

type StartViewProps = {
  /** Pre-selected from the persona chosen before accounts existed. */
  persona: Persona | null;
  mode: 'sign_up' | 'sign_in';
  returnTo: string | null;
  /** The demo picker, when this deployment runs the labelled demo. */
  demo?: ReactNode;
};

type Errors = Partial<Record<'persona' | 'nama' | 'email', string>>;

const FIELD_ID = { persona: 'persona-inovator', nama: 'nama', email: 'email' } as const;

/**
 * S01: choose how to use TemuRiset, say who you are and where to send the code. No organization or affiliation is
 * asked (UX-01). Every typed value stays after a failure (UX-09).
 */
export function StartView({ persona, mode, returnTo, demo }: StartViewProps) {
  const router = useRouter();
  const form = useRef<HTMLFormElement>(null);
  const page = useLocale();
  const words = useMessages().start;
  const signUp = mode === 'sign_up';
  const [name, setName] = useState('');
  // An email typed before switching language starts the field; nothing else is carried.
  const carried = useSyncExternalStore(subscribeNever, carriedEmail, () => '');
  const [typedEmail, setEmail] = useState<string | null>(null);
  const email = typedEmail ?? carried;
  // The account's language starts as the page's; the visitor can still change it below.
  const [locale, setLocale] = useState<string>(page);
  // Start from the browser's zone when the list has it, so most people never open the settings.
  const browserZone = useSyncExternalStore(subscribeNever, supportedBrowserZone, () => DEFAULT_ZONE);
  const [chosenZone, setTimeZone] = useState<string | null>(null);
  const timeZone = chosenZone ?? browserZone;
  const [errors, setErrors] = useState<Errors>({});
  const [failure, setFailure] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);

  function validate(chosen: string | null): Errors {
    const found: Errors = {};
    if (signUp && !chosen) found.persona = words.errorPersona;
    if (signUp && !name.trim()) found.nama = words.errorName;
    if (!EMAIL_PATTERN.test(email.trim())) found.email = words.errorEmail;
    return found;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    const chosen = form.current ? (new FormData(form.current).get('persona') as string | null) : null;
    const found = validate(chosen);
    setErrors(found);
    setFailure(null);
    if (Object.keys(found).length) {
      setAttempt((count) => count + 1);
      return;
    }
    const pending: PendingSignIn = signUp
      ? { email: email.trim(), purpose: 'sign_up', display_name: name.trim(), locale, time_zone: timeZone, persona: chosen ?? 'inovator', returnTo }
      : { email: email.trim(), purpose: 'sign_in', locale: page, returnTo };
    setBusy(true);
    try {
      await send('POST', '/api/v1/auth/code', codeRequest(pending));
      savePending(pending);
      forgetEmail();
      router.push(localHref(page, '/start/kode'));
    } catch (error) {
      const apiError = ApiError.from(error);
      const wait = apiError.recovery.retry_after_seconds;
      setFailure(wait ? `${apiError.message} ${words.retryIn(Math.ceil(wait / 60))}` : apiError.message);
      setAttempt((count) => count + 1);
      setBusy(false);
    }
  }

  // Switching between sign-up and sign-in keeps where the visitor was going.
  const back = returnTo ? `kembali=${encodeURIComponent(returnTo)}` : '';
  const otherMode = localHref(page, signUp ? `/start?masuk=1${back ? `&${back}` : ''}` : `/start${back ? `?${back}` : ''}`);
  const summary = Object.entries(errors).map(([field, message]) => ({ fieldId: FIELD_ID[field as keyof Errors], message }));

  return (
    <AuthShell
      title={signUp ? words.titleSignUp : words.titleSignIn}
      subtitle={signUp ? words.subtitleSignUp : words.subtitleSignIn}>
      {demo}
      {summary.length || failure ? (
        <ErrorSummary errors={summary} focusKey={attempt}>
          {failure}
        </ErrorSummary>
      ) : null}
      <form ref={form} onSubmit={submit} noValidate className="tr-panel tr-stack">
        {signUp ? (
          <>
            <ChoiceGroup
              legend={words.personaLegend}
              name="persona"
              hint={words.personaHint}
              options={personaChoices(words)}
              defaultValue={persona ?? undefined}
              error={errors.persona}
              required
            />
            <TextField id="nama" label={words.name} value={name} onChange={setName} error={errors.nama} autoComplete="name" required />
          </>
        ) : null}
        <TextField
          id="email"
          type="email"
          label={words.email}
          hint={words.emailHint}
          value={email}
          onChange={setEmail}
          error={errors.email}
          autoComplete="email"
          required
        />
        {signUp ? (
          <>
            <Disclosure label={words.settings(labelOf(LOCALES, locale), labelOf(TIME_ZONES, timeZone))}>
              <div className="tr-stack">
                <Select id="bahasa" label={words.language} value={locale} onChange={setLocale} options={LOCALES} emptyLabel={null} />
                <Select id="zona-waktu" label={words.zone} hint={words.zoneHint} value={timeZone} onChange={setTimeZone} options={TIME_ZONES} emptyLabel={null} />
              </div>
            </Disclosure>
            <p className="tr-muted">{words.noOrganization}</p>
          </>
        ) : null}
        <div className="tr-row">
          <Button type="submit" intent="primary" icon="arrow" busy={busy} busyLabel={words.sending}>
            {words.send}
          </Button>
        </div>
      </form>
      <p>
        {signUp ? words.haveAccount : words.noAccount}
        <Link className="tr-link" href={otherMode}>
          {signUp ? words.signIn : words.signUp}
        </Link>
      </p>
      <p>
        {words.newsQuestion}{' '}
        <Link className="tr-link" href={localHref(page, '/langganan')}>
          {words.newsLink}
        </Link>
      </p>
    </AuthShell>
  );
}
