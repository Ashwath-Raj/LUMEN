import { Outlet } from 'react-router-dom';

/**
 * Shell for unauthenticated screens (Restricted Access login, and any future
 * step-up auth). Deliberately isolated from RootLayout — no top nav, no
 * sidebar, nothing that assumes a session exists.
 *
 * Intentionally light-themed: the Figma "Restricted Access" screen is a
 * stark white/graphite terminal-boot look, distinct from the dark tactical
 * theme used everywhere after an operator authenticates. That contrast is
 * deliberate (pre-session vs. inside-the-system) so it's kept as-is here
 * rather than forced into the dark palette.
 */
export default function AuthLayout() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#FAFAF9] px-4 py-12">
      <Outlet />
    </div>
  );
}
