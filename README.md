# DeepLynx ↔ Istari Integration Modules

Istari integration modules for [DeepLynx](https://github.com/idaholab/DeepLynx), Idaho National Lab's digital twin data warehouse. Pull graph data, render visualizations, run compliance checks, and push results back — all from inside Istari's outer loop.

## Inner Loop / Outer Loop

DeepLynx is the **system of record** — requirements, subsystems, components, simulations, and risks stored as a knowledge graph. Istari provides the **outer loop**: orchestrating data extraction, running analysis, and writing results back so both systems tell the same story.

```
┌─── Outer Loop: Istari ── pull · visualize · analyze · push ────────────────┐
│                                                                              │
│  ┌─ @deeplynx:pull_graph ───────────────────────────────────────────────┐  │
│  │ Query DeepLynx API → records + edges + ontology → structured JSON     │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                          │
│  ┌─ @deeplynx:pull_graph_image ──┴──────────────────────────────────────┐  │
│  │ Fetch graph topology → force-directed layout → render PNG/SVG         │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                          │
│  ┌─ analysis / compliance ───────┴──────────────────────────────────────┐  │
│  │ Walk requirements vs. simulations → PASS / FAIL / UNCHECKED           │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                          │
│  ┌─ @deeplynx:push_results ─────┴──────────────────────────────────────┐  │
│  │ Write compliance records back to DeepLynx + tag needs-review          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Versioned artifacts: graph data · images · compliance reports · receipts    │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Prerequisites: DeepLynx running (see github.com/idaholab/DeepLynx)
pip install requests networkx matplotlib Pillow

# Pull all records and edges from a project
mkdir -p /tmp/pull && cp pull_graph/example-input/input.json /tmp/pull/
python pull_graph/pull_graph.py /tmp/pull

# Render a subsystem graph as PNG + SVG
mkdir -p /tmp/image && cp pull_graph_image/example-input/input.json /tmp/image/
python pull_graph_image/pull_graph_image.py /tmp/image

# Push analysis results back to DeepLynx
mkdir -p /tmp/push && cp push_results/example-input/input.json /tmp/push/
python push_results/push_results.py /tmp/push

# Or run the full compliance workflow
python use-cases/check-thermal-compliance/check_thermal_compliance.py
```

## Modules

| Module | What It Does | Artifacts |
|--------|-------------|-----------|
| [`@deeplynx:pull_graph`](pull_graph/) | Fetch all records + edges, enrich with class/relationship names, filter by type | `graph_records.json`, `graph_edges.json`, `requirements.json`, `graph_summary.md` |
| [`@deeplynx:pull_graph_image`](pull_graph_image/) | Fetch graph topology for a record, render force-directed diagram | `graph_{name}.png`, `graph_{name}.svg`, `graph_data.json` |
| [`@deeplynx:push_results`](push_results/) | Create records + edges in DeepLynx with tags | `push_receipt.json` |

## Use Cases

End-to-end workflows showing how engineers use DeepLynx data inside Istari. Each includes a [K-script](https://medium.com/@bladekotelly/k-scripts-the-fastest-and-most-flexible-way-to-articulate-a-user-experience-97264d9c4786) describing the user experience and working code.

| # | Use Case | Question It Answers |
|---|----------|-------------------|
| 1 | [Check Thermal Compliance](use-cases/check-thermal-compliance/) | Does my drone design pass thermal requirements — without leaving Istari? |

## Supported Tool

| Category | Tool | What Istari Does With It |
|----------|------|--------------------------|
| **Graph Database** | DeepLynx (INL) | Pull records/edges/ontology, render graph visualizations, push compliance results back as new records with tags |

## Repo Structure

```
deeplynx-istari-modules/
├── shared/                              # Shared DeepLynx API client
│   ├── __init__.py                      # Re-exports DeepLynxClient + utils
│   ├── deeplynx_client.py               # HTTP client wrapping DeepLynx REST API
│   └── utils.py                         # I/O helpers (read_input, write_output, write_artifact)
├── pull_graph/                          # @deeplynx:pull_graph module
│   ├── module_manifest.json             # Istari module manifest (input/output schema)
│   ├── pull_graph.py                    # Entry point — fetch + enrich + filter
│   ├── example-input/input.json         # Sample input for local testing
│   └── example-output/                  # Real output from live DeepLynx run
├── pull_graph_image/                    # @deeplynx:pull_graph_image module
│   ├── module_manifest.json
│   ├── pull_graph_image.py              # Entry point — fetch graph + render
│   ├── rendering.py                     # networkx + matplotlib rendering engine
│   ├── example-input/input.json
│   └── example-output/
├── push_results/                        # @deeplynx:push_results module
│   ├── module_manifest.json
│   ├── push_results.py                  # Entry point — create records + edges
│   ├── example-input/input.json
│   └── example-output/
├── use-cases/
│   └── check-thermal-compliance/        # End-to-end compliance workflow
│       ├── check_thermal_compliance.py  # Orchestrator — runs all 4 steps
│       ├── compliance_checks.py         # Reusable check library
│       ├── example-output/              # Pre-computed results
│       ├── README.md                    # K-script and walkthrough
│       └── CLAUDE.md                    # AI context (IDs, gotchas)
├── CLAUDE.md                            # AI context for the whole repo
├── pyproject.toml                       # Python dependencies
└── .gitignore
```

Each module directory includes its own `CLAUDE.md` with tool-specific IDs, API routes, and gotchas for AI-assisted development.

## DeepLynx API Reference

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| List records | `GET /api/v1/organizations/{org}/projects/{proj}/records` | Returns all records with properties as JSON string |
| Get record graph | `GET .../records/{id}/graph?depth=N` | Max depth 3; returns `{nodes[], links[]}` |
| Create record | `POST .../records?dataSourceId=N` | Accepts `class_name`, `tags` as string names |
| List edges | `GET .../edges` | Returns all edges with origin/destination IDs |
| Create edge | `POST .../edges?dataSourceId=N` | Accepts `relationship_name` (not just ID) |
| List classes | `GET /api/v1/projects/{proj}/classes` | Project-scoped (no org in path) |
| List relationships | `GET /api/v1/projects/{proj}/relationships` | Project-scoped |
| List tags | `GET /api/v1/projects/{proj}/tags` | Project-scoped |

## SDK Tips

| Gotcha | Details |
|--------|---------|
| Properties is a JSON string | Record responses return `properties` as a string — must `json.loads()` before accessing values |
| Class/relationship routes are project-scoped | Use `/projects/{id}/classes`, NOT `/organizations/{org}/projects/{id}/classes` |
| `original_id` must be unique per data source | Use timestamps in IDs when pushing records (e.g., `COMPLIANCE-PERF-007-20260304T170123`) |
| Graph API max depth is 3 | `GET /records/{id}/graph?depth=4` will be clamped to 3 |
| Tags as string names | `CreateRecordRequestDto` accepts `tags: ["needs-review"]` — server resolves to IDs |
| Auth can be disabled | Set `DISABLE_BACKEND_AUTHENTICATION=true` in DeepLynx config for local dev |

## Links

- [DeepLynx GitHub](https://github.com/idaholab/DeepLynx) — Idaho National Lab's digital twin data warehouse
- [Istari SDK Docs](https://docs.istaridigital.com/developers/SDK/setup) — Istari Digital Python SDK
- [Integration Basics](https://docs.istaridigital.com/integrations/integration_basics) — How Istari modules work
- [DeepLynx User Guide](https://github.com/cbensonIstari/deeplynx-user-guide) — Installation, setup, and UI walkthrough
