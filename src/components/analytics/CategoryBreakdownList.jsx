/**
 * "Category Analysis" panel — ranked list of crime categories with count
 * and share-of-total, e.g. "Property Crimes / 812 / 38%".
 */
export default function CategoryBreakdownList({ categories = [] }) {
  return (
    <ul className="flex flex-col divide-y divide-border-subtle">
      {categories.map((cat) => (
        <li key={cat.id} className="flex items-center justify-between py-2 text-sm">
          <span className="text-ink-secondary">{cat.label}</span>
          <span className="flex items-center gap-3">
            <span className="font-mono text-xs text-ink-muted">{cat.count}</span>
            <span className="font-mono text-xs text-accent-gold w-10 text-right">{cat.share}%</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
