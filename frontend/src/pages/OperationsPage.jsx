import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { monthLabel, num, percent, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Heatmap } from "@/shared/ui/charts/Heatmap";
import { CardSkeleton, EmptyState, ErrorState, Skeleton } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";

// Average revenue per completed session, used to price the lost slots.
const AVG_SESSION_VALUE = 2689296;

function Panel({ query, children, rows = 5 }) {
  if (query.loading) return <CardSkeleton rows={rows} />;
  if (query.error) return <ErrorState message={query.error} />;
  const empty = Array.isArray(query.data) ? !query.data.length : !query.data;
  if (empty) return <EmptyState title="داده‌ای در این بازه نیست." hint="فیلترها را تغییر دهید." />;
  return children(query.data);
}

export function OperationsPage() {
  const { queryString } = useFilters();
  const trend = useApiQuery((s) => analyticsApi.appointmentTrend(queryString, s), [queryString]);
  const heat = useApiQuery((s) => analyticsApi.heatmap(queryString, s), [queryString]);
  const chairs = useApiQuery((s) => analyticsApi.chairs(queryString, s), [queryString]);

  const totals = (trend.data ?? []).reduce(
    (a, m) => ({
      total: a.total + m.total,
      lost: a.lost + m.cancelled + m.noshow,
      done: a.done + m.done,
    }),
    { total: 0, lost: 0, done: 0 },
  );
  const lostRate = totals.total ? (totals.lost / totals.total) * 100 : 0;
  const util = chairs.data?.assumptions;

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
              value={tomanShort(totals.lost * AVG_SESSION_VALUE)}
              tone="negative"
              hint="نوبت ازدست‌رفته × متوسط ارزش جلسه"
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
              <Insight tone="caution">
                {num(totals.lost)} نوبت ازدست‌رفته ({percent(lostRate.toFixed(1))}) معادل حدود{" "}
                {tomanShort(totals.lost * AVG_SESSION_VALUE)} درآمد بالقوه است. این ظرفیتی است
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
                  data={data.chairs.map((c) => ({ chair: `یونیت ${num(c.chair)}`, ...c }))}
                  xKey="chair"
                  bars={[{ key: "total", label: "نوبت رزروشده", color: "#1f757b" }]}
                  height={200}
                />
                <p className="mt-3 rounded-xl bg-ink-50 px-4 py-3 text-xs leading-7 text-ink-600">
                  بهره‌وری کلی: <b className="text-ink-900">{percent(data.overall_utilisation)}</b>
                  {" "}({num(data.booked_slots)} از {num(data.capacity_slots)} بازه)
                  <br />
                  مبنای محاسبه: {num(util?.chairs)} یونیت، ساعت {num(util?.open_hour)} تا {num(util?.close_hour)}،
                  {" "}{num(util?.working_days_per_week)} روز کاری، بازه‌های {num(util?.slot_minutes)} دقیقه‌ای.
                </p>
                <Insight tone="warn">
                  بهره‌وری {percent(data.overall_utilisation)} یافته است، نه خطای نمودار.
                  ظرفیت خالی یعنی رشد درآمد بدون سرمایه‌گذاری تازه ممکن است.
                </Insight>
              </>
            )}
          </Panel>
        </Card>
      </div>
    </>
  );
}
