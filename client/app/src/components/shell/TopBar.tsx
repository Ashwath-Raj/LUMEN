/**
 * `TopBar` — shell top bar (arch §D shell): wordmark → /briefing, ⌘K global
 * search, scope indicator, `DegradationPill`, role badge, notification tray.
 *
 * Session 1 completes the bar: search and tray are now real interactions
 * (`GlobalSearch`, `NotificationTray`) with their resolution/live-data wired in
 * later sessions. Scope and role read from the session (§20 server scoping);
 * they stay neutral placeholders until the login session populates them. No
 * feature navigation beyond the §C set is added here.
 */
import { Link } from "react-router-dom";

import { useSession } from "@/providers/sessionContext";
import { Badge } from "@/design/primitives";
import { DegradationPill } from "./DegradationPill";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationTray } from "./NotificationTray";

/** §20.1 role → display label. */
const ROLE_LABEL: Record<string, string> = {
  state_analyst: "State Analyst",
  district_sp: "District SP",
  investigating_officer: "Investigating Officer",
  station_officer: "Station Officer",
  auditor: "Auditor",
};

export function TopBar() {
  const { scopeLabel, operator, role } = useSession();

  return (
    <header
      className="flex items-center gap-4 border-b border-line bg-panel px-4 lg:px-6"
      style={{ height: "56px" }}
    >
      <Link
        to="/briefing"
        className="font-display text-panel-title text-ink-primary"
      >
        LUMEN
      </Link>

      <GlobalSearch />

      {/* Scope indicator (§D shell) — hidden on narrow widths to protect the
          search field; the role badge carries the essential context. */}
      <span className="hidden text-caption text-ink-muted lg:inline">
        {scopeLabel ?? "Scope pending"}
      </span>

      <DegradationPill />

      {role ? (
        <Badge tone="var(--signal)" title="Your role (§20.1)">
          {ROLE_LABEL[role] ?? role}
        </Badge>
      ) : null}

      {operator ? (
        <span className="hidden text-caption text-ink-muted md:inline">
          {operator.name}
        </span>
      ) : null}

      <NotificationTray />
    </header>
  );
}
