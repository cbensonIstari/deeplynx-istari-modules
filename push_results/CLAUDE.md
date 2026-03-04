# @deeplynx:push_results — AI Context

## What This Does

Creates new records and edges in DeepLynx from analysis results. Supports class assignment, tag attachment on creation, and bidirectional edge creation. Writes a receipt with all created IDs and any errors.

## IDs

| Resource | ID |
|----------|-----|
| Module | `@deeplynx:push_results` v0.1.0 |
| Organization | `1` |
| Project (Recon Drone MK-IV) | `2` |
| Data Source | `2` |

## Entry Point

```bash
python push_results.py <work_dir>
```

Reads `input.json` from `work_dir`, writes `output.json` + `push_receipt.json` there.

## Artifacts Produced

| Artifact | Description |
|----------|-------------|
| `push_receipt.json` | Created record IDs, edge IDs, and any errors |

## API Routes Used

```python
POST /api/v1/organizations/{org}/projects/{proj}/records?dataSourceId=N   # create record
POST /api/v1/organizations/{org}/projects/{proj}/edges?dataSourceId=N     # create edge
```

## Create Record Body

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

## Create Edge Body

```json
{
  "origin_id": 66,
  "destination_id": 25,
  "relationship_name": "analyzes"
}
```

## Key Files

| File | Purpose |
|------|---------|
| `push_results.py` | Entry point — iterate records, create in DeepLynx, write receipt |
| `module_manifest.json` | Istari module manifest with input/output schema |
| `example-input/input.json` | Sample input for local testing |
| `example-output/` | Real push receipt from live DeepLynx run |

## Gotchas

- **`original_id` must be unique per data source** — Duplicate causes 500 error. Use timestamps (e.g., `COMPLIANCE-PERF-007-20260304T170123`).
- **`properties` must be an object in POST** — Unlike GET responses (JSON string), POST expects a proper object.
- **`dataSourceId` query param is required** — Both records and edges need it. Omitting returns 400.
- **Tags are string names** — `tags: ["needs-review"]` in the body. Server auto-creates tags that don't exist.
- **`class_name` and `relationship_name` resolved server-side** — Pass names, not IDs. Server looks them up in the ontology.
- **Edge direction** — `"outgoing"`: new record → target. `"incoming"`: target → new record. Default is `"outgoing"`.
- **Errors are non-fatal** — If one record fails, the module continues with the rest and logs errors in the receipt.
