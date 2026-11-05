import { Button } from '@/components/tr/Button';
import { ChoiceGroup } from '@/components/tr/ChoiceGroup';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import type { Persona } from '@/features/persona';
import { FEATURES } from '@/features/registry';
import { ServiceStatus } from '@/features/ServiceStatus';
import { FeatureList, PersonaContext, PROVENANCE } from '@/views/parts';
import { PERSONA_CHOICES } from '@/views/StartView';

type SettingsViewProps = {
  action: (formData: FormData) => Promise<void>;
  persona: Persona;
  saved: boolean;
  invalid: boolean;
};

/** S18 in the base release: change the persona view, check the service, and read every planned feature. */
export function SettingsView({ action, persona, saved, invalid }: SettingsViewProps) {
  return (
    <Screen
      persona={persona}
      current="profil"
      title="Profil dan privasi"
      subtitle="Akun, privasi, dan laporan segera hadir."
      provenance={PROVENANCE}
      context={<PersonaContext persona={persona} />}>
      {saved ? <Status tone="success" label="Tampilan tersimpan" live /> : null}
      {invalid ? (
        <Status tone="danger" icon="alert" label="Pilihan belum dipilih" live="alert">
          <p>Pilih salah satu tampilan lalu simpan.</p>
        </Status>
      ) : null}
      <section id="tampilan" className="tr-panel tr-stack" aria-labelledby="judul-tampilan">
        <h2 id="judul-tampilan" className="tr-sys-type-heading-sm">
          Tampilan
        </h2>
        <form action={action} className="tr-stack">
          <input type="hidden" name="origin" value="settings" />
          <ChoiceGroup
            legend="Menu yang ditampilkan"
            name="persona"
            hint="Mengubah tampilan tidak mengubah data atau hak akses."
            options={PERSONA_CHOICES}
            defaultValue={persona}
            required
          />
          <div className="tr-row">
            <Button type="submit" intent="primary">
              Simpan tampilan
            </Button>
          </div>
        </form>
      </section>
      <section className="tr-stack" aria-labelledby="judul-layanan">
        <h2 id="judul-layanan" className="tr-sys-type-heading-sm">
          Layanan
        </h2>
        <ServiceStatus />
      </section>
      <div id="rencana">
        <FeatureList ids={FEATURES.map((feature) => feature.id)} title="Rencana fitur" />
      </div>
    </Screen>
  );
}
