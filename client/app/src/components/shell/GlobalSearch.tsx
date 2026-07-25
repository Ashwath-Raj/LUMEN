/**
 * `GlobalSearch` — the ⌘K command palette (arch §D shell). Resolves, per the
 * specification: a CrimeNo → its case workspace, names → person / officer
 * results, districts / stations → the map. "Backed by `GET /cases?q=` +
 * semantic search" — here the live `/investigation/cases?q=` (CrimeNo and
 * brief-facts full text), `/persons` (resolved identities), and the authentic
 * district/station reference set. Officers are surfaced from the case rows that
 * name them (there is no officer registry endpoint in the OpenAPI).
 *
 * Interaction: ⌘K/Ctrl-K opens from anywhere, ↑/↓ move, Enter opens, Esc
 * closes; results are grouped by entity type with the fixed §F glyphs. Every
 * result navigates — the palette never shows a dead row.
 */
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2 } from "lucide-react";

import { useCases, usePersons } from "@/api";
import { useKarnatakaBoundaries } from "@/features/geo/useKarnatakaBoundaries";
import { Panel } from "@/design/primitives";
import { ENTITY_GLYPH } from "@/design/tokens";
import { cn } from "@/utils/cn";

interface Hit {
  id: string;
  glyph: string;
  group: "Cases" | "People" | "Officers" | "Districts";
  label: string;
  sublabel?: string;
  to: string;
}

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [term, setTerm] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Debounce so each keystroke doesn't hit the case endpoint.
  const [debounced, setDebounced] = useState("");
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(term.trim()), 180);
    return () => window.clearTimeout(t);
  }, [term]);

  const enabled = open && debounced.length >= 2;
  const cases = useCases(enabled ? { q: debounced, limit: 6 } : { limit: 0 });
  const persons = usePersons(200, 0);
  const boundaries = useKarnatakaBoundaries();

  // ⌘K / Ctrl-K opens; Esc closes (§F full keyboard reach).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
    else {
      setTerm("");
      setActive(0);
    }
  }, [open]);

  const hits = useMemo<Hit[]>(() => {
    const q = debounced.toLowerCase();
    if (q.length < 2) return [];
    const out: Hit[] = [];

    // Cases (CrimeNo + full text) → /case/:id
    for (const c of cases.data?.items ?? []) {
      out.push({
        id: `case:${c.case_master_id}`,
        glyph: ENTITY_GLYPH.case,
        group: "Cases",
        label: c.crime_no,
        sublabel: `${c.title} · ${c.station_name}`,
        to: `/case/${c.case_master_id}`,
      });
      // Officers named on a case → their caseload (no officer registry exists).
      if (c.officer_name && c.officer_name.toLowerCase().includes(q)) {
        const id = `officer:${c.officer_name}`;
        if (!out.some((h) => h.id === id)) {
          out.push({
            id,
            glyph: ENTITY_GLYPH.officer,
            group: "Officers",
            label: c.officer_name,
            sublabel: c.station_name,
            to: `/cases?q=${encodeURIComponent(c.officer_name)}`,
          });
        }
      }
    }

    // Resolved identities → /person/:id
    for (const p of persons.data?.persons ?? []) {
      if (p.canonical_name.toLowerCase().includes(q)) {
        out.push({
          id: `person:${p.person_id}`,
          glyph: ENTITY_GLYPH.person,
          group: "People",
          label: p.canonical_name,
          sublabel: p.description,
          to: `/person/${p.person_id}`,
        });
      }
    }

    // Districts → the map (§D "districts/stations → /geo")
    for (const f of boundaries.data?.districts.features ?? []) {
      if (f.properties.district_name.toLowerCase().includes(q)) {
        out.push({
          id: `district:${f.properties.district_id}`,
          glyph: ENTITY_GLYPH.district,
          group: "Districts",
          label: f.properties.district_name,
          sublabel: "Open on the map",
          to: `/geo?district=${f.properties.district_id}`,
        });
      }
    }

    return out.slice(0, 20);
  }, [debounced, cases.data, persons.data, boundaries.data]);

  useEffect(() => setActive(0), [hits.length]);

  function choose(hit: Hit | undefined) {
    if (!hit) return;
    setOpen(false);
    navigate(hit.to);
  }

  function onListKeyDown(e: ReactKeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, hits.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(hits[active]);
    }
  }

  // Group hits while preserving order.
  const grouped = useMemo(() => {
    const map = new Map<Hit["group"], Hit[]>();
    for (const h of hits) {
      const list = map.get(h.group) ?? [];
      list.push(h);
      map.set(h.group, list);
    }
    return [...map.entries()];
  }, [hits]);

  const busy = enabled && cases.isFetching;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex flex-1 items-center gap-2 rounded border border-line bg-void px-3 py-2 text-caption text-ink-faint hover:border-signal/40"
        aria-label="Search cases, people, districts (Command K)"
        aria-haspopup="dialog"
      >
        <Search size={16} />
        <span>Search cases, people, districts…</span>
        <kbd className="ml-auto font-mono text-caption text-ink-faint">⌘K</kbd>
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-overlay flex items-start justify-center bg-void/70 pt-[12vh]"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <Panel
            elevated
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            className="flex max-h-[70vh] w-full max-w-xl flex-col"
          >
            <div className="flex items-center gap-2 border-b border-line px-4 py-3">
              <Search size={16} className="text-ink-faint" aria-hidden />
              <input
                ref={inputRef}
                type="text"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                onKeyDown={onListKeyDown}
                placeholder="CrimeNo, person, officer, district…"
                aria-label="Search"
                className="flex-1 bg-transparent text-body text-ink-primary outline-none placeholder:text-ink-faint"
              />
              {busy ? (
                <Loader2 size={14} className="animate-spin text-ink-faint" aria-hidden />
              ) : (
                <kbd className="font-mono text-caption text-ink-faint">Esc</kbd>
              )}
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-2">
              {debounced.length < 2 ? (
                <p className="px-2 py-6 text-center text-caption text-ink-faint">
                  Type at least two characters. A CrimeNo opens its case; a name
                  opens the person or their caseload; a district opens the map.
                </p>
              ) : hits.length === 0 ? (
                <p className="px-2 py-6 text-center text-caption text-ink-muted">
                  No cases, people, officers or districts match “{debounced}”.
                </p>
              ) : (
                grouped.map(([group, rows]) => (
                  <div key={group} className="mb-2">
                    <p className="px-2 py-1 text-caption uppercase tracking-wide text-ink-faint">
                      {group}
                    </p>
                    {rows.map((hit) => {
                      const index = hits.indexOf(hit);
                      return (
                        <button
                          key={hit.id}
                          type="button"
                          onMouseEnter={() => setActive(index)}
                          onClick={() => choose(hit)}
                          className={cn(
                            "flex w-full items-center gap-2 rounded px-2 py-1.5 text-left",
                            index === active ? "bg-raised" : "hover:bg-raised",
                          )}
                        >
                          <span aria-hidden className="text-signal">
                            {hit.glyph}
                          </span>
                          <span className="min-w-0 flex-1 truncate text-caption text-ink-primary">
                            {hit.label}
                          </span>
                          {hit.sublabel ? (
                            <span className="max-w-[45%] truncate text-caption text-ink-faint">
                              {hit.sublabel}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                ))
              )}
            </div>
          </Panel>
        </div>
      ) : null}
    </>
  );
}
