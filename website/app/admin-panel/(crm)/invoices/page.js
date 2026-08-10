import { listInvoices } from "../../../../lib/queries";
import { Badge, FilterTabs, PageHead, Pagination, Table, fa, faDate, toman } from "../../ui";

const FILTERS = [
  { label: "همه", value: "" },
  { label: "پرداخت‌شده", value: "پرداخت‌شده" },
  { label: "پرداخت بخشی", value: "بخشی" },
  { label: "معوق", value: "معوق" },
];

export default async function InvoicesPage({ searchParams }) {
  const status = searchParams?.status ?? "";
  const page = Number(searchParams?.page ?? 1) || 1;
  const { rows, meta } = await listInvoices({ status, page });

  const pageBalance = rows.reduce((a, r) => a + Math.max(r.balance, 0), 0);

  return (
    <>
      <PageHead title="فاکتورها" sub={`${fa(meta.total)} فاکتور${status ? ` با وضعیت «${status}»` : ""}`}>
        {pageBalance > 0 ? (
          <span className="rounded-lg bg-rose-50 px-4 py-2 text-sm font-bold text-rose-700">
            مانده این صفحه: {toman(pageBalance)}
          </span>
        ) : null}
      </PageHead>
      <FilterTabs options={FILTERS} active={status} basePath="/admin-panel/invoices" />

      <Table head={["کد", "بیمار", "تاریخ صدور", "مبلغ کل", "سهم بیمه", "سهم بیمار", "پرداختی", "مانده", "وضعیت"]}>
        {rows.map((i) => (
          <tr key={i.invoice_id} className="hover:bg-slate-50">
            <td className="px-4 py-3 font-mono text-xs text-slate-400">
              INV-{String(i.invoice_id).padStart(5, "0")}
            </td>
            <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{i.patient}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-500">{faDate(i.issue_date)}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-700">{toman(i.total_amount)}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-500">{toman(i.insurance_covered)}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-700">{toman(i.patient_share)}</td>
            <td className="whitespace-nowrap px-4 py-3 text-emerald-700">{toman(i.paid)}</td>
            <td
              className={`whitespace-nowrap px-4 py-3 font-bold ${
                i.balance > 0 ? "text-rose-700" : "text-slate-400"
              }`}
            >
              {i.balance > 0 ? toman(i.balance) : "—"}
            </td>
            <td className="px-4 py-3">
              <Badge>{i.status}</Badge>
            </td>
          </tr>
        ))}
      </Table>

      <Pagination meta={meta} basePath="/admin-panel/invoices" params={status ? { status } : {}} />
    </>
  );
}
