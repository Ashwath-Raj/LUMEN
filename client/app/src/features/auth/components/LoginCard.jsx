import { AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import Button from '@/design/primitives/Button.jsx';

/**
 * "RESTRICTED ACCESS / FORM-1A-AUTH" card. Credentials are handled entirely
 * by Catalyst's hosted login page (LUMEN_MASTER_SPEC_V3 §20.2) — this app
 * never collects a clearance ID or passphrase itself, so the card's action
 * is a single redirect trigger rather than a form submission.
 *
 * Deliberately light-themed per the Figma — see AuthLayout.jsx for why
 * this diverges from the dark tactical theme used post-login.
 */
export default function LoginCard({ onSubmit }) {
  return (
    <div className="w-full max-w-md bg-white border border-neutral-200 rounded-sm shadow-xl shadow-black/5">
      <div className="px-8 pt-7 pb-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-display text-xl text-neutral-900">Authentication</p>
            <p className="text-neutral-500 text-sm mt-0.5">Sector-07-Alpha Fusion Center</p>
          </div>
          <span className="font-mono text-[11px] tracking-wide border border-neutral-300 text-neutral-500 rounded-sm px-2 py-1 shrink-0">
            FORM-1A-AUTH
          </span>
        </div>

        <div className="h-px bg-neutral-200 mt-5 mb-6" />

        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <ShieldCheck size={28} strokeWidth={1.5} className="text-neutral-400" />
          <p className="text-neutral-600 text-sm leading-relaxed max-w-xs">
            Identity verification is handled by Catalyst Authentication. You
            will be redirected to a secure sign-in page.
          </p>
        </div>

        <div className="flex gap-3 border border-neutral-200 rounded-sm p-3.5 mt-2 bg-neutral-50">
          <AlertTriangle size={16} strokeWidth={1.75} className="text-neutral-500 shrink-0 mt-0.5" />
          <p className="text-xs text-neutral-500 leading-relaxed">
            Authorized Personnel Only. All actions are logged, timestamped, and monitored by
            internal security directives.
          </p>
        </div>

        <Button
          type="button"
          variant="plain"
          onClick={onSubmit}
          className="w-full mt-6 bg-white border border-neutral-900 text-neutral-900 hover:bg-neutral-900 hover:text-white flex items-center justify-center gap-2 uppercase tracking-wide font-semibold py-3"
        >
          Continue to Sign-In
          <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}
