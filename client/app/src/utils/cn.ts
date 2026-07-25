/** Class-name join helper (clsx). The one styling-composition utility. */
import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
