import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { dashboardApi } from "@/features/dashboard/api/dashboardApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { FilterNote } from "@/features/analytics/components/FilterNote";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, percent, toman, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Donut } from "@/shared/ui/charts/Donut";
import { StackedBar } from "@/shared/ui/charts/StackedBar";
import { Panel } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

const METHOD_COLORS = ["#1f757b", "#4fb0b3", "#d9a441", "#83cfcf"];

export function FinancePage() {
  const { queryString } = useFilters();
  const ar = useApiQuery((s) => analyticsApi.receivables(queryString, s), [queryString]);
  const methods = useApiQuery((s) => analyticsApi.paymentMethods(queryString, s), [queryString]);
  const cost = useApiQuery((s) => analyticsApi.consumableCost(queryString, s), [queryString]);
  const stock = useApiQuery((s) => dashboardApi.inventory(s));

  const d = ar.data;
  // Comes from the server rather than being recomputed here. Dividing cash
  // received in the window by what was billed in the window mixes cohorts —
  // payments settle older invoices, so a filtered month reported rates above
  // 100%. The server matches payments to the window's own invoices.
  const collectionRate = d?.collection_rate ?? 0;
  const totalCost = (cost.data ?? []).reduce((s, c) => s + c.cost, 0);
  const totalRev = (cost.data ?? []).reduce((s, c) => s + c.revenue, 0);

  return (
    <>
      <PageHeader title="مالی و انبار" subtitle="صفحه ۵ داشبورد — وصول مطالبات، روش پرداخت و بهای مواد" />
      <FilterBar />

      <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="کل صورتحساب" value={tomanShort(d?.billed ?? 0)} hint="مبلغ ناخالص فاکتورها" />
        <StatCard label="سهم بیمه" value={tomanShort(d?.insurance ?? 0)} tone="info" hint="کسرشده از فاکتور" />
        <StatCard label="وصول‌شده (نقد در بازه)" value={tomanShort(d?.collected ?? 0)} tone="positive" hint={`نرخ وصول فاکتورهای همین بازه ${percent(collectionRate)}`} />
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
                  // Cohort figure, not cash-in-period: these three must add up
                  // to the billed total, and cash from older invoices does not
                  // belong inside this window's bar.
                  { label: "وصول‌شده از بیمار", value: data.collected_on_window_invoices, color: "#1f757b" },
                  { label: "معوق", value: data.outstanding, color: "#e11d48" },
                ]}
              />
              <FilterNote endpoint="receivables" />
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
                <FilterNote endpoint="payment-methods" />
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
