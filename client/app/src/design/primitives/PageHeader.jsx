/**
 * Standard page header: label-eyebrow + font-display title, with an
 * optional right-aligned slot for status chips, live clocks, or actions.
 * Used across every module page to keep header markup from being
 * re-typed 30 times.
 */
export default function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <header className="flex items-start justify-between gap-4 flex-wrap">
      <div>
        {eyebrow && <p className="label-eyebrow">{eyebrow}</p>}
        <h1 className="font-display text-3xl mt-1">{title}</h1>
        {description && <p className="text-ink-muted text-sm mt-1 max-w-xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </header>
  );
}
