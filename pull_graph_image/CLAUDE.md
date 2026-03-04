# @deeplynx:pull_graph_image — AI Context

## What This Does

Queries DeepLynx graph API for a specific record, builds a networkx directed graph, computes BFS depth for color assignment, runs a force-directed layout, and renders a visual node-and-edge diagram as PNG/SVG using matplotlib.

## IDs

| Resource | ID |
|----------|-----|
| Module | `@deeplynx:pull_graph_image` v0.1.0 |
| Organization | `1` |
| Project (Recon Drone MK-IV) | `2` |
| Propulsion Subsystem (good test root) | `20` |

## Entry Point

```bash
python pull_graph_image.py <work_dir>
```

Reads `input.json` from `work_dir`, writes `output.json` + image artifacts there.

## Artifacts Produced

| Artifact | Description |
|----------|-------------|
| `graph_{name}.png` | Raster graph image (1600x1200 @ 150 DPI default) |
| `graph_{name}.svg` | Vector version for reports |
| `graph_data.json` | Raw graph topology from DeepLynx `{nodes[], links[]}` |

## API Route Used

```python
GET /api/v1/organizations/{org}/projects/{proj}/records/{id}/graph?depth=N
# Returns: {nodes: [{id, label, type}], links: [{source, target, relationshipName, edgeId}]}
# Max depth = 3
```

## Rendering Details

| Feature | Value |
|---------|-------|
| Graph library | `networkx.DiGraph` |
| Layout | `spring_layout` (k=2.5, iterations=150, seed=42) |
| Renderer | `matplotlib` with `Agg` backend (headless) |
| Root color | Purple `#7C3AED` (900px node) |
| Depth 1 | Blue `#3B82F6` (450px) |
| Depth 2 | Orange `#F97316` (450px) |
| Depth 3+ | Gray `#9CA3AF` (450px) |
| Edge labels | Relationship names in white-background badges |
| Background | `#FAFAFA` |

## Key Files

| File | Purpose |
|------|---------|
| `pull_graph_image.py` | Entry point — fetch graph, delegate to renderer |
| `rendering.py` | networkx + matplotlib rendering engine |
| `module_manifest.json` | Istari module manifest with input/output schema |
| `example-input/input.json` | Sample input for local testing |
| `example-output/` | Real rendered images from live DeepLynx run |

## Gotchas

- **Graph API max depth is 3** — `?depth=4` is silently clamped to 3.
- **Root node `type` is `"root"`** — Other nodes have class-like type strings. The module identifies root by `type == "root"`.
- **Layout seed=42** — Ensures reproducible positioning. Change seed for different arrangements.
- **Long labels auto-wrapped** — Labels > 20 chars are split at the nearest space to midpoint.
- **`matplotlib.use("Agg")`** — Must be called before any pyplot import. Enables headless rendering.
- **Filename sanitization** — Root label is sanitized (non-alphanumeric → `_`, truncated to 50 chars) for safe filenames.
