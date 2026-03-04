# @deeplynx:push_results — Push Analysis Results Back to DeepLynx

Write analysis results back to DeepLynx as new records with edges and tags — without opening the DeepLynx UI or copy-pasting into forms.

## What It Does

Takes an array of record specifications (name, properties, class, tags, edges), creates each record in DeepLynx via the REST API, creates edges to link them to existing records, and writes a receipt with all created IDs.

```
┌─ @deeplynx:push_results ────────────────────────────────────────────────┐
│                                                                          │
│  input.json                                                              │
│  ├── deeplynx_url: "http://localhost:5000"                               │
│  ├── organization_id: 1                                                  │
│  ├── project_id: 2                                                       │
│  ├── data_source_id: 2                                                   │
│  └── records: [                                                          │
│        {                                                                 │
│          name: "Compliance: PERF-007 FAIL"                               │
│          class_name: "Thermal Analysis"                                  │
│          tags: ["needs-review"]                                          │
│          link_to: [{record_id: 25, relationship_name: "analyzes"}]       │
│        }                                                                 │
│      ]                                                                   │
│                                                                          │
│         ↓                                                                │
│  For each record:                                                        │
│    POST /records?dataSourceId=2  → create record with tags               │
│    POST /edges?dataSourceId=2    → create edges to existing records      │
│         ↓                                                                │
│  push_receipt.json    Created record IDs, edge IDs, any errors           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Try It

```bash
# Prerequisites: DeepLynx running at localhost:5000
pip install requests

mkdir -p /tmp/push && cp example-input/input.json /tmp/push/
python push_results.py /tmp/push

# Check the receipt
cat /tmp/push/push_receipt.json
```

## Input Schema

```json
{
  "deeplynx_url": "http://localhost:5000",
  "organization_id": 1,
  "project_id": 2,
  "data_source_id": 2,
  "records": [
    {
      "name": "Compliance Check: PERF-007 Thermal Envelope FAIL",
      "description": "Automated compliance check result",
      "original_id": "COMPLIANCE-PERF-007-20260304T170123",
      "properties": {
        "status": "FAIL",
        "requirement_id": "PERF-007",
        "simulation": "THERM-001",
        "max_junction_temp": "82 C"
      },
      "class_name": "Thermal Analysis",
      "tags": ["needs-review"],
      "link_to": [
        {
          "record_id": 25,
          "relationship_name": "analyzes",
          "direction": "outgoing"
        }
      ]
    }
  ],
  "bearer_token": null
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `deeplynx_url` | yes | Base URL of the DeepLynx API |
| `organization_id` | yes | DeepLynx organization ID |
| `project_id` | yes | DeepLynx project ID |
| `data_source_id` | yes | Data source to associate new records with |
| `records` | yes | Array of records to create |
| `records[].name` | yes | Record display name |
| `records[].description` | yes | Record description |
| `records[].original_id` | yes | Unique ID within the data source (use timestamps) |
| `records[].properties` | yes | Key-value properties (object, not string) |
| `records[].class_name` | no | Ontology class name (server-resolved) |
| `records[].tags` | no | Tag names to attach (server-resolved) |
| `records[].link_to` | no | Edges to create to existing records |
| `records[].link_to[].record_id` | yes | Target record ID |
| `records[].link_to[].relationship_name` | yes | Relationship name (server-resolved) |
| `records[].link_to[].direction` | no | `"outgoing"` (default) or `"incoming"` |

## Output

```json
{
  "records_created": 2,
  "edges_created": 2,
  "errors": 0,
  "artifacts": ["push_receipt.json"]
}
```

## Artifacts

| File | Description |
|------|-------------|
| `push_receipt.json` | Created record IDs, edge IDs, and any errors encountered |

## Example Output

See [`example-output/`](example-output/) for a real push receipt from creating compliance check records in the Recon Drone MK-IV project.

## API Routes Used

```
POST /api/v1/organizations/{org}/projects/{proj}/records?dataSourceId=N
POST /api/v1/organizations/{org}/projects/{proj}/edges?dataSourceId=N
```

### Create Record Body

```json
{
  "name": "Compliance Check: PERF-007",
  "description": "Automated compliance check result",
  "original_id": "COMPLIANCE-PERF-007-20260304T170123",
  "properties": {"status": "FAIL", "max_junction_temp": "82 C"},
  "class_name": "Thermal Analysis",
  "tags": ["needs-review"]
}
```

### Create Edge Body

```json
{
  "origin_id": 66,
  "destination_id": 25,
  "relationship_name": "analyzes"
}
```

## Gotchas

- **`original_id` must be unique per data source** — Duplicate `original_id` causes a 500 error. Use timestamps in IDs (e.g., `COMPLIANCE-PERF-007-20260304T170123`).
- **`properties` must be an object in create requests** — Unlike GET responses (where it's a string), POST requests expect a proper JSON object.
- **`dataSourceId` is required** — It's a query parameter on both `POST /records` and `POST /edges`. Omitting it returns 400.
- **Tags are string names** — Pass `tags: ["needs-review"]` in the create body. The server resolves names to IDs, creating the tag if it doesn't exist.
- **`class_name` and `relationship_name` are resolved server-side** — You can pass names instead of IDs. The server looks them up in the project's ontology.
- **Edge direction** — `"outgoing"` means the new record is the origin; `"incoming"` means it's the destination. Default is `"outgoing"`.
