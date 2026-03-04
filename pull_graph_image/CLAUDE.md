# @deeplynx:pull_graph_image — AI Context

## Module ID
`@deeplynx:pull_graph_image` v0.1.0

## What It Does
Queries DeepLynx graph API for a specific record, computes force-directed layout with networkx, renders a visual node-and-edge diagram as PNG/SVG using matplotlib.

## Entry Point
```bash
python pull_graph_image.py <work_dir>
```

## API Route Used
- `GET /api/v1/organizations/{org}/projects/{proj}/records/{id}/graph?depth=N`
- Returns `{nodes: [{id, label, type}], links: [{source, target, relationshipName, edgeId}]}`
- Max depth = 3

## Rendering Details
- Uses `networkx.spring_layout` (force-directed, analogous to DeepLynx UI's ForceAtlas2)
- BFS from root to compute depth-based coloring: purple (root), blue (1), orange (2), gray (3+)
- Root node larger (900) than others (450)
- Edge labels show relationship names
- `matplotlib.use("Agg")` for headless rendering

## Gotchas
- `type` field on root node is "root"; other nodes have class-like type strings
- Layout seed=42 for reproducible positioning
- Long labels auto-wrapped at nearest space to midpoint
