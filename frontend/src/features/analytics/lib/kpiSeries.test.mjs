// node --test src/features/analytics/lib/kpiSeries.test.mjs
import assert from "node:assert/strict";
import test from "node:test";

import { completeMonths, latestOf, momDelta, seriesOf, sumOf } from "./kpiSeries.js";

const thisMonth = () => {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}`;
};
const shift = (months) => {
  const n = new Date();
  n.setMonth(n.getMonth() + months);
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}`;
};

test("the running month and anything after it are excluded", () => {
  const rows = [
    { month: shift(-2), revenue: 100 },
    { month: shift(-1), revenue: 200 },
    { month: thisMonth(), revenue: 7 },   // part-elapsed
    { month: shift(1), revenue: 0 },      // future bookings
  ];
  assert.deepEqual(completeMonths(rows).map((r) => r.month), [shift(-2), shift(-1)]);
});

test("momDelta compares the last two complete months", () => {
  const rows = [{ month: "2026-05", v: 200 }, { month: "2026-06", v: 150 }];
  assert.equal(momDelta(rows, "v"), -25);

  const up = [{ month: "2026-05", v: 200 }, { month: "2026-06", v: 260 }];
  assert.equal(momDelta(up, "v"), 30);
});

test("a delta from zero is suppressed rather than reported as infinite", () => {
  // Growth from nothing is not a percentage a manager can act on, and
  // Infinity would render as garbage in the chip.
  assert.equal(momDelta([{ month: "a", v: 0 }, { month: "b", v: 500 }], "v"), null);
  assert.equal(momDelta([{ month: "a", v: 5 }], "v"), null, "one month has no predecessor");
  assert.equal(momDelta([], "v"), null);
});

test("series, sum and latest read the same rows", () => {
  const rows = [{ month: "a", v: 1 }, { month: "b", v: 2 }, { month: "c", v: 3 }];
  assert.deepEqual(seriesOf(rows, "v"), [1, 2, 3]);
  assert.equal(sumOf(rows, "v"), 6);
  assert.equal(latestOf(rows, "v"), 3);
  // Missing keys must not poison the arithmetic with NaN.
  assert.deepEqual(seriesOf([{ month: "a" }], "v"), [0]);
  assert.equal(sumOf([{ month: "a" }], "v"), 0);
});
