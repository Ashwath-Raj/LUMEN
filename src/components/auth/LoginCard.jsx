import { useState } from 'react';
import { Briefcase, Fingerprint, AlertTriangle, ArrowRight } from 'lucide-react';
import Button from '@/components/common/Button.jsx';

/**
 * "RESTRICTED ACCESS / FORM-1A-AUTH" card: Clearance ID + Biometric /
 * Passphrase fields, warning notice, "INITIALIZE SESSION" submit.
 * Wraps onSubmit so LoginPage owns the actual authService call.
 *
 * Deliberately light-themed per the Figma — see AuthLayout.jsx for why
 * this diverges from the dark tactical theme used post-login.
 */
export default function LoginCard({ onSubmit, isSubmitting, errorMessage }) {
  const [clearanceId, setClearanceId] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [touched, setTouched] = useState(false);

  const clearanceError = touched && !clearanceId ? 'Clearance ID is required.' : null;
  const passphraseError = touched && !passphrase ? 'Passphrase is required.' : null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setTouched(true);
    if (!clearanceId || !passphrase) return;
    onSubmit?.({ clearanceId, passphrase });
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="w-full max-w-md bg-white border border-neutral-200 rounded-sm shadow-xl shadow-black/5"
    >
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

        <div className="flex flex-col gap-5">
          <div>
            <label
              htmlFor="clearanceId"
              className="flex items-center gap-2 text-neutral-800 text-sm font-medium mb-2"
            >
              <Briefcase size={15} strokeWidth={1.75} />
              Clearance ID
            </label>
            <input
              id="clearanceId"
              value={clearanceId}
              onChange={(e) => setClearanceId(e.target.value)}
              placeholder="Enter 9-digit identifier"
              autoComplete="off"
              aria-invalid={Boolean(clearanceError)}
              aria-describedby={clearanceError ? 'clearanceId-error' : undefined}
              className="w-full bg-transparent border-b border-neutral-300 focus:border-neutral-900 outline-none py-1.5 text-neutral-900 placeholder:text-neutral-400 transition-colors"
            />
            {clearanceError && (
              <p id="clearanceId-error" className="text-xs text-status-critical mt-1">
                {clearanceError}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="passphrase"
              className="flex items-center gap-2 text-neutral-800 text-sm font-medium mb-2"
            >
              <Fingerprint size={15} strokeWidth={1.75} />
              Biometric / Passphrase
            </label>
            <input
              id="passphrase"
              type="password"
              value={passphrase}
              onChange={(e) => setPassphrase(e.target.value)}
              autoComplete="current-password"
              aria-invalid={Boolean(passphraseError)}
              aria-describedby={passphraseError ? 'passphrase-error' : undefined}
              className="w-full bg-transparent border-b border-neutral-300 focus:border-neutral-900 outline-none py-1.5 text-neutral-900 tracking-widest transition-colors"
            />
            {passphraseError && (
              <p id="passphrase-error" className="text-xs text-status-critical mt-1">
                {passphraseError}
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-3 border border-neutral-200 rounded-sm p-3.5 mt-6 bg-neutral-50">
          <AlertTriangle size={16} strokeWidth={1.75} className="text-neutral-500 shrink-0 mt-0.5" />
          <p className="text-xs text-neutral-500 leading-relaxed">
            Authorized Personnel Only. All actions are logged, timestamped, and monitored by
            internal security directives.
          </p>
        </div>

        {errorMessage && (
          <p role="alert" className="text-sm text-status-critical mt-4">
            {errorMessage}
          </p>
        )}

        <Button
          type="submit"
          variant="plain"
          disabled={isSubmitting}
          className="w-full mt-6 bg-white border border-neutral-900 text-neutral-900 hover:bg-neutral-900 hover:text-white disabled:opacity-60 flex items-center justify-center gap-2 uppercase tracking-wide font-semibold py-3"
        >
          {isSubmitting ? 'Verifying...' : 'Initialize Session'}
          {!isSubmitting && <ArrowRight size={16} />}
        </Button>
      </div>
    </form>
  );
}
