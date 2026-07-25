/**
 * Design primitives barrel (arch §F design/primitives/).
 *
 * the foundational primitives the shell and routing need:
 * Panel, Button, Stat, EmptyState, ErrorState, DataGrid, Skeleton. The
 * remaining §F primitives (PipelineStages, AuditRow) and the D1–D13 components
 * are built in their feature sessions, each in its own directory.
 */
export { Panel } from "./Panel";
export { Badge } from "./Badge";
export { Button } from "./Button";
export { Stat } from "./Stat";
export { EmptyState } from "./EmptyState";
export { ErrorState } from "./ErrorState";
export { DataGrid, type Column, type Density, type SortTerm } from "./DataGrid";
export { Pagination } from "./Pagination";
export { Tabs, type TabItem } from "./Tabs";
export { Skeleton } from "./Skeleton";
