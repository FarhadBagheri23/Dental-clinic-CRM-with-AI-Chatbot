import { PageHeader } from "@/app/layouts/PanelLayout";
import { dashboardApi } from "@/features/dashboard/api/dashboardApi";
import { num, percent, toman, tomanShort } from "@/shared/lib/format";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { Card, StatCard } from "@/shared/ui/Card";
import { AreaChart } from "@/shared/ui/charts/AreaChart";
import { BarList } from "@/shared/ui/charts/BarList";
import { Donut } from "@/shared/ui/charts/Donut";
import { CardSkeleton, EmptyState, ErrorState, Skeleton } from "@/shared/ui/Feedback";
import { Table, Td, Tr } from "@/shared/ui/Table";

const STATUS_COLORS = ["#1f757b", "#4fb0b3", "#d9a441", "#e11d48", "#9aa4a5"];

/** Renders loading / error / empty consistently so every panel behaves the
 *  same instead of each one inventing its own states. */
function Panel({ query, skeleton, children, empty }) {
  if (query.loading) return skeleton;
  if (query.error) return <ErrorState message={query.error} />;
  if (empty?.(query.data)) return <EmptyState title="داده‌ای برای نمایش نیست." />;
  return children(query.data);
}

export function DashboardPage() {
  const summary = useApiQuery((s) => dashboardApi.summary(s));
  const trend = useApiQuery((s) => dashboardApi.revenueTrend(s));
  const dentists = useApiQuery((s) => dashboardApi.dentists(s));
  const services = useApiQuery((s) => dashboardApi.services(s));
  const inventory = useApiQuery((s) => dashboardApi.inventory(s));

  const kpi = summary.data;
  const critical = inventory.data?.filter((c) => c.critical) ?? [];

  return (
    <>
      <PageHeader title="داشبورد مدیریتی" subtitle="نمای کلی عملکرد کلینیک بر اساس داده‌های ثبت‌شده">
        <span className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          متصل به پایگاه داده
        </span>
      </PageHeader>

      {/* --------------------------------------------------------- KPIs */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summary.loading
          ? Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-[7.5rem] rounded-2xl" />)
          : summary.error
            ? <ErrorState message={summary.error} className="sm:col-span-2 xl:col-span-4" />
            : (
              <>
                <StatCard
                  label="درآمد کل"
                  value={tomanShort(kpi.revenue)}
                  hint={`${num(kpi.counts.sessions)} جلسه درمان`}
                />
                <StatCard
                  label="وصول‌شده"
                  value={tomanShort(kpi.collected)}
                  hint={`نرخ وصول ${percent(kpi.collection_rate)}`}
                  tone="positive"
                />
                <StatCard
                  label="مطالبات معوق"
                  value={tomanShort(kpi.outstanding)}
                  hint="سهم بیمار پرداخت‌نشده"
                  tone={kpi.outstanding > 0 ? "negative" : "default"}
                />
                <StatCard
                  label="سهم بیمه‌ها"
                  value={tomanShort(kpi.insurance_covered)}
                  hint="کسرشده از فاکتورها"
                  tone="info"
                />
              </>
            )}
      </section>

      {kpi && (
        <section className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="بیماران" value={num(kpi.counts.patients)} hint="پرونده ثبت‌شده" />
          <StatCard label="کل نوبت‌ها" value={num(kpi.counts.appointments)} hint="۱۲ ماه گذشته" />
          <StatCard label="نوبت‌های پیش‌رو" value={num(kpi.counts.upcoming)} hint="در انتظار مراجعه" tone="info" />
          <StatCard
            label="اقلام نیازمند سفارش"
            value={num(critical.length)}
            hint="زیر حد سفارش"
            tone={critical.length ? "negative" : "positive"}
          />
        </section>
      )}

      {/* ------------------------------------------------ revenue trend */}
      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <Card title="روند درآمد و وصولی" className="xl:col-span-2">
          <Panel query={trend} skeleton={<Skeleton className="h-56 rounded-xl" />} empty={(d) => !d?.length}>
            {(data) => (
              <AreaChart
                data={data}
                series={[
                  { key: "revenue", label: "درآمد", color: "#1f757b" },
                  { key: "collected", label: "وصول‌شده", color: "#d9a441" },
                ]}
              />
            )}
          </Panel>
        </Card>

        <Card title="وضعیت نوبت‌ها">
          <Panel query={summary} skeleton={<CardSkeleton rows={4} />} empty={(d) => !d?.appointment_status?.length}>
            {(data) => (
              <Donut
                data={data.appointment_status}
                colors={STATUS_COLORS}
                centerLabel="کل نوبت‌ها"
                centerValue={num(data.counts.appointments)}
              />
            )}
          </Panel>
        </Card>
      </div>

      {/* ------------------------------------------- dentists & services */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card title="عملکرد پزشکان" bodyClassName="p-3">
          <Panel query={dentists} skeleton={<div className="p-2"><CardSkeleton rows={5} /></div>} empty={(d) => !d?.length}>
            {(data) => (
              <BarList
                items={data.map((d) => ({
                  label: d.name,
                  sub: d.specialty,
                  value: d.revenue,
                  display: tomanShort(d.revenue),
                }))}
              />
            )}
          </Panel>
        </Card>

        <Card title="خدمات پردرآمد" bodyClassName="">
          <Panel query={services} skeleton={<div className="p-5"><CardSkeleton rows={5} /></div>} empty={(d) => !d?.length}>
            {(data) => (
              <Table head={["خدمت", "دسته", "تعداد", "درآمد"]}>
                {data.map((s) => (
                  <Tr key={s.name}>
                    <Td bold>{s.name}</Td>
                    <Td className="text-ink-500">{s.category}</Td>
                    <Td>{num(s.n)}</Td>
                    <Td bold>{tomanShort(s.revenue)}</Td>
                  </Tr>
                ))}
              </Table>
            )}
          </Panel>
        </Card>
      </div>

      {/* ------------------------------------------------------ inventory */}
      <Card title="اقلام رو به اتمام" className="mt-5" bodyClassName="">
        <Panel
          query={inventory}
          skeleton={<div className="p-5"><CardSkeleton rows={4} /></div>}
          empty={(d) => !d?.length}
        >
          {(data) => (
            <Table head={["قلم", "موجودی", "حد سفارش", "تأمین‌کننده", "وضعیت"]}>
              {data.slice(0, 8).map((c) => (
                <Tr key={c.consumable_id}>
                  <Td bold>{c.name}</Td>
                  <Td>{`${num(c.stock_quantity)} ${c.unit}`}</Td>
                  <Td className="text-ink-500">{num(c.min_stock_level)}</Td>
                  <Td className="text-ink-500">{c.supplier ?? "—"}</Td>
                  <Td>
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${
                        c.critical
                          ? "border-rose-200 bg-rose-50 text-rose-700"
                          : "border-accent-200 bg-accent-50 text-accent-700"
                      }`}
                    >
                      {c.critical ? "بحرانی" : "نزدیک به حد"}
                    </span>
                  </Td>
                </Tr>
              ))}
            </Table>
          )}
        </Panel>
      </Card>

      <p className="mt-6 text-center text-xs text-ink-400">
        مجموع درآمد ثبت‌شده: {kpi ? toman(kpi.revenue) : "—"}
      </p>
    </>
  );
}
