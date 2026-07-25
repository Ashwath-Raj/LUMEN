/**
 * `useInspector` — the InspectorPanel selection as URL state (arch §C "selected
 * entity serializes to query params"; D10). The selected entity is stored as
 * `?inspect=kind:id`, so: browser back closes/changes the selection, a workspace
 * view is shareable with its inspector open, and refresh reproduces it — without
 * any in-memory selection state.
 *
 * Returns the current selection token (parsed) and select/clear actions. The
 * page maps the token to a concrete `EntityRef` from its already-loaded data
 * (no extra fetch for entities the workspace already holds).
 */
import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import {
  encodeEntityRef,
  parseEntityRefToken,
  type EntityRef,
  type EntityRefKind,
} from "@/components/entity";
import { writeParams } from "@/utils/urlState";

const PARAM = "inspect";

export interface InspectorSelection {
  kind: EntityRefKind;
  id: string;
}

export function useInspector() {
  const [params, setParams] = useSearchParams();

  const selection = useMemo<InspectorSelection | null>(() => {
    const token = params.get(PARAM);
    return token ? parseEntityRefToken(token) : null;
  }, [params]);

  const select = useCallback(
    (ref: Pick<EntityRef, "kind" | "id">) => {
      setParams(writeParams(params, { [PARAM]: encodeEntityRef(ref) }));
    },
    [params, setParams],
  );

  const clear = useCallback(() => {
    setParams(writeParams(params, { [PARAM]: null }));
  }, [params, setParams]);

  return { selection, select, clear };
}
