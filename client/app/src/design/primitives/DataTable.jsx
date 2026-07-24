/**
 * Generic table for the many roster/log/list screens (Active Personnel
 * Roster, Forensic Audit Log, Coordination Log, Evidence by Locker...).
 *
 * columns: [{ key, header, render?(row) }]
 * rows: array of data objects
 * onRowClick?(row): when provided, rows become clickable (e.g. navigate
 * into a case) with hover/cursor affordance.
 */
export default function DataTable({ columns, rows, getRowKey = (row, i) => row.id ?? i, onRowClick }) {
  return (
    <table className="w-full text-sm text-left">
      <thead>
        <tr className="border-b border-border-subtle">
          {columns.map((col) => (
            <th key={col.key} className="label-eyebrow font-normal py-2 pr-4">
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr
            key={getRowKey(row, i)}
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            className={`border-b border-border-subtle/60 ${
              onRowClick ? 'cursor-pointer hover:bg-surface-2' : ''
            }`}
          >
            {columns.map((col) => (
              <td key={col.key} className="py-2 pr-4 text-ink-secondary">
                {col.render ? col.render(row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
