/**
 * Rail navigation config — arch §C rail order ("Command → Geo → Cases → Ask →
 * Forecasts → Quality; System/Admin collapsed at the bottom").
 *
 * `/case/:id` and `/person/:id` are intentionally ABSENT — they are drilled
 * into, never in the rail (§C). `/anomalies` is reached from the Command stat
 * and the tray, not the rail (§C).
 */
import {
  LayoutGrid,
  Map,
  FolderSearch,
  MessageSquare,
  TrendingUp,
  ShieldCheck,
  Activity,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Collapsed into the bottom group (System/Admin). */
  secondary?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/command", label: "Command", icon: LayoutGrid },
  { to: "/geo", label: "Geo", icon: Map },
  { to: "/cases", label: "Cases", icon: FolderSearch },
  { to: "/ask", label: "Ask", icon: MessageSquare },
  { to: "/forecasts", label: "Forecasts", icon: TrendingUp },
  { to: "/quality", label: "Quality", icon: ShieldCheck },
  { to: "/system", label: "System", icon: Activity, secondary: true },
  { to: "/admin", label: "Admin", icon: Users, secondary: true },
];
