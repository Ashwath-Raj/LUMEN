/**
 * "Crime Trend Analysis" bar chart on the Command Center. Hand-rolled SVG
 * rather than pulling in a charting library — the visual (flat bars, gold
 * accent on the peak day, mono axis labels) is simple enough that a
 * dependency isn't justified, and it keeps bundle size down.
 *
 * data: [{ label, value }]
 */
export default function CrimeTrendChart({ data = [] }) {
  if (data.length === 0) return null;

  const max = Math.max(...data.map((d) => d.value));
  const peakIndex = data.findIndex((d) => d.value === max);

  const width = 100;
  const height = 100;
  const barWidth = width / data.length;

  return (
    <div className="h-56">
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="w-full h-44">
        {data.map((d, i) => {
          const barHeight = (d.value / max) * (height - 8);
          const x = i * barWidth + barWidth * 0.18;
          const w = barWidth * 0.64;
          const y = height - barHeight;
          const isPeak = i === peakIndex;
          return (
            <rect
              key={d.label}
              x={x}
              y={y}
              width={w}
              height={barHeight}
              rx={1}
              className={isPeak ? 'fill-accent-gold' : 'fill-surface-3'}
            />
          );
        })}
      </svg>
      <div className="flex justify-between mt-2">
        {data.map((d) => (
          <span key={d.label} className="font-mono text-[10px] text-ink-muted flex-1 text-center">
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
}
