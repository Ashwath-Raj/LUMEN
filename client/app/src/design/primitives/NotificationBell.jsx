import { Bell } from 'lucide-react';

/**
 * Bell icon + unread dot in the top nav. `count` will be wired to
 * notificationService once the backend endpoint exists.
 */
export default function NotificationBell({ count = 0 }) {
  return (
    <button
      type="button"
      aria-label={count > 0 ? `${count} unread notifications` : 'Notifications'}
      className="relative text-ink-secondary hover:text-ink-primary"
    >
      <Bell size={17} strokeWidth={1.75} />
      {count > 0 && (
        <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-status-critical" />
      )}
    </button>
  );
}
