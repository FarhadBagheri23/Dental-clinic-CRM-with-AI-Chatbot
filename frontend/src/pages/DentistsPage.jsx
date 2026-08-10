import { useFilters } from "@/app/providers/FiltersProvider";
import { PageHeader } from "@/app/layouts/PanelLayout";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, percent, tomanShort } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { BarList } from "@/shared/ui/charts/BarList";
import { CardSkeleton, EmptyState, ErrorState } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

export function DentistsPage() {
  const { queryString } = useFilters();
  const q = useApiQuery((s) => analyticsApi.dentists(queryString, s), [queryString]);
  const data = q.data ?? [];

  const totalRevenue = data.reduce((s, d) => s + d.revenue, 0) || 1;
  const topTwoShare = data.slice(0, 2).reduce((s, d) => s + d.revenue, 0) / totalRevenue;
  // Highest revenue vs highest margin — different people when commission varies.
  const byMargin = [...data].sort((a, b) => b.margin - a.margin);
  const inversion = data[0] && byMargin[0] && data[0].name !== byMargin[0].name;
  const leastReliable = [...data].sort(
    (a, b) => b.cancel_rate + b.noshow_rate - (a.cancel_rate + a.noshow_rate),
  )[0];

  if (q.loading) {
    return (
      <>
        <PageHeader title="عملکرد پزشکان" subtitle="صفحه ۳ داشبورد" />
        <FilterBar />
        <Card><CardSkeleton rows={8} /></Card>
      </>
    );
  }
  if (q.error) return <><PageHeader title="عملکرد پزشکان" /><FilterBar /><ErrorState message={q.error} /></>;
  if (!data.length) {
    return (
      <>
        <PageHeader title="عملکرد پزشکان" subtitle="صفحه ۳ داشبورد" />
        <FilterBar />
        <Card><EmptyState title="داده‌ای در این بازه نیست." hint="فیلترها را تغییر دهید." /></Card>
      </>
    );
  }

  return (
    <>
      <PageHeader title="عملکرد پزشکان" subtitle="صفحه ۳ داشبورد — درآمد، کمیسیون و پایداری" />
      <FilterBar />

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="درآمد هر پزشک" bodyClassName="p-3">
          <BarList
            items={data.map((d) => ({
              label: d.name, sub: d.specialty, value: d.revenue, display: tomanShort(d.revenue),
            }))}
          />
        </Card>

        <Card title="تعداد جلسات هر پزشک">
          <BarChart
            data={data.map((d) => ({ name: d.name.replace("دکتر ", ""), sessions: d.sessions }))}
            xKey="name"
            bars={[{ key: "sessions", label: "جلسه", color: "#4fb0b3" }]}
          />
          <Insight tone="warn">
            ترتیب این نمودار با نمودار درآمد یکی نیست: پزشکی که بیشترین جلسه را دارد،
            لزوماً بیشترین درآمد را نمی‌سازد — تفاوت در نوع خدمت است، نه در تلاش.
          </Insight>
        </Card>
      </div>

      <Card title="کمیسیون و حاشیه سود کلینیک" className="mt-5" bodyClassName="">
        <Table head={["پزشک", "تخصص", "جلسات", "بیماران", "درآمد", "نرخ کمیسیون", "کمیسیون", "سهم کلینیک", "لغو", "غیبت"]}>
          {data.map((d) => (
            <Tr key={d.dentist_id}>
              <Td bold>{d.name}</Td>
              <Td className="text-ink-500">{d.specialty}</Td>
              <Td>{num(d.sessions)}</Td>
              <Td>{num(d.patients)}</Td>
              <Td bold>{tomanShort(d.revenue)}</Td>
              <Td className="text-ink-500">{percent(d.commission_rate)}</Td>
              <Td className="text-accent-700">{tomanShort(d.commission)}</Td>
              <Td bold className="text-emerald-700">{tomanShort(d.margin)}</Td>
              <Td className={d.cancel_rate > 10 ? "font-bold text-rose-700" : ""}>{percent(d.cancel_rate)}</Td>
              <Td className={d.noshow_rate > 8 ? "font-bold text-rose-700" : ""}>{percent(d.noshow_rate)}</Td>
            </Tr>
          ))}
        </Table>

        <div className="space-y-3 p-5 pt-4">
          <Insight tone="caution">
            تمرکز {percent(Math.round(topTwoShare * 100))} از درآمد روی دو پزشک
            ({data[0].name} و {data[1]?.name}) یک ریسک عملیاتی است: خروج یکی از آن‌ها
            بخش بزرگی از درآمد را همزمان از بین می‌برد.
          </Insight>

          {inversion && (
            <Insight tone="warn">
              وارونگی کمیسیون: بیشترین درآمد متعلق به {data[0].name} است، اما بیشترین سهم
              خالص برای کلینیک را {byMargin[0].name} می‌سازد
              ({tomanShort(byMargin[0].margin)}) — چون نرخ کمیسیون از {percent(data[0].commission_rate)} تا{" "}
              {percent(byMargin[0].commission_rate)} تفاوت دارد. رتبه‌بندی بر پایه درآمد ناخالص گمراه‌کننده است.
            </Insight>
          )}

          {leastReliable && (
            <Insight>
              بیشترین اتلاف نوبت مربوط به {leastReliable.name} است:
              {" "}{percent(leastReliable.cancel_rate)} لغو و {percent(leastReliable.noshow_rate)} غیبت.
            </Insight>
          )}
        </div>
      </Card>
    </>
  );
}
