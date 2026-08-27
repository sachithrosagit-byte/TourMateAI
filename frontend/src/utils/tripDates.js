// Date math for itineraries. Backend dates are ISO "YYYY-MM-DD" strings;
// parse them at UTC noon so local timezones can't shift the calendar day.

function parse(iso) {
  return iso ? new Date(`${iso}T12:00:00Z`) : null
}

const MS_PER_DAY = 24 * 60 * 60 * 1000

/** Inclusive number of days between two ISO dates, or null if either is missing. */
export function dayCount(startIso, endIso) {
  const start = parse(startIso)
  const end = parse(endIso)
  if (!start || !end || end < start) return null
  return Math.round((end - start) / MS_PER_DAY) + 1
}

/** "12–15 Aug 2026" / "28 Aug – 2 Sep 2026" style range, or null. */
export function formatTripRange(startIso, endIso) {
  const start = parse(startIso)
  const end = parse(endIso)
  if (!start && !end) return null
  const day = { day: 'numeric', timeZone: 'UTC' }
  const dayMonth = { day: 'numeric', month: 'short', timeZone: 'UTC' }
  const full = { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }
  if (!start || !end) return (start || end).toLocaleDateString(undefined, full)
  const sameMonth =
    start.getUTCFullYear() === end.getUTCFullYear() &&
    start.getUTCMonth() === end.getUTCMonth()
  const startLabel = start.toLocaleDateString(undefined, sameMonth ? day : dayMonth)
  return `${startLabel} – ${end.toLocaleDateString(undefined, full)}`
}

/** ISO "YYYY-MM-DD" for day N (1-based) of a trip, or null without a start date.
 *  Used to line an itinerary day up against a forecast day. */
export function dayIsoDate(startIso, dayNumber) {
  const start = parse(startIso)
  if (!start || !dayNumber) return null
  const date = new Date(start.getTime() + (dayNumber - 1) * MS_PER_DAY)
  return date.toISOString().slice(0, 10)
}

/** "Mon, 12 Aug" for day N (1-based) of a trip, or null without a start date. */
export function dayDateLabel(startIso, dayNumber) {
  const start = parse(startIso)
  if (!start || !dayNumber) return null
  const date = new Date(start.getTime() + (dayNumber - 1) * MS_PER_DAY)
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}
