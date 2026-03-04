# @deeplynx:pull_graph — AI Context

## Module ID
`@deeplynx:pull_graph` v0.1.0

## What It Does
Queries DeepLynx REST API to pull all records and edges from a project, enriches them with class names and relationship names, and writes structured JSON artifacts.

## Entry Point
```bash
python pull_graph.py <work_dir>
```
Reads `input.json` from `work_dir`, writes output files there.

## API Routes Used
- `GET /api/v1/organizations/{org}/projects/{proj}/records` — all records
- `GET /api/v1/organizations/{org}/projects/{proj}/edges` — all edges
- `GET /api/v1/projects/{proj}/classes` — class lookup (project-scoped, NOT org-scoped)
- `GET /api/v1/projects/{proj}/relationships` — relationship lookup

## Gotchas
- `properties` field in record responses is a JSON **string**, not an object — must `json.loads()` it
- Classes and relationships use project-scoped routes (no org in path)
- Requirement classes are "System Requirement" and "Performance Requirement" (space-separated)
