# Use Case: Check Thermal Compliance — AI Context

## What This Does

End-to-end compliance checking against a DeepLynx graph: pull records + edges, render the Propulsion subsystem graph, run automated PASS/FAIL checks by walking requirement → simulation edges, and push failure records back to DeepLynx tagged `needs-review`.

## IDs

| Resource | ID |
|----------|----|
| DeepLynx Organization | `1` |
| DeepLynx Project (Recon Drone MK-IV) | `2` |
| DeepLynx Data Source | `2` |
| Propulsion Subsystem Record | `20` |

## DeepLynx Instance

| Setting | Value |
|---------|-------|
| API URL | `http://localhost:5000` |
| UI URL | `http://localhost:3100` |
| Auth | Disabled (`DISABLE_BACKEND_AUTHENTICATION=true`) |
| Data | 65 records, 84 edges, 19 classes, 15 relationships, 6 tags |

## Modules Used (4 inner loops)

| Module | Function | What It Does |
|--------|----------|-------------|
| `@deeplynx:pull_graph` | `pull_graph` | Fetches all records + edges, enriches with class/relationship names |
| `@deeplynx:pull_graph_image` | `pull_graph_image` | Renders graph as PNG/SVG via networkx + matplotlib |
| `compliance_checks.py` | `run_compliance_checks` | Walks requirement edges to find linked simulations, checks PASS/FAIL |
| `@deeplynx:push_results` | `push_results` | Creates compliance records in DeepLynx with tags |

## Artifacts Produced

| Artifact | Source | Description |
|----------|--------|-------------|
| `graph_records.json` | pull_graph | 65 records with parsed properties and class names |
| `graph_edges.json` | pull_graph | 84 edges with relationship names and record names |
| `requirements.json` | pull_graph | 15 requirements filtered from records |
| `graph_summary.md` | pull_graph | Markdown summary with class/relationship counts |
| `graph_Propulsion.png` | pull_graph_image | 20-node graph centered on Propulsion subsystem |
| `graph_Propulsion.svg` | pull_graph_image | Vector version of the graph |
| `compliance_report.json` | compliance_checks | 15 check results with details |
| `compliance_report.md` | compliance_checks | Human-readable compliance report |
| `push_receipt.json` | push_results | Created record and edge IDs |

## Compliance Check Results

| Status | Count | Details |
|--------|-------|---------|
| PASS | 4 | FEA-001 (structural), CFD-001 (drag), CFD-002 (speed), CFD-003 (wind) |
| FAIL | 1 | PERF-007 (thermal) — ANSYS Icepak shows 82°C junction temp, status MARGINAL |
| UNCHECKED | 10 | No simulation linked to these requirements |

## Key Files

| File | Purpose |
|------|---------|
| `check_thermal_compliance.py` | Main orchestration script — runs all 4 steps |
| `compliance_checks.py` | Reusable compliance check library |
| `example-output/compliance_report.md` | Pre-computed report showing the FAIL |
| `example-output/graph_Propulsion.png` | Pre-rendered Propulsion graph |

## API Routes Used

```python
# Pull (all via shared/deeplynx_client.py)
GET /api/v1/organizations/1/projects/2/records          # all records
GET /api/v1/organizations/1/projects/2/edges            # all edges
GET /api/v1/projects/2/classes                           # class lookup
GET /api/v1/projects/2/relationships                     # relationship lookup
GET /api/v1/organizations/1/projects/2/records/20/graph?depth=2  # Propulsion graph

# Push
POST /api/v1/organizations/1/projects/2/records?dataSourceId=2  # create record
```

## Gotchas

- **Properties field is a JSON string**: Record responses have `properties` as a string — must `json.loads()` before accessing values
- **Class/relationship/tag routes are project-scoped**: Use `/projects/{id}/classes`, NOT `/organizations/{org}/projects/{id}/classes`
- **`original_id` must be unique per data source**: Use timestamps in IDs when pushing records (e.g., `COMPLIANCE-PERF-007-20260304T170123`)
- **Duplicate original_id causes 500 error**: If you re-run without unique timestamps, the push will fail
- **Graph API max depth is 3**: `GET /records/{id}/graph?depth=4` will be clamped to 3
- **Tags as string names**: `CreateRecordRequestDto` accepts `tags: ["needs-review"]` as string names — server resolves to IDs
- **Propulsion lookup**: The `find_propulsion_record()` function filters by `class_name == "Subsystem"` to avoid matching "PERF-002: Propulsion Efficiency" (a requirement, not the subsystem)
