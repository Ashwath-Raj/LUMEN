import EmptyState from '@/components/common/EmptyState.jsx';
import { Share2 } from 'lucide-react';

const KIND_COLOR = {
  cluster: 'fill-accent-gold stroke-accent-gold',
  category: 'fill-status-info stroke-status-info',
  flag: 'fill-status-critical stroke-status-critical',
  default: 'fill-ink-secondary stroke-ink-secondary',
};

/**
 * Renders the entity-relationship graph seen in "Linked Network" (FIR
 * Intelligence), the Investigation "Network" tab, and Analytics'
 * "Behavioral Pattern Correlation". Simple radial layout — nodes placed
 * evenly around a circle, edges drawn between them — which is enough to
 * communicate relationship structure without a heavyweight graph library.
 *
 * nodes: [{ id, label, kind }]
 * edges: [{ source, target, label? }]
 */
export default function NetworkGraph({ nodes = [], edges = [] }) {
  if (nodes.length === 0) {
    return (
      <EmptyState
        icon={Share2}
        title="No linked entities"
        message="Relationships will appear here once entities are connected."
      />
    );
  }

  const size = 100;
  const center = size / 2;
  const radius = size * 0.36;

  const positions = Object.fromEntries(
    nodes.map((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      return [
        node.id,
        { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) },
      ];
    })
  );

  return (
    <div className="w-full h-64">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
        {edges.map((edge, i) => {
          const from = positions[edge.source];
          const to = positions[edge.target];
          if (!from || !to) return null;
          return (
            <line
              key={i}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              className="stroke-border-strong"
              strokeWidth={0.4}
              strokeDasharray="1.5 1"
            />
          );
        })}

        {nodes.map((node) => {
          const pos = positions[node.id];
          const colorClass = KIND_COLOR[node.kind] ?? KIND_COLOR.default;
          return (
            <g key={node.id}>
              <circle cx={pos.x} cy={pos.y} r={2.6} className={colorClass} strokeWidth={0.5} />
              <text
                x={pos.x}
                y={pos.y - 4}
                textAnchor="middle"
                className="fill-ink-secondary"
                style={{ fontSize: '3px', fontFamily: 'IBM Plex Mono, monospace' }}
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
