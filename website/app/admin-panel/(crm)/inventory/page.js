import { col } from "../../../../lib/mongo";
import { getLowStock } from "../../../../lib/queries";
import { Card, PageHead, Table, fa, toman } from "../../ui";

export default async function InventoryPage() {
  const consumables = await col("consumables");
  const [all, lowStock] = await Promise.all([
    consumables.find({}, { projection: { _id: 0 } }).sort({ name: 1 }).toArray(),
    getLowStock(),
  ]);

  const critical = lowStock.filter((c) => c.critical);
  const stockValue = all.reduce((a, c) => a + c.stock_quantity * c.unit_price, 0);
  const reorderCost = critical.reduce(
    (a, c) => a + Math.max(c.min_stock_level * 2 - c.stock_quantity, 0) * c.unit_price,
    0,
  );

  return (
    <>
      <PageHead title="انبار مواد مصرفی" sub={`${fa(all.length)} قلم کالا`} />

      <section className="mb-8 grid gap-4 sm:grid-cols-3">
        <Card label="ارزش موجودی" value={toman(stockValue)} hint="بر مبنای قیمت واحد" />
        <Card
          label="زیر حد سفارش"
          value={fa(critical.length)}
          hint="نیاز به سفارش فوری"
          tone={critical.length ? "text-rose-700" : "text-emerald-700"}
        />
        <Card label="برآورد هزینه سفارش" value={toman(reorderCost)} hint="تا دو برابر حد سفارش" />
      </section>

      {critical.length ? (
        <section className="mb-8">
          <h2 className="mb-3 font-black text-rose-700">🔴 نیازمند سفارش فوری</h2>
          <Table head={["نام کالا", "موجودی", "حد سفارش", "واحد", "تأمین‌کننده"]}>
            {critical.map((c) => (
              <tr key={c.consumable_id} className="bg-rose-50/40 hover:bg-rose-50">
                <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{c.name}</td>
                <td className="px-4 py-3 font-bold text-rose-700">{fa(c.stock_quantity)}</td>
                <td className="px-4 py-3 text-slate-500">{fa(c.min_stock_level)}</td>
                <td className="px-4 py-3 text-slate-500">{c.unit}</td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">{c.supplier ?? "—"}</td>
              </tr>
            ))}
          </Table>
        </section>
      ) : (
        <p className="mb-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-center text-sm font-bold text-emerald-800">
          ✅ وضعیت انبار مطلوب است — هیچ قلمی زیر حد سفارش نیست.
        </p>
      )}

      <h2 className="mb-3 font-black text-slate-900">همه اقلام</h2>
      <Table head={["نام کالا", "واحد", "موجودی", "حد سفارش", "قیمت واحد", "ارزش موجودی", "تأمین‌کننده"]}>
        {all.map((c) => {
          const low = c.stock_quantity <= c.min_stock_level;
          const warn = !low && c.stock_quantity <= c.min_stock_level * 1.5;
          return (
            <tr key={c.consumable_id} className="hover:bg-slate-50">
              <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">
                {low ? "🔴 " : warn ? "🟡 " : ""}
                {c.name}
              </td>
              <td className="px-4 py-3 text-slate-500">{c.unit}</td>
              <td className={`px-4 py-3 font-bold ${low ? "text-rose-700" : "text-slate-700"}`}>
                {fa(c.stock_quantity)}
              </td>
              <td className="px-4 py-3 text-slate-500">{fa(c.min_stock_level)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-600">{toman(c.unit_price)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                {toman(c.stock_quantity * c.unit_price)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-500">{c.supplier ?? "—"}</td>
            </tr>
          );
        })}
      </Table>
    </>
  );
}
