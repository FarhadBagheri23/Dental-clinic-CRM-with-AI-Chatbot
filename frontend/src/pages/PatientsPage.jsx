import { useEffect, useState } from "react";

import { PageHeader } from "@/app/layouts/PanelLayout";
import { recordsApi } from "@/features/dashboard/api/dashboardApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { date, num } from "@/shared/lib/format";
import { Card } from "@/shared/ui/Card";
import { CardSkeleton, ErrorState, Pagination } from "@/shared/ui/Feedback";
import { Table, Td, Tr } from "@/shared/ui/Table";

export function PatientsPage() {
  const [term, setTerm] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  // Debounced: typing a 10-digit national code would otherwise fire ten
  // requests, and the last one is the only answer that matters.
  useEffect(() => {
    const id = setTimeout(() => {
      setQuery(term);
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [term]);

  const result = useApiQuery((s) => recordsApi.patients({ q: query, page }, s), [query, page]);

  return (
    <>
      <PageHeader title="بیماران" subtitle="جست‌وجو بر اساس نام، کد ملی یا شماره تماس">
        <div className="relative w-full sm:w-80">
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="جست‌وجوی بیمار…"
            aria-label="جست‌وجوی بیمار"
            className="h-11 w-full rounded-xl border border-ink-200 bg-white pr-11 pl-4 text-sm
              transition-colors placeholder:text-ink-400 hover:border-ink-300
              focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
          <svg className="pointer-events-none absolute inset-y-0 right-0 mr-3.5 h-full w-5 text-ink-400" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path strokeLinecap="round" d="M20 20l-3.5-3.5" />
          </svg>
        </div>
      </PageHeader>

      <Card bodyClassName="">
        {result.loading ? (
          <div className="p-5"><CardSkeleton rows={6} /></div>
        ) : result.error ? (
          <div className="p-5"><ErrorState message={result.error} /></div>
        ) : (
          <>
            <Table
              head={["کد", "نام و نام خانوادگی", "کد ملی", "جنسیت", "تماس", "بیمه", "تاریخ ثبت"]}
              empty={query ? `نتیجه‌ای برای «${query}» یافت نشد.` : "رکوردی یافت نشد."}
            >
              {result.data.rows.map((p) => (
                <Tr key={p.patient_id}>
                  <Td className="text-ink-400">{num(p.patient_id)}</Td>
                  <Td bold>{`${p.first_name} ${p.last_name}`}</Td>
                  <Td className="field-ltr tabular-nums">{p.national_code}</Td>
                  <Td>{p.gender ?? "—"}</Td>
                  <Td className="field-ltr tabular-nums">{p.phone ?? "—"}</Td>
                  <Td>{p.insurance ?? <span className="text-ink-400">آزاد</span>}</Td>
                  <Td>{date(p.registration_date)}</Td>
                </Tr>
              ))}
            </Table>
            <Pagination meta={result.data.meta} onChange={setPage} />
          </>
        )}
      </Card>
    </>
  );
}
