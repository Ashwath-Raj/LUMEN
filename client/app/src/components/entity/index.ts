/**
 * Entity component family (D4) — one semantic entity rendered compact or full,
 * plus the `EntityRef` descriptor that decouples entity data from its display.
 */
export { EntityCard } from "./EntityCard";
export {
  encodeEntityRef,
  parseEntityRefToken,
  type EntityRef,
  type EntityRefKind,
  type EntityField,
} from "./entityRef";
