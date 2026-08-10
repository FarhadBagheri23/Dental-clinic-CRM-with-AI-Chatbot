const VARIANTS = {
  primary:
    "bg-brand-700 text-white shadow-card hover:bg-brand-800 active:bg-brand-900 disabled:bg-ink-300 disabled:shadow-none",
  ghost: "text-ink-600 hover:bg-ink-100 hover:text-ink-900",
};

export function Button({
  variant = "primary",
  loading = false,
  disabled = false,
  className = "",
  children,
  ...props
}) {
  return (
    <button
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`inline-flex h-12 w-full items-center justify-center gap-2.5 rounded-xl
        px-5 text-sm font-bold transition-colors duration-150
        disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
        />
      )}
      {children}
    </button>
  );
}
