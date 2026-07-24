/**
 * Pulsing skeleton block(s), used inside panels while useAsyncData's
 * isLoading is true. `rows` renders multiple lines (e.g. for a table).
 */
export default function Skeleton({ className = 'h-4 w-full', rows = 1 }) {
  if (rows === 1) {
    return <div className={`animate-pulse rounded-sm bg-surface-2 ${className}`} />;
  }
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`animate-pulse rounded-sm bg-surface-2 ${className}`} />
      ))}
    </div>
  );
}
