/**
 * `Button` — the one button primitive (salvaged from the prototype, re-tokened).
 * `--signal` is the only interactive accent (§31.2). No gradients/glows (§B).
 */
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/utils/cn";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANT: Record<Variant, string> = {
  primary:
    "bg-signal/15 text-signal border border-signal/40 hover:bg-signal/25",
  secondary:
    "bg-raised text-ink-primary border border-line hover:border-signal/40",
  ghost: "text-ink-muted hover:text-ink-primary hover:bg-raised",
};

export function Button({
  variant = "secondary",
  className,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center gap-2 rounded px-3 py-2 text-body",
        "transition-colors duration-DEFAULT ease-ease",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT[variant],
        className,
      )}
      {...rest}
    />
  );
}
