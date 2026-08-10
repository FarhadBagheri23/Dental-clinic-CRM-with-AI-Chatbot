# Full Data Analysis — Dental Clinic BI
تحلیل کامل داده‌ها · کلینیک دندان‌پزشکی · فرهاد باقری طاهری · Sharif University

Analysis date: 9 August 2026 (last completed session in dataset)
Source: `dental_clinic_bi.xlsx` — 500 patients, 3,000 appointments, 2,400 sessions, 400 invoices, 13 months

---

## Executive summary

The clinic bills **6.45 billion Toman** across 13 months, collects **78.2%** of what patients owe, and operates at roughly **10% chair utilisation**. Three findings dominate everything else:

Revenue is dangerously concentrated. Two of eight dentists produce **56.9%** of all revenue from **25%** of sessions. If either leaves, more than half the practice leaves with them.

The commission structure is inverted. The two dentists on the **highest** commission rate (45%) generate the **lowest** average ticket. The clinic pays the most for its least profitable work, and margin varies from 55% to 75% by dentist purely because of how commissions were set.

Capacity is the largest untapped asset. 1,866 chair-hours were used against 18,720 available. Even after allowing for the Friday closure, the clinic is running at a fraction of what its six chairs could deliver.

---

## 1. Dentist performance

| Dentist | Specialty | Comm. | Revenue | Share | Sessions | Avg ticket | Margin | Margin % |
|---|---|---|---|---|---|---|---|---|
| غزاله مقدم | ایمپلنت | 25% | 2,033,780,000 | 31.5% | 286 | 7,111,119 | 1,525,335,000 | 75.0% |
| پویا رستمی | ارتودنسی | 25% | 1,640,340,000 | 25.4% | 306 | 5,360,588 | 1,230,255,000 | 75.0% |
| علی کریمی | عمومی | 30% | 799,690,000 | 12.4% | 436 | 1,834,151 | 559,783,000 | 70.0% |
| علی علوی | عمومی | 45% | 709,690,000 | 11.0% | 412 | 1,722,549 | 390,329,500 | 55.0% |
| میلاد میرزایی | عمومی | 45% | 586,440,000 | 9.1% | 351 | 1,670,769 | 322,542,000 | 55.0% |
| کامران اکبری | کودکان | 35% | 239,230,000 | 3.7% | 373 | 641,367 | 155,499,500 | 65.0% |
| پدرام مرادی | جراح | 25% | 226,190,000 | 3.5% | 127 | 1,781,024 | 169,642,500 | 75.0% |
| الهام غفاری | جراح | 35% | 218,950,000 | 3.4% | 109 | 2,008,716 | 142,317,500 | 65.0% |

The volume-to-value relationship is inverted across the practice. علی کریمی performs the most sessions of anyone (436) and earns 12.4% of revenue. کامران اکبری performs 373 sessions — third-highest volume — for 3.7% of revenue, because paediatric work carries a 641,367 Toman average ticket against غزاله مقدم's 7.1 million. Volume and value are almost unrelated here, which means any dashboard ranking dentists by appointment count will tell the manager the opposite of the truth.

The commission problem deserves its own emphasis. علی علوی and میلاد میرزایی sit on 45% commission and produce average tickets of 1.72 and 1.67 million. غزاله مقدم and پویا رستمی sit on 25% and produce 7.11 and 5.36 million. The result is a clinic margin of 55% on the low-value work and 75% on the high-value work. Whoever set these rates inverted the incentive: the practice retains least from the work it can least afford to subsidise.

**Reliability** varies sharply and is worth a separate look:

| Dentist | Appointments | Cancellation | No-show |
|---|---|---|---|
| الهام غفاری | 202 | 18.3% | 10.4% |
| پدرام مرادی | 181 | 10.5% | 8.8% |
| غزاله مقدم | 373 | 10.2% | 4.6% |
| پویا رستمی | 382 | 8.4% | 5.2% |
| میلاد میرزایی | 416 | 7.7% | 2.4% |
| علی علوی | 484 | 6.0% | 4.5% |
| علی کریمی | 520 | 5.8% | 4.4% |
| کامران اکبری | 442 | 5.2% | 4.8% |

الهام غفاری loses 28.7% of her booked slots to cancellation or no-show — more than five times میلاد میرزایی's no-show rate and triple the clinic-wide cancellation average. Of 202 appointments only 109 converted to sessions. Whether the cause is scheduling practice, patient mix, or surgical cases being deferred, it is the single clearest operational anomaly in the dataset.

Across the clinic, **390 slots (13.0%)** were lost to cancellation and no-show. At the average ticket of 2,689,296 Toman that represents roughly **1.05 billion Toman** of unrealised revenue — an amount comparable to two months of peak billing.

---

## 2. Service profitability

Ranking services by revenue is the obvious move and the wrong one. A chair is a fixed asset and the correct denominator is time, not session count.

| Service | Category | Revenue | Margin % | n | Avg price | Min | **Revenue/chair-hour** |
|---|---|---|---|---|---|---|---|
| ارتودنسی ثابت | درمانی | 1,151,900,000 | 75.0% | 27 | 42,662,963 | 120 | **21,331,481** |
| پروتز کامل متحرک | درمانی | 182,980,000 | 61.1% | 13 | 14,075,385 | 60 | **14,075,385** |
| ایمپلنت دندان | جراحی | 1,029,990,000 | 75.0% | 46 | 22,391,087 | 120 | **11,195,543** |
| روکش زیرکونیا | زیبایی | 374,850,000 | 75.0% | 46 | 8,148,913 | 60 | **8,148,913** |
| پیوند استخوان | جراحی | 533,450,000 | 75.0% | 46 | 11,596,739 | 90 | **7,731,159** |
| لمینت سرامیکی | زیبایی | 525,260,000 | 61.9% | 54 | 9,727,037 | 90 | **6,484,691** |
| ویزیت دوره‌ای ارتودنسی | درمانی | 473,400,000 | 75.0% | 225 | 2,104,000 | 20 | **6,312,000** |
| روکش PFM | درمانی | 297,020,000 | 59.4% | 72 | 4,125,278 | 60 | **4,125,278** |
| بلیچینگ | زیبایی | 91,280,000 | 61.1% | 29 | 3,147,586 | 60 | **3,147,586** |
| کشیدن دندان عقل نهفته | جراحی | 345,910,000 | 69.7% | 78 | 4,434,744 | 90 | **2,956,496** |
| عصب‌کشی دوکاناله | درمانی | 211,830,000 | 59.4% | 72 | 2,942,083 | 75 | **2,353,667** |
| پر کردن آمالگام | درمانی | 85,190,000 | 65.0% | 84 | 1,014,167 | 45 | **1,352,222** |
| پر کردن کامپوزیت | درمانی | 860,630,000 | 63.1% | 690 | 1,247,290 | 60 | **1,247,290** |
| رادیوگرافی پانورامیک | تشخیصی | 54,990,000 | 72.0% | 137 | 401,387 | 20 | **1,204,161** |
| فلوراید تراپی | درمانی | 18,480,000 | 65.0% | 57 | 324,211 | 20 | **972,632** |
| فیشورسیلانت | درمانی | 55,610,000 | 65.0% | 118 | 471,271 | 30 | **942,542** |
| جرم‌گیری | درمانی | 87,060,000 | 60.8% | 134 | 649,701 | 45 | **866,269** |
| رادیوگرافی پری‌اپیکال | تشخیصی | 13,780,000 | 59.5% | 72 | 191,389 | 15 | **765,556** |
| معاینه و تشخیص | تشخیصی | 60,700,000 | 64.9% | 400 | 151,750 | 20 | **455,250** |

The spread runs 47-fold, from 455,250 Toman per chair-hour for معاینه و تشخیص to 21,331,481 for ارتودنسی ثابت. Twenty-seven orthodontic cases generate more revenue than the 690 composite fillings that consume 690 chair-hours.

This does not mean the clinic should stop doing examinations. معاینه و تشخیص is the entry point — 400 of them across 268 treated patients — and it feeds everything downstream. The correct reading is that diagnostic work is an acquisition cost, and the dashboard should present it as such rather than letting it look like a failing service line.

By category, درمانی carries the volume (1,492 sessions, 53.1% of revenue) while جراحی converts far less activity into more money per case (170 sessions, 29.6% of revenue) at the best margin in the practice, 74.0%.

---

## 3. Capacity and utilisation

Six chairs, thirteen operating hours (08:00–20:00), 260 operating days observed, Fridays closed.

**Theoretical capacity: 18,720 chair-hours. Actual use: 1,866. Utilisation: 10.0%.**

Utilisation is remarkably even across chairs — every unit sits between 9.2% and 10.7% — which tells you scheduling is balanced but demand is thin. No chair is a bottleneck and no chair is idle relative to the others.

| Chair | Appointments | Hours used |
|---|---|---|
| یونیت 1 | 406 | 313 |
| یونیت 2 | 423 | 326 |
| یونیت 3 | 370 | 286 |
| یونیت 4 | 390 | 292 |
| یونیت 5 | 396 | 316 |
| یونیت 6 | 415 | 333 |

Demand by hour is close to flat between 08:00 and 19:00, ranging only from 173 to 233 appointments, with a mild peak at 16:00 and a sharp fall at 20:00 (88). There is no strong rush hour to smooth, which again points at demand rather than scheduling as the constraint.

By weekday, شنبه dominates at 677 appointments against 311–364 for یکشنبه through پنج‌شنبه. Saturday opens the Iranian week and carries roughly double the load of any other day. جمعه is correctly closed throughout.

At current pricing, closing even a fraction of the utilisation gap dwarfs every other lever in this analysis. Recovering the 390 lost slots alone would add an estimated 1.05 billion Toman.

---

## 4. Revenue trend

| Month | Revenue | Sessions | Patients | MoM | Avg ticket | Consumables | Cons. % |
|---|---|---|---|---|---|---|---|
| 2025-08 | 310,000 | 2 | 2 | — | 155,000 | 135,390 | 43.7% |
| 2025-09 | 2,430,000 | 11 | 10 | +683.9% | 220,909 | 1,428,000 | 58.8% |
| 2025-10 | 71,140,000 | 27 | 25 | +2827.6% | 2,634,815 | 6,233,390 | 8.8% |
| 2025-11 | 304,930,000 | 46 | 36 | +328.6% | 6,628,913 | 10,341,060 | 3.4% |
| 2025-12 | 428,080,000 | 81 | 68 | +40.4% | 5,284,938 | 34,161,410 | 8.0% |
| 2026-01 | 437,010,000 | 110 | 89 | +2.1% | 3,972,818 | 34,940,270 | 8.0% |
| 2026-02 | 581,300,000 | 159 | 123 | +33.0% | 3,655,975 | 69,612,200 | 12.0% |
| 2026-03 | 605,990,000 | 252 | 161 | +4.2% | 2,404,722 | 129,530,590 | 21.4% |
| 2026-04 | 909,060,000 | 361 | 208 | +50.0% | 2,518,172 | 212,427,790 | 23.4% |
| 2026-05 | 1,105,240,000 | 472 | 249 | +21.6% | 2,341,610 | 274,535,110 | 24.8% |
| 2026-06 | **1,178,680,000** | 500 | 263 | +6.6% | 2,357,360 | 312,970,720 | 26.6% |
| 2026-07 | 741,280,000 | 326 | 190 | −37.1% | 2,273,865 | 235,173,850 | 31.7% |
| 2026-08 | 88,860,000 | 53 | 48 | −88.0% | 1,676,604 | 49,575,330 | 55.8% |

Two patterns matter and one caveat is essential.

**Average ticket is falling steadily** — 6.63 million in November down to 2.27 million in July. Session volume grew 10-fold over the same period while revenue grew only 2.4-fold. The clinic is acquiring lower-value work as it scales: more fillings and examinations, proportionally fewer implants and orthodontic cases. This is the most important trend in the dataset and it is invisible on a revenue chart alone. Put average ticket on the same axis as revenue.

**Consumable cost is rising as a share of revenue** — 3.4% in November to 31.7% in July. Some of this is mix shift toward درمانی work, which is consumable-heavy; some may reflect the data generator distributing usage more evenly than revenue. Treat the direction as a finding and the exact slope with caution.

**Caveat for your defence:** the July and August figures reflect the data generation window closing, not a business decline. August contains only nine days. If a chart shows revenue collapsing, say so before the examiner asks. The honest framing is that the trend series is meaningful through June 2026 and the final two points are partial.

---

## 5. Collections and accounts receivable

Patients were billed **5,461,611,500** Toman after insurance. **4,269,998,000** was collected — a **78.2%** collection rate — leaving **1,191,613,500** outstanding across 159 invoices.

| Status | Invoices | Billed | Paid | Balance |
|---|---|---|---|---|
| پرداخت‌شده | 241 | 3,462,108,000 | 3,462,108,000 | 0 |
| بخشی | 99 | 1,401,029,000 | 807,890,000 | 593,139,000 |
| معوق | 60 | 598,474,500 | 0 | 598,474,500 |

Sixty invoices have received no payment at all. Ageing the unpaid balance:

| Age | Invoices | Balance |
|---|---|---|
| 0–30 days | 79 | 629,849,500 |
| 31–60 days | 77 | 546,811,500 |
| 61–90 days | 3 | 14,952,500 |

**46% of outstanding money is already more than 30 days old.** Nothing has yet reached 90 days, which means the clinic still has time to act, but the 31–60 bucket is nearly as large as the current one — collections are not keeping pace with billing.

The ten largest debtors account for 338 million Toman, roughly 28% of the total outstanding, with individual balances between 26.6 and 43.6 million. This is a short enough list to work by phone. Concentration is an advantage here.

---

## 6. Insurance

| Provider | Invoices | Billed total | Covered | Patient share | Collected | Coverage % | **Collection %** |
|---|---|---|---|---|---|---|---|
| بدون بیمه | 97 | 1,562,060,000 | 0 | 1,562,060,000 | 1,296,580,000 | 0% | **83.0%** |
| بیمه دانا | 53 | 645,570,000 | 161,392,500 | 484,177,500 | 408,355,000 | 25% | **84.3%** |
| بیمه سینا | 61 | 944,890,000 | 0 | 944,890,000 | 796,900,000 | 0% | **84.3%** |
| بیمه ایران | 50 | 859,520,000 | 128,928,000 | 730,592,000 | 551,829,000 | 15% | **75.5%** |
| بیمه آسیا | 67 | 1,372,650,000 | 274,530,000 | 1,098,120,000 | 778,380,000 | 20% | **70.9%** |
| تامین اجتماعی | 72 | 1,069,620,000 | 427,848,000 | 641,772,000 | 437,954,000 | 40% | **68.2%** |

The result is counterintuitive and worth presenting deliberately: **coverage percentage and collection percentage move in opposite directions.** تامین اجتماعی covers the most (40%) and collects the worst (68.2%). Uninsured patients, who owe the entire amount themselves, pay 83.0% of it.

The plausible reading is behavioural rather than financial — patients who expect insurance to handle billing engage less with the remaining balance, and the smaller residual feels less urgent. For the clinic it means the highest-coverage patients need the most follow-up, which is the reverse of where collection effort naturally goes.

بیمه آسیا carries the single largest outstanding balance at 319,740,000 Toman.

---

## 7. Patients

Of 500 registered patients, **268 (54%) have ever attended a session**. The remaining 232 registered and never converted to treatment. That is the largest single growth opportunity in the dataset and it costs nothing to pursue — these people already chose the clinic once.

Among those who did attend, engagement is deep: 142 patients have seven or more sessions, 114 have four to six, and only 12 have fewer than four. There is no meaningful one-visit-and-gone population. The problem is conversion, not retention.

Revenue concentration follows a familiar shape. The **top 10% of patients generate 33.1% of revenue; the top 20% generate 55.3%**.

| Age group | Patients | Billed | Outstanding |
|---|---|---|---|
| زیر ۱۸ | 104 | 1,269,000,000 | 254,750,500 |
| ۱۸–۳۰ | 92 | 1,139,668,500 | 292,611,500 |
| ۳۱–۴۵ | 122 | 1,301,529,500 | 233,648,000 |
| ۴۶–۶۰ | 106 | 1,118,383,000 | 291,860,500 |
| بالای ۶۰ | 76 | 633,030,500 | 118,743,000 |

Billing is spread evenly across age groups. The ۱۸–۳۰ band carries the highest outstanding balance (292.6 million) against the second-lowest billing — the weakest payment behaviour in the practice. زیر ۱۸ bills the second-highest amount, driven by orthodontics, and is the group most worth protecting.

Women account for 257 patients and 3.01 billion in billing against 243 men and 2.45 billion — a 23% higher spend per patient.

---

## 8. Consumables

Total consumption: **1,371,065,110 Toman, or 21.2% of revenue.** Current stock on hand is valued at **1,837,061,350** — more than a year of consumption sitting on shelves.

| Item | Cost | Quantity |
|---|---|---|
| کامپوزیت A3 | 152,528,200 | 401.39 |
| کامپوزیت A2 | 148,272,200 | 390.19 |
| فایل روتاری | 148,023,000 | 328.94 |
| سمان رزینی | 131,294,400 | 386.16 |
| سیلر کانال ریشه | 98,150,400 | 306.72 |
| سمان گلاس‌آینومر | 77,294,700 | 368.07 |
| فیشورسیلانت رزینی | 77,235,200 | 275.84 |
| باندینگ | 71,585,000 | 286.34 |

Cost intensity by category exposes a pricing problem:

| Category | Consumable cost | Revenue | Cost as % of revenue |
|---|---|---|---|
| تشخیصی | 77,646,550 | 129,470,000 | **60.0%** |
| درمانی | 1,127,785,980 | 3,424,100,000 | 32.9% |
| زیبایی | 130,856,630 | 991,390,000 | 13.2% |
| جراحی | 34,775,950 | 1,909,350,000 | **1.8%** |

Diagnostic services consume 60 Toman of materials for every 100 Toman billed. Combined with the lowest revenue per chair-hour in the practice, تشخیصی is effectively being delivered at or below cost. That is defensible as patient acquisition — but only if it is a deliberate decision rather than an unnoticed one. جراحی at 1.8% is the mirror image: high price, minimal materials, 74% margin.

**Six items are below minimum stock and need reordering:**

| Item | On hand | Minimum | Unit price | Supplier |
|---|---|---|---|---|
| کش ارتودنسی | 24.53 | 58.56 | 35,000 | دنتال سنتر ایران |
| گوتاپرکا | 44.98 | 157.85 | 90,000 | شرکت آریا مد |
| آلژینات قالب‌گیری | 49.24 | 64.62 | 55,000 | پخش دنداطب |
| باندینگ | 74.34 | 190.45 | 250,000 | شرکت آریا مد |
| فایل روتاری | 81.15 | 190.43 | 450,000 | دنتال سنتر ایران |
| فیشورسیلانت رزینی | 107.01 | 165.35 | 280,000 | پخش دنداطب |

Two of the six come from شرکت آریا مد and two from دنتال سنتر ایران, so this is two purchase orders rather than six. فایل روتاری is the most urgent by value — 450,000 per unit and 109 units below minimum.

---

## 9. Treatment plan pipeline

| Status | Plans | Estimated | Spent | Remaining | Avg progress |
|---|---|---|---|---|---|
| فعال | 233 | 7,987,930,000 | 4,060,740,000 | 3,927,190,000 | 56.4% |
| تکمیل‌شده | 151 | 2,219,580,000 | 2,219,220,000 | 60,280,000 | 97.4% |
| معلق | 10 | 246,440,000 | 133,690,000 | 112,750,000 | 58.0% |
| لغو | 6 | 41,200,000 | 40,660,000 | 1,460,000 | 98.1% |

The forward pipeline is **3.93 billion Toman** across 233 active plans — more than three times the best month on record. Active plans sit at 56.4% average completion, spread from 31% to 84%, so this is genuine committed work rather than speculation.

Only two active plans have gone more than 60 days without a session, so plan abandonment is not currently a problem. The completion rate is high (151 completed against 6 cancelled) and worth stating plainly in your report: patients who start treatment here finish it.

---

## 10. What the dashboard should show

The analysis points at five things the three pages must communicate, and one thing they must avoid.

**Page 1 (مدیر)** should lead with revenue and its trend, but pair revenue with average ticket on the same chart. Revenue alone hides the mix shift that is the practice's real story. The dentist bar chart should be sorted by revenue, never by session count, and ideally show margin alongside so the commission inversion is visible. The service table should rank by revenue per chair-hour, not gross revenue — that single choice turns a routine ranking into an insight.

**Page 2 (پذیرش)** should surface the six low-stock items, the 31–60 day AR bucket, and today's schedule. The occupancy heatmap will look sparse at 10% utilisation; that is the finding, not a rendering fault, so label it clearly. Note that only two appointments fall on 9 August itself — widen the "today" table to a rolling seven days or the panel will look empty during your defence.

**Page 3 (بیمار)** now works properly since active plans carry real remaining scope. The progress bar will show a spread from 31% to 84% rather than a uniform 98%.

**Avoid** presenting the July and August revenue decline without annotation. It is an artifact of the data generation window, and an examiner who spots it before you explain it will assume you did not look.

---

## Appendix — reference figures

| Metric | Value |
|---|---|
| Total revenue | 6,454,310,000 Toman |
| Total billed to patients (post-insurance) | 5,461,611,500 |
| Total collected | 4,269,998,000 (78.2%) |
| Outstanding | 1,191,613,500 |
| Consumable cost | 1,371,065,110 (21.2% of revenue) |
| Stock on hand | 1,837,061,350 |
| Forward pipeline (active plans) | 3,927,190,000 |
| Chair utilisation | 10.0% |
| Completion / cancellation / no-show | 80.0% / 8.0% / 5.0% |
| Lost slots | 390 (13.0%), ≈1,048,825,375 Toman |
| Patients treated | 268 of 500 (54%) |
| Revenue from top 10% of patients | 33.1% |
| Peak month | 2026-06 — 1,178,680,000 |
| Operating pattern | 6 chairs, 08:00–20:00, closed جمعه |
