/**
 * Sign in — `/login` (arch §C.2, spec §26.1 row 17: Catalyst Authentication).
 *
 * This is the WORKING sign-in that opens the app: it calls the session's
 * `login()`, which in the Catalyst runtime redirects to the hosted login, and
 * under plain `npm run dev` (no Catalyst) establishes the dev mock session (see
 * authService.ts). On success it returns the analyst to where they were headed
 * (`location.state.from`) or to `/briefing`. Without this, `RequireAuth` bounces
 * every authenticated route here and nothing downstream is reachable — which is
 * exactly what left the shell/rail unrenderable.
 *
 * The full §C.2 visual panel (crest, richer copy) is a Session-6 polish item;
 * this is the honest minimum: crest, email/password, sign in, the scope note,
 * and inline §29.3 error rendering. In dev the credential fields are presentation
 * only — the mock session ignores them (stated on the page).
 */
import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, Loader2 } from "lucide-react";

import { useSession } from "@/providers/sessionContext";
import { Button, Panel } from "@/design/primitives";

interface FromState {
  from?: { pathname?: string };
}

export default function LoginPage() {
  const { login } = useSession();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Return to where the analyst was headed, else the Command Center — the
  // operational landing page (E.1).
  const dest = (location.state as FromState | null)?.from?.pathname ?? "/command";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const operator = await login();
      // In the Catalyst runtime `login()` redirects the page and returns null;
      // in dev it returns the mock operator synchronously — navigate onward.
      if (operator) navigate(dest, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed.");
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen w-full items-center justify-center px-6">
      <Panel elevated className="w-full max-w-sm p-8">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <ShieldCheck size={28} strokeWidth={1.5} className="text-signal" aria-hidden />
          <h1 className="font-display text-page-title text-ink-primary">LUMEN</h1>
          <p className="text-caption text-ink-muted">
            Crime Intelligence Platform · Karnataka State Police
          </p>
        </div>

        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <label className="flex flex-col gap-1">
            <span className="text-caption uppercase tracking-wide text-ink-muted">
              Email
            </span>
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded border border-line bg-void px-3 py-2 text-body text-ink-primary outline-none focus:border-signal/50"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-caption uppercase tracking-wide text-ink-muted">
              Password
            </span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded border border-line bg-void px-3 py-2 text-body text-ink-primary outline-none focus:border-signal/50"
            />
          </label>

          {error ? (
            <p role="alert" className="text-caption text-risk-high">
              {error}
            </p>
          ) : null}

          <Button
            type="submit"
            variant="primary"
            disabled={submitting}
            className="justify-center"
          >
            {submitting ? (
              <Loader2 size={16} className="animate-spin" aria-hidden />
            ) : null}
            Sign in
          </Button>
        </form>

        <p className="mt-4 text-caption text-ink-faint">
          Access is scoped to your role and jurisdiction; every access is logged.
        </p>
        {import.meta.env.DEV ? (
          <p className="mt-2 text-caption text-ink-faint">
            Dev mode: any credentials establish a local session (Catalyst
            Authentication is used in the deployed build).
          </p>
        ) : null}
      </Panel>
    </main>
  );
}
