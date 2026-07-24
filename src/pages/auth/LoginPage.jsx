import { useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth.js';
import LoginCard from '@/components/auth/LoginCard.jsx';
import { SYSTEM_BUILD } from '@/config/constants.js';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (credentials) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await login(credentials);
      navigate(location.state?.from?.pathname ?? '/dashboard', { replace: true });
    } catch (err) {
      setErrorMessage(err?.message || 'Authentication failed. Verify your credentials and retry.');
    } finally {
      setIsSubmitting(false);
    }
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

      <LoginCard onSubmit={handleSubmit} isSubmitting={isSubmitting} errorMessage={errorMessage} />

      <div className="text-center font-mono text-[11px] text-neutral-400 tracking-wide">
        <p>{SYSTEM_BUILD}</p>
        <p>CONNECTION: SECURE (ENCRYPTED)</p>
      </div>
    </div>
  );
}
