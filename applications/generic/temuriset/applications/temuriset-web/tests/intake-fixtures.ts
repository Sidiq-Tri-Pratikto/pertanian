import type { Mandate, PartnerProfile } from '@/features/intake/model';

import { PERSONAL } from './fixtures';

export const OTHER_PARTY = '00000000-0000-4000-8000-0000000000ee';

export const MITRA_A: PartnerProfile = {
  party_id: PERSONAL,
  party_name: 'Mitra A',
  version: 1,
  subtype: 'Mitra validasi prototipe',
  thesis: 'Membantu prototipe menjadi siap uji lapangan.',
  sectors: ['Air dan sanitasi', 'Pertanian'],
  stages: ['PROTOTYPE', 'PILOT'],
  regions: ['Indonesia'],
  support_forms: ['Pendanaan proyek', 'Fasilitas uji'],
  relationship_forms: ['PROJECT'],
  review_expectations: '',
  check_range: null,
  availability: {
    source: 'OWNER_CONFIRMED',
    source_label: 'Dikonfirmasi pemilik profil',
    intake_status: 'OPEN',
    current_intake_status: 'OPEN',
    label: 'Pitching dibuka',
    intake_from: null,
    intake_until: null,
  },
  contact_route: 'IN_APP',
  external_url: null,
  operation_id: null,
};

export const RECIPIENT_E: PartnerProfile = {
  ...MITRA_A,
  party_id: OTHER_PARTY,
  party_name: 'Dana Riset E',
  subtype: 'Direktori pendanaan',
  thesis: 'Pendanaan riset terapan.',
  stages: [],
  regions: [],
  support_forms: ['Hibah'],
  availability: {
    source: 'SOURCE_REPORTED',
    source_label: 'Dilaporkan sumber',
    intake_status: 'UNCONFIRMED',
    current_intake_status: 'UNCONFIRMED',
    label: 'Ketersediaan belum dikonfirmasi',
    intake_from: null,
    intake_until: null,
  },
  contact_route: 'EXTERNAL',
  external_url: 'https://example.org/formulir-demo',
};

export const INVESTOR_B: PartnerProfile = {
  ...MITRA_A,
  party_name: 'Investor B',
  check_range: {
    subject: 'investorCheck',
    basis: 'per_investment',
    min: '50000.0000',
    max: '150000.0000',
    currency: 'USD',
    period: 'per investasi',
    months: null,
    unknown_reason: null,
  },
};

const stageRequirement: Mandate['requirements'][number] = {
  id: 'r1',
  label: 'Tahap inovasi',
  field: 'stage',
  operator: 'in_set',
  value: ['PROTOTYPE', 'PILOT'],
  mandatory: true,
  applies_at: 'SUBMISSION',
  verification_mode: 'DECLARATION',
  visibility: 'PUBLIC',
  reason: 'Mitra ini hanya menguji inovasi yang sudah memiliki prototipe.',
  version: 1,
};

export const A1: Mandate = {
  id: 'a1',
  partner_party_id: PERSONAL,
  version: 2,
  current_version_id: 'a1-v2',
  kind: 'SPECIFIC',
  status: 'ACTIVE',
  closes_at: '2027-03-01T00:00:00Z',
  number: 1,
  title: 'Validasi prototipe enam bulan',
  outcome: 'Prototipe teruji di lapangan dalam enam bulan.',
  included: 'Uji fungsi dan uji lapangan terbatas',
  excluded: 'Sertifikasi dan produksi massal',
  support: 'Pendanaan proyek dan pendampingan uji',
  accepted_stages: ['PROTOTYPE', 'PILOT'],
  relationship_forms: ['PROJECT'],
  sectors: ['Air dan sanitasi'],
  keywords: ['prototipe', 'validasi'],
  timing: 'Dibuka sampai 31 Desember 2026',
  financial: {
    subject: 'partner',
    basis: 'total_period',
    min: '15000.0000',
    max: '40000.0000',
    currency: 'USD',
    period: '6 bulan',
    months: 6,
    scope: 'biaya pilot enam bulan',
    noncash: '',
    terms: '',
    unknown_reason: null,
  },
  requirements: [stageRequirement],
  target_availability: { available: true, reason: null },
  general_intake_label: null,
  operation_id: null,
};

export const DRAFT: Mandate = { ...A1, id: 'd1', version: 1, status: 'DRAFT', target_availability: { available: false, reason: 'TARGET_NOT_ACTIVE' } };
