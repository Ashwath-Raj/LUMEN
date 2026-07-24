import Badge from '@/components/common/Badge.jsx';

/**
 * "Sector Intel" panel — a short AI-generated analytical note with
 * classification tags (e.g. NARCOTICS, ELEVATED RISK).
 */
export default function SectorIntelCard({ headline, body, tags = [] }) {
  return (
    <div className="panel p-4">
      <h3 className="font-display text-lg mb-2">Sector Intel</h3>
      <p className="text-sm text-ink-primary">{headline}</p>
      <p className="text-sm text-ink-muted mt-2 leading-relaxed">{body}</p>
      <div className="flex gap-2 mt-3 flex-wrap">
        {tags.map((tag) => (
          <Badge key={tag} tone="warning">
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  );
}
