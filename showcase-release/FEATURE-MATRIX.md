# Feature matrix

| Capability | Showcase runtime | Existing upstream LUMEN codebase | Production integration status |
|---|---|---|---|
| Command-centre dashboard | Runnable | React feature surface and API router exist | Needs deployment/integration validation |
| Case registry and dossiers | Runnable on synthetic SQLite | React feature surface and FastAPI case router exist | Needs canonical-data integration validation |
| Entity resolution | Synthetic co-occurrence demo with confidence fields | Dedicated normalization/scoring/pipeline modules exist | Needs labelled validation and workflow integration |
| Knowledge graph | Synthetic person-case projection | NetworkX graph backend/projection modules exist | Needs production data and scheduled projection validation |
| Geospatial | Synthetic coordinate plot | Leaflet frontend and geospatial API surfaces exist | Needs coordinate provenance and tile/service validation |
| District indicators | Descriptive heuristics | Prediction/anomaly modules exist in upstream code | Models need dataset/metrics validation; no operational forecasts claimed |
| AI assistant | Deterministic retrieval and templates | AI orchestration/retriever/provider/evaluation modules exist | QuickML transport and end-to-end model serving must be configured and tested |
| Data quality and governance | Demonstration page and sample controls | Governance/quality/policy modules exist | Production enforcement and authorization tests required |
| Audit view | Local audit event table | Event/audit modules exist | Full operational audit, retention and tamper-resistance require verification |
| Zoho Catalyst | Not used by local runtime | Configuration and service mapping documented upstream | No claim of successful production deployment in this package |
