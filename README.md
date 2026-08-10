# سامانه هوش تجاری کلینیک دندان‌پزشکی

**پروژه پایانی درس هوش تجاری — دانشگاه صنعتی شریف**
**دانشجو:** فرهاد باقری طاهری

سامانه‌ای کامل شامل مدل داده، مولد داده مصنوعی، داشبورد تحلیلی، چت‌بات چندنقشی و وب‌سایت ارائه، برای یک کلینیک دندان‌پزشکی.

---

## ساختار پروژه

```
BUIISNESS_INTELIGENCE/
├── dental_clinic_erd.dbml       مدل داده — منبع اصلی حقیقت (۱۲ موجودیت)
├── ErdDiagram.pdf               نمودار ER (خروجی dbdiagram.io)
├── data/                        ۱۲ فایل CSV تولیدشده (۱۰٬۹۷۴ رکورد)
├── scripts/generate_data.py     مولد داده + ۴۰ بررسی قوانین کسب‌وکار
├── website/                     وب‌سایت کلینیک — Next.js 14 (RTL، فارسی)
│   └── app/clinic-data.json     خروجی مولد؛ منبع داده سایت
├── chatbot-flows/               ۵ سناریوی کامل چت‌بات برای Voiceflow
├── report/report.md             گزارش نهایی (۱۰ بخش)
└── README.md                    همین فایل
```

---

## ۱. تولید داده

### پیش‌نیازها

- Python 3.10 یا بالاتر
- کتابخانه `Faker`

### نصب

توزیع‌های جدید لینوکس اجازه نصب سراسری بسته‌ها را نمی‌دهند (PEP 668)، بنابراین از محیط مجازی استفاده کنید:

```bash
cd ~/Desktop/BUIISNESS_INTELIGENCE

python3 -m venv .venv
source .venv/bin/activate          # ویندوز: .venv\Scripts\activate
pip install faker
```

### اجرا

```bash
python scripts/generate_data.py
```

خروجی: ۱۲ فایل CSV در پوشه `data/`، فایل `website/app/clinic-data.json` برای سایت،
و گزارش اعتبارسنجی.

```
  insurance.csv                   5 rows
  patients.csv                  500 rows
  dentists.csv                    8 rows
  staff.csv                       6 rows
  services.csv                   25 rows
  appointments.csv             3000 rows
  treatment_plans.csv           400 rows
  treatment_sessions.csv       2400 rows
  invoices.csv                  400 rows
  payments.csv                  600 rows
  consumables.csv                30 rows
  consumable_usage.csv         4000 rows

Business rule checks (40 total)
  [PASS] ...
VIOLATIONS FOUND: 0  — all business rules satisfied.
```

> اسکریپت با `SEED = 42` اجرا می‌شود و **تکرارپذیر** است — هر بار همان داده تولید می‌شود.
> فقط تاریخ‌ها نسبت به «امروز» محاسبه می‌شوند، پس اگر چند روز بعد دوباره اجرا کنید،
> بازه ۱۲ ماهه جابه‌جا می‌شود.
>
> اگر خروجی با کد خطای `1` تمام شد، یعنی حداقل یک قانون کسب‌وکار نقض شده است.
> ردیف‌های `[FAIL]` را در گزارش ببینید.

### نمای کلی داده تولیدشده

| موجودیت | تعداد | نکته |
|---|---:|---|
| بیمار | ۵۰۰ | کد ملی با رقم کنترل معتبر، سن ۳ تا ۹۵ |
| نوبت | ۳٬۰۰۰ | ۱۲ ماه گذشته، ۸۰٪ انجام‌شده |
| جلسه درمان | ۲٬۴۰۰ | یکی به ازای هر نوبت انجام‌شده |
| فاکتور | ۴۰۰ | یکی به ازای هر طرح درمان |
| **جمع کل** | **۱۰٬۹۷۴** | |

---

## ۲. بارگذاری داده در Google Sheets

Looker Studio می‌تواند مستقیماً CSV بخواند، اما Google Sheets امکان به‌روزرسانی و ویرایش می‌دهد.

1. به [sheets.google.com](https://sheets.google.com) بروید و یک **Spreadsheet جدید** بسازید.
2. نام آن را بگذارید: `Dental Clinic BI Data`
3. برای **هر یک از ۱۲ فایل CSV**:
   - یک برگه (Sheet) جدید بسازید و نام آن را دقیقاً مانند نام فایل بگذارید (مثلاً `patients`)
   - از منو: **File → Import → Upload** و فایل CSV را انتخاب کنید
   - در پنجره Import، این تنظیمات را انتخاب کنید:
     - **Import location:** `Replace current sheet`
     - **Separator type:** `Comma`
     - **Convert text to numbers, dates, and formulas:** ✅ فعال
   - روی **Import data** کلیک کنید.
4. تکرار برای هر ۱۲ فایل.

### نکات مهم

- **کدگذاری فارسی:** فایل‌ها با `utf-8-sig` (شامل BOM) ذخیره شده‌اند؛ متن فارسی بدون تنظیم اضافه درست نمایش داده می‌شود.
- **ستون‌های تاریخ:** اگر Sheets ستون `scheduled_datetime` را به‌عنوان متن شناسایی کرد، آن ستون را انتخاب کنید و **Format → Number → Date time** را بزنید.
- **ستون‌های مبلغ:** `total_amount`، `actual_cost` و `amount` باید عدد باشند نه متن. با **Format → Number → Number** بررسی کنید.
- **نام برگه‌ها را تغییر ندهید** — در Looker Studio هر برگه یک منبع داده جداگانه است و نام آن در تنظیمات نمودارها استفاده می‌شود.

---

## ۳. اتصال به Looker Studio و ساخت داشبورد

### اتصال منابع داده

1. به [lookerstudio.google.com](https://lookerstudio.google.com) بروید.
2. **Create → Report** را بزنید.
3. در پنجره Add data، کانکتور **Google Sheets** را انتخاب کنید.
4. فایل `Dental Clinic BI Data` و برگه موردنظر را انتخاب کنید → **Add**.
5. مراحل ۳ و ۴ را برای بقیه برگه‌ها تکرار کنید (**Resource → Manage added data sources → Add a data source**).

### تعریف ترکیب داده (Blend)

برای نمودارهایی که به چند جدول نیاز دارند، از **Blend** استفاده کنید:

**Resource → Manage blends → Add a blend**

| ترکیب موردنیاز | جداول | کلید اتصال |
|---|---|---|
| درآمد هر پزشک | `treatment_sessions` + `treatment_plans` + `dentists` | `plan_id`، سپس `dentist_id` |
| درآمد هر خدمت | `treatment_sessions` + `services` | `service_id` |
| وصول مطالبات | `invoices` + `payments` | `invoice_id` |
| مصرف مواد | `consumable_usage` + `consumables` | `consumable_id` |

### فیلدهای محاسباتی پیشنهادی

در هر منبع داده، از طریق **Add a field** این فیلدها را بسازید:

```sql
-- مانده حساب هر فاکتور (روی blend فاکتور و پرداخت)
Outstanding = SUM(patient_share) - SUM(amount)

-- ماه شمسی برای محور زمانی (تقریبی — بر مبنای میلادی)
Month = MONTH(issue_date)

-- نرخ غیبت (روی appointments)
NoShowRate = COUNT_DISTINCT(CASE WHEN status = 'غایب' THEN appointment_id END)
             / COUNT_DISTINCT(appointment_id)

-- کمیسیون پزشک (روی blend جلسه و پزشک)
Commission = SUM(actual_cost) * commission_rate / 100

-- وضعیت موجودی (روی consumables)
StockStatus = CASE
  WHEN stock_quantity <= min_stock_level THEN 'کمبود'
  WHEN stock_quantity <= min_stock_level * 1.5 THEN 'هشدار'
  ELSE 'مطلوب'
END
```

### تنظیم راست‌به‌چپ

Looker Studio پشتیبانی RTL کامل ندارد. برای خوانایی بهتر:

- در **Theme and layout → Theme**، فونت را روی `Vazirmatn` یا `Tahoma` بگذارید
- تراز متن هر عنصر متنی را روی **راست‌چین** تنظیم کنید
- در جدول‌ها، ستون‌های متنی فارسی را راست‌چین و ستون‌های عددی را چپ‌چین کنید

### دریافت لینک Embed

1. از منو: **File → Embed report**
2. گزینه **Enable embedding** را فعال کنید
3. تب **Embed URL** را انتخاب و آدرس را کپی کنید
4. آن را در فایل `website/app/page.js` در متغیر `LOOKER_STUDIO_URL` قرار دهید

---

## ۴. اجرای وب‌سایت به‌صورت محلی

### پیش‌نیاز

Node.js نسخه ۱۸٫۱۷ یا بالاتر:

```bash
node --version
```

### اجرا

```bash
cd website
npm install
npm run dev
```

سایت روی [http://localhost:3000](http://localhost:3000) بالا می‌آید.

### ساخت نسخه تولیدی

```bash
npm run build
npm run start
```

### تنظیم آدرس‌ها

در ابتدای فایل [`website/app/sections.jsx`](website/app/sections.jsx) دو متغیر وجود دارد:

```js
export const LOOKER_STUDIO_URL  = "";   // آدرس Embed داشبورد
export const VOICEFLOW_EMBED_URL = "";  // آدرس نمونه اولیه دستیار آنلاین
```

تا زمانی که خالی باشند، هر بخش به‌جای iframe یک راهنمای گام‌به‌گام نمایش می‌دهد.
اطلاعات تماس، آدرس و ساعات کاری کلینیک نیز در همان فایل، در ثابت `CLINIC` قرار دارد.

### بخش‌های سایت

| بخش | محتوا |
|---|---|
| خانه | معرفی کلینیک، شاخص‌ها، خدمات منتخب، کادر درمان، بیمه‌های طرف قرارداد |
| خدمات و تعرفه‌ها | هر ۲۵ خدمت به تفکیک دسته، با قیمت پایه و مدت زمان |
| کادر درمان | هر ۸ پزشک به تفکیک تخصص، با سابقه و شماره نظام پزشکی |
| نوبت آنلاین | دستیار گفت‌وگومحور رزرو نوبت (Voiceflow) |
| پنل مدیریت | داشبورد تحلیلی داخلی (Looker Studio) |

> **سایت از پایگاه داده تغذیه می‌شود.** فهرست پزشکان، کاتالوگ خدمات و اعداد
> صفحه اصلی از فایل `website/app/clinic-data.json` خوانده می‌شوند که توسط
> `scripts/generate_data.py` تولید می‌شود. با هر بار اجرای مولد، سایت به‌طور
> خودکار با داده جدید هم‌گام می‌شود — هیچ عددی در کد سایت دستی نوشته نشده است.
>
> ⚠️ پیش از اجرای `npm run build`، حتماً یک‌بار `python scripts/generate_data.py`
> را اجرا کنید تا `clinic-data.json` ساخته شود؛ در غیر این صورت build با خطای
> «ماژول یافت نشد» متوقف می‌شود.

---

## ۵. انتشار روی Vercel

### روش الف — از طریق GitHub (پیشنهادی)

1. پروژه را روی GitHub قرار دهید:

   ```bash
   git init
   git add .
   git commit -m "Dental clinic BI project"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```

2. به [vercel.com/new](https://vercel.com/new) بروید و با GitHub وارد شوید.
3. مخزن را انتخاب و **Import** کنید.
4. در تنظیمات پروژه:
   - **Framework Preset:** `Next.js`
   - **Root Directory:** `website` ← **این مورد را حتماً تنظیم کنید**
   - Build Command و Output Directory را دست نزنید
5. **Deploy** را بزنید. پس از حدود یک دقیقه آدرس `https://<project>.vercel.app` آماده است.

### روش ب — از طریق CLI

```bash
npm install -g vercel
cd website
vercel          # پیش‌نمایش
vercel --prod   # انتشار نهایی
```

### به‌روزرسانی پس از انتشار

هر `git push` روی شاخه `main` به‌صورت خودکار انتشار مجدد را فعال می‌کند. پس از پر کردن `LOOKER_STUDIO_URL` و `VOICEFLOW_EMBED_URL`، فقط کافی است تغییر را push کنید.

---

## ۶. راه‌اندازی چت‌بات در Voiceflow

پوشه [`chatbot-flows/`](chatbot-flows/) شامل ۵ سناریوی کامل است. هر فایل دارای دیالوگ کامل، قوانین اعتبارسنجی، پیام‌های خطا، قالب کد پیگیری و نکات پیاده‌سازی است.

| فایل | نقش | نوع عملیات |
|---|---|---|
| [`flow-1-book-appointment.md`](chatbot-flows/flow-1-book-appointment.md) | بیمار | رزرو نوبت |
| [`flow-2-treatment-status.md`](chatbot-flows/flow-2-treatment-status.md) | بیمار | پیگیری وضعیت (خواندنی) |
| [`flow-3-register-patient.md`](chatbot-flows/flow-3-register-patient.md) | پذیرش | ثبت بیمار جدید |
| [`flow-4-consumable-usage.md`](chatbot-flows/flow-4-consumable-usage.md) | دستیار | ثبت مصرف مواد |
| [`flow-5-manager-quick-report.md`](chatbot-flows/flow-5-manager-quick-report.md) | مدیر | گزارش تجمیعی |

### مراحل راه‌اندازی

1. در [voiceflow.com](https://www.voiceflow.com) ثبت‌نام و یک **Chat Assistant** جدید بسازید.
2. زبان پروژه را روی **Persian / Farsi** و جهت را راست‌به‌چپ تنظیم کنید.
3. برای هر فلو یک Topic جداگانه بسازید و بلوک‌ها را طبق بخش **Voiceflow Implementation Notes** انتهای هر فایل بچینید.
4. توابع اعتبارسنجی (کد ملی، تاریخ، مقدار) را در **Code Block** با JavaScript پیاده کنید.
5. برای اتصال به داده واقعی، بلوک‌های **API** را به لایه سرویس خود وصل کنید. تا آن زمان می‌توانید از پاسخ‌های ثابت (Mock) استفاده کنید.
6. از **Share → Prototype** لینک عمومی بگیرید و در `VOICEFLOW_EMBED_URL` قرار دهید.

### نکات مهم پیاده‌سازی

- **نرمال‌سازی ارقام:** کاربر ممکن است ارقام فارسی (`۰۱۲۳`) یا عربی (`٠١٢٣`) وارد کند. در ابتدای هر Code Block به لاتین تبدیل کنید.
- **تبدیل تاریخ:** ورودی کاربر شمسی است اما پایگاه داده میلادی؛ تبدیل را در Code Block انجام دهید.
- **اعتبارسنجی سه‌لایه:** ربات (تجربه کاربری) → API (امنیت) → پایگاه داده (یکپارچگی). هرگز فقط به لایه اول تکیه نکنید.
- **شمارنده تلاش:** پس از ۳ خطای پی‌درپی، کاربر را به پشتیبانی انسانی هدایت کنید.

---

## ۷. گزارش نهایی

فایل [`report/report.md`](report/report.md) شامل اسکلت کامل گزارش در ۱۰ بخش است. بخش‌های نشانه‌گذاری‌شده با `[[...]]` را با اطلاعات خود کامل کنید.

برای تبدیل به PDF:

```bash
# با Pandoc
pandoc report/report.md -o report/report.pdf --pdf-engine=xelatex -V mainfont="Vazirmatn"

# یا: فایل را در VS Code باز کنید و افزونه "Markdown PDF" را اجرا کنید
```

---

## رفع اشکال

| مشکل | راه‌حل |
|---|---|
| `ModuleNotFoundError: No module named 'faker'` | محیط مجازی فعال نیست: `source .venv/bin/activate` |
| `error: externally-managed-environment` | از venv استفاده کنید (بخش ۱)، نه `pip install` سراسری |
| متن فارسی در اکسل به‌هم‌ریخته است | فایل‌ها `utf-8-sig` هستند؛ در اکسل از **Data → From Text/CSV** استفاده کنید نه دابل‌کلیک |
| `npm run build` خطای نسخه Node می‌دهد | Next.js 14 حداقل به Node 18.17 نیاز دارد: `node --version` |
| داشبورد در سایت لود نمی‌شود | در Looker Studio گزینه **Enable embedding** را فعال کنید |
| `Module not found: ./clinic-data.json` | ابتدا `python scripts/generate_data.py` را اجرا کنید |
| اعداد فاکتور با جلسات نمی‌خواند | `python scripts/generate_data.py` را دوباره اجرا کنید — همه CSVها باید از یک اجرا باشند |
| Vercel خطای build می‌دهد | **Root Directory** را روی `website` تنظیم کنید |

---

## پشته فناوری

| لایه | فناوری |
|---|---|
| مدل داده | DBML — رندر در dbdiagram.io |
| تولید داده | Python 3.12 + Faker (fa_IR) |
| ذخیره‌سازی | CSV → Google Sheets |
| تحلیل و بصری‌سازی | Google Looker Studio |
| چت‌بات | Voiceflow |
| وب‌سایت | Next.js 14 (App Router) + Tailwind CSS + Vazirmatn |
| انتشار | Vercel |
