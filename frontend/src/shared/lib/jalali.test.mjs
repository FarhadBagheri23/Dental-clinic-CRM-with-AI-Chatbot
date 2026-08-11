// node --test src/shared/lib/jalali.test.mjs
import assert from "node:assert/strict";
import test from "node:test";

import {
  addDays,
  fromISODate,
  jalaliMonthDays,
  leadingBlanks,
  startOfJalaliMonth,
  toISODate,
  toJalali,
} from "./jalali.js";

test("Gregorian -> Jalali on a known Nowruz", () => {
  // 1404-01-01 fell on 2025-03-21.
  assert.deepEqual(toJalali(new Date(2025, 2, 21)), { year: 1404, month: 1, day: 1 });
});

test("month grid covers exactly one Jalali month", () => {
  // Esfand 1403 is a leap Esfand: 30 days.
  const days = jalaliMonthDays(new Date(2025, 2, 1));
  assert.equal(days.length, 30);
  assert.deepEqual(toJalali(days[0]), { year: 1403, month: 12, day: 1 });
  assert.deepEqual(toJalali(days.at(-1)), { year: 1403, month: 12, day: 30 });

  // First six months are 31 days, next five are 30.
  assert.equal(jalaliMonthDays(new Date(2025, 3, 15)).length, 31); // Farvardin
  assert.equal(jalaliMonthDays(new Date(2025, 9, 15)).length, 30); // Mehr
});

test("leadingBlanks puts the 1st under its weekday, Saturday-first", () => {
  // 1404-01-01 = Friday 2025-03-21, the last column of a Saturday-first week.
  assert.equal(leadingBlanks(new Date(2025, 2, 21)), 6);
  // 1404-02-01 = Monday 2025-04-21 -> two blanks (Sat, Sun).
  assert.equal(leadingBlanks(new Date(2025, 3, 21)), 2);
});

test("month navigation lands on month boundaries", () => {
  const days = jalaliMonthDays(new Date(2025, 3, 15)); // Farvardin 1404
  assert.deepEqual(toJalali(addDays(days.at(-1), 1)), { year: 1404, month: 2, day: 1 });
  assert.deepEqual(
    toJalali(startOfJalaliMonth(addDays(days[0], -1))),
    { year: 1403, month: 12, day: 1 },
  );
});

test("ISO round-trip stays on the same local day", () => {
  // toISOString() would report 2025-03-20 for a UTC+N locale — the bug this guards.
  assert.equal(toISODate(new Date(2025, 2, 21)), "2025-03-21");
  assert.equal(toISODate(fromISODate("2026-01-01")), "2026-01-01");
  assert.equal(fromISODate("nope"), null);
  assert.equal(fromISODate(""), null);
});
