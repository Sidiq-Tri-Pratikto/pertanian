import { HDTag } from '@/components/hd/HDTag';

/** Says where the numbers on a screen come from. Every screen with demo data shows it. */
export function HDProvenanceTag({ origins }: { origins: string[] }) {
  if (origins.includes('simulated')) {
    return <HDTag>Demo · Data simulasi</HDTag>;
  }
  if (origins.includes('import')) {
    return <HDTag>Data impor</HDTag>;
  }
  return null;
}
