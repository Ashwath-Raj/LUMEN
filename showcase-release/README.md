# LUMEN — Local Showcase Package

A one-command, Ubuntu-friendly demonstration runtime for the LUMEN AI Crime Intelligence Platform concept from the KSP Datathon. It provides an end-to-end local walkthrough of the platform's central workflow surfaces without requiring cloud credentials, Node.js, npm packages, a database server, or API keys.

> **Important boundary:** this ZIP is a runnable *showcase layer* that can sit beside the existing `lumen-development` repository. It is not a claim that the original Catalyst deployment is complete. The local runtime uses clearly labelled synthetic data, SQLite, deterministic retrieval and descriptive heuristics. It is not an operational Karnataka State Police system and must not be connected to real case data.

## Start on Ubuntu

```bash
unzip LUMEN-Showcase.zip
cd LUMEN-Showcase
chmod +x start.sh clone-and-start.sh test.sh
./start.sh
```

The browser opens at `http://127.0.0.1:8765`. Stop the server with `Ctrl+C` in the terminal.

No Python packages are installed: the runtime uses Python 3.10+ standard-library modules only (`http.server`, `sqlite3`, `json`, `unittest`).

### Start by cloning the original repository

The optional helper clones the public LUMEN `lumen-development` branch, copies this showcase runtime into `showcase/`, and starts it:

```bash
./clone-and-start.sh
```

Or select the destination:

```bash
./clone-and-start.sh "$HOME/Projects/LUMEN"
```

This helper requires Git and network access on the machine running it. It does not commit changes or overwrite tracked upstream files; it creates/updates the `showcase/` folder only.

## What is included

| Module | Local showcase behavior |
|---|---|
| Command centre | Case counts, monthly trend, category distribution, district activity indicators and recent local events |
| Case registry | Search, district filter and interactive synthetic case dossiers |
| Network intelligence | Entity nodes, co-occurrence edges, candidate review and entity dossiers |
| Geospatial | Synthetic case coordinates plotted over an illustrative Karnataka-region outline |
| Insights & forecasts | Descriptive district activity scores and volume-deviation signals |
| Intelligence assistant | Deterministic retrieval over the synthetic corpus with evidence references and policy refusals |
| Data quality & trust | Completeness metrics, explicit runtime boundaries and design controls |
| Audit activity | Selected local events such as case dossier views and assistant queries |

## Run the checks

```bash
./test.sh
```

The tests exercise the HTTP health endpoint, seeded corpus, case dossier, graph API, assistant evidence flow, protected-attribute refusal, quality boundary and frontend serving.

## Useful options

```bash
./showcase/start.sh --help
PORT=9000 ./showcase/start.sh
./showcase/start.sh --no-browser
./showcase/start.sh --reset-demo-data
```

Environment variables:

- `PORT` — HTTP port, default `8765`.
- `LUMEN_HOST` — bind host, default `127.0.0.1`. Keep localhost for a personal demo.
- `LUMEN_DB` — SQLite file path. Defaults to `showcase/data/lumen_showcase.sqlite3`.
- `LUMEN_OPEN_BROWSER=0` — disable automatic browser launch.

## Technical layout

```text
LUMEN-Showcase/
├── start.sh                 # launch the standalone local runtime
├── clone-and-start.sh       # clone upstream + install showcase folder + launch
├── test.sh                  # run API tests
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── COMPLETION-STATUS.md
└── showcase/
    ├── server.py            # HTTP API, SQLite schema, synthetic seed, retrieval
    ├── start.sh
    ├── data/                # SQLite DB is created on first start
    ├── tests/
    └── web/                 # responsive HTML/CSS/JS application
```

## What this package does not claim

- No production Catalyst deployment is performed by this local runtime.
- No Zoho QuickML or Gemini model is called. The assistant uses deterministic retrieval and response templates so the showcase works without keys.
- The district risk bands and anomaly signals are descriptive calculations over generated data, not validated predictive models.
- The graph contains generated case-person associations, not verified identities or real criminal networks.
- The coordinate view plots generated offsets around district-centre reference coordinates. It is not a verified incident map.
- There is no production authentication, authorization, KSP integration, legal corpus, real audit authority, evidence chain of custody, or operational monitoring in this local demo.

For the full product path, use `docs/COMPLETION-STATUS.md` as the implementation checklist and the upstream `docs/LUMEN_MASTER_SPEC_V3.md` as the architecture contract.
