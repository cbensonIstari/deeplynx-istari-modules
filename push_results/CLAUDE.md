# @deeplynx:push_results — AI Context

## Module ID
`@deeplynx:push_results` v0.1.0

## What It Does
Creates new records and edges in DeepLynx from analysis results. Supports tag attachment and bidirectional edge creation.

## Entry Point
```bash
python push_results.py <work_dir>
```

## API Routes Used
- `POST /api/v1/organizations/{org}/projects/{proj}/records?dataSourceId=N` — create record
- `POST /api/v1/organizations/{org}/projects/{proj}/edges?dataSourceId=N` — create edge

## Create Record Body
```json
{
  "name": "...",
  "description": "...",
  "original_id": "unique-id",
  "properties": { "key": "value" },
  "class_name": "Thermal Analysis",
  "tags": ["needs-review"]
}
```
- `original_id` is required and must be unique per data source
- `class_name` is resolved server-side (alternative: `class_id`)
- `tags` is a list of tag name strings (server creates/resolves them)

## Create Edge Body
```json
{
  "origin_id": 66,
  "destination_id": 25,
  "relationship_name": "analyzes"
}
```
- `relationship_name` is resolved server-side (alternative: `relationship_id`)

## Gotchas
- `properties` must be a JSON **object** (not a string) in create requests
- `dataSourceId` is a required query parameter for all create operations
- Tags passed as string names are auto-resolved by the server
