import { useState } from "react";

import { PageHeader } from "@/app/layouts/PanelLayout";
import { recordsApi } from "@/features/dashboard/api/dashboardApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { date, num, tomanShort } from "@/shared/lib/format";
import { Badge } from "@/shared/ui/Badge";
import { Card } from "@/shared/ui/Card";
import { CardSkeleton, ErrorState, FilterTabs, Pagination } from "@/shared/ui/Feedback";
import { Table, Td, Tr } from "@/shared/ui/Table";

const FILTERS = [
  { label: "همه", value: "" },
  { label: "پرداخت‌شده", value: "پرداخت‌شده" },
  { label: "بخشی", value: "بخشی" },
  { label: "معوق", value: "معوق" },
];

export function InvoicesPage() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const result = useApiQuery((s) => recordsApi.invoices({ status, page }, s), [status, page]);

  return (
    <>
      <PageHeader title="فاکتورها" subtitle="صورتحساب‌ها، سهم بیمه و مانده بدهی بیماران" />

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
            <Table head={["کد", "بیمار", "تاریخ", "مبلغ کل", "سهم بیمه", "سهم بیمار", "پرداختی", "مانده", "وضعیت"]}>
              {result.data.rows.map((inv) => (
                <Tr key={inv.invoice_id}>
                  <Td className="text-ink-400">{num(inv.invoice_id)}</Td>
                  <Td bold>{inv.patient ?? "—"}</Td>
                  <Td>{date(inv.issue_date)}</Td>
                  <Td bold>{tomanShort(inv.total_amount)}</Td>
                  <Td className="text-ink-500">{tomanShort(inv.insurance_covered)}</Td>
                  <Td>{tomanShort(inv.patient_share)}</Td>
                  <Td className="text-emerald-700">{tomanShort(inv.paid)}</Td>
                  <Td className={inv.balance > 0 ? "font-bold text-rose-700" : "text-ink-400"}>
                    {tomanShort(inv.balance)}
                  </Td>
                  <Td><Badge>{inv.status}</Badge></Td>
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
