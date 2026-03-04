# Helpful Hints for AI

Context for AI assistants (Claude, Copilot, etc.) working with this repo.

## DeepLynx Instance

| Setting | Value |
|---------|-------|
| API URL | `http://localhost:5000` |
| UI URL | `http://localhost:3100` |
| Auth | Disabled (`DISABLE_BACKEND_AUTHENTICATION=true`) |
| Runtime | Docker Compose — .NET 10.0 backend + PostgreSQL 18 |

## IDs

| Resource | ID |
|----------|-----|
| Organization | `1` |
| Project (Recon Drone MK-IV) | `2` |
| Data Source | `2` |
| Propulsion Subsystem Record | `20` |

## Sample Data (Recon Drone MK-IV)

| Metric | Count |
|--------|-------|
| Records | 65 |
| Edges | 84 |
| Classes | 19 |
| Relationship types | 15 |
| Tags | 6 (`critical-path`, `needs-review`, `flight-tested`, `COTS`, `custom-design`, `marginal`) |

## URL Structure

DeepLynx API routes follow two patterns:

```
# Records and edges — org + project scoped
/api/v1/organizations/{org}/projects/{proj}/records
/api/v1/organizations/{org}/projects/{proj}/edges
/api/v1/organizations/{org}/projects/{proj}/records/{id}/graph?depth=N

# Classes, relationships, tags — project scoped only
/api/v1/projects/{proj}/classes
/api/v1/projects/{proj}/relationships
/api/v1/projects/{proj}/tags
```

## Modules in This Repo

| Module | Function | Entry Point |
|--------|----------|-------------|
| `@deeplynx:pull_graph` | `pull_graph` | `python pull_graph/pull_graph.py <work_dir>` |
| `@deeplynx:pull_graph_image` | `pull_graph_image` | `python pull_graph_image/pull_graph_image.py <work_dir>` |
| `@deeplynx:push_results` | `push_results` | `python push_results/push_results.py <work_dir>` |

## Key Integration Functions

| Function | Tool | OS | Purpose |
|----------|------|----|---------|
| `@deeplynx:pull_graph` | `deeplynx` v2.0.0 | Ubuntu 22.04 | Fetch records + edges → enriched JSON + requirements + summary |
| `@deeplynx:pull_graph_image` | `deeplynx` v2.0.0 | Ubuntu 22.04 | Fetch graph topology → force-directed layout → PNG/SVG image |
| `@deeplynx:push_results` | `deeplynx` v2.0.0 | Ubuntu 22.04 | Create records + edges with tags → push receipt |

## SDK Quick Reference

```python
from shared import DeepLynxClient, read_input, write_output, write_artifact

# Initialize client
client = DeepLynxClient(
    base_url="http://localhost:5000",
    org_id=1,
    project_id=2,
    bearer_token=None,  # omit when auth disabled
)

# Pull operations
client.get_all_records()                        # → list[dict]
client.get_all_edges()                          # → list[dict]
client.get_record(record_id)                    # → dict
client.get_record_graph(record_id, depth=2)     # → {nodes[], links[]}
client.get_classes()                            # → list[dict]
client.get_relationships()                      # → list[dict]
client.get_tags()                               # → list[dict]

# Push operations
client.create_record(data_source_id, {
    "name": "...",
    "description": "...",
    "original_id": "unique-id",
    "properties": {"key": "value"},
    "class_name": "Thermal Analysis",
    "tags": ["needs-review"],
})                                              # → dict (created record)

client.create_edge(data_source_id, {
    "origin_id": 66,
    "destination_id": 25,
    "relationship_name": "analyzes",
})                                              # → dict (created edge)

# I/O contract (file-based, Istari module pattern)
input_data = read_input(work_dir)               # reads work_dir/input.json
write_output({"key": "val"}, work_dir)          # writes work_dir/output.json
write_artifact("file.json", content, work_dir)  # writes work_dir/file.json
```

## Graph Response Format

```json
{
  "nodes": [
    {"id": 20, "label": "Propulsion", "type": "root"},
    {"id": 7,  "label": "T-Motor U8 II", "type": "Component"}
  ],
  "links": [
    {"source": 20, "target": 7, "relationshipName": "contains", "edgeId": 42}
  ]
}
```

- `type` is `"root"` for the queried record; other nodes have class-like type strings
- Max traversal depth is 3 — deeper values are clamped

## Ontology Classes

| Class | Count | Description |
|-------|-------|-------------|
| System Requirement | 8 | SYS-001 through SYS-008 |
| Performance Requirement | 7 | PERF-001 through PERF-007 |
| Subsystem | 6 | Airframe, Propulsion, Power, Payload, Avionics, Comms |
| Component | 12 | Motors, batteries, props, wing spar, etc. |
| Thermal Analysis | 1 | THERM-001: Electronics Bay Summer |
| FEA Result | 1 | FEA-001: Wing Spar 4g Load |
| CFD Result | 3 | CFD-001/002/003 |
| Material | 3 | Toray T700, Ti-6Al-4V, Al 6061-T6 |
| Risk | 3 | Battery, GPS jamming, motor failure |
| Trade Study | 3 | Motor, battery, material selection |

## Gotchas

| Issue | Details |
|-------|---------|
| **Properties is a JSON string** | Record responses return `properties` as a string, not an object — must `json.loads()` |
| **Class/relationship routes are project-scoped** | Use `/projects/{id}/classes`, NOT `/organizations/{org}/projects/{id}/classes` |
| **`original_id` must be unique per data source** | Re-running push with same ID causes 500 error — use timestamps |
| **Graph API max depth is 3** | `?depth=4` is silently clamped to 3 |
| **Tags as string names** | Create requests accept `tags: ["name"]` — server resolves to tag IDs |
| **Python 3.9 compatibility** | Use `from __future__ import annotations` for `str | None` syntax |
| **Propulsion lookup** | Filter by `class_name == "Subsystem"` to avoid matching PERF-002 (a requirement with "Propulsion" in the name) |
| **Requirement classes** | Two separate classes: `"System Requirement"` and `"Performance Requirement"` (space-separated) |
