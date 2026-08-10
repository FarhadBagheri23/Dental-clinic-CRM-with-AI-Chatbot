import { useId, useState } from "react";

/**
 * Labelled input. `ltr` forces left-to-right for English-only credentials —
 * without it the caret starts on the right inside this RTL page and typed
 * ASCII appears to jump around.
 */
export function TextField({
  label,
  error,
  hint,
  ltr = false,
  type = "text",
  revealable = false,
  className = "",
  ...props
}) {
  const id = useId();
  const [revealed, setRevealed] = useState(false);
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  const inputType = revealable && revealed ? "text" : type;

  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 block text-sm font-bold text-ink-700">
        {label}
      </label>

      <div className="relative">
        <input
          id={id}
          type={inputType}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`h-12 w-full rounded-xl border bg-white px-4 text-[15px]
            text-ink-900 transition-colors duration-150
            placeholder:text-ink-400
            focus:outline-none focus:ring-2 focus:ring-offset-1
            ${revealable ? "ltr:pr-12 rtl:pl-12" : ""}
            ${ltr ? "field-ltr" : ""}
            ${
              error
                ? "border-rose-300 focus:border-rose-400 focus:ring-rose-200"
                : "border-ink-200 hover:border-ink-300 focus:border-brand-500 focus:ring-brand-200"
            }`}
          {...props}
        />

        {revealable && (
          <button
            type="button"
            tabIndex={-1}
            onClick={() => setRevealed((v) => !v)}
            aria-label={revealed ? "پنهان کردن رمز عبور" : "نمایش رمز عبور"}
            className="absolute inset-y-0 grid w-12 place-items-center text-ink-400
              transition-colors hover:text-ink-700 ltr:right-0 rtl:left-0"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" viewBox="0 0 24 24" aria-hidden="true">
              {revealed ? (
                <path strokeLinecap="round" d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.4 5.2A9.5 9.5 0 0112 5c5 0 9 4.5 9 7a11 11 0 01-2.4 3.5M6.3 6.9C3.9 8.4 3 10.7 3 12c0 2.5 4 7 9 7 1.4 0 2.7-.35 3.8-.9" />
              ) : (
                <>
                  <path strokeLinecap="round" d="M3 12c0-2.5 4-7 9-7s9 4.5 9 7-4 7-9 7-9-4.5-9-7z" />
                  <circle cx="12" cy="12" r="2.6" />
                </>
              )}
            </svg>
          </button>
        )}
      </div>

      {error ? (
        <p id={`${id}-error`} className="mt-2 text-xs leading-6 text-rose-700">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-2 text-xs leading-6 text-ink-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
