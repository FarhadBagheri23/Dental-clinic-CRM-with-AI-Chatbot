import { listPatients } from "../../../../lib/queries";
import { PageHead, Pagination, Table, fa, faDate } from "../../ui";

export default async function PatientsPage({ searchParams }) {
  const q = searchParams?.q ?? "";
  const page = Number(searchParams?.page ?? 1) || 1;
  const { rows, meta } = await listPatients({ q, page });

  return (
    <>
      <PageHead title="بیماران" sub={`${fa(meta.total)} پرونده ثبت‌شده`}>
        <form action="/admin-panel/patients" className="flex gap-2">
          <input
            name="q"
            defaultValue={q}
            placeholder="نام، کد ملی یا شماره تماس"
            className="w-64 rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <button className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-bold text-white transition hover:bg-brand-700">
            جستجو
          </button>
          {q ? (
            <a
              href="/admin-panel/patients"
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-600 transition hover:bg-slate-50"
            >
              پاک‌کردن
            </a>
          ) : null}
        </form>
      </PageHead>

      <Table
        head={["کد", "نام و نام خانوادگی", "کد ملی", "جنسیت", "تماس", "بیمه", "حساسیت", "تاریخ ثبت"]}
        empty={q ? `نتیجه‌ای برای «${q}» یافت نشد.` : "بیماری ثبت نشده است."}
      >
        {rows.map((p) => (
          <tr key={p.patient_id} className="hover:bg-slate-50">
            <td className="px-4 py-3 font-mono text-xs text-slate-400">
              PAT-{String(p.patient_id).padStart(5, "0")}
            </td>
            <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">
              {p.first_name} {p.last_name}
            </td>
            <td className="px-4 py-3 font-mono text-xs text-slate-600" dir="ltr">
              {p.national_code}
            </td>
            <td className="px-4 py-3 text-slate-500">{p.gender}</td>
            <td className="px-4 py-3 font-mono text-xs text-slate-600" dir="ltr">
              {p.phone}
            </td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-600">
              {p.insurance ?? <span className="text-slate-400">آزاد</span>}
            </td>
            <td className="px-4 py-3">
              {p.allergies ? (
                <span className="whitespace-nowrap rounded-full border border-rose-200 bg-rose-50 px-2.5 py-0.5 text-[11px] font-bold text-rose-700">
                  ⚠️ {p.allergies}
                </span>
              ) : (
                <span className="text-slate-300">—</span>
              )}
            </td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-500">{faDate(p.registration_date)}</td>
          </tr>
        ))}
      </Table>

      <Pagination meta={meta} basePath="/admin-panel/patients" params={q ? { q } : {}} />
    </>
  );
}
