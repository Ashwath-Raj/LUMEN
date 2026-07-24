/** Joins truthy class names — avoids pulling in a dependency for this alone. */
export function cx(...classes) {
  return classes.filter(Boolean).join(' ');
}
