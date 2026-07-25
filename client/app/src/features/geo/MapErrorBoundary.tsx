/**
 * `MapErrorBoundary` — catches a Leaflet load/render failure (the lazy map chunk
 * failing to import, or a runtime error inside the canvas) and renders the table
 * fallback instead (arch D9; brief: "Only fall back to the tabular representation
 * if Leaflet itself cannot load"). A data 501 does NOT reach here — that keeps
 * the map visible with the degraded banner.
 */
import { Component, type ReactNode } from "react";

import { GeoTableFallback } from "./GeoTableFallback";
import type { GeoDistrict } from "@/types/geo";

interface Props {
  children: ReactNode;
  /** District data to show in the fallback table if the map fails. */
  districts: GeoDistrict[];
}

interface State {
  failed: boolean;
}

export class MapErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <GeoTableFallback districts={this.props.districts} />;
    }
    return this.props.children;
  }
}
