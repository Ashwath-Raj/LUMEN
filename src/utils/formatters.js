/** Formats a Date/ISO string as the "09:44:12" / "14:01:22Z" style timestamp seen throughout the logs. */
export function formatOpsTimestamp(date, { withZone = false } = {}) {
  const d = new Date(date);
  const time = d.toISOString().substring(11, 19);
  return withZone ? `${time}Z` : time;
}

/** Formats a case/reference ID with the platform's dash convention, e.g. CASE-2024-0892. */
export function formatReferenceId(prefix, year, sequence) {
  return `${prefix}-${year}-${String(sequence).padStart(4, '0')}`;
}

/** Formats lat/lng as the "47.6062° N, 122.3321° W" style used in incident cards. */
export function formatCoordinates(lat, lng) {
  const latDir = lat >= 0 ? 'N' : 'S';
  const lngDir = lng >= 0 ? 'E' : 'W';
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lng).toFixed(4)}° ${lngDir}`;
}
