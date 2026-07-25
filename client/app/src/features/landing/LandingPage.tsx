/**
 * Mission Briefing — public landing `/` (arch §C.1). "Government software
 * introducing itself." One centred column.
 *
 * This is the working minimum that makes the entry point real (masthead +
 * "Enter Command Center" → /login), not a dead placeholder. The full §C.1
 * content (problem SVG flow, how-it-works, demo roadmap, architecture strip) is
 * Session-6 polish; kept intentionally lean here so the foundation functions.
 */
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6">
      <div className="flex flex-col gap-2">
        <h1 className="font-display text-page-title text-ink-primary">LUMEN</h1>
        <p className="text-body text-ink-muted">
          Crime Intelligence Platform · Karnataka State Police
        </p>
      </div>

      <p className="max-w-prose text-body text-ink-muted">
        A connected chain of investigation workspaces: unified records, entity
        resolution, a knowledge graph, and explainable AI in support of officer
        decisions — never in place of them.
      </p>

      <div>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 rounded border border-signal/40 bg-signal/15 px-4 py-2 text-body text-signal hover:bg-signal/25"
        >
          Enter Command Center
          <ArrowRight size={16} aria-hidden />
        </Link>
      </div>

      <p className="text-caption text-ink-faint">
        AI-assisted, officer-decided. Access is scoped and audited.
      </p>
    </main>
  );
}
