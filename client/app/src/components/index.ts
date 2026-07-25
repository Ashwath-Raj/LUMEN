/**
 * Components barrel (arch §G: `components/` owns D1–D13). The reusable component
 * families; feature sessions import from here and never redefine a
 * reusable-looking component inside a feature folder (§G).
 *
 * D1 insight · D2 confidence · D3 evidence · D4 entity · D5 CrimeNoDecoder ·
 * D8 graph · D10 inspector · D11 filters · D12 trust · D13 shell · states ·
 * intelligence workbench · person identity
 */
export * from "./insight";
export * from "./confidence";
export * from "./evidence";
export * from "./trust";
export * from "./states";
export * from "./entity";
export * from "./filters";
export * from "./inspector";
export * from "./graph";
export * from "./person";
export * from "./intelligence";
export { CrimeNoDecoder } from "./case/CrimeNoDecoder";

export { PanelErrorBoundary } from "./PanelErrorBoundary";
