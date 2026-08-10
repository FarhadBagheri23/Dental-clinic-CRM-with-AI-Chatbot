import { useState } from "react";

import { PageHeader } from "@/app/layouts/PanelLayout";
import { recordsApi } from "@/features/dashboard/api/dashboardApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { dateTime, num } from "@/shared/lib/format";
import { Badge } from "@/shared/ui/Badge";
import { Card } from "@/shared/ui/Card";
import { CardSkeleton, ErrorState, FilterTabs, Pagination } from "@/shared/ui/Feedback";
import { Table, Td, Tr } from "@/shared/ui/Table";

const FILTERS = [
  { label: "همه", value: "" },
  { label: "رزرو", value: "رزرو" },
  { label: "انجام‌شده", value: "انجام‌شده" },
  { label: "لغو", value: "لغو" },
  { label: "غایب", value: "غایب" },
];

export function AppointmentsPage() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const result = useApiQuery((s) => recordsApi.appointments({ status, page }, s), [status, page]);

  return (
    <>
      <PageHeader title="نوبت‌ها" subtitle="فهرست نوبت‌های ثبت‌شده در ۱۲ ماه گذشته" />

      <FilterTabs
        options={FILTERS}
        value={status}
        onChange={(v) => {
          setStatus(v);
          setPage(1);
        }}
      />

      <Card className="mt-5" bodyClassName="">
        {result.loading ? (
          <div className="p-5"><CardSkeleton rows={6} /></div>
        ) : result.error ? (
          <div className="p-5"><ErrorState message={result.error} /></div>
        ) : (
          <>
            <Table head={["کد", "بیمار", "پزشک", "تخصص", "زمان", "یونیت", "وضعیت"]}>
              {result.data.rows.map((a) => (
                <Tr key={a.appointment_id}>
                  <Td className="text-ink-400">{num(a.appointment_id)}</Td>
                  <Td bold>{a.patient ?? "—"}</Td>
                  <Td>{a.dentist ?? "—"}</Td>
                  <Td className="text-ink-500">{a.specialty ?? "—"}</Td>
                  <Td>{dateTime(a.scheduled_datetime)}</Td>
                  <Td>{a.chair_number ? num(a.chair_number) : "—"}</Td>
                  <Td><Badge>{a.status}</Badge></Td>
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
