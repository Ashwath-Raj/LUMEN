import { forwardRef } from 'react';

const VARIANT_CLASSES = {
  primary: 'bg-accent-gold text-surface-0 hover:bg-accent-goldMuted',
  ghost: 'bg-transparent border border-border-strong text-ink-primary hover:bg-surface-2',
  danger: 'bg-status-critical text-ink-primary hover:opacity-90',
  plain: '',
};

/**
 * Base button used everywhere ("INITIALIZE SESSION", "NEW INVESTIGATION",
 * "APPLY PARAMETERS", etc. all share this). Visual polish comes later —
 * this locks in the variant API pages/components will rely on.
 */
const Button = forwardRef(function Button(
  { variant = 'primary', className = '', ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
});

export default Button;
