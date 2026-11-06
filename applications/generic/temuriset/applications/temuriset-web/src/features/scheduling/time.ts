/** Time on screen: stored instants are UTC; every reader sees them in their own IANA zone (FR-002). */

const ZONES: Record<string, string> = { 'Asia/Jakarta': 'WIB', 'Asia/Makassar': 'WITA', 'Asia/Jayapura': 'WIT' };

function format(iso: string, zone: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat('id-ID', { timeZone: zone, ...options }).format(new Date(iso));
}

/** "WIB (Asia/Jakarta)", or the IANA name for zones without an Indonesian abbreviation. */
export function zoneLabel(zone: string): string {
  return ZONES[zone] ? `${ZONES[zone]} (${zone})` : zone;
}

export function longDate(iso: string, zone: string): string {
  return format(iso, zone, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
}

export function clock(iso: string, zone: string): string {
  return format(iso, zone, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
}

/** "16.00–17.00 WIB (Asia/Jakarta)" for a half-open interval. */
export function slotTime(start: string, end: string, zone: string): string {
  return `${clock(start, zone)}–${clock(end, zone)} ${zoneLabel(zone)}`;
}

/** The viewer's wall-clock value for `<input type="datetime-local">`, from a UTC instant. */
export function toLocalInput(iso: string, zone: string): string {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
      .formatToParts(new Date(iso))
      .map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** The UTC instant of a wall-clock value in a zone, e.g. "2026-11-04T16:00" in Asia/Jakarta is 09:00Z. */
export function fromLocalInput(value: string, zone: string): string {
  const guess = new Date(`${value}:00Z`);
  // Shift by the zone's offset at that moment; twice, so a change of offset in between still lands right.
  let instant = guess.getTime();
  for (let step = 0; step < 2; step += 1) {
    const shown = new Date(`${toLocalInput(new Date(instant).toISOString(), zone)}:00Z`).getTime();
    instant += guess.getTime() - shown;
  }
  return new Date(instant).toISOString();
}
