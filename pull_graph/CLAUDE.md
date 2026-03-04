# @deeplynx:pull_graph — AI Context

## What This Does

Queries DeepLynx REST API to pull all records and edges from a project, enriches them with class/relationship names, parses the properties JSON string into a dict, filters requirements, and writes structured JSON artifacts.

## IDs

| Resource | ID |
|----------|-----|
| Module | `@deeplynx:pull_graph` v0.1.0 |
| Organization | `1` |
| Project (Recon Drone MK-IV) | `2` |

## Entry Point

```bash
python pull_graph.py <work_dir>
```

Reads `input.json` from `work_dir`, writes `output.json` + artifacts there.

## Artifacts Produced

| Artifact | Description |
|----------|-------------|
| `graph_records.json` | All records enriched with `class_name` and parsed `properties` |
| `graph_edges.json` | All edges enriched with `relationship_name`, `origin_name`, `destination_name` |
| `requirements.json` | Records filtered to `System Requirement` + `Performance Requirement` classes |
| `graph_summary.md` | Markdown summary with class counts, relationship counts, tags |

## API Routes Used

```python
GET /api/v1/organizations/{org}/projects/{proj}/records      # all records
GET /api/v1/organizations/{org}/projects/{proj}/edges        # all edges
GET /api/v1/projects/{proj}/classes                           # class lookup (project-scoped)
GET /api/v1/projects/{proj}/relationships                     # relationship lookup (project-scoped)
```

## Key Files

| File | Purpose |
|------|---------|
| `pull_graph.py` | Main entry point — fetch, enrich, filter, write artifacts |
| `module_manifest.json` | Istari module manifest with input/output schema |
| `example-input/input.json` | Sample input for local testing |
| `example-output/` | Real output from live DeepLynx run |

## Gotchas

- **Properties field is a JSON string** — Record responses have `properties` as a string. Module auto-parses with `json.loads()`.
- **Class/relationship routes are project-scoped** — Use `/projects/{id}/classes`, NOT `/organizations/{org}/projects/{id}/classes`. Getting this wrong returns 404.
- **Requirement classes have spaces** — `"System Requirement"` and `"Performance Requirement"`, not camelCase.
- **Records can be filtered by `record_types`** — Optional input field; omit to pull all records.
