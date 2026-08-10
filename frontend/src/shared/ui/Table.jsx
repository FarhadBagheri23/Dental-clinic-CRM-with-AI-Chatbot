export function Table({ head, children, empty = "رکوردی یافت نشد." }) {
  const rows = Array.isArray(children) ? children.flat().filter(Boolean) : [children];

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] text-right text-sm">
        <thead className="border-b border-ink-200 bg-ink-50/70 text-xs text-ink-500">
          <tr>
            {head.map((h) => (
              <th key={h} scope="col" className="whitespace-nowrap px-4 py-3 font-bold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-100">
          {rows.length ? (
            children
          ) : (
            <tr>
              <td colSpan={head.length} className="px-4 py-16 text-center text-ink-400">
                {empty}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = "", bold = false }) {
  return (
    <td
      className={`whitespace-nowrap px-4 py-3 ${
        bold ? "font-bold text-ink-800" : "text-ink-600"
      } ${className}`}
    >
      {children}
    </td>
  );
}

export function Tr({ children }) {
  return <tr className="transition-colors hover:bg-ink-50/60">{children}</tr>;
}
