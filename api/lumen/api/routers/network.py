"""
Criminal-network surface — LUMEN_MASTER_SPEC_V3 §14.4, §29.1
(`GET /network/query/{q1..q10}` — "Named queries — insight + graph").

§28 rule 1 keeps the router thin: parse params → one call into the existing
`graph.queries` module (which owns all ten named queries) → return the §14.4
`GraphQueryResult` contract. NOTHING is computed here; every query already
exists and is exercised by the graph test-suite.

§14.4's invariant is structural in the returned contract: "Every result returns
`Insight` **plus** graph payload, never a bare graph, and every result carries
its limitations line" — `GraphQueryResult` is exactly that pair, and §8
invariant 2 makes the limitations unomittable.

Also serves the two graph reads the workspace/dossier need (§29.1):
  GET /persons/{id}/network  → ego graph  (mounted here, not on persons.py,
                               so the graph module stays this router's only
                               dependency; the path is §29.1's exact path)
  GET /cases/{id}/graph      → investigation-board payload
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models.graph import LumenGraphEdge
from lumen.db.models.identity import LumenPerson
from lumen.graph import queries as q

router = APIRouter(tags=["Network"])


def _parse_as_of(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be ISO-8601")


@router.get("/network/query/{qid}")
def named_query(
    qid: str,
    # Q1 / Q2 person selectors
    person_a: str | None = Query(default=None),
    person_b: str | None = Query(default=None),
    group_a: list[str] | None = Query(default=None),
    group_b: list[str] | None = Query(default=None),
    # Q4 district · Q5 top-n · Q7/Q10 case · Q9 as-of
    district_id: int | None = Query(default=None),
    top_n: int = Query(default=10, ge=1, le=50),
    case_id: int | None = Query(default=None),
    as_of: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Run one of the ten §14.4 named queries. Missing required parameters are
    a 422 (§29.3 VALIDATION_FAILED), never a silent empty graph."""
    key = qid.lower()

    def need(value, name: str):
        if value is None:
            raise HTTPException(status_code=422, detail=f"{qid} requires '{name}'")
        return value

    if key == "q1":
        result = q.q1_shortest_connection(db, need(person_a, "person_a"), need(person_b, "person_b"))
    elif key == "q2":
        result = q.q2_hidden_intermediary(db, need(group_a, "group_a"), need(group_b, "group_b"))
    elif key == "q3":
        result = q.q3_communities(db)
    elif key == "q4":
        result = q.q4_most_influential(db, need(district_id, "district_id"))
    elif key == "q5":
        result = q.q5_repeat_pairs(db, top_n=top_n)
    elif key == "q6":
        result = q.q6_cross_district(db)
    elif key == "q7":
        result = q.q7_two_hop_cases(db, need(case_id, "case_id"))
    elif key == "q8":
        result = q.q8_signature_families(db)
    elif key == "q9":
        result = q.q9_emerging_clusters(db, as_of=_parse_as_of(as_of))
    elif key == "q10":
        result = q.q10_spree_chain(db, need(case_id, "case_id"))
    else:
        raise HTTPException(status_code=404, detail="Unknown named query; §14.4 defines q1–q10.")

    return result.model_dump(mode="json")


@router.get("/persons/{person_id}/network")
def person_ego_graph(
    person_id: str,
    depth: int = Query(default=1, ge=1, le=2),
    db: Session = Depends(get_db),
) -> dict:
    """§29.1 ego graph. Built from the persisted `lumen_graph_edge` projection —
    no traversal is computed in the request path (§14.5)."""
    if db.get(LumenPerson, person_id) is None:
        raise HTTPException(status_code=404, detail="Person not found")

    seen_nodes: set[str] = {person_id}
    edges: list[dict] = []
    frontier = {person_id}

    for _ in range(depth):
        if not frontier:
            break
        rows = (
            db.query(LumenGraphEdge)
            .filter(
                (LumenGraphEdge.src_id.in_(frontier)) | (LumenGraphEdge.dst_id.in_(frontier))
            )
            .all()
        )
        next_frontier: set[str] = set()
        for e in rows:
            edges.append({
                "src_type": e.src_type, "src_id": e.src_id,
                "dst_type": e.dst_type, "dst_id": e.dst_id,
                "rel": e.rel, "weight": e.weight, "props": e.props or {},
            })
            for nid in (e.src_id, e.dst_id):
                if nid not in seen_nodes:
                    next_frontier.add(nid)
                seen_nodes.add(nid)
        frontier = next_frontier

    names = {
        p.person_id: p.canonical_name
        for p in db.query(LumenPerson).filter(LumenPerson.person_id.in_(seen_nodes)).all()
    }
    nodes = [
        {"type": "person", "id": n, "label": names.get(n, n)}
        for n in sorted(seen_nodes)
    ]
    # De-duplicate edges (an edge touching two frontier nodes is collected twice).
    unique = {(e["src_id"], e["dst_id"], e["rel"]): e for e in edges}
    return {"contract_version": "v1", "nodes": nodes, "edges": list(unique.values())}


@router.get("/cases/{case_id}/graph")
def case_board_graph(case_id: int, db: Session = Depends(get_db)) -> dict:
    """§29.1 investigation-board payload: the case, its accused participants,
    its officer, and the persons those accused resolve to — read from the
    canonical rows and the persisted projection. Nothing inferred here."""
    from lumen.db.models import canonical as m
    from lumen.db.models.identity import LumenPersonLink

    case = db.get(m.CaseMaster, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    nodes: list[dict] = [{"type": "case", "id": str(case_id), "label": case.CrimeNo}]
    edges: list[dict] = []

    if case.PolicePersonID:
        emp = db.get(m.Employee, case.PolicePersonID)
        oid = f"officer:{case.PolicePersonID}"
        nodes.append({"type": "officer", "id": oid,
                      "label": (emp.FirstName if emp else f"Employee {case.PolicePersonID}")})
        edges.append({"src_type": "case", "src_id": str(case_id), "dst_type": "officer",
                      "dst_id": oid, "rel": "INVESTIGATED_BY", "weight": 1.0, "props": {}})

    accused_rows = db.query(m.Accused).filter(m.Accused.CaseMasterID == case_id).all()
    for a in accused_rows:
        aid = f"accused:{a.AccusedMasterID}"
        nodes.append({"type": "participant", "id": aid,
                      "label": a.PersonID or a.AccusedName or aid})
        edges.append({"src_type": "case", "src_id": str(case_id), "dst_type": "participant",
                      "dst_id": aid, "rel": "ASSOCIATED_WITH", "weight": 1.0, "props": {}})

        link = (
            db.query(LumenPersonLink)
            .filter(LumenPersonLink.accused_master_id == a.AccusedMasterID)
            .first()
        )
        if link is not None:
            person = db.get(LumenPerson, link.person_id)
            if person is not None:
                pid = person.person_id
                if not any(n["id"] == pid for n in nodes):
                    nodes.append({"type": "person", "id": pid, "label": person.canonical_name})
                edges.append({"src_type": "participant", "src_id": aid, "dst_type": "person",
                              "dst_id": pid, "rel": "RESOLVES_TO",
                              "weight": link.confidence or 0.0, "props": {}})

    return {"contract_version": "v1", "nodes": nodes, "edges": edges}
