/**
 * `WorkstationNotice` — the honest small-screen notice (§F responsive): below
 * 1024 px LUMEN shows a static message rather than a broken tablet/mobile
 * layout ("a broken tablet layout is worse than an honest notice"). Desktop-
 * first, supported ≥ 1280; the app content is designed for 1440.
 *
 * Implemented with a Tailwind `max-*` breakpoint so there is no JS resize
 * listener; it covers the whole viewport and sits above the shell only when the
 * viewport is too small.
 */
import { MonitorSmartphone } from "lucide-react";

export function WorkstationNotice() {
  return (
    <div className="fixed inset-0 z-toast hidden flex-col items-center justify-center gap-3 bg-void px-8 text-center max-[1023px]:flex">
      <MonitorSmartphone
        size={32}
        strokeWidth={1.5}
        className="text-ink-muted"
        aria-hidden
      />
      <p className="max-w-sm text-body text-ink-primary">
        LUMEN is designed for operations workstations.
      </p>
      <p className="max-w-sm text-caption text-ink-muted">
        Please open it on a display 1280 px or wider.
      </p>
    </div>
  );
}
