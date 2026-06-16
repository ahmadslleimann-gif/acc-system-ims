interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
}

export default function DataTable<T extends { id: number | string }>({
  columns,
  rows,
  loading,
}: {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
}) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[640px]">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((c) => (
              <th key={c.key} className="table-th">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td className="table-td text-slate-400" colSpan={columns.length}>
                Loading…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td className="table-td text-slate-400" colSpan={columns.length}>
                No records.
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50">
                {columns.map((c) => (
                  <td key={c.key} className="table-td">
                    {c.render ? c.render(row) : (row as Record<string, unknown>)[c.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
