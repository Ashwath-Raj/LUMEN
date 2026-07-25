/**
 * `CounterfactualsNote` (part of D1) — the §8 `counterfactuals`: "what would have
 * to change for this conclusion to change". Rendered as plain statements; empty
 * is legitimate (unlike limitations), so an empty list renders nothing.
 */
interface CounterfactualsNoteProps {
  counterfactuals: string[];
}

export function CounterfactualsNote({
  counterfactuals,
}: CounterfactualsNoteProps) {
  const items = counterfactuals.filter((s) => s.trim());
  if (items.length === 0) return null;
  return (
    <section aria-label="Counterfactuals" className="flex flex-col gap-1">
      <h4 className="text-caption uppercase tracking-wide text-ink-muted">
        What would change this
      </h4>
      <ul className="list-disc pl-4 text-caption text-ink-muted">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
