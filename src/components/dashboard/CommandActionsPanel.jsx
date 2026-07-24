import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

/**
 * "Command Actions" panel — quick links into the module each action leads
 * to (Initiate Investigation -> Investigation, Deploy Resources ->
 * Operations, Generate Briefing -> Analytics).
 */
export default function CommandActionsPanel({ actions = [] }) {
  return (
    <div className="panel p-4">
      <h3 className="font-display text-lg mb-3">Command Actions</h3>
      <ul className="flex flex-col divide-y divide-border-subtle">
        {actions.map((action) => (
          <li key={action.id}>
            <Link
              to={action.to}
              className="flex items-center justify-between py-2.5 text-sm text-ink-secondary hover:text-accent-gold transition-colors"
            >
              {action.label}
              <ChevronRight size={15} />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
