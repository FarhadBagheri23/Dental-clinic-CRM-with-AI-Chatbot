"use client";

import clinic from "./clinic-data.json";
import { CLINIC, VOICEFLOW_EMBED_URL } from "../lib/config";

export { CLINIC };

const fa = (n) => n.toLocaleString("fa-IR");
const toman = (n) => `${fa(n)} تومان`;

const CATEGORY_META = {
  تشخیصی: { icon: "🔍", tone: "bg-sky-50 text-sky-700 border-sky-200" },
  درمانی: { icon: "🦷", tone: "bg-brand-50 text-brand-700 border-brand-200" },
  جراحی: { icon: "⚕️", tone: "bg-rose-50 text-rose-700 border-rose-200" },
  زیبایی: { icon: "✨", tone: "bg-amber-50 text-amber-700 border-amber-200" },
};
const CATEGORY_ORDER = ["تشخیصی", "درمانی", "جراحی", "زیبایی"];

const AVATAR_TONES = [
  "from-brand-500 to-brand-700",
  "from-sky-500 to-sky-700",
  "from-teal-500 to-teal-700",
  "from-cyan-500 to-cyan-700",
];

const FEATURED = [
  "معاینه و تشخیص",
  "جرم‌گیری",
  "پر کردن کامپوزیت",
  "ایمپلنت دندان",
  "ارتودنسی ثابت",
  "لمینت سرامیکی",
];

function SectionHead({ eyebrow, title, sub }) {
  return (
    <div className="mx-auto mb-10 max-w-2xl text-center">
      {eyebrow ? (
        <span className="mb-3 inline-block rounded-full bg-brand-50 px-4 py-1 text-xs font-bold text-brand-700">
          {eyebrow}
        </span>
      ) : null}
      <h2 className="text-2xl font-black text-slate-900 sm:text-3xl">{title}</h2>
      {sub ? <p className="mt-3 text-sm leading-8 text-slate-600">{sub}</p> : null}
    </div>
  );
}

function ServiceCard({ s }) {
  const meta = CATEGORY_META[s.category] ?? CATEGORY_META["درمانی"];
  return (
    <div className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-3">
        <span className="text-2xl">{meta.icon}</span>
        <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${meta.tone}`}>
          {s.category}
        </span>
      </div>
      <h3 className="font-bold text-slate-900">{s.name}</h3>
      <p className="mt-2 flex-1 text-sm leading-7 text-slate-600">{s.description}</p>
      <div className="mt-4 flex items-end justify-between border-t border-slate-100 pt-3">
        <span className="text-xs text-slate-500">{fa(s.duration_minutes)} دقیقه</span>
        <span className="text-sm font-black text-brand-700">{toman(s.base_price)}</span>
      </div>
    </div>
  );
}

function DoctorCard({ d, i }) {
  const initial = d.name.replace("دکتر ", "").charAt(0);
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div
        className={`mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br ${
          AVATAR_TONES[i % AVATAR_TONES.length]
        } text-3xl font-black text-white shadow-inner`}
      >
        {initial}
      </div>
      <h3 className="font-bold text-slate-900">{d.name}</h3>
      <p className="mt-1 text-sm font-medium text-brand-700">متخصص {d.specialty}</p>
      <p className="mt-3 text-xs text-slate-500">{fa(d.experience_years)} سال سابقه در این کلینیک</p>
      <p className="mt-1 text-xs text-slate-400">شماره نظام: {d.license_number}</p>
    </div>
  );
}

function Placeholder({ title, steps, note }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-brand-200 bg-white p-8 text-center">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-50 text-2xl">
        🔗
      </div>
      <h3 className="mb-3 text-lg font-bold text-slate-800">{title}</h3>
      <ol className="mx-auto max-w-xl space-y-2 text-right text-sm leading-7 text-slate-600">
        {steps.map((s, i) => (
          <li key={i} className="flex gap-2">
            <span className="shrink-0 font-bold text-brand-600">{fa(i + 1)}.</span>
            <span>{s}</span>
          </li>
        ))}
      </ol>
      {note ? (
        <p className="mt-5 inline-block rounded-lg bg-slate-100 px-3 py-2 font-mono text-xs text-slate-500">
          {note}
        </p>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ home */

export function Home({ go }) {
  const featured = clinic.services.filter((s) => FEATURED.includes(s.name));
  // Exact counts straight from the clinic database — no rounding, no "+".
  const stats = [
    { v: fa(clinic.stats.patients), l: "بیمار ثبت‌شده" },
    { v: fa(clinic.stats.dentists), l: "پزشک متخصص" },
    { v: fa(clinic.stats.services), l: "خدمت درمانی" },
    { v: fa(clinic.stats.sessions_last_year), l: "درمان موفق در سال گذشته" },
  ];

  return (
    <div className="space-y-20">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-bl from-brand-800 via-brand-600 to-brand-500 px-6 py-20 text-white shadow-xl sm:px-14">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-16 -top-16 h-72 w-72 rounded-full bg-white/10 blur-2xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 -right-10 h-80 w-80 rounded-full bg-brand-400/20 blur-3xl"
        />
        <div className="relative mx-auto max-w-3xl text-center">
          <span className="mb-5 inline-block rounded-full bg-white/15 px-4 py-1.5 text-xs font-bold backdrop-blur">
            بیش از ۱۲ سال تجربه در خدمات دندان‌پزشکی
          </span>
          <h1 className="text-3xl font-black leading-[1.5] sm:text-5xl sm:leading-[1.4]">
            لبخند سالم،
            <br />
            اعتماد ماندگار
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-base leading-9 text-brand-50 sm:text-lg">
            از معاینه و جرم‌گیری تا ایمپلنت، ارتودنسی و طراحی لبخند — با کادری مجرب،
            تجهیزات روز و پذیرش بیمه‌های اصلی.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <button
              onClick={() => go("booking")}
              className="rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-brand-700 shadow-lg transition hover:bg-brand-50"
            >
              رزرو نوبت آنلاین
            </button>
            <button
              onClick={() => go("services")}
              className="rounded-xl border border-white/40 px-7 py-3.5 text-sm font-bold text-white transition hover:bg-white/10"
            >
              مشاهده خدمات و تعرفه‌ها
            </button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => (
          <div
            key={s.l}
            className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm"
          >
            <div className="text-3xl font-black text-brand-600 sm:text-4xl">{s.v}</div>
            <div className="mt-2 text-xs leading-6 text-slate-500 sm:text-sm">{s.l}</div>
          </div>
        ))}
      </section>

      <section>
        <SectionHead
          eyebrow="خدمات ما"
          title="آنچه در کلینیک ارائه می‌دهیم"
          sub="تعرفه‌ها شفاف و بر اساس نوع درمان اعلام می‌شود. هزینه نهایی پس از معاینه و بررسی شرایط دهان و دندان شما تعیین می‌گردد."
        />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {featured.map((s) => (
            <ServiceCard key={s.name} s={s} />
          ))}
        </div>
        <div className="mt-8 text-center">
          <button
            onClick={() => go("services")}
            className="rounded-xl border border-brand-300 px-6 py-3 text-sm font-bold text-brand-700 transition hover:bg-brand-50"
          >
            مشاهده هر {fa(clinic.stats.services)} خدمت
          </button>
        </div>
      </section>

      <section>
        <SectionHead eyebrow="چرا کلینیک ما" title="آنچه ما را متمایز می‌کند" />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: "👨‍⚕️",
              t: "کادر متخصص",
              d: "هشت دندان‌پزشک در پنج تخصص: عمومی، ارتودنسی، جراحی، کودکان و ایمپلنت.",
            },
            {
              icon: "🛡️",
              t: "استریلیزاسیون کامل",
              d: "رعایت کامل پروتکل‌های کنترل عفونت و استفاده از وسایل یکبارمصرف در تمام مراحل.",
            },
            {
              icon: "🧾",
              t: "پذیرش بیمه",
              d: "قرارداد مستقیم با بیمه‌های اصلی و امکان پرداخت اقساطی برای درمان‌های بلندمدت.",
            },
            {
              icon: "📱",
              t: "نوبت‌دهی هوشمند",
              d: "رزرو نوبت به‌صورت شبانه‌روزی از طریق دستیار آنلاین، بدون نیاز به تماس تلفنی.",
            },
          ].map((c) => (
            <div
              key={c.t}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-2xl">
                {c.icon}
              </div>
              <h3 className="mb-2 font-bold text-slate-900">{c.t}</h3>
              <p className="text-sm leading-7 text-slate-600">{c.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <SectionHead eyebrow="کادر درمان" title="با پزشکان ما آشنا شوید" />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {clinic.dentists.slice(0, 4).map((d, i) => (
            <DoctorCard key={d.license_number} d={d} i={i} />
          ))}
        </div>
        <div className="mt-8 text-center">
          <button
            onClick={() => go("doctors")}
            className="rounded-xl border border-brand-300 px-6 py-3 text-sm font-bold text-brand-700 transition hover:bg-brand-50"
          >
            معرفی کامل کادر درمان
          </button>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">
        <h2 className="text-xl font-black text-slate-900">بیمه‌های طرف قرارداد</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-slate-600">
          سهم بیمه در زمان صدور صورتحساب به‌صورت خودکار کسر می‌شود. کافی است هنگام
          پذیرش، دفترچه یا کارت بیمه خود را همراه داشته باشید.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {clinic.insurance.map((n) => (
            <span
              key={n}
              className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-2.5 text-sm font-bold text-slate-700"
            >
              {n}
            </span>
          ))}
        </div>
      </section>

      <section className="overflow-hidden rounded-3xl bg-slate-900 px-6 py-14 text-center text-white sm:px-12">
        <h2 className="text-2xl font-black leading-relaxed sm:text-3xl">
          امروز وقت رسیدگی به لبخندتان است
        </h2>
        <p className="mx-auto mt-4 max-w-lg text-sm leading-8 text-slate-300">
          نوبت خود را در کمتر از یک دقیقه رزرو کنید، یا برای مشاوره با ما تماس بگیرید.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <button
            onClick={() => go("booking")}
            className="rounded-xl bg-brand-500 px-7 py-3.5 text-sm font-bold text-white transition hover:bg-brand-400"
          >
            رزرو نوبت
          </button>
          <a
            href={`tel:${CLINIC.phone}`}
            className="rounded-xl border border-white/25 px-7 py-3.5 text-sm font-bold transition hover:bg-white/10"
          >
            تماس: {CLINIC.phone}
          </a>
        </div>
      </section>
    </div>
  );
}

/* --------------------------------------------------------- services page */

export function Services() {
  return (
    <div className="space-y-12">
      <SectionHead
        eyebrow="تعرفه‌ها"
        title="خدمات و تعرفه‌های کلینیک"
        sub="مبالغ زیر تعرفه پایه هر خدمت است. هزینه نهایی بسته به شرایط دهان و دندان، تعداد جلسات و پوشش بیمه شما متفاوت خواهد بود."
      />

      {CATEGORY_ORDER.map((cat) => {
        const items = clinic.services.filter((s) => s.category === cat);
        if (!items.length) return null;
        const meta = CATEGORY_META[cat];
        return (
          <section key={cat}>
            <div className="mb-5 flex items-center gap-3 border-b border-slate-200 pb-3">
              <span className="text-2xl">{meta.icon}</span>
              <h3 className="text-lg font-black text-slate-900">خدمات {cat}</h3>
              <span className="mr-auto text-xs text-slate-400">{fa(items.length)} خدمت</span>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((s) => (
                <ServiceCard key={s.name} s={s} />
              ))}
            </div>
          </section>
        );
      })}

      <p className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-center text-sm leading-7 text-amber-900">
        ⚠️ تعرفه‌ها ممکن است بر اساس مصوبات سالانه نظام پزشکی به‌روزرسانی شوند. برای
        دریافت برآورد دقیق، لطفاً یک نوبت معاینه رزرو کنید.
      </p>
    </div>
  );
}

/* ---------------------------------------------------------- doctors page */

export function Doctors() {
  const bySpecialty = clinic.dentists.reduce((acc, d) => {
    (acc[d.specialty] ||= []).push(d);
    return acc;
  }, {});

  return (
    <div className="space-y-12">
      <SectionHead
        eyebrow="کادر درمان"
        title="پزشکان کلینیک"
        sub="تیم ما متشکل از دندان‌پزشکان عمومی و متخصص است که در تمام مراحل درمان همراه شما هستند."
      />
      {Object.entries(bySpecialty).map(([spec, list]) => (
        <section key={spec}>
          <div className="mb-5 flex items-center gap-3 border-b border-slate-200 pb-3">
            <h3 className="text-lg font-black text-slate-900">تخصص {spec}</h3>
            <span className="mr-auto text-xs text-slate-400">{fa(list.length)} پزشک</span>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {list.map((d, i) => (
              <DoctorCard key={d.license_number} d={d} i={i} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------- booking page */

export function Booking() {
  return (
    <div className="space-y-8">
      <SectionHead
        eyebrow="نوبت‌دهی آنلاین"
        title="دستیار هوشمند رزرو نوبت"
        sub="به‌صورت شبانه‌روزی نوبت بگیرید، وضعیت درمانتان را پیگیری کنید یا مانده حسابتان را ببینید — بدون نیاز به تماس تلفنی."
      />

      <div className="grid gap-5 sm:grid-cols-3">
        {[
          { icon: "📅", t: "رزرو نوبت", d: "انتخاب پزشک، تاریخ و ساعت از میان وقت‌های آزاد." },
          { icon: "📋", t: "پیگیری درمان", d: "مشاهده جلسات انجام‌شده و نوبت بعدی شما." },
          { icon: "💳", t: "مانده حساب", d: "بررسی صورتحساب، سهم بیمه و پرداخت‌های انجام‌شده." },
        ].map((c) => (
          <div key={c.t} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 text-2xl">{c.icon}</div>
            <h3 className="mb-1.5 font-bold text-slate-900">{c.t}</h3>
            <p className="text-sm leading-7 text-slate-600">{c.d}</p>
          </div>
        ))}
      </div>

      {VOICEFLOW_EMBED_URL ? (
        <iframe
          src={VOICEFLOW_EMBED_URL}
          title="دستیار هوشمند رزرو نوبت"
          className="h-[calc(100vh-18rem)] min-h-[560px] w-full rounded-2xl border border-slate-200 bg-white shadow-sm"
          allow="microphone"
        />
      ) : (
        <Placeholder
          title="دستیار آنلاین هنوز متصل نشده است"
          steps={[
            "پروژه را در Voiceflow بسازید و سناریوهای پوشه chatbot-flows را پیاده کنید.",
            "از منوی Share گزینه Prototype را انتخاب کنید.",
            "لینک عمومی نمایش‌داده‌شده را کپی کنید.",
            "آن را در متغیر VOICEFLOW_EMBED_URL در ابتدای فایل app/sections.jsx قرار دهید.",
          ]}
          note="website/app/sections.jsx → VOICEFLOW_EMBED_URL"
        />
      )}

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center">
        <p className="text-sm leading-8 text-slate-700">
          ترجیح می‌دهید تلفنی صحبت کنید؟ در ساعات کاری با شماره{" "}
          <a href={`tel:${CLINIC.phone}`} className="font-black text-brand-700">
            {CLINIC.phone}
          </a>{" "}
          در خدمت شما هستیم.
        </p>
      </div>
    </div>
  );
}
