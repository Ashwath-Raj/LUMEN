import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-surface-0">
      <p className="label-eyebrow">Error 404</p>
      <h1 className="font-display text-3xl">Record not found</h1>
      <Link to="/dashboard" className="text-accent-gold text-sm">
        Return to Command Center
      </Link>
    </div>
  );
}
