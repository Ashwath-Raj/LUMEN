import { ShieldCheck } from 'lucide-react';
import { useAuth } from '@/app/hooks/useAuth.js';
import LoginCard from '@/features/auth/components/LoginCard.jsx';
import { SYSTEM_BUILD } from '@/app/config/constants.js';

/**
 * Login is a redirect to Catalyst's hosted login page (LUMEN_MASTER_SPEC_V3
 * §20.2, Catalyst Authentication — "replaces bespoke JWT entirely"), not a
 * credential form this app submits. `LoginCard` below is kept as the entry
 * point into that redirect so the existing "Restricted Access" visual design
 * is preserved rather than replaced.
 */
export default function LoginPage() {
  const { login } = useAuth();

  const handleSubmit = () => {
    login();
  };

  return (
    <div className="flex flex-col items-center gap-8 w-full">
      <div className="flex flex-col items-center gap-3">
        <div className="w-14 h-14 rounded-full border border-neutral-300 flex items-center justify-center">
          <ShieldCheck size={22} strokeWidth={1.5} className="text-neutral-900" />
        </div>
        <div className="text-center">
          <p className="font-display text-2xl font-semibold text-neutral-900 tracking-wide">LUMEN</p>
          <p className="font-mono text-xs tracking-widest2 text-neutral-500 mt-1">
            RESTRICTED ACCESS
          </p>
        </div>
      </div>

      <LoginCard onSubmit={handleSubmit} />

      <div className="text-center font-mono text-[11px] text-neutral-400 tracking-wide">
        <p>{SYSTEM_BUILD}</p>
        <p>CONNECTION: SECURE (ENCRYPTED)</p>
      </div>
    </div>
  );
}
