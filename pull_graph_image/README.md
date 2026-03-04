# @deeplynx:pull_graph_image — Render a DeepLynx Graph as PNG/SVG

Pull graph topology for any record in DeepLynx and render a force-directed node-and-edge diagram — without opening the DeepLynx UI or installing graphviz.

## What It Does

Queries the DeepLynx graph API for a specific record, builds a networkx directed graph, computes BFS depth for color assignment, runs a force-directed spring layout, and renders the result as PNG and/or SVG using matplotlib.

```
┌─ @deeplynx:pull_graph_image ────────────────────────────────────────────┐
│                                                                          │
│  input.json                                                              │
│  ├── deeplynx_url: "http://localhost:5000"                               │
│  ├── organization_id: 1                                                  │
│  ├── project_id: 2                                                       │
│  ├── root_record_id: 20  (Propulsion subsystem)                          │
│  ├── depth: 2                                                            │
│  └── format: "both"                                                      │
│                                                                          │
│         ↓                                                                │
│  GET /records/20/graph?depth=2 → {nodes: [...], links: [...]}            │
│         ↓                                                                │
│  Build networkx DiGraph from nodes + links                               │
│  BFS from root → assign depth (0=root, 1=neighbors, 2=second hop)       │
│  Spring layout (150 iterations, seed=42)                                 │
│  Depth-based colors: purple root → blue → orange → gray                  │
│         ↓                                                                │
│  graph_Propulsion.png     Raster image (1600x1200 @ 150 DPI)            │
│  graph_Propulsion.svg     Vector image (scalable, good for reports)      │
│  graph_data.json          Raw graph topology from DeepLynx              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Try It

```bash
# Prerequisites: DeepLynx running at localhost:5000
pip install requests networkx matplotlib Pillow

mkdir -p /tmp/image && cp example-input/input.json /tmp/image/
python pull_graph_image.py /tmp/image

# Open the rendered image
open /tmp/image/graph_*.png
```

## Input Schema

```json
{
  "deeplynx_url": "http://localhost:5000",
  "organization_id": 1,
  "project_id": 2,
  "root_record_id": 20,
  "depth": 2,
  "format": "both",
  "width": 1600,
  "height": 1200,
  "dpi": 150,
  "layout": "spring",
  "show_edge_labels": true,
  "bearer_token": null
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `deeplynx_url` | yes | — | Base URL of the DeepLynx API |
| `organization_id` | yes | — | DeepLynx organization ID |
| `project_id` | yes | — | DeepLynx project ID |
| `root_record_id` | yes | — | Record ID to center the graph on |
| `depth` | no | `2` | Edge traversal depth (1–3, max 3) |
| `format` | no | `"both"` | Output format: `"png"`, `"svg"`, or `"both"` |
| `width` | no | `1600` | Image width in pixels |
| `height` | no | `1200` | Image height in pixels |
| `dpi` | no | `150` | Image resolution |
| `layout` | no | `"spring"` | Layout algorithm: `"spring"` or `"kamada_kawai"` |
| `show_edge_labels` | no | `true` | Whether to show relationship names on edges |

## Output

```json
{
  "node_count": 20,
  "edge_count": 20,
  "root_label": "Propulsion",
  "artifacts": ["graph_Propulsion.png", "graph_Propulsion.svg", "graph_data.json"]
}
```

## Artifacts

| File | Description |
|------|-------------|
| `graph_{name}.png` | Raster graph image with depth-colored nodes and labeled edges |
| `graph_{name}.svg` | Vector version of the same graph (scalable, embeddable in reports) |
| `graph_data.json` | Raw graph topology from DeepLynx (`{nodes[], links[]}`) |

## Rendering Details

| Feature | Implementation |
|---------|---------------|
| Graph library | networkx `DiGraph` |
| Layout | `spring_layout` (force-directed, 150 iterations, k=2.5, seed=42) |
| Rendering | matplotlib with `Agg` backend (headless) |
| Root color | Purple `#7C3AED` (900px node) |
| Depth 1 | Blue `#3B82F6` (450px nodes) |
| Depth 2 | Orange `#F97316` (450px nodes) |
| Depth 3+ | Gray `#9CA3AF` (450px nodes) |
| Edge labels | Relationship names in white-background badges |
| Label wrapping | Long labels auto-wrapped at nearest space to midpoint |
| Background | Light gray `#FAFAFA` |

The color scheme matches the DeepLynx UI's visual conventions. Layout uses networkx's `spring_layout` (a Fruchterman-Reingold variant), which produces results similar to DeepLynx UI's Sigma.js + ForceAtlas2.

## Example Output

See [`example-output/`](example-output/) for a real graph rendered from the Propulsion subsystem (20 nodes, 20 edges) in the Recon Drone MK-IV project.

## Gotchas

- **Graph API max depth is 3** — `?depth=4` is silently clamped to 3. Request depth 2 for a focused view, depth 3 for the full neighborhood.
- **Root node `type` is `"root"`** — Other nodes have class-like type strings (e.g., `"Component"`, `"System Requirement"`). The module identifies root by `type == "root"`.
- **Layout is deterministic** — `seed=42` ensures the same graph always renders to the same positions. Change the seed if you want a different arrangement.
- **Matplotlib `Agg` backend** — The module uses headless rendering. No display server or GUI toolkit required.
