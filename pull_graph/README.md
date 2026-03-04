# @deeplynx:pull_graph — Pull Records and Edges from DeepLynx

Pull all records, edges, and ontology from a DeepLynx project into structured JSON artifacts — without opening the DeepLynx UI or exporting CSVs manually.

## What It Does

Queries four DeepLynx API endpoints (records, edges, classes, relationships), enriches each record with its human-readable class name and parses the `properties` JSON string into a proper object, enriches each edge with relationship and record names, then writes everything as structured artifacts.

```
┌─ @deeplynx:pull_graph ──────────────────────────────────────────────────┐
│                                                                          │
│  input.json                                                              │
│  ├── deeplynx_url: "http://localhost:5000"                               │
│  ├── organization_id: 1                                                  │
│  ├── project_id: 2                                                       │
│  └── record_types: ["System Requirement"] (optional filter)              │
│                                                                          │
│         ↓                                                                │
│  GET /records → GET /edges → GET /classes → GET /relationships           │
│         ↓                                                                │
│  Enrich records with class_name, parse properties JSON string            │
│  Enrich edges with relationship_name + origin/destination names          │
│  Filter requirements (System Requirement + Performance Requirement)      │
│         ↓                                                                │
│  graph_records.json    65 records with class names + parsed properties   │
│  graph_edges.json      84 edges with relationship + record names         │
│  requirements.json     15 requirements filtered from records             │
│  graph_summary.md      Class/relationship/tag counts                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Try It

```bash
# Prerequisites: DeepLynx running at localhost:5000
pip install requests

mkdir -p /tmp/pull && cp example-input/input.json /tmp/pull/
python pull_graph.py /tmp/pull

# Check results
cat /tmp/pull/graph_summary.md
python -c "import json; d=json.load(open('/tmp/pull/graph_records.json')); print(f'{len(d)} records')"
```

## Input Schema

```json
{
  "deeplynx_url": "http://localhost:5000",
  "organization_id": 1,
  "project_id": 2,
  "record_types": ["System Requirement", "Component"],
  "bearer_token": null
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `deeplynx_url` | yes | Base URL of the DeepLynx API |
| `organization_id` | yes | DeepLynx organization ID |
| `project_id` | yes | DeepLynx project ID |
| `record_types` | no | Class names to filter records by. Omit to pull all. |
| `bearer_token` | no | Auth token (omit if auth is disabled) |

## Output

```json
{
  "record_count": 65,
  "edge_count": 84,
  "class_count": 19,
  "requirement_count": 15,
  "artifacts": ["graph_records.json", "graph_edges.json", "requirements.json", "graph_summary.md"]
}
```

## Artifacts

| File | Description |
|------|-------------|
| `graph_records.json` | All records enriched with `class_name` and parsed `properties` |
| `graph_edges.json` | All edges enriched with `relationship_name`, `origin_name`, `destination_name` |
| `requirements.json` | Records filtered to System Requirement + Performance Requirement classes |
| `graph_summary.md` | Markdown summary — record counts by class, edge counts by relationship, tags |

## Example Output

See [`example-output/`](example-output/) for real output captured from a live DeepLynx instance with the Recon Drone MK-IV project (65 records, 84 edges, 19 classes).

## API Routes Used

```
GET /api/v1/organizations/{org}/projects/{proj}/records
GET /api/v1/organizations/{org}/projects/{proj}/edges
GET /api/v1/projects/{proj}/classes            ← project-scoped, no org
GET /api/v1/projects/{proj}/relationships      ← project-scoped, no org
```

## Gotchas

- **Properties is a JSON string** — Record `properties` field comes back as a string, not an object. The module runs `json.loads()` on it automatically.
- **Class/relationship routes are project-scoped** — Use `/projects/{id}/classes`, NOT `/organizations/{org}/projects/{id}/classes`. Getting this wrong returns 404.
- **Requirement classes have spaces** — `"System Requirement"` and `"Performance Requirement"`, not camelCase or hyphenated.
