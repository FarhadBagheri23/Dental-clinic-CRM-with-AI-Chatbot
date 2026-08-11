import { PageHeader } from "@/app/layouts/PanelLayout";
import { useFilters } from "@/app/providers/FiltersProvider";
import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { FilterBar } from "@/features/analytics/components/FilterBar";
import { FilterNote } from "@/features/analytics/components/FilterNote";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { date, monthLabel, num, percent, tomanShort } from "@/shared/lib/format";
import { Card, StatCard } from "@/shared/ui/Card";
import { BarChart } from "@/shared/ui/charts/BarChart";
import { Donut } from "@/shared/ui/charts/Donut";
import { StackedBar } from "@/shared/ui/charts/StackedBar";
import { EmptyState, Panel, Skeleton } from "@/shared/ui/Feedback";
import { Insight } from "@/shared/ui/Insight";
import { Table, Td, Tr } from "@/shared/ui/Table";

/** Page 6 — the clinical half of the dashboard.
 *
 *  Revenue pages answer "what did we bill?". A dentist and a clinic manager
 *  also need "what did we diagnose and never deliver?" and "who stopped
 *  coming?" — the two questions that drive a dental practice and that no
 *  invoice-based chart can see.
 */
export function ClinicalPage() {
  const { queryString } = useFilters();
  const plans = useApiQuery((s) => analyticsApi.treatmentPlans(queryString, s), [queryString]);
  const recall = useApiQuery((s) => analyticsApi.recall(queryString, s), [queryString]);

  const p = plans.data;
  const r = recall.data;

  return (
    <>
      <PageHeader
        title="طرح درمان و بازگشت بیمار"
        subtitle="صفحه ۶ داشبورد — پذیرش طرح، درمانِ تأییدشده‌ی انجام‌نشده و فراخوان دوره‌ای"
      />
      <FilterBar />

      {/* --------------------------------------------------------- KPIs */}
      <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {plans.loading || recall.loading ? (
          Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-[7.5rem] rounded-2xl" />)
        ) : (
          <>
            <StatCard
              label="نرخ پذیرش طرح درمان"
              value={percent(p?.acceptance_rate ?? 0)}
              hint={`از ${num(p?.total_plans ?? 0)} طرح ارائه‌شده`}
              tone={(p?.acceptance_rate ?? 0) >= 80 ? "positive" : "negative"}
            />
            <StatCard
              label="نرخ تکمیل طرح"
              value={percent(p?.completion_rate ?? 0)}
              hint={`میانگین ${num(p?.avg_sessions_per_plan ?? 0)} جلسه در هر طرح`}
              tone="info"
            />
            <StatCard
              label="درمان تأییدشده، انجام‌نشده"
              value={tomanShort(p?.unrealised_value ?? 0)}
              hint="در طرح‌های باز — بیمار پذیرفته، هنوز انجام نشده"
              tone="negative"
            />
            <StatCard
              label="بیماران نیازمند فراخوان"
              value={num(r?.lapsed ?? 0)}
              hint={`بیش از ${num(r?.recall_days ?? 180)} روز بدون مراجعه`}
              tone={(r?.lapsed ?? 0) ? "negative" : "positive"}
            />
          </>
        )}
      </section>

      {/* ----------------------------------------------- plan lifecycle */}
      <div className="grid gap-5 xl:grid-cols-3">
        <Card title="چرخه طرح درمان" className="xl:col-span-2" bodyClassName="">
          <Panel query={plans} rows={6}>
            {(d) => (
              <>
                <div className="p-5 pb-0">
                  <StackedBar
                    segments={[
                      { label: "انجام و ثبت‌شده", value: d.delivered_value, color: "#1f757b" },
                      { label: "باز و انجام‌نشده", value: d.unrealised_value, color: "#d9a441" },
                      {
                        label: "کنارگذاشته‌شده",
                        value: Math.max(d.planned_value - d.delivered_value - d.unrealised_value, 0),
                        color: "#c3caca",
                      },
                    ]}
                  />
                </div>

                <Table head={["وضعیت طرح", "تعداد", "ارزش برآوردی", "انجام‌شده", "درصد اجرا"]}>
                  {d.by_status.map((s) => (
                    <Tr key={s.status}>
                      <Td bold>{s.status}</Td>
                      <Td>{num(s.n)}</Td>
                      <Td>{tomanShort(s.planned)}</Td>
                      <Td className="text-brand-700">{tomanShort(s.delivered)}</Td>
                      <Td bold>{percent(s.planned ? Math.round((s.delivered / s.planned) * 100) : 0)}</Td>
                    </Tr>
                  ))}
                </Table>

                <div className="space-y-3 p-5 pt-4">
                  <FilterNote endpoint="treatment-plans" />
                  <Insight tone="caution">
                    {tomanShort(d.unrealised_value)} درمانِ پذیرفته‌شده در طرح‌های باز مانده است.
                    این ارزان‌ترین درآمد کلینیک است: بیمار قبلاً تشخیص و قیمت را پذیرفته و
                    برای وصول آن به جذب بیمار جدید نیازی نیست — فقط به پیگیری تلفنی.
                  </Insight>
                  {d.planned_value > 0 && d.unrealised_value / d.planned_value < 0.05 && (
                    <p className="text-xs leading-6 text-ink-400">
                      توجه: این عدد در داده‌ی تولیدشده کوچک است، چون مولد داده جلسات هر طرح را
                      تقریباً تا سقف برآورد پیش می‌برد. در داده واقعی کلینیک، فاصله «برآورد»
                      تا «انجام‌شده» معمولاً بسیار بزرگ‌تر است و همین شاخص، اصلی‌ترین
                      کاربرد این صفحه خواهد بود.
                    </p>
                  )}
                  <Insight>
                    میانگین ارزش هر طرح {tomanShort(d.avg_plan_value)} و میانگین{" "}
                    {num(d.avg_sessions_per_plan)} جلسه است. طرح‌های چندجلسه‌ای هرچه طولانی‌تر
                    شوند، احتمال رهاشدن‌شان بیشتر می‌شود؛ فشرده‌کردن فاصله جلسات مستقیماً
                    نرخ تکمیل را بالا می‌برد.
                  </Insight>
                </div>
              </>
            )}
          </Panel>
        </Card>

        <Card title="وضعیت بازگشت بیماران">
          <Panel query={recall} rows={5}>
            {(d) => (
              <>
                <Donut
                  data={[
                    { status: "فعال (در دوره فراخوان)", n: d.active },
                    { status: "لغزیده از فراخوان", n: d.lapsed },
                    { status: "ثبت‌نام‌شده، بدون درمان", n: d.never_treated },
                  ]}
                  colors={["#1f757b", "#e11d48", "#c3caca"]}
                  centerLabel="نرخ فعال"
                  centerValue={percent(d.recall_rate)}
                />
                <Insight tone="warn">
                  کلینیک دندان‌پزشکی کسب‌وکار بازگشت است، نه جذب. شمار کل بیماران فقط بالا
                  می‌رود و هیچ‌وقت هشدار نمی‌دهد؛ آنچه باید پایش شود سهم بیمارانی است که
                  در دوره {num(d.recall_days)} روزه بازگشته‌اند.
                </Insight>
                {d.never_treated > 0 && (
                  <Insight tone="caution">
                    {num(d.never_treated)} بیمار ثبت‌نام شده‌اند و هرگز درمانی نگرفته‌اند.
                    این‌ها در شمار «کل بیماران» دیده می‌شوند اما هیچ درآمدی نساخته‌اند —
                    فاصله میان پذیرش و شروع درمان، نه فاصله میان بازاریابی و پذیرش.
                  </Insight>
                )}
                {d.lapsed === 0 && (
                  <p className="mt-3 text-xs leading-6 text-ink-400">
                    توجه: هیچ بیمار لغزیده‌ای دیده نمی‌شود چون پنجره داده تولیدشده حدود
                    ۱۲ ماه است و جلسات هر بیمار در همین بازه پخش شده‌اند. این محدودیت
                    داده است، نه نشانه بازگشت کامل بیماران.
                  </p>
                )}
              </>
            )}
          </Panel>
        </Card>
      </div>

      {/* ------------------------------------------------ overdue plans */}
      <Card
        title="طرح‌های عقب‌افتاده — فهرست تماس"
        className="mt-5"
        bodyClassName=""
        action={
          p ? (
            <span className="rounded-lg bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700">
              {num(p.overdue_count)} طرح · {tomanShort(p.overdue_value)}
            </span>
          ) : null
        }
      >
        <Panel query={plans} rows={5}>
          {(d) =>
            d.overdue_plans.length ? (
              <>
                <Table head={["بیمار", "تلفن", "پزشک", "پایان برآوردی", "تأخیر", "جلسات", "باقی‌مانده"]}>
                  {d.overdue_plans.map((row) => (
                    <Tr key={row.plan_id}>
                      <Td bold>{row.patient}</Td>
                      <Td className="text-ink-500 field-ltr">{row.phone}</Td>
                      <Td className="text-ink-500">{row.dentist}</Td>
                      <Td className="text-ink-500">{date(row.estimated_end_date)}</Td>
                      <Td className="font-bold text-rose-700">{`${num(row.days_overdue)} روز`}</Td>
                      <Td>{num(row.sessions)}</Td>
                      <Td bold>{tomanShort(row.remaining)}</Td>
                    </Tr>
                  ))}
                </Table>
                <div className="p-5 pt-4">
                  <Insight tone="caution">
                    این طرح‌ها از تاریخ پایان برآوردی خود گذشته‌اند و هنوز باز هستند.
                    هر ردیف یک تماس مشخص است، نه یک شاخص: بیشترین مبلغ باقی‌مانده در بالای
                    فهرست آمده تا وقت محدود پذیرش صرف پرارزش‌ترین پیگیری‌ها شود.
                  </Insight>
                </div>
              </>
            ) : (
              <div className="p-5">
                <EmptyState title="طرح عقب‌افتاده‌ای وجود ندارد." />
              </div>
            )
          }
        </Panel>
      </Card>

      {/* ---------------------------------------- recall list + new/old */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card title="بیماران لغزیده از فراخوان — به ترتیب ارزش" bodyClassName="">
          <Panel query={recall} rows={5}>
            {(d) =>
              d.recall_list.length ? (
                <>
                  <Table head={["بیمار", "تلفن", "آخرین مراجعه", "بی‌مراجعه", "مراجعات", "ارزش تاکنون"]}>
                    {d.recall_list.map((row) => (
                      <Tr key={row.patient_id}>
                        <Td bold>{row.name}</Td>
                        <Td className="text-ink-500 field-ltr">{row.phone}</Td>
                        <Td className="text-ink-500">{date(row.last)}</Td>
                        <Td className="font-bold text-rose-700">{`${num(row.days_since)} روز`}</Td>
                        <Td>{num(row.visits)}</Td>
                        <Td bold>{tomanShort(row.revenue)}</Td>
                      </Tr>
                    ))}
                  </Table>
                  <div className="p-5 pt-4">
                    <Insight>
                      مجموع ارزش تاریخی بیماران لغزیده {tomanShort(d.recall_value_at_risk)} است.
                      مرتب‌سازی بر پایه ارزش انجام شده، نه طول غیبت — طولانی‌ترین غیبت
                      همیشه ارزشمندترین تماس نیست.
                    </Insight>
                  </div>
                </>
              ) : (
                <div className="p-5"><EmptyState title="همه بیماران در دوره فراخوان‌اند." /></div>
              )
            }
          </Panel>
        </Card>

        <Card title="بیمار جدید در برابر بیمار بازگشتی">
          <Panel query={recall} rows={6}>
            {(d) => (
              <>
                <BarChart
                  data={d.new_vs_returning.map((m) => ({ ...m, label: monthLabel(m.month) }))}
                  xKey="label"
                  bars={[
                    { key: "new", label: "بیمار جدید", color: "#4fb0b3" },
                    { key: "returning", label: "بازگشتی", color: "#1f757b" },
                  ]}
                  height={250}
                />
                <Insight tone="warn">
                  رشدی که فقط از بیمار جدید بیاید گران و شکننده است. سهم ستون تیره در هر ماه
                  نشان می‌دهد چه اندازه از فعالیت کلینیک از بیمارانی می‌آید که قبلاً جذب
                  شده‌اند — همان بخشی که هزینه بازاریابی ندارد.
                </Insight>
              </>
            )}
          </Panel>
        </Card>
      </div>
    </>
  );
}
