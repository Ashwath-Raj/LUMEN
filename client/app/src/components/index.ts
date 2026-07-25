/**
 * Components barrel (arch §G: `components/` owns D1–D13). The reusable component
 * families; feature sessions import from here and never redefine a
 * reusable-looking component inside a feature folder (§G).
 *
 * Session 1:  D1 insight · D2 confidence · D3 evidence · D12 trust · D13 shell · states
 * Session 2:  D4 entity · D5 case (CrimeNoDecoder) · D10 inspector · D11 filters
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
export { CrimeNoDecoder } from "./case/CrimeNoDecoder";

export { PanelErrorBoundary } from "./PanelErrorBoundary";
