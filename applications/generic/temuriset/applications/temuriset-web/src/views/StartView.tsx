'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';

import { send } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { ErrorSummary } from '@/components/tr/ErrorSummary';
import { Select } from '@/components/tr/Select';
import { TextField } from '@/components/tr/TextField';
import { PERSONA_LABEL, type Persona } from '@/features/persona';
import { codeRequest, EMAIL_PATTERN, LOCALES, savePending, TIME_ZONES, type PendingSignIn } from '@/features/signIn';
import { AuthShell } from '@/views/AuthShell';

export const PERSONA_CHOICES = [
  { value: 'inovator', label: 'Saya punya inovasi dan mencari dukungan', hint: PERSONA_LABEL.inovator },
  { value: 'mitra', label: 'Saya berinvestasi atau memberi dukungan', hint: PERSONA_LABEL.mitra },
];

type StartViewProps = {
  /** Pre-selected from the persona chosen before accounts existed. */
  persona: Persona | null;
  mode: 'sign_up' | 'sign_in';
  returnTo: string | null;
};

type Errors = Partial<Record<'persona' | 'nama' | 'email', string>>;

const FIELD_ID = { persona: 'persona-inovator', nama: 'nama', email: 'email' } as const;

/**
 * S01: choose how to use TemuRiset, say who you are and where to send the code. No organization or affiliation is
 * asked (UX-01). Every typed value stays after a failure (UX-09).
 */
export function StartView({ persona, mode, returnTo }: StartViewProps) {
  const router = useRouter();
  const form = useRef<HTMLFormElement>(null);
  const signUp = mode === 'sign_up';
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [locale, setLocale] = useState('id');
  const [timeZone, setTimeZone] = useState('Asia/Jakarta');
  const [errors, setErrors] = useState<Errors>({});
  const [failure, setFailure] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);

  function validate(chosen: string | null): Errors {
    const found: Errors = {};
    if (signUp && !chosen) found.persona = 'Pilih cara Anda memakai TemuRiset.';
    if (signUp && !name.trim()) found.nama = 'Isi nama tampilan.';
    if (!EMAIL_PATTERN.test(email.trim())) found.email = 'Isi email dengan format nama@contoh.com.';
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
      : { email: email.trim(), purpose: 'sign_in', returnTo };
    setBusy(true);
    try {
      await send('POST', '/api/v1/auth/code', codeRequest(pending));
      savePending(pending);
      router.push('/start/kode');
    } catch (error) {
      const apiError = ApiError.from(error);
      const wait = apiError.recovery.retry_after_seconds;
      setFailure(wait ? `${apiError.message} Coba lagi dalam ${Math.ceil(wait / 60)} menit.` : apiError.message);
      setAttempt((count) => count + 1);
      setBusy(false);
    }
  }

  // Switching between sign-up and sign-in keeps where the visitor was going.
  const back = returnTo ? `kembali=${encodeURIComponent(returnTo)}` : '';
  const switchHref = signUp ? `/start?masuk=1${back ? `&${back}` : ''}` : `/start${back ? `?${back}` : ''}`;
  const summary = Object.entries(errors).map(([field, message]) => ({ fieldId: FIELD_ID[field as keyof Errors], message }));

  return (
    <AuthShell
      title={signUp ? 'Selamat datang di TemuRiset' : 'Masuk ke TemuRiset'}
      subtitle={signUp ? 'Pertemukan inovasi dengan investor dan mitra yang tepat.' : 'Kami kirim kode verifikasi ke email akun Anda.'}>
      {summary.length || failure ? (
        <ErrorSummary errors={summary} focusKey={attempt}>
          {failure}
        </ErrorSummary>
      ) : null}
      <form ref={form} onSubmit={submit} noValidate className="tr-panel tr-stack">
        {signUp ? (
          <>
            <ChoiceGroup
              legend="Apa yang ingin Anda lakukan?"
              name="persona"
              hint="Pilihan ini hanya mengatur menu dan bahasa, bukan hak akses."
              options={PERSONA_CHOICES}
              defaultValue={persona ?? undefined}
              error={errors.persona}
              required
            />
            <TextField id="nama" label="Nama tampilan" value={name} onChange={setName} error={errors.nama} autoComplete="name" required />
          </>
        ) : null}
        <TextField
          id="email"
          type="email"
          label="Email"
          hint="Kode verifikasi dikirim ke sini. Email terverifikasi hanya membuktikan Anda memegang alamat ini."
          value={email}
          onChange={setEmail}
          error={errors.email}
          autoComplete="email"
          required
        />
        {signUp ? (
          <>
            <Select id="bahasa" label="Bahasa" value={locale} onChange={setLocale} options={LOCALES} emptyLabel={null} />
            <Select id="zona-waktu" label="Zona waktu" hint="Jadwal pertemuan ditampilkan dalam zona ini." value={timeZone} onChange={setTimeZone} options={TIME_ZONES} emptyLabel={null} />
            <p className="tr-muted">Tanpa perusahaan atau institusi pun Anda dapat mulai.</p>
          </>
        ) : null}
        <div className="tr-row">
          <Button type="submit" intent="primary" icon="arrow" busy={busy} busyLabel="Mengirim kode…">
            Kirim kode
          </Button>
        </div>
      </form>
      <p>
        {signUp ? 'Sudah punya akun? ' : 'Belum punya akun? '}
        <Link className="tr-link" href={switchHref}>
          {signUp ? 'Masuk' : 'Daftar'}
        </Link>
      </p>
    </AuthShell>
  );
}
