import { useEffect, useRef, useState } from "react";

import {
  WEEKDAYS,
  addDays,
  fromISODate,
  jalaliDate,
  jalaliDay,
  jalaliMonthDays,
  jalaliTitle,
  leadingBlanks,
  sameDay,
  startOfJalaliMonth,
  toISODate,
} from "@/shared/lib/jalali";

function Chevron({ dir }) {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={dir === "right" ? "M9 18l6-6-6-6" : "M15 18l-6-6 6-6"} />
    </svg>
  );
}

function NavButton({ label, onClick, dir }) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="rounded-lg p-1.5 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
    >
      <Chevron dir={dir} />
    </button>
  );
}

/** Shamsi date field. The value in and out is a Gregorian `YYYY-MM-DD` so the
 *  API contract is unchanged — only what the user reads and clicks is Jalali. */
export function JalaliDateInput({ label, value, onChange, min, max, placeholder = "انتخاب تاریخ" }) {
  const [open, setOpen] = useState(false);
  const selected = fromISODate(value);
  const [cursor, setCursor] = useState(() => selected ?? new Date());
  const root = useRef(null);

  // A picker that stays open while the user clicks elsewhere feels stuck, and
  // Escape is the expected way out of any popover.
  useEffect(() => {
    if (!open) return;
    const close = (e) => {
      if (e.type === "keydown" ? e.key === "Escape" : !root.current?.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  const openPicker = () => {
    // Reopening on the month the user last chose beats always landing on today.
    setCursor(selected ?? fromISODate(max) ?? new Date());
    setOpen((o) => !o);
  };

  const days = jalaliMonthDays(cursor);
  const blanks = leadingBlanks(days[0]);
  const today = new Date();
  const outOfRange = (d) => {
    const iso = toISODate(d);
    return (min && iso < min) || (max && iso > max);
  };

  const pick = (d) => {
    onChange(toISODate(d));
    setOpen(false);
  };

  return (
    <div className="relative flex min-w-0 flex-col gap-1.5" ref={root}>
      <span className="text-[11px] font-bold text-ink-500">{label}</span>

      <button
        type="button"
        onClick={openPicker}
        aria-haspopup="dialog"
        aria-expanded={open}
        // The visible label is a sibling span, not a <label for>, so the
        // button would otherwise reach a screen reader unnamed.
        aria-label={label}
        className={`flex h-10 min-w-0 items-center justify-between gap-2 rounded-lg border bg-white
          px-3 text-sm transition-colors hover:border-ink-300
          focus:outline-none focus:ring-2 focus:ring-brand-200
          ${open ? "border-brand-500 ring-2 ring-brand-200" : "border-ink-200"}
          ${selected ? "text-ink-800" : "text-ink-400"}`}
      >
        <span className="truncate">{selected ? jalaliDate(selected) : placeholder}</span>
        <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-ink-400" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M3 10h18M8 3v4M16 3v4" />
        </svg>
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={label}
          className="absolute top-full z-40 mt-2 w-[17.5rem] animate-fade-up rounded-2xl
            border border-ink-200 bg-white p-3 shadow-lift"
        >
          {/* The panel is RTL, so the first child sits on the right — which is
              where "previous" belongs when reading right-to-left. */}
          <div className="flex items-center justify-between">
            <NavButton
              label="ماه قبل"
              dir="right"
              onClick={() => setCursor(startOfJalaliMonth(addDays(days[0], -1)))}
            />
            <span className="text-sm font-bold text-ink-800">{jalaliTitle(cursor)}</span>
            <NavButton label="ماه بعد" dir="left" onClick={() => setCursor(addDays(days.at(-1), 1))} />
          </div>

          <div className="mt-3 grid grid-cols-7 gap-1 text-center">
            {WEEKDAYS.map((d, i) => (
              <span key={d} className={`py-1 text-[11px] font-bold ${i === 6 ? "text-rose-400" : "text-ink-400"}`}>
                {d}
              </span>
            ))}

            {Array.from({ length: blanks }, (_, i) => <span key={`b${i}`} />)}

            {days.map((d) => {
              const disabled = outOfRange(d);
              const isSelected = sameDay(d, selected);
              return (
                <button
                  key={toISODate(d)}
                  type="button"
                  disabled={disabled}
                  onClick={() => pick(d)}
                  aria-current={isSelected ? "date" : undefined}
                  className={`h-8 rounded-lg text-[13px] tabular-nums transition-colors
                    ${isSelected
                      ? "bg-brand-600 font-bold text-white"
                      : disabled
                        ? "cursor-not-allowed text-ink-300"
                        : sameDay(d, today)
                          ? "bg-accent-50 font-bold text-accent-700 hover:bg-accent-100"
                          : "text-ink-700 hover:bg-brand-50 hover:text-brand-700"}`}
                >
                  {jalaliDay(d)}
                </button>
              );
            })}
          </div>

          <div className="mt-2 flex items-center justify-between border-t border-ink-100 pt-2">
            <button
              type="button"
              onClick={() => (outOfRange(today) ? setCursor(today) : pick(today))}
              className="rounded-lg px-2 py-1 text-xs font-bold text-brand-700 transition-colors hover:bg-brand-50"
            >
              امروز
            </button>
            <button
              type="button"
              onClick={() => { onChange(""); setOpen(false); }}
              className="rounded-lg px-2 py-1 text-xs font-bold text-ink-500 transition-colors hover:bg-ink-100"
            >
              پاک کردن
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
