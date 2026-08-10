import { listAppointments } from "../../../../lib/queries";
import { Badge, FilterTabs, PageHead, Pagination, Table, fa, faDateTime } from "../../ui";

const FILTERS = [
  { label: "همه", value: "" },
  { label: "رزرو", value: "رزرو" },
  { label: "انجام‌شده", value: "انجام‌شده" },
  { label: "لغو", value: "لغو" },
  { label: "غایب", value: "غایب" },
];

export default async function AppointmentsPage({ searchParams }) {
  const status = searchParams?.status ?? "";
  const page = Number(searchParams?.page ?? 1) || 1;
  const { rows, meta } = await listAppointments({ status, page });

  return (
    <>
      <PageHead title="نوبت‌ها" sub={`${fa(meta.total)} نوبت${status ? ` با وضعیت «${status}»` : ""}`} />
      <FilterTabs options={FILTERS} active={status} basePath="/admin-panel/appointments" />

      <Table head={["کد", "زمان", "بیمار", "پزشک", "تخصص", "یونیت", "وضعیت"]}>
        {rows.map((a) => (
          <tr key={a.appointment_id} className="hover:bg-slate-50">
            <td className="px-4 py-3 font-mono text-xs text-slate-400">
              APT-{String(a.appointment_id).padStart(5, "0")}
            </td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-700">{faDateTime(a.scheduled_datetime)}</td>
            <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-800">{a.patient}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-600">{a.dentist}</td>
            <td className="whitespace-nowrap px-4 py-3 text-slate-500">{a.specialty}</td>
            <td className="px-4 py-3 text-slate-500">{fa(a.chair_number)}</td>
            <td className="px-4 py-3">
              <Badge>{a.status}</Badge>
            </td>
          </tr>
        ))}
      </Table>

      <Pagination
        meta={meta}
        basePath="/admin-panel/appointments"
        params={status ? { status } : {}}
      />
    </>
  );
}
