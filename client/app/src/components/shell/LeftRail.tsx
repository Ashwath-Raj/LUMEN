/**
 * `LeftRail` — the shell's orientation rail (arch §D shell, §C rail order).
 * Icons + labels, collapsible; the rail is orientation, entity references are
 * navigation (§B "drill-in, never sidebar-hop").
 *
 * A11y (§F): full keyboard reach — Alt+1…9 jump to the Nth rail item; the
 * collapse toggle has an accessible label; the active item is marked
 * aria-current. Labels are hidden (not removed) when collapsed so the nav stays
 * screen-reader complete.
 *
 * Session 1 completes the rail (collapse + Alt keys); feature navigation beyond
 * the existing §C set is intentionally NOT added here.
 */
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { cn } from "@/utils/cn";
import { NAV_ITEMS } from "./navigation";

export function LeftRail() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const primary = NAV_ITEMS.filter((i) => !i.secondary);
  const secondary = NAV_ITEMS.filter((i) => i.secondary);

  // §F: Alt+1…9 jump to the Nth rail item (primary then secondary, in order).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!e.altKey || e.ctrlKey || e.metaKey) return;
      const n = Number(e.key);
      if (!Number.isInteger(n) || n < 1 || n > 9) return;
      const item = NAV_ITEMS[n - 1];
      if (item) {
        e.preventDefault();
        navigate(item.to);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navigate]);

  return (
    <nav
      className="flex h-full flex-col border-r border-line bg-panel py-4"
      style={{ width: collapsed ? "64px" : "var(--rail-width)" }}
      aria-label="Primary"
    >
      <div className="flex flex-1 flex-col gap-1 px-2">
        {primary.map((item, i) => (
          <RailLink key={item.to} item={item} index={i} collapsed={collapsed} />
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-1 border-t border-line px-2 pt-2">
        {secondary.map((item, i) => (
          <RailLink
            key={item.to}
            item={item}
            index={primary.length + i}
            collapsed={collapsed}
          />
        ))}
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-pressed={collapsed}
          className="mt-1 flex items-center gap-3 rounded px-3 py-2 text-ink-faint hover:bg-raised hover:text-ink-primary"
        >
          {collapsed ? (
            <PanelLeftOpen size={20} strokeWidth={1.5} />
          ) : (
            <PanelLeftClose size={20} strokeWidth={1.5} />
          )}
          {!collapsed ? <span className="text-caption">Collapse</span> : null}
        </button>
      </div>
    </nav>
  );
}

function RailLink({
  item,
  index,
  collapsed,
}: {
  item: (typeof NAV_ITEMS)[number];
  index: number;
  collapsed: boolean;
}) {
  const { to, label, icon: Icon } = item;
  return (
    <NavLink
      to={to}
      title={collapsed ? `${label} (Alt+${index + 1})` : undefined}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded px-3 py-2 text-body",
          "transition-colors duration-DEFAULT ease-ease",
          isActive
            ? "bg-raised text-signal"
            : "text-ink-muted hover:bg-raised hover:text-ink-primary",
        )
      }
    >
      <Icon size={20} strokeWidth={1.5} className="shrink-0" />
      <span className={cn(collapsed && "sr-only")}>{label}</span>
      {!collapsed ? (
        <kbd className="ml-auto font-mono text-caption text-ink-faint">
          ⌥{index + 1}
        </kbd>
      ) : null}
    </NavLink>
  );
}
