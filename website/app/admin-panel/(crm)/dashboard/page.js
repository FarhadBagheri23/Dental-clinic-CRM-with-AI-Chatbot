import { getDashboard, getDentistPerformance, getTopServices, getLowStock } from "../../../../lib/queries";
import { LOOKER_STUDIO_URL } from "../../../../lib/config";
import { Badge, Card, PageHead, Table, fa, toman } from "../../ui";

export default async function DashboardPage() {
  const [kpi, dentists, services, lowStock] = await Promise.all([
    getDashboard(),
    getDentistPerformance(),
    getTopServices(6),
    getLowStock(),
  ]);

  const critical = lowStock.filter((c) => c.critical);
  const totalDentistRevenue = dentists.reduce((a, d) => a + d.revenue, 0) || 1;

  return (
    <>
      <PageHead title="داشبورد مدیریتی" sub="نمای کلی عملکرد کلینیک بر اساس داده‌های ثبت‌شده">
        <span className="rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
          ● متصل به پایگاه داده
        </span>
      </PageHead>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card label="درآمد کل" value={toman(kpi.revenue)} hint={`${fa(kpi.counts.sessions)} جلسه درمان`} />
        <Card
          label="وصول‌شده"
          value={toman(kpi.collected)}
          hint={`نرخ وصول ${fa(kpi.collectionRate)}٪`}
          tone="text-emerald-700"
        />
        <Card
          label="مطالبات معوق"
          value={toman(kpi.outstanding)}
          hint="سهم بیمار پرداخت‌نشده"
          tone={kpi.outstanding > 0 ? "text-rose-700" : "text-slate-900"}
        />
        <Card label="سهم بیمه‌ها" value={toman(kpi.insuranceCovered)} hint="کسرشده از فاکتورها" />
      </section>

      <section className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card label="بیماران" value={fa(kpi.counts.patients)} hint="پرونده ثبت‌شده" />
        <Card label="کل نوبت‌ها" value={fa(kpi.counts.appointments)} hint="۱۲ ماه گذشته" />
        <Card label="نوبت‌های پیش‌رو" value={fa(kpi.counts.upcoming)} hint="در انتظار مراجعه" tone="text-sky-700" />
        <Card
          label="اقلام نیازمند سفارش"
          value={fa(critical.length)}
          hint="زیر حد سفارش"
          tone={critical.length ? "text-rose-700" : "text-emerald-700"}
        />
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <section>
          <h2 className="mb-3 font-black text-slate-900">عملکرد پزشکان</h2>
          <Table head={["پزشک", "تخصص", "جلسات", "درآمد", "سهم"]}>
            {dentists.map((d) => (
              <tr key={d.name} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{d.name}</td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-500">{d.specialty}</td>
                <td className="px-4 py-3 text-slate-600">{fa(d.sessions)}</td>
                <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{toman(d.revenue)}</td>
                <td className="px-4 py-3 text-slate-500">
                  {fa(Math.round((d.revenue / totalDentistRevenue) * 100))}٪
                </td>
              </tr>
            ))}
          </Table>
        </section>

        <section>
          <h2 className="mb-3 font-black text-slate-900">خدمات پردرآمد</h2>
          <Table head={["خدمت", "دسته", "تعداد", "درآمد"]}>
            {services.map((s) => (
              <tr key={s.name} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{s.name}</td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-500">{s.category}</td>
                <td className="px-4 py-3 text-slate-600">{fa(s.n)}</td>
                <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{toman(s.revenue)}</td>
              </tr>
            ))}
          </Table>
        </section>

        <section>
          <h2 className="mb-3 font-black text-slate-900">وضعیت نوبت‌ها</h2>
          <Table head={["وضعیت", "تعداد", "سهم"]}>
            {kpi.appointmentStatus.map((r) => (
              <tr key={r.status} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Badge>{r.status}</Badge>
                </td>
                <td className="px-4 py-3 font-bold text-slate-800">{fa(r.n)}</td>
                <td className="px-4 py-3 text-slate-500">
                  {fa(Math.round((r.n / kpi.counts.appointments) * 100))}٪
                </td>
              </tr>
            ))}
          </Table>
        </section>

        <section>
          <h2 className="mb-3 font-black text-slate-900">وضعیت فاکتورها</h2>
          <Table head={["وضعیت", "تعداد"]}>
            {kpi.invoiceStatus.map((r) => (
              <tr key={r.status} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Badge>{r.status}</Badge>
                </td>
                <td className="px-4 py-3 font-bold text-slate-800">{fa(r.n)}</td>
              </tr>
            ))}
          </Table>
        </section>
      </div>

      <section className="mt-8">
        <h2 className="mb-3 font-black text-slate-900">داشبورد تحلیلی</h2>
        {LOOKER_STUDIO_URL ? (
          <iframe
            src={LOOKER_STUDIO_URL}
            title="داشبورد تحلیلی کلینیک"
            className="h-[80vh] min-h-[600px] w-full rounded-2xl border border-slate-200 bg-white shadow-sm"
            allowFullScreen
          />
        ) : (
          <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-sm leading-8 text-slate-600">
              گزارش Looker Studio هنوز متصل نشده است. آدرس Embed را در متغیر{" "}
              <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">LOOKER_STUDIO_URL</code>{" "}
              در فایل <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">app/sections.jsx</code>{" "}
              قرار دهید.
            </p>
          </div>
        )}
      </section>
    </>
  );
}
