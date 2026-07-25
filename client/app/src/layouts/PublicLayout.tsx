/**
 * `PublicLayout` — bare layout for the public/pre-auth surfaces (C.1 Mission
 * Briefing landing, C.2 Authentication). No rail, no top bar — "government
 * software introducing itself" (arch §C.1). One centred column.
 */
import { Outlet } from "react-router-dom";

export function PublicLayout() {
  return (
    <div className="flex min-h-screen w-screen flex-col items-center bg-void">
      <Outlet />
    </div>
  );
}
