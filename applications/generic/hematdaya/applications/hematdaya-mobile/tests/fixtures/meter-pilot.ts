/** One model in the pilot's server catalog. */
export const plannedMeter = {
  id: 'shelly-plug-pm-gen3',
  name: 'Shelly Plug PM Gen3',
  status: 'planned',
  measurement_kind: 'counter',
  cadence_seconds: 60,
  scope_kind: 'device',
} as const;
