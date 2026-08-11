import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { FilterNote } from "@/features/analytics/components/FilterNote";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { monthLabel, num, percent, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Heatmap } from "@/shared/ui/charts/Heatmap";
import { Panel, Skeleton } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";

export function OperationsPage() {
  const { queryString } = useFilters();
  const trend = useApiQuery((s) => analyticsApi.appointmentTrend(queryString, s), [queryString]);
  const heat = useApiQuery((s) => analyticsApi.heatmap(queryString, s), [queryString]);
  const chairs = useApiQuery((s) => analyticsApi.chairs(queryString, s), [queryString]);
  // Priced server-side: the average session value moves with the filters, so
  // a hardcoded constant here was wrong on every narrowed window.
  const lost = useApiQuery((s) => analyticsApi.lostSlots(queryString, s), [queryString]);

  const totals = (trend.data ?? []).reduce(
    (a, m) => ({
      total: a.total + m.total,
      lost: a.lost + m.cancelled + m.noshow,
      done: a.done + m.done,
    }),
    { total: 0, lost: 0, done: 0 },
  );
  const lostRate = totals.total ? (totals.lost / totals.total) * 100 : 0;
  const lostRevenue = lost.data?.lost_revenue ?? 0;
  const util = chairs.data?.assumptions;
  // The chairs are staffed for different shift lengths, so comparing the
  // shortest-staffed against the longest is the comparison that matters.
  const byShift = [...(chairs.data?.chairs ?? [])].sort(
    (a, b) => a.staffed_hours_per_day - b.staffed_hours_per_day,
  );
  const shortShift = byShift[0];
  const longShift = byShift.at(-1);

  return (
    <>
      <PageHeader title="عملیات و بهره‌وری" subtitle="صفحه ۴ داشبورد — اتلاف نوبت، الگوی مراجعه و ظرفیت یونیت" />
      <FilterBar />

      <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {trend.loading ? (
          Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-[7.5rem] rounded-2xl" />)
        ) : (
          <>
            <StatCard label="کل نوبت‌ها" value={num(totals.total)} hint="در بازه انتخاب‌شده" />
            <StatCard label="نوبت‌های انجام‌شده" value={num(totals.done)} tone="positive" hint={percent(Math.round((totals.done / (totals.total || 1)) * 100))} />
            <StatCard label="نوبت‌های ازدست‌رفته" value={num(totals.lost)} tone="negative" hint={`${percent(lostRate.toFixed(1))} لغو و غیبت`} />
            <StatCard
              label="درآمد ازدست‌رفته (برآورد)"
              value={tomanShort(lostRevenue)}
              tone="negative"
              hint={`${num(lost.data?.lost_chair_hours ?? 0)} ساعت یونیت × ${tomanShort(lost.data?.avg_session_value ?? 0)}`}
            />
          </>
        )}
      </section>

      <Card title="نرخ لغو و غیبت به تفکیک ماه">
        <Panel query={trend}>
          {(data) => (
            <>
              <BarChart
                data={data.map((m) => ({ ...m, label: monthLabel(m.month) }))}
                xKey="label"
                bars={[
                  { key: "cancel_rate", label: "نرخ لغو ٪", color: "#d9a441" },
                  { key: "noshow_rate", label: "نرخ غیبت ٪", color: "#e11d48" },
                ]}
                line={{ key: "total", label: "کل نوبت‌ها", color: "#1f757b" }}
                formatValue={(v) => percent(v)}
                height={250}
              />
              <FilterNote endpoint="appointment-trend" />
              <Insight tone="caution">
                {num(totals.lost)} نوبت ازدست‌رفته ({percent(lostRate.toFixed(1))}) معادل حدود{" "}
                {tomanShort(lostRevenue)} درآمد بالقوه است. این ظرفیتی است
                که رزرو شده اما هیچ خروجی نداشته — سیاست یادآوری پیامکی و پیش‌پرداخت،
                مستقیم روی همین عدد اثر می‌گذارد.
              </Insight>
              {data[0] && data[0].total < 50 && (
                <p className="mt-3 text-xs leading-6 text-ink-400">
                  توجه: ماه نخست بازه ({monthLabel(data[0].month)}) تنها {num(data[0].total)} نوبت دارد و
                  نرخ‌های آن به‌دلیل پایه کوچک بی‌ثبات است؛ این محدودیت پنجره تولید داده است، نه یافته عملیاتی.
                </p>
              )}
            </>
          )}
        </Panel>
      </Card>

      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        <Card title="توزیع نوبت در ساعات هفته" className="xl:col-span-2">
          <Panel query={heat} rows={7}>
            {(data) => (
              <>
                <Heatmap data={data} />
                <FilterNote endpoint="heatmap" />
                <Insight>
                  تراکم مراجعه در ساعات میانی روز است و جمعه‌ها تعطیل. خانه‌های روشن،
                  ظرفیت فروخته‌نشده‌اند — جابه‌جایی خدمات پرارزش به این ساعات،
                  بدون افزودن یونیت یا نیرو درآمد می‌سازد.
                </Insight>
              </>
            )}
          </Panel>
        </Card>

        <Card title="بهره‌وری یونیت‌ها">
          <Panel query={chairs} rows={6}>
            {(data) => (
              <>
                <BarChart
                  data={data.chairs.map((c) => ({ ...c, chair: `یونیت ${num(c.chair)}` }))}
                  xKey="chair"
                  bars={[{ key: "utilisation", label: "بهره‌وری ٪", color: "#1f757b" }]}
                  formatValue={(v) => percent(v)}
                  height={200}
                />
                <p className="mt-3 rounded-xl bg-ink-50 px-4 py-3 text-xs leading-7 text-ink-600">
                  بهره‌وری کلی: <b className="text-ink-900">{percent(data.overall_utilisation)}</b>
                  {" "}({num(data.booked_hours)} از {num(data.capacity_hours)} ساعت یونیت)
                  <br />
                  مبنای محاسبه: زمان واقعی خدمات انجام‌شده تقسیم بر ساعات <b>نیروگذاری‌شده</b>؛
                  {" "}{num(util?.chairs)} یونیت با مجموع {num(util?.staffed_hours_per_day)} ساعت در روز،
                  {" "}{num(util?.working_days_in_window)} روز کاری در این بازه.
                </p>
                <Insight tone="warn">
                  بهره‌وری {percent(data.overall_utilisation)} یافته است، نه خطای نمودار.
                  ظرفیت خالی یعنی رشد درآمد بدون سرمایه‌گذاری تازه ممکن است.
                </Insight>
                {shortShift && longShift && shortShift.utilisation > longShift.utilisation * 1.5 && (
                  <Insight tone="caution">
                    یونیت‌های با شیفت کوتاه‌تر بهره‌ورترند: یونیت {num(shortShift.chair)} با
                    {" "}{num(shortShift.staffed_hours_per_day)} ساعت نیروگذاری در روز به
                    {" "}{percent(shortShift.utilisation)} می‌رسد، اما یونیت {num(longShift.chair)} با
                    {" "}{num(longShift.staffed_hours_per_day)} ساعت تنها {percent(longShift.utilisation)}.
                    یعنی مسئله کمبود یونیت نیست؛ ساعت‌های نیروگذاری‌شده روی یونیت‌های کم‌تقاضا
                    هزینه می‌شود. کوتاه‌کردن شیفت‌های بلند، بهره‌وری را بدون از دست دادن نوبت بالا می‌برد.
                  </Insight>
                )}
              </>
            )}
          </Panel>
        </Card>
      </div>
    </>
  );
}
