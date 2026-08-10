import { num } from "@/shared/lib/format";

// MongoDB $dayOfWeek is 1=Sunday. The Persian week starts Saturday, so the
// display order is Sat(7), Sun(1) … Fri(6).
const DAYS = [
  { dow: 7, label: "شنبه" },
  { dow: 1, label: "یکشنبه" },
  { dow: 2, label: "دوشنبه" },
  { dow: 3, label: "سه‌شنبه" },
  { dow: 4, label: "چهارشنبه" },
  { dow: 5, label: "پنج‌شنبه" },
  { dow: 6, label: "جمعه" },
];

export function Heatmap({ data, hourFrom = 8, hourTo = 20 }) {
  const hours = Array.from({ length: hourTo - hourFrom }, (_, i) => hourFrom + i);
  const lookup = new Map(data.map((d) => [`${d.dow}-${d.hour}`, d.n]));
  const max = Math.max(...data.map((d) => d.n), 1);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[34rem] border-separate border-spacing-1">
        <thead>
          <tr>
            <th className="w-20" />
            {hours.map((h) => (
              <th key={h} scope="col" className="pb-1 text-center text-[10px] font-medium text-ink-400 tabular-nums">
                {num(h)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DAYS.map((d) => (
            <tr key={d.dow}>
              <th scope="row" className="pl-2 text-right text-[11px] font-medium text-ink-600">
                {d.label}
              </th>
              {hours.map((h) => {
                const n = lookup.get(`${d.dow}-${h}`) ?? 0;
                // Opacity encodes density; a zero cell stays visibly empty
                // rather than fading into the lightest occupied shade.
                const t = n === 0 ? 0 : 0.12 + (n / max) * 0.88;
                return (
                  <td
                    key={h}
                    title={`${d.label} ساعت ${num(h)} — ${num(n)} نوبت`}
                    className="h-7 rounded-md text-center text-[10px] tabular-nums"
                    style={{
                      background: n === 0 ? "#eef0f0" : `rgba(31,117,123,${t})`,
                      color: t > 0.55 ? "white" : "#5f6a6b",
                    }}
                  >
                    {n || ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-3 flex items-center justify-end gap-2 text-[11px] text-ink-500">
        <span>کمتر</span>
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <span key={t} className="h-3 w-6 rounded"
            style={{ background: t === 0 ? "#eef0f0" : `rgba(31,117,123,${0.12 + t * 0.88})` }} />
        ))}
        <span>بیشتر</span>
      </div>
    </div>
  );
}
