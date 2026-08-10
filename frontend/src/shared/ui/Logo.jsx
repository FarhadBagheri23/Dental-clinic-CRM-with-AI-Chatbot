export function ToothMark({ className = "h-7 w-7" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C9.6 2 8.6 3 7 3c-1.3 0-2-.5-3-.5C2.5 2.5 2 4 2 6.2c0 2.6.9 4 1.6 5.6.5 1.2.8 2.5 1 3.9.3 2 .5 4 1 5.4.3.8.8 1.1 1.4 1 .7-.1 1-.8 1.2-1.9.2-1.1.4-2.6.7-3.9.3-1.4.9-2.3 2.1-2.3s1.8.9 2.1 2.3c.3 1.3.5 2.8.7 3.9.2 1.1.5 1.8 1.2 1.9.6.1 1.1-.2 1.4-1 .5-1.4.7-3.4 1-5.4.2-1.4.5-2.7 1-3.9.7-1.6 1.6-3 1.6-5.6C22 4 21.5 2.5 20 2.5c-1 0-1.7.5-3 .5-1.6 0-2.6-1-5-1z" />
    </svg>
  );
}

export function LogoLockup({ className = "", tone = "dark" }) {
  const ring = tone === "light" ? "bg-white/10 text-white" : "bg-brand-700 text-white";
  const text = tone === "light" ? "text-white" : "text-ink-900";
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <span className={`grid h-11 w-11 place-items-center rounded-2xl shadow-card ${ring}`}>
        <ToothMark className="h-6 w-6" />
      </span>
      <span className={`text-[15px] font-black leading-tight ${text}`}>
        کلینیک باقری طاهری
        <span className={`block text-xs font-medium ${tone === "light" ? "text-brand-100/80" : "text-ink-500"}`}>
          پنل مدیریت
        </span>
      </span>
    </div>
  );
}
