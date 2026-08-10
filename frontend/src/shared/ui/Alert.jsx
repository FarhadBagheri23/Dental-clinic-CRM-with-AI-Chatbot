const TONES = {
  error: "border-rose-200 bg-rose-50 text-rose-800",
  info: "border-brand-200 bg-brand-50 text-brand-800",
};

export function Alert({ tone = "error", children, className = "" }) {
  if (!children) return null;
  return (
    <div
      // assertive: a failed login must interrupt a screen reader, otherwise
      // the user retypes into a form that already rejected them.
      role="alert"
      aria-live={tone === "error" ? "assertive" : "polite"}
      className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-sm
        leading-7 ${TONES[tone]} ${className}`}
    >
      <svg className="mt-1.5 h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM9 5a1 1 0 012 0v5a1 1 0 11-2 0V5zm1 9.5a1.25 1.25 0 100-2.5 1.25 1.25 0 000 2.5z"
          clipRule="evenodd"
        />
      </svg>
      <span>{children}</span>
    </div>
  );
}
