import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { dashboardApi } from "@/features/dashboard/api/dashboardApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, percent, toman, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Donut } from "@/shared/ui/charts/Donut";
import { StackedBar } from "@/shared/ui/charts/StackedBar";
import { CardSkeleton, EmptyState, ErrorState } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

const METHOD_COLORS = ["#1f757b", "#4fb0b3", "#d9a441", "#83cfcf"];

function Panel({ query, children, rows = 5 }) {
  if (query.loading) return <CardSkeleton rows={rows} />;
  if (query.error) return <ErrorState message={query.error} />;
  const empty = Array.isArray(query.data) ? !query.data.length : !query.data;
  if (empty) return <EmptyState title="داده‌ای در این بازه نیست." hint="فیلترها را تغییر دهید." />;
  return children(query.data);
}

export function FinancePage() {
  const { queryString } = useFilters();
  const ar = useApiQuery((s) => analyticsApi.receivables(queryString, s), [queryString]);
  const methods = useApiQuery((s) => analyticsApi.paymentMethods(queryString, s), [queryString]);
  const cost = useApiQuery((s) => analyticsApi.consumableCost(queryString, s), [queryString]);
  const stock = useApiQuery((s) => dashboardApi.inventory(s));

  const d = ar.data;
  const collectionRate = d?.patient_share ? (d.collected / d.patient_share) * 100 : 0;
  const totalCost = (cost.data ?? []).reduce((s, c) => s + c.cost, 0);
  const totalRev = (cost.data ?? []).reduce((s, c) => s + c.revenue, 0);

  return (
    <>
      <PageHeader title="مالی و انبار" subtitle="صفحه ۵ داشبورد — وصول مطالبات، روش پرداخت و بهای مواد" />
      <FilterBar />

      <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="کل صورتحساب" value={tomanShort(d?.billed ?? 0)} hint="مبلغ ناخالص فاکتورها" />
        <StatCard label="سهم بیمه" value={tomanShort(d?.insurance ?? 0)} tone="info" hint="کسرشده از فاکتور" />
        <StatCard label="وصول‌شده" value={tomanShort(d?.collected ?? 0)} tone="positive" hint={`نرخ وصول ${percent(collectionRate.toFixed(1))}`} />
        <StatCard label="مطالبات معوق" value={tomanShort(d?.outstanding ?? 0)} tone="negative" hint="سهم بیمار پرداخت‌نشده" />
      </section>

      <Card title="زنجیره وصول مطالبات">
        <Panel query={ar} rows={3}>
          {(data) => (
            <>
              <StackedBar
                total={data.billed}
                segments={[
                  { label: "سهم بیمه", value: data.insurance, color: "#83cfcf" },
                  { label: "وصول‌شده از بیمار", value: data.collected, color: "#1f757b" },
                  { label: "معوق", value: data.outstanding, color: "#e11d48" },
                ]}
              />
              <Insight tone="caution">
                {percent((100 - collectionRate).toFixed(1))} از سهم بیمار وصول نشده است
                ({toman(data.outstanding)}). این رقم سرمایه در گردشی است که کلینیک
                تأمین کرده اما دریافت نکرده — سیاست پیش‌پرداخت برای خدمات گران، مستقیم‌ترین اهرم است.
              </Insight>
            </>
          )}
        </Panel>
      </Card>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card title="تفکیک روش پرداخت">
          <Panel query={methods} rows={4}>
            {(data) => (
              <>
                <Donut
                  data={data.map((m) => ({ status: m.method, n: m.n }))}
                  colors={METHOD_COLORS}
                  centerLabel="تراکنش"
                  centerValue={num(data.reduce((s, m) => s + m.n, 0))}
                />
                <Table head={["روش", "تعداد", "مبلغ"]}>
                  {data.map((m) => (
                    <Tr key={m.method}>
                      <Td bold>{m.method}</Td>
                      <Td>{num(m.n)}</Td>
                      <Td bold>{tomanShort(m.amount)}</Td>
                    </Tr>
                  ))}
                </Table>
              </>
            )}
          </Panel>
        </Card>

        <Card title="بهای مواد مصرفی به تفکیک دسته خدمت">
          <Panel query={cost} rows={4}>
            {(data) => (
              <>
                <BarChart
                  data={data}
                  xKey="category"
                  bars={[
                    { key: "revenue", label: "درآمد", color: "#1f757b" },
                    { key: "cost", label: "بهای مواد", color: "#d9a441" },
                  ]}
                  formatValue={tomanShort}
                />
                <Insight>
                  بهای مواد مصرفی {tomanShort(totalCost)} است، معادل{" "}
                  {percent(((totalCost / (totalRev || 1)) * 100).toFixed(1))} درآمد مرتبط.
                  دسته‌هایی که ستون طلایی‌شان نسبت به ستون سبز بلندتر است، حاشیه سود کمتری دارند.
                </Insight>
              </>
            )}
          </Panel>
        </Card>
      </div>

      <Card title="اقلام زیر حد سفارش" className="mt-5" bodyClassName="">
        <Panel query={stock} rows={5}>
          {(items) => (
            <Table head={["قلم", "موجودی", "حد سفارش", "قیمت واحد", "ارزش موجودی", "تأمین‌کننده", "وضعیت"]}>
              {items.map((c) => (
                <Tr key={c.consumable_id}>
                  <Td bold>{c.name}</Td>
                  <Td className={c.critical ? "font-bold text-rose-700" : ""}>
                    {`${num(c.stock_quantity)} ${c.unit}`}
                  </Td>
                  <Td className="text-ink-500">{num(c.min_stock_level)}</Td>
                  <Td>{toman(c.unit_price)}</Td>
                  <Td>{tomanShort(c.stock_quantity * c.unit_price)}</Td>
                  <Td className="text-ink-500">{c.supplier ?? "—"}</Td>
                  <Td>
                    <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${
                      c.critical
                        ? "border-rose-200 bg-rose-50 text-rose-700"
                        : "border-accent-200 bg-accent-50 text-accent-700"
                    }`}>
                      {c.critical ? "بحرانی" : "نزدیک به حد"}
                    </span>
                  </Td>
                </Tr>
              ))}
            </Table>
          )}
        </Panel>
      </Card>
    </>
  );
}
