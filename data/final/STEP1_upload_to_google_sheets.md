# STEP 1 — Getting the data into Google Sheets
Dental Clinic BI · Sharif University · فرهاد باقری طاهری

---

## The structure decision: ONE workbook, 16 tabs

You asked whether to use one sheet per table or one workbook per table. **One workbook with multiple tabs — definitively.**

Looker Studio's Google Sheets connector selects a *single worksheet (tab)* per data source, not a whole file. So twelve separate workbooks buys you nothing and costs you a lot: twelve files to share, twelve permission sets to keep in sync, twelve URLs to re-authorise, and twelve chances for the professor to open one and get "Request access."

Your data is tiny by Sheets standards — roughly 21,000 rows and 320,000 cells against a 10 million cell ceiling. There is no performance argument for splitting.

I have already merged everything into a single file: `dental_clinic_bi.xlsx`.

---

## What is inside the workbook

**Twelve raw tabs** — one per ERD entity, matching your dbdiagram exactly. These exist so the professor can trace your ERD to real tables. Three of them are enriched with derived columns that cost nothing and save you work later:

| Tab | Rows | Added columns |
|---|---|---|
| `insurance` | 5 | — |
| `patients` | 500 | `total_billed`, `total_paid`, `outstanding`, `age`, `age_group`, `reg_month`, `company_name` |
| `dentists` | 8 | `dentist_name` |
| `staff` | 6 | `staff_name` |
| `services` | 25 | — |
| `appointments` | 3,000 | — |
| `treatment_plans` | 400 | `sessions_done`, `spent`, `progress_pct`, `remaining_cost`, `patient_name`, `dentist_name` |
| `treatment_sessions` | 2,400 | — |
| `invoices` | 400 | — |
| `payments` | 600 | — |
| `consumables` | 30 | `stock_value`, `is_low_stock`, `stock_status` |
| `consumable_usage` | 4,000 | — |

**Four fact tabs** — pre-joined, denormalised tables built specifically for Looker Studio:

| Tab | Rows | Powers |
|---|---|---|
| `fact_sessions` | 2,400 | Revenue trend, revenue by dentist, revenue by category, top services, treatment history |
| `fact_appointments` | 3,000 | Occupancy heatmap, cancellation rate, today's appointments, appointments per dentist |
| `fact_invoices` | 400 | Outstanding balances, overdue payments, collection rate, payment history |
| `fact_consumable_usage` | 4,000 | Monthly consumables cost, cost per dentist, cost per service |

### Why the fact tabs matter more than anything else in this step

This is the single most important architectural decision in your project, so it is worth understanding before you click anything.

Looker Studio's data blending is deliberately limited. A blend accepts at most five tables, joins only on exactly-matching key fields, and — critically — **cannot chain a join through an intermediate table to reach a third one**. Your ERD is properly normalised, which means almost every interesting metric requires two or three hops.

Take "revenue by dentist," your Page 1 bar chart. The path is `treatment_sessions → treatment_plans → dentists`. The dentist's name lives two tables away from the money. In a blend you would join sessions to plans, get `dentist_id`, and then discover you cannot join the *result* of that blend to `dentists` to turn the ID into a name. You would end up with a bar chart labelled 1, 2, 3, 4 instead of میلاد میرزایی.

"Revenue by service category" is the same story: `treatment_sessions → services` for the category, and the money is in sessions. That one hop a blend can do. But "monthly consumables cost by dentist" is `consumable_usage → consumables` for price *and* `consumable_usage → treatment_sessions → treatment_plans → dentists` for the name. Four tables, three hops. Not possible.

The fix is the standard BI answer, and it is what every real dashboard does: flatten the joins upstream, before the data reaches the reporting layer. `fact_sessions` already carries `dentist_name`, `service_name`, `category`, `patient_name`, `company_name`, `year_month` and the money on every single row. Your bar chart becomes: dimension `dentist_name`, metric `actual_cost`. No blend at all.

Say this in your report and in your defence. Building a star schema — dimension tables plus wide fact tables — is a recognised BI design pattern (Kimball dimensional modelling), and demonstrating that you understood *why* normalised OLTP structure is wrong for OLAP reporting is worth marks on its own. You are not taking a shortcut; you are doing the thing correctly.

**Rule for the whole project: build every chart from a fact tab. Reach for a blend only when nothing else works.**

### Extra columns I pre-computed for you

These exist so you do not have to write Looker Studio calculated fields for them:

- `year_month` (`2026-08`) — the trend-line dimension. Sorts correctly as text, no date-granularity fights.
- `hour`, `hour_label`, `weekday`, `chair_label` — the occupancy heatmap axes.
- `is_completed`, `is_cancelled`, `is_noshow`, `is_booked` — 1/0 flags. Cancellation rate is now `AVG(is_cancelled)`, a one-token metric instead of a `CASE` statement.
- `balance` = `patient_share − paid_amount`, plus `is_overdue` and `has_balance` flags.
- `usage_cost` = `quantity_used × unit_price`.
- `dentist_commission` and `clinic_margin` — for the "most profitable services" table, so you can rank by true margin rather than gross revenue. That distinction will impress a BI examiner.
- `progress_pct` on `treatment_plans` — stored as a 0–1 fraction, which is what Looker Studio's bullet/progress charts expect.

---

## Three data problems I found and fixed

Your generator produced clean data — I checked all twelve foreign-key relationships and found **zero orphan rows**, invoice arithmetic (`total = insurance_covered + patient_share`) balanced on all 400 invoices, zero overpayments, tooth numbers all within 1–32, and every session date inside its plan's date range. That is genuinely solid.

But three things would have shown as empty or zero on your dashboard:

**1. Current month had no revenue.** The dataset's internal "today" was 26 July 2026 — every appointment after that was still `رزرو`. Your "Revenue this month vs last month," "New patients this month," and "Today's appointments" widgets would all have rendered zero on defence day. I shifted every operational date forward by 16 days, so the last completed session now lands on 11 August 2026 (20 Mordad 1405). Birth dates and hire dates were left untouched. All relative gaps are preserved, so no business rule broke.

Current month now reads: **103,600,000 Toman across 60 sessions**, against 771,720,000 Toman last month, 12 new patients, and 217 future bookings still sitting ahead of today.

**2. 144 appointments had a blank `created_by_staff_id`.** Assigned to the two reception staff (IDs 1 and 2), which is who actually books appointments in your model.

**3. No consumable was below its minimum stock level** — all thirty were above, so your Page 2 "Low-stock consumables" KPI would have permanently displayed zero. I pushed six items below their thresholds.

---

## Exact steps

### 1. Upload to Drive

Open [drive.google.com](https://drive.google.com), then either drag `dental_clinic_bi.xlsx` into the window, or **New → File upload** and select it.

### 2. Convert to Google Sheets

Right-click the uploaded file → **Open with → Google Sheets**. It opens in Sheets viewing mode.

Then **File → Save as Google Sheets**. This creates a true Sheets document — a separate file. Delete the leftover `.xlsx` afterwards to avoid confusion.

> **Do not skip the conversion.** Looker Studio's Google Sheets connector cannot read an `.xlsx` sitting in Drive. It only sees native Sheets documents. This trips up a lot of people.

### 3. Set the locale — do this before anything else

**File → Settings → General → Locale → United States**, then **Save settings**.

This is not cosmetic. Under an Iran locale, Sheets may parse `2026-08-11` ambiguously and expects `٬` as a decimal separator. Looker Studio then fails to recognise your date columns as dates, and every time-series chart silently breaks. US locale gives you unambiguous ISO date parsing and `.` decimals.

Leave the timezone as Tehran — that only affects `NOW()`, which you are not using.

### 4. Verify the leading zeros survived

Click the `patients` tab. Look at `phone` and `national_code`.

You should see `09132677360`, not `9132677360` or `9.13E+09`.

All 500 phone numbers and 39 national codes in your data begin with a zero. I formatted those columns as text inside the workbook, so conversion should preserve them. If any lost their zero, select the column → **Format → Number → Plain text**, then re-paste that column from the CSV in `final/`.

### 5. Rename the file

Something like `Dental_Clinic_BI_Data` — the professor will see this name.

---

## Sharing with your professor

Do this now rather than at the end, because a Looker Studio report shared without its underlying data source shows the viewer nothing but permission errors.

Click **Share** (top right) → enter `farshid.abdi@gmail.com` → set the role to **Viewer** → **Send**.

Leave the general access setting on "Restricted." Explicitly sharing with his address is cleaner than a public link, and it is what an examiner expects to see.

> When you build the Looker Studio report later, you must share **both** the report and this spreadsheet with him. Two separate share actions. Forgetting the second one is the single most common way these projects arrive broken.

---

## Pitfalls to avoid

**Never insert rows, columns, or a title above row 1.** Looker Studio reads row 1 as the header. One inserted row and every field in every data source unbinds, and every chart on all three pages breaks at once.

**Never add a totals row at the bottom of a tab.** It becomes a data row and quietly corrupts every sum and average.

**Do not rename tabs after connecting them to Looker Studio.** The data source binds to the tab name. Renaming breaks the link, and the error message does not tell you why.

**Do not translate the column headers to Persian.** Keep `actual_cost`, `dentist_name`, and so on in English. You will set Persian display names inside Looker Studio, where they belong — the presentation layer. Persian field names in formulas are painful to debug, especially with mixed RTL/LTR text in a formula editor.

**Avoid merged cells anywhere.** Looker Studio handles them badly.

**Do not sort or filter a tab and then save a filter view** expecting it to affect Looker Studio. It reads the underlying data regardless. Do all filtering in Looker Studio.

---

## Verification checklist

Before moving to Step 2, confirm:

- [ ] File is a native Google Sheet, not an `.xlsx` in Drive
- [ ] All 16 tabs present
- [ ] Locale set to United States
- [ ] `patients!G2` shows `09132677360` with its leading zero
- [ ] `fact_sessions` has 2,400 rows and 26 columns, header in row 1
- [ ] `fact_appointments` has 3,000 rows and 27 columns
- [ ] No blank rows above any header
- [ ] Shared with `farshid.abdi@gmail.com` as Viewer

---

## Reference numbers

Keep these — they are what your dashboard should reproduce. If a Looker Studio chart disagrees, your filter or blend is wrong, not the data.

| Metric | Value |
|---|---|
| Total revenue (all time) | 6,454,310,000 Toman |
| Total collected | 4,269,998,000 Toman |
| Outstanding balance | 1,191,613,500 Toman |
| Consumables cost (all time) | 1,371,065,110 Toman |
| Revenue — current month (2026-08) | 103,600,000 Toman |
| Revenue — previous month (2026-07) | 771,720,000 Toman |
| Cancellation rate | 8.00% |
| No-show rate | 5.00% |
| Completion rate | 80.00% |
| Patients with an outstanding balance | 137 of 500 |
| Overdue invoices | 60 of 400 |
| Active treatment plans | 233 of 400 |
| Low-stock consumables | 6 of 30 |
| Months of trend data | 13 |
| Clinic operating hours | 08:00 – 20:00, chairs 1–6 |

Revenue by category: درمانی 3,424,100,000 · جراحی 1,909,350,000 · زیبایی 991,390,000 · تشخیصی 129,470,000
