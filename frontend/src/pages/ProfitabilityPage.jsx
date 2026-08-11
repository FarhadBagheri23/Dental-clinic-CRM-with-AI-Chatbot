import { PageHeader } from "@/app/layouts/PanelLayout";
import { useFilters } from "@/app/providers/FiltersProvider";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { FilterNote } from "@/features/analytics/components/FilterNote";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num, percent, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarList } from "@/shared/ui/charts/BarList";
import { StackedBar } from "@/shared/ui/charts/StackedBar";
import { Panel, Skeleton } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

/** Page 7 — profitability and receivables.
 *
 *  Every other page in this panel measures production: what was booked,
 *  delivered and billed. None of them can answer the two questions an owner
 *  and an accountant ask first — what is left after the cost of delivering
 *  the work, and when does the money actually arrive.
 *
 *  The costs subtracted here are the ones the data records: materials
 *  consumed, dentist commission, and salaried payroll. Rent, utilities and
 *  equipment are in no table, so "operating margin" below is genuinely above
 *  net profit and is labelled as such rather than being passed off as one.
 */
export function ProfitabilityPage() {
  const { queryString } = useFilters();
  const profit = useApiQuery((s) => analyticsApi.profitability(queryString, s), [queryString]);
  const aging = useApiQuery((s) => analyticsApi.aging(queryString, s), [queryString]);

  const p = profit.data;
  const a = aging.data;
  const t = p?.totals;

  return (
    <>
      <PageHeader
        title="سودآوری و مطالبات"
        subtitle="صفحه ۷ داشبورد — حاشیه سود هر خدمت، ساختار هزینه، تخفیف پنهان و سن مطالبات"
      />
      <FilterBar />

      {/* --------------------------------------------------------- KPIs */}
      <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {profit.loading || aging.loading ? (
          Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-[7.5rem] rounded-2xl" />)
        ) : (
          <>
            <StatCard
              label="حاشیه سود ناخالص"
              value={percent(t?.margin_pct ?? 0)}
              hint={`${tomanShort(t?.gross_margin ?? 0)} پس از مواد و کمیسیون`}
              tone={(t?.margin_pct ?? 0) >= 40 ? "positive" : "negative"}
            />
            <StatCard
              label="حقوق پرسنل به درآمد"
              value={percent(t?.payroll_pct ?? 0)}
              hint={`${num(p?.payroll?.headcount ?? 0)} نفر — ${tomanShort(p?.payroll?.monthly ?? 0)} در ماه`}
              tone={(t?.payroll_pct ?? 0) <= 25 ? "positive" : "negative"}
            />
            <StatCard
              label="دوره وصول مطالبات (DSO)"
              value={`${num(a?.dso ?? 0)} روز`}
              hint={`میانگین تسویه هر فاکتور ${num(a?.avg_days_to_settle ?? 0)} روز`}
              tone={(a?.dso ?? 0) <= 45 ? "positive" : "negative"}
            />
            <StatCard
              label="مطالبات بیش از ۹۰ روز"
              value={percent(a?.over_90_share ?? 0)}
              hint={`از ${tomanShort(a?.outstanding ?? 0)} مطالبات باز`}
              tone={(a?.over_90_share ?? 0) > 0 ? "negative" : "positive"}
            />
          </>
        )}
      </section>

      {/* ------------------------------------------------ cost structure */}
      <div className="grid gap-5 xl:grid-cols-3">
        <Card title="ساختار هزینه — هر تومان درآمد کجا می‌رود" className="xl:col-span-2">
          <Panel query={profit} rows={6}>
            {(d) => (
              <>
                <StackedBar
                  segments={[
                    { label: "مواد مصرفی", value: d.totals.material_cost, color: "#d9a441" },
                    { label: "کمیسیون پزشک", value: d.totals.commission, color: "#e11d48" },
                    { label: "حقوق پرسنل", value: d.totals.payroll, color: "#8b6db1" },
                    {
                      label: "باقی‌مانده (پیش از اجاره و سربار)",
                      value: Math.max(d.totals.operating_margin, 0),
                      color: "#1f757b",
                    },
                  ]}
                  total={d.totals.revenue}
                />
                <Insight>
                  از {tomanShort(d.totals.revenue)} درآمد،{" "}
                  {percent(d.totals.commission_pct)} به کمیسیون پزشکان و{" "}
                  {percent(d.totals.material_pct)} به مواد مصرفی می‌رود. کمیسیون
                  بزرگ‌ترین قلم هزینه است و برخلاف مواد، با نرخ قرارداد هر پزشک
                  تعیین می‌شود — یعنی قابل مذاکره است، نه ثابت.
                </Insight>
                <Insight tone="warn">
                  «باقی‌مانده» سود خالص نیست. اجاره، قبوض، استهلاک تجهیزات و
                  بازاریابی در هیچ جدولی ثبت نشده‌اند، پس نقطه سربه‌سر واقعی
                  کلینیک از این داده قابل محاسبه نیست. برای رسیدن به سود خالص
                  باید این هزینه‌ها هم ثبت شوند.
                </Insight>
              </>
            )}
          </Panel>
        </Card>

        <Card title="تخفیف پنهان — تفاوت تعرفه و مبلغ نهایی">
          <Panel query={profit} rows={5}>
            {(d) => (
              <>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-ink-500">تعرفه رسمی خدمات ارائه‌شده</p>
                    <p className="mt-1 text-lg font-black tabular-nums text-ink-800">
                      {tomanShort(d.discount.list_value)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-ink-500">مبلغ واقعی صورتحساب</p>
                    <p className="mt-1 text-lg font-black tabular-nums text-ink-800">
                      {tomanShort(d.discount.billed)}
                    </p>
                  </div>
                  <div className="rounded-xl bg-rose-50 p-4">
                    <p className="text-xs text-rose-700">تخفیف داده‌شده</p>
                    <p className="mt-1 text-xl font-black tabular-nums text-rose-700">
                      {tomanShort(d.discount.given_away)}
                    </p>
                    <p className="mt-1 text-xs text-rose-600">
                      {percent(d.discount.pct)} از تعرفه
                    </p>
                  </div>
                </div>
                <Insight tone="caution">
                  تخفیف در هیچ گزارش دیگری دیده نمی‌شود، چون درآمد همیشه از مبلغ
                  نهایی خوانده می‌شود. اما هر تومان تخفیف مستقیماً از سود کم
                  می‌شود، نه از درآمد — هزینه مواد و کمیسیون همان مقدار می‌ماند.
                </Insight>
              </>
            )}
          </Panel>
        </Card>
      </div>

      {/* ------------------------------------------- margin per service */}
      <Card
        title="حاشیه سود هر خدمت — از ضعیف‌ترین به بهترین"
        className="mt-5"
        bodyClassName=""
      >
        <Panel query={profit} rows={6}>
          {(d) => {
            const losers = d.services.filter((s) => s.margin_pct < 0);
            return (
              <>
                <Table
                  head={["خدمت", "دسته", "جلسات", "درآمد", "مواد", "کمیسیون", "سود ناخالص", "حاشیه"]}
                >
                  {d.services.map((s) => (
                    <Tr key={s.service_id}>
                      <Td bold>{s.name}</Td>
                      <Td className="text-ink-500">{s.category}</Td>
                      <Td>{num(s.sessions)}</Td>
                      <Td>{tomanShort(s.revenue)}</Td>
                      <Td className="text-ink-500">{tomanShort(s.material_cost)}</Td>
                      <Td className="text-ink-500">{tomanShort(s.commission)}</Td>
                      <Td className={s.gross_margin < 0 ? "font-bold text-rose-700" : "text-brand-700"}>
                        {tomanShort(s.gross_margin)}
                      </Td>
                      <Td bold className={s.margin_pct < 0 ? "text-rose-700" : ""}>
                        {percent(s.margin_pct)}
                      </Td>
                    </Tr>
                  ))}
                </Table>

                <div className="space-y-3 p-5 pt-4">
                  {losers.length > 0 && (
                    <Insight tone="caution">
                      {num(losers.length)} خدمت با حاشیه منفی انجام می‌شود — یعنی
                      مواد مصرفی و کمیسیون پزشک از مبلغ صورتحساب بیشتر است.
                      هرچه این خدمات بیشتر انجام شوند، کلینیک بیشتر ضرر می‌کند.
                      کم‌حاشیه‌ترین آن‌ها «{losers[0].name}» است. سه راه دارد:
                      اصلاح تعرفه، کاهش بهای مواد، یا بازنگری در نرخ کمیسیون
                      همان خدمت.
                    </Insight>
                  )}
                  <Insight>
                    این جدول از کم‌حاشیه به پرحاشیه مرتب شده، برخلاف بقیه پنل که
                    بر پایه درآمد مرتب می‌شوند. دلیلش این است که پرکارترین خدمت
                    معمولاً در صدر گزارش‌های درآمدی می‌نشیند و همان خدمت ممکن است
                    کمترین سود را بسازد — چیزی که فقط در این ترتیب دیده می‌شود.
                  </Insight>
                </div>
              </>
            );
          }}
        </Panel>
      </Card>

      {/* --------------------------------------------------- A/R ageing */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card title="سن مطالبات — چقدر از پول، چند وقت است معطل مانده">
          <Panel query={aging} rows={5}>
            {(d) => (
              <>
                <BarList
                  items={d.buckets.map((b) => ({
                    label: b.bucket,
                    value: b.amount,
                    sub: `${num(b.n)} فاکتور`,
                    display: tomanShort(b.amount),
                  }))}
                />
                <FilterNote endpoint="aging" />
                <Insight tone="warn">
                  مبلغ کل مطالبات به تنهایی بی‌معنی است: {tomanShort(d.outstanding)}{" "}
                  مطالبات تازه با {tomanShort(d.outstanding)} مطالبات یک‌ساله
                  یکسان دیده می‌شود، در حالی که اولی جریان نقدی عادی است و دومی
                  عملاً سوخت‌شده. تقسیم بر سن، تنها راه تفکیک این دو است.
                </Insight>
                <Insight>
                  DSO برابر {num(d.dso)} روز است: یعنی به‌طور متوسط{" "}
                  {num(d.dso)} روز از درآمد کلینیک، وصول‌نشده روی زمین مانده.
                  میانگین زمان تسویه هر فاکتور {num(d.avg_days_to_settle)} روز
                  است — فاصله این دو عدد نشان می‌دهد بخشی از فاکتورها اصلاً
                  تسویه نشده‌اند.
                </Insight>
              </>
            )}
          </Panel>
        </Card>

        <Card title="بزرگ‌ترین مطالبات باز — فهرست پیگیری" bodyClassName="">
          <Panel query={aging} rows={5}>
            {(d) =>
              d.worst.length ? (
                <>
                  <Table head={["بیمار", "تلفن", "سهم بیمار", "پرداخت‌شده", "مانده", "سن"]}>
                    {d.worst.map((row) => (
                      <Tr key={row.invoice_id}>
                        <Td bold>{row.patient}</Td>
                        <Td className="text-ink-500 field-ltr">{row.phone}</Td>
                        <Td className="text-ink-500">{tomanShort(row.patient_share)}</Td>
                        <Td className="text-ink-500">{tomanShort(row.paid)}</Td>
                        <Td bold className="text-rose-700">{tomanShort(row.balance)}</Td>
                        <Td>{`${num(row.age_days)} روز`}</Td>
                      </Tr>
                    ))}
                  </Table>
                  <div className="p-5 pt-4">
                    <Insight tone="caution">
                      بر پایه مانده مرتب شده، نه سن. وقت حسابداری محدود است و
                      قدیمی‌ترین فاکتور همیشه گران‌ترین آن نیست — ده تماس بالای
                      این فهرست بیشتر از صد تماس تصادفی پول برمی‌گرداند.
                    </Insight>
                  </div>
                </>
              ) : (
                <div className="p-5 text-sm text-ink-500">مطالبات بازی وجود ندارد.</div>
              )
            }
          </Panel>
        </Card>
      </div>
    </>
  );
}
