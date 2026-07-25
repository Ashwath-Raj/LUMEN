/**
 * `PlaceholderPage` — the TODO placeholder every feature route renders until its
 * session builds it out (arch §H roadmap; Session 0 leaves pages as TODO
 * placeholders). It names the surface, its spec/arch reference, and the session
 * that implements it — so the routing is real and navigable now, and each
 * feature session replaces exactly one placeholder.
 *
 * This is NOT a feature: it renders no product data, wires no endpoint. It
 * exists only to make the IA (arch §C) real and the build green before
 * Sessions 1–6.
 */
import { Panel } from "@/design/primitives";

interface PlaceholderPageProps {
  title: string;
  /** Arch/spec reference, e.g. "arch §E.4 · spec §30.4". */
  reference: string;
  /** The roadmap session that implements this surface (arch §H). */
  session: string;
  summary: string;
}

export function PlaceholderPage({
  title,
  reference,
  session,
  summary,
}: PlaceholderPageProps) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <p className="text-caption uppercase tracking-wide text-ink-faint">
        {reference}
      </p>
      <h1 className="mt-1 font-display text-page-title text-ink-primary">
        {title}
      </h1>
      <Panel className="mt-6 px-4 py-4">
        <p className="text-body text-ink-muted">{summary}</p>
        <p className="mt-3 text-caption text-ink-faint">
          TODO — implemented in {session}. Session 0 established the route,
          layout, and data-access scaffold only; no feature is built yet.
        </p>
      </Panel>
    </div>
  );
}
