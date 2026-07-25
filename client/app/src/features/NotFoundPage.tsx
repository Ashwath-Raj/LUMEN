/**
 * 404 — a real route so an unknown path never white-screens (arch §G error
 * handling ethos). Uses the NOT_FOUND ErrorState rendering language (arch §E).
 */
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md px-6 py-16 text-center">
      <h1 className="font-display text-page-title text-ink-primary">
        No record for this reference
      </h1>
      <p className="mt-2 text-body text-ink-muted">
        The page you requested does not exist.
      </p>
      <Link to="/command" className="mt-4 inline-block text-body text-signal hover:underline">
        Return to Command Center
      </Link>
    </div>
  );
}
