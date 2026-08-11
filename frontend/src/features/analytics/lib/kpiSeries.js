/** Turns the /analytics/kpis monthly series into card-ready figures.
 *
 *  The one rule worth stating: months from the current calendar month onward
 *  are dropped. The dataset carries appointments booked into the future and
 *  the running month is only part-elapsed, so a raw "latest vs previous"
 *  comparison reports every KPI as collapsing — the classic incomplete-period
 *  artefact that makes a BI dashboard untrustworthy on the day it ships.
 */

const currentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export function completeMonths(rows) {
  const cutoff = currentMonth();
  return (rows ?? []).filter((r) => r.month < cutoff);
}

/** Percentage change of `key` between the last two complete months. */
export function momDelta(rows, key) {
  if (rows.length < 2) return null;
  const [prev, last] = rows.slice(-2).map((r) => Number(r[key]) || 0);
  // A jump from nothing is not a percentage anyone can act on.
  if (!prev) return null;
  return ((last - prev) / prev) * 100;
}

export const seriesOf = (rows, key) => rows.map((r) => Number(r[key]) || 0);

export const sumOf = (rows, key) => rows.reduce((s, r) => s + (Number(r[key]) || 0), 0);

/** Latest complete month's value — for stock-like metrics where summing
 *  twelve months would be meaningless (patient counts, not money). */
export const latestOf = (rows, key) => (rows.length ? Number(rows.at(-1)[key]) || 0 : 0);

export const monthsCovered = (rows) => rows.length;
