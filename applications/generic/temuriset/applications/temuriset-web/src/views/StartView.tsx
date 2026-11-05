import { Button } from '@/components/tr/Button';
import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { Status } from '@/components/tr/Status';
import { PERSONA_LABEL, type Persona } from '@/features/persona';

export const PERSONA_CHOICES = [
  { value: 'inovator', label: 'Saya punya inovasi dan mencari dukungan', hint: PERSONA_LABEL.inovator },
  { value: 'mitra', label: 'Saya berinvestasi atau memberi dukungan', hint: PERSONA_LABEL.mitra },
];

type StartViewProps = {
  action: (formData: FormData) => Promise<void>;
  persona: Persona | null;
  /** True after a submission without a choice. */
  invalid: boolean;
};

/** S01: choose how to use TemuRiset. No company, institution or account is needed to look around. */
export function StartView({ action, persona, invalid }: StartViewProps) {
  return (
    <div className="tr-root tr-screen">
      <header className="tr-bar">
        <div className="tr-bar__in">
          <span className="tr-wordmark tr-sys-type-body-strong">TemuRiset</span>
        </div>
      </header>
      <div className="tr-page">
        <main id="isi" tabIndex={-1} className="tr-page__main tr-section">
          <div className="tr-page__head">
            <h1 className="tr-sys-type-heading-lg">Selamat datang di TemuRiset</h1>
            <p className="tr-muted">Pertemukan inovasi dengan investor dan mitra yang tepat.</p>
          </div>
          {invalid ? (
            <Status tone="danger" icon="alert" label="Pilihan belum dipilih" live="alert">
              <p>Pilih salah satu cara memakai TemuRiset untuk melanjutkan.</p>
            </Status>
          ) : null}
          <form action={action} className="tr-panel tr-stack">
            <input type="hidden" name="origin" value="start" />
            <ChoiceGroup
              legend="Apa yang ingin Anda lakukan?"
              name="persona"
              hint="Pilihan ini hanya mengatur menu dan bahasa, bukan hak akses."
              options={PERSONA_CHOICES}
              defaultValue={persona ?? undefined}
              required
            />
            <p className="tr-muted">
              Tanpa perusahaan atau institusi pun Anda dapat mulai. Akun dan masuk dengan email segera hadir.
            </p>
            <div className="tr-row">
              <Button type="submit" intent="primary" icon="arrow">
                Lanjutkan
              </Button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
