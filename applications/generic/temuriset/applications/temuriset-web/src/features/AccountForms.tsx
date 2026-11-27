'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent, type ReactNode } from 'react';

import { newIdempotencyKey, send, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ContextSwitcher } from '@/components/tr/ContextSwitcher';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Select } from '@/components/tr/Select';
import { Status } from '@/components/tr/Status';
import { TextField } from '@/components/tr/TextField';
import { contextOptions } from '@/features/ContextBar';
import { CAPABILITY_LABEL, ORGANIZATION_KINDS } from '@/features/organizations';
import { EMAIL_PATTERN, LOCALES, TIME_ZONES } from '@/features/signIn';
import { rememberLocale } from '@/features/i18n/locale';
import { t } from '@/features/i18n/t';

const PERSONAS = [
  { value: 'inovator', label: 'Inovator' },
  { value: 'mitra', label: 'Investor/Mitra' },
];

/** One form's failure and success handling: a focused summary on failure, a polite status on success. */
function useSubmission() {
  const [failure, setFailure] = useState<{ fieldId?: string; message: string; requestId?: string | null } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [done, setDone] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function run(action: () => Promise<string>) {
    if (busy) return;
    setBusy(true);
    setDone(null);
    try {
      setDone(await action());
      setFailure(null);
    } catch (error) {
      const { message, requestId } = ApiError.from(error);
      setFailure({ message, requestId });
      setAttempt((count) => count + 1);
    } finally {
      setBusy(false);
    }
  }
  function invalid(fieldId: string, message: string) {
    setFailure({ fieldId, message });
    setAttempt((count) => count + 1);
  }
  function feedback(id: string): ReactNode {
    return (
      <>
        {failure ? (
          <ErrorSummary id={`${id}-galat`} errors={failure.fieldId ? [{ fieldId: failure.fieldId, message: failure.message }] : []} focusKey={attempt}>
            {failure.fieldId ? null : failure.message}
            {failure.requestId ? <span>{` ${t('Referensi {id}', { id: failure.requestId })}`}</span> : null}
          </ErrorSummary>
        ) : null}
        <div aria-live="polite">{done ? <Status tone="success" label={done} /> : null}</div>
      </>
    );
  }
  return { run, invalid, feedback, busy, fieldError: (fieldId: string) => (failure?.fieldId === fieldId ? failure.message : null) };
}

/** Save account preferences against the version last read or saved. */
export function AccountForm({ me, emailNotificationsAvailable = false }: { me: Me; emailNotificationsAvailable?: boolean }) {
  const router = useRouter();
  const [name, setName] = useState(me.account.display_name);
  const [persona, setPersona] = useState(me.account.persona);
  const [locale, setLocale] = useState(me.account.locale);
  const [timeZone, setTimeZone] = useState(me.account.time_zone);
  const [emailNotifications, setEmailNotifications] = useState(me.account.email_notifications);
  const [version, setVersion] = useState(me.account.version);
  const submission = useSubmission();

  function save(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return submission.invalid('akun-nama', t('Isi nama tampilan.'));
    return submission.run(async () => {
      const saved = await send<Me>('PATCH', '/api/v1/me', {
        display_name: name.trim(),
        persona,
        locale,
        time_zone: timeZone,
        ...(emailNotificationsAvailable ? { email_notifications: emailNotifications } : {}),
        expected_version: version,
      });
      setVersion(saved.account.version);
      setEmailNotifications(saved.account.email_notifications);
      if (locale !== me.account.locale) {
        // The page language follows the account's language right away.
        rememberLocale(locale === 'en' ? 'en' : 'id');
        window.location.reload();
      }
      router.refresh();
      return t('Akun tersimpan');
    });
  }

  const zones = TIME_ZONES.some((zone) => zone.value === timeZone) ? TIME_ZONES : [{ value: timeZone, label: timeZone }, ...TIME_ZONES];
  return (
    <form onSubmit={save} noValidate className="tr-stack">
      {submission.feedback('akun')}
      <TextField id="akun-nama" label={t('Nama tampilan')} value={name} onChange={setName} error={submission.fieldError('akun-nama')} required />
      <Select id="akun-tampilan" label={t('Menu yang ditampilkan')} hint={t('Mengubah tampilan tidak mengubah data atau hak akses.')} value={persona} onChange={setPersona} options={PERSONAS} emptyLabel={null} />
      <Select id="akun-bahasa" label={t('Bahasa')} value={locale} onChange={setLocale} options={LOCALES} emptyLabel={null} />
      <Select id="akun-zona" label={t('Zona waktu')} value={timeZone} onChange={setTimeZone} options={zones} emptyLabel={null} />
      {emailNotificationsAvailable ? (
        <label className="tr-choice" htmlFor="akun-pemberitahuan-email">
          <input
            type="checkbox"
            id="akun-pemberitahuan-email"
            checked={emailNotifications}
            disabled={submission.busy}
            onChange={(event) => setEmailNotifications(event.target.checked)}
            aria-labelledby="akun-pemberitahuan-email-label"
            aria-describedby="akun-pemberitahuan-email-petunjuk"
          />
          <span className="tr-choice__body">
            <span id="akun-pemberitahuan-email-label" className="tr-sys-type-label">{t('Pemberitahuan lewat email')}</span>
            <span id="akun-pemberitahuan-email-petunjuk" className="tr-sys-type-support">
              {t('Dapatkan pemberitahuan umum tentang aktivitas pitching. Kode masuk dan undangan tetap dikirim terpisah.')}
            </span>
          </span>
        </label>
      ) : null}
      <div className="tr-row">
        <Button type="submit" intent="primary" busy={submission.busy} busyLabel={t('Menyimpan…')}>
          {t('Simpan akun')}
        </Button>
      </div>
    </form>
  );
}

/** Create an organization only when one is needed; nobody has to. */
export function CreateOrganizationForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [kind, setKind] = useState('');
  const key = useRef(newIdempotencyKey());
  const submission = useSubmission();

  function create(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return submission.invalid('organisasi-nama', t('Isi nama organisasi.'));
    if (!kind) return submission.invalid('organisasi-jenis', t('Pilih jenis organisasi.'));
    return submission.run(async () => {
      await send('POST', '/api/v1/organizations', { name: name.trim(), kind }, { idempotencyKey: key.current });
      key.current = newIdempotencyKey();
      setName('');
      setKind('');
      router.refresh();
      return t('Organisasi dibuat. Pilih organisasi itu di "Bertindak sebagai" untuk mengelolanya.');
    });
  }

  return (
    <form onSubmit={create} noValidate className="tr-stack">
      {submission.feedback('organisasi')}
      <TextField id="organisasi-nama" label={t('Nama organisasi')} value={name} onChange={(value) => { setName(value); key.current = newIdempotencyKey(); }} error={submission.fieldError('organisasi-nama')} required />
      <Select id="organisasi-jenis" label={t('Jenis organisasi')} value={kind} onChange={(value) => { setKind(value); key.current = newIdempotencyKey(); }} options={ORGANIZATION_KINDS} error={submission.fieldError('organisasi-jenis')} required />
      <div className="tr-row">
        <Button type="submit" busy={submission.busy} busyLabel={t('Membuat…')}>
          {t('Buat organisasi')}
        </Button>
      </div>
    </form>
  );
}

/** Invite a member with chosen capabilities, acting as the organization shown read-only beside the action. */
export function InviteForm({ me, organizationId }: { me: Me; organizationId: string }) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [chosen, setChosen] = useState<string[]>([]);
  const key = useRef(newIdempotencyKey());
  const submission = useSubmission();

  function toggle(capability: string) {
    key.current = newIdempotencyKey();
    setChosen((current) => (current.includes(capability) ? current.filter((item) => item !== capability) : [...current, capability]));
  }

  function invite(event: FormEvent) {
    event.preventDefault();
    if (!EMAIL_PATTERN.test(email.trim())) return submission.invalid('undang-email', t('Isi email dengan format nama@contoh.com.'));
    if (!chosen.length) return submission.invalid('undang-edit_portfolio', t('Pilih setidaknya satu kewenangan.'));
    return submission.run(async () => {
      await send(
        'POST',
        `/api/v1/organizations/${organizationId}/invitations`,
        { acting_party_id: me.active_party_id, email: email.trim(), capabilities: chosen },
        { idempotencyKey: key.current },
      );
      key.current = newIdempotencyKey();
      setEmail('');
      setChosen([]);
      router.refresh();
      return t('Undangan dikirim. Berlaku 7 hari.');
    });
  }

  return (
    <form onSubmit={invite} noValidate className="tr-stack">
      {submission.feedback('undang')}
      <TextField id="undang-email" type="email" label={t('Email anggota')} value={email} onChange={(value) => { setEmail(value); key.current = newIdempotencyKey(); }} error={submission.fieldError('undang-email')} required />
      <fieldset className="tr-fieldset">
        <legend className="tr-field__label tr-sys-type-label">{t('Kewenangan')}</legend>
        <div className="tr-choices">
          {Object.entries(CAPABILITY_LABEL).map(([capability, label]) => (
            <label key={capability} htmlFor={`undang-${capability}`} className="tr-choice">
              <input type="checkbox" id={`undang-${capability}`} checked={chosen.includes(capability)} onChange={() => toggle(capability)} />
              <span className="tr-choice__body">
                <span className="tr-sys-type-label">{t(label)}</span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
      <ContextSwitcher readOnly value={me.active_party_id} options={contextOptions(me)} actionLabel={t('Mengundang sebagai')} />
      <div className="tr-row">
        <Button type="submit" intent="primary" busy={submission.busy} busyLabel={t('Mengirim…')}>
          {t('Kirim undangan')}
        </Button>
      </div>
    </form>
  );
}

/** Revoke a pending invitation. */
export function RevokeButton({ me, invitationId, email }: { me: Me; invitationId: string; email: string }) {
  const router = useRouter();
  const submission = useSubmission();
  return (
    <div className="tr-stack">
      {submission.feedback(`cabut-${invitationId}`)}
      <Button
        busy={submission.busy}
        busyLabel={t('Mencabut…')}
        onClick={() =>
          submission.run(async () => {
            await send('POST', `/api/v1/invitations/${invitationId}/revoke`, { acting_party_id: me.active_party_id });
            router.refresh();
            return t('Undangan dicabut');
          })
        }>
        Cabut undangan<span className="tr-sr"> untuk {email}</span>
      </Button>
    </div>
  );
}

/** Join an organization after reading what the invitation grants. */
export function AcceptInvitationButton({ token }: { token: string }) {
  const router = useRouter();
  const submission = useSubmission();
  return (
    <div className="tr-stack">
      {submission.feedback('terima')}
      <div className="tr-row">
        <Button
          intent="primary"
          busy={submission.busy}
          busyLabel={t('Bergabung…')}
          onClick={() =>
            submission.run(async () => {
              await send('POST', `/api/v1/invitations/${token}/accept`);
              router.push('/settings?bergabung=1');
              router.refresh();
              return t('Anda sudah bergabung');
            })
          }>
          {t('Terima undangan')}
        </Button>
      </div>
    </div>
  );
}

/** End the session in this browser. */
export function SignOutButton() {
  const router = useRouter();
  const submission = useSubmission();
  return (
    <div className="tr-stack">
      {submission.feedback('keluar')}
      <div className="tr-row">
        <Button
          busy={submission.busy}
          busyLabel={t('Keluar…')}
          onClick={() =>
            submission.run(async () => {
              await send('POST', '/api/v1/auth/sign-out');
              router.push('/start?masuk=1');
              router.refresh();
              return t('Anda sudah keluar');
            })
          }>
          {t('Keluar')}
        </Button>
      </div>
    </div>
  );
}
