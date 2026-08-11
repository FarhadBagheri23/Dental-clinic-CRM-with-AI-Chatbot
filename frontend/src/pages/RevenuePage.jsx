import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, tomanShort } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Panel } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

export function RevenuePage() {
  const { queryString } = useFilters();
  const byCategory = useApiQuery((s) => analyticsApi.revenueByCategory(queryString, s), [queryString]);
  const mix = useApiQuery((s) => analyticsApi.serviceMix(queryString, s), [queryString]);

  const topByHour = [...(mix.data ?? [])].sort((a, b) => b.revenue_per_hour - a.revenue_per_hour)[0];
  const topByRevenue = mix.data?.[0];

  return (
    <>
      <PageHeader title="تحلیل درآمد و خدمات" subtitle="صفحه ۲ داشبورد — ترکیب درآمد به تفکیک دسته و خدمت" />
      <FilterBar />

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="درآمد به تفکیک دسته خدمت">
          <Panel query={byCategory}>
            {(data) => (
              <>
                <BarChart
                  data={data}
                  xKey="category"
                  bars={[{ key: "revenue", label: "درآمد", color: "#1f757b" }]}
                  formatValue={tomanShort}
                />
                <Insight>
                  دسته «{data[0].category}» با {tomanShort(data[0].revenue)} بیشترین سهم را دارد،
                  اما {num(data[0].sessions)} جلسه لازم داشته است — یعنی درآمد بالا از حجم می‌آید نه از قیمت.
                </Insight>
              </>
            )}
          </Panel>
        </Card>

        <Card title="مقایسه تعداد جلسه با درآمد">
          <Panel query={mix}>
            {(data) => (
              <>
                <BarChart
                  data={data.slice(0, 8)}
                  xKey="name"
                  bars={[{ key: "revenue", label: "درآمد", color: "#1f757b" }]}
                  line={{ key: "sessions", label: "تعداد جلسه", color: "#d9a441" }}
                  formatValue={tomanShort}
                />
                <Insight tone="warn">
                  پرتقاضاترین خدمت، پردرآمدترین نیست. خط طلایی (تعداد جلسه) و ستون‌ها هم‌راستا نیستند.
                </Insight>
              </>
            )}
          </Panel>
        </Card>
      </div>

      <Card title="۱۰ خدمت برتر — رتبه‌بندی بر پایه درآمد هر ساعت یونیت" className="mt-5" bodyClassName="">
        <Panel query={mix} rows={8}>
          {(data) => (
            <>
              <Table head={["خدمت", "دسته", "تعداد جلسه", "درآمد", "متوسط هر جلسه", "ساعت یونیت", "درآمد هر ساعت"]}>
                {[...data]
                  .sort((a, b) => b.revenue_per_hour - a.revenue_per_hour)
                  .map((s) => (
                    <Tr key={s.name}>
                      <Td bold>{s.name}</Td>
                      <Td className="text-ink-500">{s.category}</Td>
                      <Td>{num(s.sessions)}</Td>
                      <Td>{tomanShort(s.revenue)}</Td>
                      <Td>{tomanShort(s.avg_ticket)}</Td>
                      <Td className="text-ink-500">{num(s.chair_hours)}</Td>
                      <Td bold className="text-brand-700">{tomanShort(s.revenue_per_hour)}</Td>
                    </Tr>
                  ))}
              </Table>
              {topByHour && topByRevenue && (
                <div className="p-5 pt-0">
                  <Insight>
                    رتبه‌بندی بر اساس درآمد ناخالص، «{topByRevenue.name}» را در صدر می‌گذارد؛
                    اما بر پایه درآمد هر ساعت یونیت، «{topByHour.name}» با{" "}
                    {tomanShort(topByHour.revenue_per_hour)} در ساعت صدرنشین است. ظرفیت یونیت
                    محدودترین منبع کلینیک است، پس همین معیار مبنای زمان‌بندی باید باشد.
                  </Insight>
                </div>
              )}
            </>
          )}
        </Panel>
      </Card>
    </>
  );
}
