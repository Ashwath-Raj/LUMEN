/**
 * `DataGrid` — the dense list primitive (arch §F, §D primitives). Sortable,
 * keyboard row navigation (↑↓ move, Enter opens, Space peeks), density toggle.
 * Virtualisation above 50 rows is a §G performance budget item added when a
 * a surface first needs it; the API is shaped for it now. The registry uses
 * server-side pagination (≤ page size rows rendered), so virtualisation is not
 * yet required — tracked as debt.
 *
 * Sorting is CONTROLLED when `sort` + `onToggleSort` are provided (server-side
 * multi-sort for the Case Registry): the header shows the sort direction and
 * priority, and clicking a sortable header calls back rather than sorting
 * locally. Without those props the grid is display-only .
 *
 * A row can be marked selected (`selectedId` + `rowKey`) so a surface with a
 * persistent inspector highlights the row whose entity is shown.
 */
import { useState, type KeyboardEvent, type ReactNode } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";

import { cn } from "@/utils/cn";

export interface Column<Row> {
  key: string;
  header: string;
  render: (row: Row) => ReactNode;
  /** Enables click-to-sort on this column's key. */
  sortable?: boolean;
}

export type Density = "dense" | "comfortable";

/** One controlled sort term (field + direction), highest priority first. */
export interface SortTerm {
  field: string;
  direction: "asc" | "desc";
}

interface DataGridProps<Row> {
  columns: Column<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  /** Enter on a focused row. */
  onOpen?: (row: Row) => void;
  /** Space on a focused row — peek in the InspectorPanel (wired in later sessions). */
  onPeek?: (row: Row) => void;
  density?: Density;
  /** Controlled multi-sort state (field → direction), highest priority first. */
  sort?: SortTerm[];
  /** Toggle a column's sort (append/cycle/remove is the caller's policy). */
  onToggleSort?: (field: string) => void;
  /** Highlight the row whose entity is shown in a persistent inspector. */
  selectedId?: string | null;
  /** Accessible caption for the table. */
  caption?: string;
}

export function DataGrid<Row>({
  columns,
  rows,
  rowKey,
  onOpen,
  onPeek,
  density = "dense",
  sort,
  onToggleSort,
  selectedId,
  caption,
}: DataGridProps<Row>) {
  const [focused, setFocused] = useState(0);

  const rowHeight = density === "dense" ? "h-9" : "h-11"; // 36 / 44 px (§F)

  function sortFor(field: string): { dir: "asc" | "desc"; priority: number } | null {
    if (!sort) return null;
    const idx = sort.findIndex((s) => s.field === field);
    return idx === -1 ? null : { dir: sort[idx].direction, priority: idx + 1 };
  }

  function onKeyDown(e: KeyboardEvent, index: number, row: Row) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocused(Math.min(index + 1, rows.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocused(Math.max(index - 1, 0));
    } else if (e.key === "Enter") {
      onOpen?.(row);
    } else if (e.key === " ") {
      e.preventDefault();
      onPeek?.(row);
    }
  }

  return (
    <table className="w-full border-collapse text-dense">
      {caption ? <caption className="sr-only">{caption}</caption> : null}
      <thead>
        <tr className="border-b border-line text-left text-caption uppercase tracking-wide text-ink-muted">
          {columns.map((col) => {
            const active = col.sortable ? sortFor(col.key) : null;
            const canSort = col.sortable && onToggleSort;
            return (
              <th key={col.key} className="px-3 py-2 font-normal" aria-sort={
                active ? (active.dir === "asc" ? "ascending" : "descending") : "none"
              }>
                {canSort ? (
                  <button
                    type="button"
                    onClick={() => onToggleSort!(col.key)}
                    className="inline-flex items-center gap-1 hover:text-ink-primary"
                  >
                    {col.header}
                    {active ? (
                      <span className="inline-flex items-center text-signal">
                        {active.dir === "asc" ? (
                          <ChevronUp size={12} aria-hidden />
                        ) : (
                          <ChevronDown size={12} aria-hidden />
                        )}
                        {sort && sort.length > 1 ? (
                          <span className="text-[10px]">{active.priority}</span>
                        ) : null}
                      </span>
                    ) : null}
                  </button>
                ) : (
                  col.header
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => {
          const id = rowKey(row);
          const selected = selectedId != null && id === selectedId;
          return (
            <tr
              key={id}
              tabIndex={0}
              aria-selected={selected}
              onFocus={() => setFocused(index)}
              onKeyDown={(e) => onKeyDown(e, index, row)}
              onClick={() => onOpen?.(row)}
              className={cn(
                rowHeight,
                "cursor-pointer border-b border-line/60 outline-none",
                "hover:bg-raised focus-visible:bg-raised",
                (focused === index || selected) && "bg-raised",
                selected && "shadow-[inset_2px_0_0_0_var(--signal)]",
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-3 text-ink-primary">
                  {col.render(row)}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
