/** Jalali (Shamsi) calendar helpers.
 *
 *  ponytail: no jalaali-js / moment-jalaali dependency. ICU already ships the
 *  Persian calendar, so every conversion here is a `Intl.DateTimeFormat` call
 *  plus day arithmetic on a Gregorian Date — the leap-year rules stay in ICU
 *  where they are already correct, and nothing has to be kept in sync.
 *
 *  Dates cross the API as Gregorian ISO `YYYY-MM-DD`; Jalali is presentation
 *  only, so the backend and the stored data are untouched.
 */

const parts = new Intl.DateTimeFormat("en-US-u-ca-persian", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
});

const titleFmt = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  year: "numeric",
  month: "long",
});

const dayFmt = new Intl.DateTimeFormat("fa-IR-u-ca-persian", { day: "numeric" });

const fullFmt = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

/** Saturday-first, matching the Persian week. */
export const WEEKDAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

/** Jalali {year, month, day} for a Gregorian Date. */
export function toJalali(d) {
  const p = Object.fromEntries(parts.formatToParts(d).map((x) => [x.type, x.value]));
  // The Persian era part is dropped; `year` stays a plain AP number.
  return { year: Number(p.year), month: Number(p.month), day: Number(p.day) };
}

export const jalaliTitle = (d) => titleFmt.format(d);
export const jalaliDay = (d) => dayFmt.format(d);
export const jalaliDate = (d) => fullFmt.format(d);

const DAY = 86400000;
export const addDays = (d, n) => new Date(d.getTime() + n * DAY);

/** Gregorian Date of the 1st of the Jalali month containing `d`. */
export const startOfJalaliMonth = (d) => addDays(d, 1 - toJalali(d).day);

/** Every Gregorian day in `d`'s Jalali month, in order. */
export function jalaliMonthDays(d) {
  const first = startOfJalaliMonth(d);
  const month = toJalali(first).month;
  const days = [];
  // A Jalali month is 29–31 days; walking until the month rolls over avoids
  // hardcoding which months are long and which year is leap.
  for (let i = 0; i < 32; i++) {
    const day = addDays(first, i);
    if (toJalali(day).month !== month) break;
    days.push(day);
  }
  return days;
}

/** Blank cells before the 1st, so it lands under the right weekday column. */
export const leadingBlanks = (first) => (first.getDay() + 1) % 7;

/** `YYYY-MM-DD` in local time — `toISOString` would shift across UTC. */
export function toISODate(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Parses `YYYY-MM-DD` as a local midnight Date; `null` for anything else. */
export function fromISODate(s) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s ?? "")) return null;
  const [y, m, d] = s.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return Number.isNaN(date.getTime()) ? null : date;
}

export const sameDay = (a, b) => a && b && toISODate(a) === toISODate(b);
