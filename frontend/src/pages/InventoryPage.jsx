import { PageHeader } from "@/app/layouts/PanelLayout";
import { dashboardApi } from "@/features/dashboard/api/dashboardApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, toman } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { CardSkeleton, EmptyState, ErrorState } from "@/shared/ui/Feedback";
import { Table, Td, Tr } from "@/shared/ui/Table";

export function InventoryPage() {
  const result = useApiQuery((s) => dashboardApi.inventory(s));
  const items = result.data ?? [];
  const critical = items.filter((c) => c.critical);

  return (
    <>
      <PageHeader title="انبار اقلام مصرفی" subtitle="اقلامی که به حد سفارش نزدیک شده‌اند یا از آن گذشته‌اند" />

      <section className="mb-5 grid gap-4 sm:grid-cols-3">
        <StatCard label="اقلام بحرانی" value={num(critical.length)} hint="زیر حد سفارش" tone={critical.length ? "negative" : "positive"} />
        <StatCard label="نزدیک به حد سفارش" value={num(items.length - critical.length)} hint="تا ۱٫۵ برابر حد" tone="info" />
        <StatCard
          label="ارزش موجودی این اقلام"
          value={toman(items.reduce((sum, c) => sum + c.stock_quantity * c.unit_price, 0))}
          hint="بر اساس قیمت واحد"
        />
      </section>

      <Card bodyClassName="">
        {result.loading ? (
          <div className="p-5"><CardSkeleton rows={7} /></div>
        ) : result.error ? (
          <div className="p-5"><ErrorState message={result.error} /></div>
        ) : items.length === 0 ? (
          <EmptyState title="همه اقلام بالای حد سفارش هستند." hint="نیازی به سفارش جدید نیست." />
        ) : (
          <Table head={["قلم", "موجودی", "حد سفارش", "قیمت واحد", "تأمین‌کننده", "وضعیت"]}>
            {items.map((c) => (
              <Tr key={c.consumable_id}>
                <Td bold>{c.name}</Td>
                <Td>{`${num(c.stock_quantity)} ${c.unit}`}</Td>
                <Td className="text-ink-500">{num(c.min_stock_level)}</Td>
                <Td>{toman(c.unit_price)}</Td>
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
      </Card>
    </>
  );
}
