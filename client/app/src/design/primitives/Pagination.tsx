/**
 * `Pagination` — the shared §29.2 offset/limit pager (Case Registry, Activity
 * log, any paged list). Shows the current range against the total and
 * prev/next controls; disabled at the ends. Kept a primitive so no list
 * re-implements paging math (no duplicated logic).
 */
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (offset: number) => void;
}

export function Pagination({
  total,
  limit,
  offset,
  onOffsetChange,
}: PaginationProps) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  const canPrev = offset > 0;
  const canNext = end < total;

  return (
    <div className="flex items-center justify-between border-t border-line px-3 py-2 text-caption text-ink-muted">
      <span>
        {start.toLocaleString()}–{end.toLocaleString()} of{" "}
        {total.toLocaleString()}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          disabled={!canPrev}
          aria-label="Previous page"
          className="rounded p-1 hover:bg-raised disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft size={16} />
        </button>
        <button
          type="button"
          onClick={() => onOffsetChange(offset + limit)}
          disabled={!canNext}
          aria-label="Next page"
          className="rounded p-1 hover:bg-raised disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
