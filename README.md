# DeepLynx ↔ Istari Integration Modules

Istari integration modules for [DeepLynx](https://github.com/idaholab/DeepLynx), Idaho National Lab's digital twin data warehouse. These modules let you pull data, render graph visualizations, and push analysis results between DeepLynx and Istari.

## Modules

### `@deeplynx:pull_graph`
Pull records, edges, and ontology from a DeepLynx project into structured JSON artifacts.

- **Input:** DeepLynx URL, org/project IDs, optional class filter
- **Output:** `graph_records.json`, `graph_edges.json`, `requirements.json`, `graph_summary.md`

### `@deeplynx:pull_graph_image`
Pull graph topology from DeepLynx and render a visual node-and-edge diagram as PNG/SVG.

- **Input:** DeepLynx URL, root record ID, depth (1-3), format, layout options
- **Output:** `graph_{name}.png`, `graph_{name}.svg`, `graph_data.json`

Uses networkx for graph structure and matplotlib for rendering, replicating the DeepLynx UI's force-directed layout with depth-based coloring (purple root → blue → orange → gray).

### `@deeplynx:push_results`
Push analysis results back to DeepLynx as new records with edges and tags.

- **Input:** records to create (name, properties, class, tags, edges)
- **Output:** `push_receipt.json` with created record/edge IDs

## Use Cases

### [`check-thermal-compliance`](use-cases/check-thermal-compliance/)
End-to-end workflow: pull drone design data from DeepLynx → render Propulsion subsystem graph → run compliance checks against thermal requirements → push FAIL results back to DeepLynx.

## Quick Start

```bash
# Prerequisites: DeepLynx running (see github.com/idaholab/DeepLynx)
pip install requests networkx matplotlib Pillow

# Pull all records and edges
mkdir -p /tmp/pull && cp pull_graph/example-input/input.json /tmp/pull/
python pull_graph/pull_graph.py /tmp/pull

# Render a graph image
mkdir -p /tmp/image && cp pull_graph_image/example-input/input.json /tmp/image/
python pull_graph_image/pull_graph_image.py /tmp/image

# Push results back
mkdir -p /tmp/push && cp push_results/example-input/input.json /tmp/push/
python push_results/push_results.py /tmp/push

# Or run the full compliance loop
python use-cases/check-thermal-compliance/check_thermal_compliance.py
```

## Architecture

```
┌─── Outer Loop: Istari ── version · extract · simulate · check ──────┐
│                                                                       │
│  ┌─ @deeplynx:pull_graph ─────────────────────────────────────────┐  │
│  │ Query DeepLynx API → records + edges → structured JSON          │  │
│  └─────────────────────────────┬───────────────────────────────────┘  │
│                                │                                      │
│  ┌─ @deeplynx:pull_graph_image ┴───────────────────────────────────┐ │
│  │ Query graph API → force-directed layout → render PNG/SVG         │ │
│  └─────────────────────────────┬───────────────────────────────────┘ │
│                                │                                      │
│  ┌─ analysis / simulation ─────┴───────────────────────────────────┐ │
│  │ (existing Istari modules or custom scripts)                      │ │
│  └─────────────────────────────┬───────────────────────────────────┘ │
│                                │                                      │
│  ┌─ @deeplynx:push_results ───┴───────────────────────────────────┐ │
│  │ Write results back to DeepLynx as new records + edges            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
deeplynx-istari-modules/
├── shared/                          # Shared DeepLynx API client
│   ├── deeplynx_client.py           # HTTP client wrapper
│   └── utils.py                     # I/O helpers (read_input, write_output, write_artifact)
├── pull_graph/                      # @deeplynx:pull_graph module
│   ├── module_manifest.json
│   ├── pull_graph.py
│   └── example-input/output/
├── pull_graph_image/                # @deeplynx:pull_graph_image module
│   ├── module_manifest.json
│   ├── pull_graph_image.py
│   ├── rendering.py                 # networkx + matplotlib rendering engine
│   └── example-input/output/
├── push_results/                    # @deeplynx:push_results module
│   ├── module_manifest.json
│   ├── push_results.py
│   └── example-input/output/
└── use-cases/
    └── check-thermal-compliance/    # End-to-end example
        ├── check_thermal_compliance.py
        ├── compliance_checks.py
        └── example-output/
```

## DeepLynx API Reference

| Operation | Endpoint |
|-----------|----------|
| List records | `GET /api/v1/organizations/{org}/projects/{proj}/records` |
| Get graph | `GET .../records/{id}/graph?depth=N` |
| Create record | `POST .../records?dataSourceId=N` |
| Create edge | `POST .../edges?dataSourceId=N` |
| List classes | `GET /api/v1/projects/{proj}/classes` |
| List relationships | `GET /api/v1/projects/{proj}/relationships` |
| List tags | `GET /api/v1/projects/{proj}/tags` |
