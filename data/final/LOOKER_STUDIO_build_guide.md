# Looker Studio — Complete Build Guide
داشبورد کلینیک دندان‌پزشکی · فرهاد باقری طاهری

**No connector exists for Looker Studio.** Google publishes APIs for reading report metadata, not for constructing reports. Nothing can build this for you — not me, not any tool. You click, I specify.

Budget roughly three hours for a first build. Do it in one sitting if you can; Looker Studio's autosave is reliable but rebuilding context is not.

---

## Before you start

**Re-upload the workbook.** The file in your Drive is stale — I've since fixed the Iranian weekend alignment, rescoped active treatment plans, and added two things Page 3 needs. Delete the old `dental_clinic_bi` Sheet and upload the new `dental_clinic_bi.xlsx`, then File → Save as Google Sheets, then File → Settings → Locale → **United States**.

The workbook now has 17 tabs. You will connect 8 of them.

---

## Step 2 — Create the report and connect data

Go to **lookerstudio.google.com** → **Create** → **Report**. A data source picker opens immediately.

Choose **Google Sheets** → authorise if prompted → select `dental_clinic_bi` → select worksheet **`fact_sessions`** → leave "Use first row as headers" checked → **Add**.

You now have a blank report with one data source. Add the remaining seven: **Add data** (toolbar) → Google Sheets → same spreadsheet → different worksheet.

Connect exactly these eight:

| Data source | What it drives |
|---|---|
| `fact_sessions` | All revenue: trend, by dentist, by category, top services, treatment history |
| `fact_appointments` | Occupancy, cancellation, today's schedule, appointments per dentist |
| `fact_invoices` | Outstanding balances, overdue patients, collection rate |
| `fact_payments` | Payment history (Page 3) |
| `fact_consumable_usage` | Monthly consumables cost |
| `consumables` | Low-stock list and KPI |
| `patients` | New patients this month |
| `treatment_plans` | Plan progress, sessions remaining |

**Skip the other nine.** `insurance`, `dentists`, `staff`, `services`, `appointments`, `treatment_sessions`, `invoices`, `payments`, and `consumable_usage` are all already folded into the fact tables. Connecting them adds clutter and tempts you into blends you don't need. They stay in the workbook so your ERD remains traceable — that's their only job.

### Fix the field types immediately

This is the step people skip and then lose an hour to. For each data source: **Resource → Manage added data sources → Edit**.

Check that every date field shows type **Date** or **Date & Time**, not Text:

| Data source | Field | Type |
|---|---|---|
| `fact_sessions` | `session_date` | Date & Time |
| `fact_appointments` | `scheduled_datetime` | Date & Time |
| `fact_invoices` | `issue_date` | Date |
| `fact_payments` | `payment_date` | Date & Time |
| `fact_consumable_usage` | `usage_date` | Date & Time |
| `patients` | `registration_date` | Date |
| `treatment_plans` | `start_date`, `estimated_end_date` | Date |

If one imported as Text, click its type dropdown → Date & Time → choose `YYYY-MM-DD` (or `YYYY-MM-DD HH:MM:SS`). A date field left as Text silently breaks every time-series chart and every date range control on the page, and Looker Studio gives you no warning.

Leave `year_month`, `session_day`, `appt_day`, `hour_label`, and `payment_day` as **Text**. They're pre-formatted helpers that sort correctly as strings.

Also set the aggregation on the 1/0 flag fields — `is_cancelled`, `is_noshow`, `is_completed`, `is_booked`, `is_overdue`, `has_balance`, `is_low_stock` — to **Average** if you want rates, or leave as Sum and use `AVG()` in the formula. I use `AVG()` below, so leave them alone.

---

## Step 3 — Calculated fields

Create these once, in the data source (**Edit → Add a field**), not per chart. Fields made in the data source are reusable across every page.

### In `fact_appointments`

**`نرخ اشغال یونیت`** (chair occupancy)
```
SUM(duration_minutes) / (COUNT_DISTINCT(appt_day) * 4320)
```
4320 = 6 chairs × 12 hours × 60 minutes. Set format to **Percent**. Any chart using this must be filtered to `status = انجام‌شده`, or completed and cancelled appointments get mixed together.

**`نرخ لغو`**
```
AVG(is_cancelled)
```
Format Percent.

**`نرخ عدم حضور`**
```
AVG(is_noshow)
```
Format Percent.

### In `fact_sessions`

**`درآمد هر ساعت یونیت`** (revenue per chair-hour) — the field that turns a routine service ranking into an insight
```
SUM(actual_cost) / (SUM(duration_minutes) / 60)
```

**`حاشیه سود درصد`**
```
SUM(clinic_margin) / SUM(actual_cost)
```
Format Percent.

**`میانگین مبلغ هر جلسه`** (average ticket)
```
SUM(actual_cost) / COUNT(session_id)
```

### In `fact_invoices`

**`نرخ وصول`** (collection rate)
```
SUM(paid_amount) / SUM(patient_share)
```
Format Percent.

**`روزهای معوق`** (days outstanding)
```
DATE_DIFF(CURRENT_DATE(), issue_date)
```
This one is a dimension, not a metric.

---

## Step 4 — Page 1: مدیر (Manager)

Rename the page: right-click the page tab in the left panel → Rename → `مدیر`.

Your requirement is 8 KPIs. This layout gives you 9 widgets, 5 of them scorecards.

### 1. Scorecard — درآمد این ماه

**Add a chart → Scorecard.** Data source `fact_sessions`, Metric `actual_cost` (SUM).

In **Setup**: Date Range Dimension = `session_date`, Default date range = **This month**.
In **Setup → Comparison date range** = **Previous period**.

That gives you "this month vs last month" in one widget with an automatic delta arrow. Expect roughly 88.9 million against 741.3 million — a large negative, because August has only nine days of data. Add a text box beneath saying `داده‌ها تا ۹ آگوست ۲۰۲۶`. Explain it before your examiner asks.

### 2. Scorecard — بیماران جدید این ماه

Data source `patients`, Metric `patient_id` with aggregation **Count Distinct**, Date Range Dimension `registration_date`, range **This month**. Expect 10.

### 3. Scorecard — نرخ اشغال یونیت

Data source `fact_appointments`, Metric `نرخ اشغال یونیت`.
**Add a filter**: Setup → Filter → Add a filter → Include → `status` → Equal to → `انجام‌شده`.

Expect about 10%. That is not a bug — it is the headline finding of your analysis. The clinic uses 1,866 of 18,720 available chair-hours.

### 4. Scorecard — نرخ لغو

Data source `fact_appointments`, Metric `نرخ لغو`. Expect 8.0%.

### 5. Scorecard — هزینه مواد مصرفی این ماه

Data source `fact_consumable_usage`, Metric `usage_cost` (SUM), Date Range Dimension `usage_date`, range **This month**.

### 6. Time series — روند درآمد ۱۲ ماهه

**Add a chart → Time series.** Data source `fact_sessions`.
Dimension `session_date`, granularity **Month** (click the field, set granularity in the dropdown).
Metric 1: `actual_cost` (SUM). Metric 2: `میانگین مبلغ هر جلسه`.
Date range: **Advanced → Last 13 months**.

In **Style**, put metric 2 on the **Right axis**. This is the most important chart on the page: revenue climbs while average ticket falls from 6.6 million to 2.3 million. One line rising and one falling tells the mix-shift story that revenue alone conceals.

### 7. Bar chart — درآمد به تفکیک دندان‌پزشک

Data source `fact_sessions`, Dimension `dentist_name`, Metric 1 `actual_cost` (SUM), Metric 2 `clinic_margin` (SUM). Sort by `actual_cost` descending.

**Never sort this by session count.** علی کریمی has the most sessions (436) and ranks third in revenue; کامران اکبری has 373 sessions and ranks sixth. Session count inverts the ranking.

Showing margin beside revenue exposes the commission problem — غزاله مقدم retains 75% while علی علوی retains 55%.

### 8. Donut — سهم درآمد بر اساس دسته خدمت

**Add a chart → Pie chart**, then Style → Donut. Data source `fact_sessions`, Dimension `category`, Metric `actual_cost` (SUM).

Four slices: درمانی 53.1%, جراحی 29.6%, زیبایی 15.4%, تشخیصی 2.0%.

### 9. Table — ۱۰ خدمت پرسودتر

**Add a chart → Table.** Data source `fact_sessions`, Dimension `service_name`.
Metrics: `actual_cost` (SUM), `clinic_margin` (SUM), `حاشیه سود درصد`, `درآمد هر ساعت یونیت`.
**Sort by `درآمد هر ساعت یونیت` descending**, Rows per page 10.

In Style, enable **Heatmap** on the revenue-per-hour column.

Sorting by revenue per chair-hour rather than gross revenue is the single choice that most distinguishes this from a student dashboard. ارتودنسی ثابت yields 21.3 million per chair-hour against معاینه و تشخیص at 455 thousand — a 47-fold spread invisible in a gross-revenue ranking.

---

## Step 5 — Page 2: کارشناس پذیرش (Receptionist)

Add a page: **Page → New page**, rename to `کارشناس پذیرش`.

### 1. Table — نوبت‌های امروز

Data source `fact_appointments`. Dimensions: `appt_day`, `hour_label`, `patient_name`, `phone`, `dentist_name`, `chair_label`, `status`. Sort `appt_day` then `hour_label` ascending.

Date Range Dimension `scheduled_datetime`, range **Today**.

**Practical warning:** only two appointments fall on 9 August. A two-row table looks broken during a demo. Set the range to **Advanced → Today to 7 days ahead** and title it `نوبت‌های امروز و هفته پیش‌رو` — seven days gives you seven rows and reads as a genuine reception tool.

### 2. Scorecard — تعداد نوبت این هفته

Data source `fact_appointments`, Metric `appointment_id` (Count), Date Range Dimension `scheduled_datetime`, range **This week**.

### 3. Pivot table — نقشه حرارتی اشغال یونیت

Looker Studio has no heatmap chart type. Use a pivot table.

**Add a chart → Pivot table.** Data source `fact_appointments`.
Row dimension `chair_label`. Column dimension `hour_label`. Metric `appointment_id` (Count).
Filter: `status` Equal to `انجام‌شده`.

In **Style → Metric → Type**, choose **Heatmap**. Cells shade by density.

Six rows × thirteen columns. At 10% utilisation it will look sparse — that is the finding. Title it `نقشه حرارتی اشغال یونیت‌ها` and note the utilisation rate beside it.

### 4. Table — بیماران دارای بدهی

Data source `fact_invoices`. Dimensions `patient_name`, `phone`, `issue_date`, `روزهای معوق`, `status`. Metric `balance` (SUM).
Filter: `has_balance` Equal to `1`. Sort `balance` descending. Rows 15.

In Style, enable **Conditional formatting** on `روزهای معوق`: red above 30 days. Nearly half the outstanding money — 546.8 million across 77 invoices — is already 31–60 days old.

### 5. Scorecard + table — مواد کم‌موجودی

Scorecard: data source `consumables`, Metric `is_low_stock` (SUM). Shows 6.

Table beside it: Dimensions `name`, `supplier`. Metrics `stock_quantity`, `min_stock_level`, `unit_price`. Filter `is_low_stock` Equal to `1`.

Two of the six items come from شرکت آریا مد and two from دنتال سنتر ایران — sorting by supplier turns six alerts into two purchase orders.

### 6. Bar — نوبت هر دندان‌پزشک این هفته

Data source `fact_appointments`, Dimension `dentist_name`, Metric `appointment_id` (Count), Date Range Dimension `scheduled_datetime`, range **This week**.

Add `نرخ لغو` as a second metric. الهام غفاری loses 28.7% of booked slots to cancellation and no-show, against 10% for everyone else — the clearest operational anomaly in your data, and it belongs on the receptionist's page.

---

## Step 6 — Page 3: بیمار (Patient)

New page, rename `بیمار`.

Page 3 works differently: everything filters to one patient.

### The patient selector

**Add a control → Drop-down list.** Data source `fact_sessions`, Control field `patient_name`.

Because `patient_name` is spelled identically in `fact_sessions`, `fact_invoices`, `fact_payments`, `fact_appointments`, and `treatment_plans`, this one control filters every widget on the page. That naming consistency is deliberate — it's why the fact tables exist in the form they do.

Verify it after you build the page: select one patient and confirm all six widgets change. If one doesn't, its data source is missing the field or spelling it differently.

### 1. Scorecard — جلسات باقی‌مانده

Data source `treatment_plans`, Metric `sessions_remaining` (SUM), Filter `status` Equal to `فعال`. Median across active plans is 5.

### 2. Scorecard — مانده حساب

Data source `fact_invoices`, Metric `balance` (SUM).

### 3. Table — تاریخچه درمان

Data source `fact_sessions`. Dimensions `session_day`, `service_name`, `tooth_number`, `dentist_name`. Metric `actual_cost` (SUM). Sort `session_day` descending.

### 4. Table — تاریخچه پرداخت

Data source `fact_payments`. Dimensions `payment_day`, `method`, `reference_number`. Metric `amount` (SUM). Sort `payment_day` descending.

### 5. Table — نوبت بعدی

Data source `fact_appointments`. Dimensions `appt_day`, `hour_label`, `dentist_name`, `chair_label`.
Filter: `status` Equal to `رزرو`. Sort `appt_day` **ascending**. **Rows per page = 1.**

Looker Studio has no "next appointment" card; a one-row table sorted ascending is the standard workaround. In Style, hide the header and pagination so it reads as a card.

### 6. Progress bar — پیشرفت برنامه درمان

**Add a chart → Bullet chart.** Data source `treatment_plans`, Metric `progress_pct`, Filter `status` Equal to `فعال`.
In Style set Range max to 1, and add range bands at 0.33 and 0.66.

Active plans now spread 31% to 84% with a median of 56%, so this renders as a real progress indicator.

---

## Step 7 — Filters on every page

Add four controls per page. **Add a control** for each:

| Control type | Field | Notes |
|---|---|---|
| Date range control | — | Applies to charts whose Date Range Dimension is set |
| Drop-down list | `dentist_name` | |
| Drop-down list | `category` | |
| Drop-down list | `status` | Means different things per source — see below |

**How filter controls actually scope.** A control applies to charts on the same page whose data source contains a field of that exact name. Since `dentist_name` and `category` appear identically across the fact tables, one control covers the page. Verify rather than assume — select a value and watch every chart.

**`status` is a trap.** In `fact_appointments` it holds انجام‌شده/رزرو/لغو/غایب. In `fact_invoices` it holds پرداخت‌شده/بخشی/معوق. In `treatment_plans` it holds فعال/تکمیل‌شده/معلق/لغو. One control across all three produces nonsense. Put a separate status control next to each chart group and label it explicitly — `وضعیت نوبت`, `وضعیت فاکتور`, `وضعیت برنامه`.

To pin a control to specific charts: select the control and the charts together → right-click → **Group**. Grouped controls only affect their group.

---

## Step 8 — Persian labels and Toman formatting

**Labels.** Rename in the data source, not per chart — do it once and it propagates. Resource → Manage added data sources → Edit → click a field name → type the Persian name. `actual_cost` → `مبلغ جلسه`, `dentist_name` → `دندان‌پزشک`, `patient_name` → `بیمار`, `service_name` → `خدمت`, `category` → `دسته خدمت`, `balance` → `مانده حساب`, and so on.

To override a label on one chart only, click the metric in the Setup panel and use the pencil icon.

**Money.** Looker Studio has no Toman currency option — the closest is IRR (ریال), which is wrong by a factor of ten. Use plain **Number** instead: field → **Format → Number**, decimals 0, and enable **Compact numbers** for K/M abbreviation. Then put the unit in the label: `درآمد (میلیون تومان)`.

Do not use the IRR currency format and hope nobody notices. An examiner will.

**RTL.** Looker Studio does not support right-to-left layout. Persian text renders correctly but alignment defaults to left. For each text component and table column: Style → text alignment → **Right**. Mirror your page layout manually — put titles and legends on the right side.

**Theme.** Theme and layout → pick a light theme, set canvas to 1600×900 or larger. Keep one accent colour across all three pages.

---

## Step 9 — Sharing

Two separate actions. Missing the second is the commonest way these projects arrive broken.

**Share the report.** Top right → **Share** → add `farshid.abdi@gmail.com` → **Viewer** → Send.

**Share the spreadsheet.** Open `dental_clinic_bi` in Drive → Share → same address → **Viewer** → Send.

A Looker Studio report does not carry its data with it. If the underlying Sheet isn't shared, your professor sees the layout and permission errors where every chart should be.

Then verify: **File → Embed report** or open the share link in a private browsing window. If you see charts, it works. If you see "You don't have access to this data source", the Sheet isn't shared.

Optionally, in the report's data source settings, set **Data credentials → Owner's credentials**. That makes the report render for anyone with the link regardless of Sheet permissions. Share the Sheet anyway — your professor may want to inspect the data.

---

## Pitfalls, ranked by how much time they cost

**A date field typed as Text.** Every time-series and date control fails silently. Check all seven listed in Step 2 before building anything.

**Editing the Sheet after connecting.** Never insert a row above the header, never rename a tab, never add a totals row. Any of the three unbinds fields across every chart at once. If you must add a column, add it at the right end, then Resource → Manage added data sources → **Refresh fields**.

**Blending when you don't need to.** If you find yourself opening the blend editor, stop and check whether a fact table already has the field. It almost certainly does. Blends cap at five tables, can't chain joins, and are the slowest thing in Looker Studio.

**Forgetting the `status = انجام‌شده` filter** on occupancy and revenue charts. Cancelled and no-show appointments have no sessions and no revenue; including them deflates every rate.

**Leaving the default date range** on scorecards meant to show "this month." The default is the data source's full range, so the card shows all-time and quietly contradicts its own title.

**Presenting July–August as a decline.** It's the data generation window closing. Annotate it.

**Cached data during a demo.** Looker Studio caches for up to 12 hours. Hit **Refresh data** (top right, circular arrow) before you present.

---

## Verification checklist

- [ ] 8 data sources connected, 9 tabs deliberately skipped
- [ ] All 7 date fields typed as Date or Date & Time
- [ ] 8 calculated fields created in their data sources
- [ ] Page 1 shows ≥8 KPIs; occupancy card reads ~10%; cancellation 8.0%
- [ ] Revenue trend shows both revenue and average ticket, dual axis
- [ ] Dentist bar chart sorted by revenue, not session count
- [ ] Service table sorted by revenue per chair-hour
- [ ] Page 2 heatmap renders 6 chairs × 13 hours
- [ ] Page 2 low-stock KPI shows 6
- [ ] Page 3 patient drop-down changes all six widgets
- [ ] Separate status controls per data source, individually labelled
- [ ] All money formatted as compact Number with unit in the label
- [ ] Report shared with professor **and** spreadsheet shared with professor
- [ ] Verified in a private browsing window

---

## Numbers your dashboard must reproduce

If a chart disagrees with these, the chart is wrong — a missing filter or a date range left at default.

| Metric | Expected |
|---|---|
| Total revenue | 6,454,310,000 |
| Revenue this month (2026-08) | 88,860,000 |
| Revenue last month (2026-07) | 741,280,000 |
| Peak month (2026-06) | 1,178,680,000 |
| Collected / collection rate | 4,269,998,000 / 78.2% |
| Outstanding | 1,191,613,500 |
| Chair occupancy | 10.0% |
| Cancellation / no-show / completion | 8.0% / 5.0% / 80.0% |
| New patients this month | 10 |
| Low-stock items | 6 of 30 |
| Active plans / sessions remaining | 233 / 1,448 |
| Forward pipeline | 3,927,190,000 |
| Consumables (all time) | 1,371,065,110 |
| Top 2 dentists' revenue share | 56.9% |
