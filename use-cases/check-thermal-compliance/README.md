# Use Case: Does My Design Pass Thermal Compliance? — Without Leaving Istari

## Intent

I have a drone design tracked in **DeepLynx** — requirements, subsystems, components, simulation results, and risks all stored as graph records. A systems engineer just updated the motor power draw and added a new thermal requirement. I want to know: **does the current design still pass?** I don't want to log into DeepLynx, manually export CSVs, cross-reference spreadsheets, or send emails asking "what changed?" I want to pull the latest data, see the graph, run compliance checks, and push the results back — all from one script.

## The Old Way

```
 DeepLynx                                         Istari / Analysis
 (Graph DB)                                        (Engineer's tools)
     |                                                 |
     v                                                 |
 Systems engineer updates                              |
 motor specs + adds thermal req                        |
     |                                                 |
     +--- manual CSV export --->  email/Slack -------->|
     |                                                 v
     |                                          Engineer downloads CSV,
     |                                          opens spreadsheet,
     |                                          manually checks each req
     |                                                 |
     |                                                 v
     |                                          Types up results in email
     |                                                 |
     |<-------- email with findings (days later) ------+
     v                                                 |
 Engineer manually creates                             |
 records in DeepLynx                                   |
 with compliance status                                |
```

**Problems:** Manual CSV handoffs. Copy-paste between systems. No traceability. Results in DeepLynx are always stale. When a requirement changes, the analysis team doesn't know for days. By the time they check, the design has moved on.

## The New Way (with Istari + DeepLynx)

```
┌─── Outer Loop: Istari ── pull · check · visualize · push ────────────┐
│                                                                       │
│   ┌─ @deeplynx:pull_graph ────────────────────────────────────────┐  │
│   │ Query DeepLynx → 65 records + 84 edges → structured JSON      │  │
│   └────────────────────────────────┬───────────────────────────────┘  │
│                                    │                                  │
│   ┌─ @deeplynx:pull_graph_image ──┴───────────────────────────────┐  │
│   │ Fetch Propulsion graph → force-directed layout → render PNG    │  │
│   └────────────────────────────────┬───────────────────────────────┘  │
│                                    │                                  │
│   ┌─ compliance_checks.py ────────┴───────────────────────────────┐  │
│   │ Compare simulation results against requirement thresholds      │  │
│   │ → 4 PASS / 1 FAIL / 10 UNCHECKED                              │  │
│   └────────────────────────────────┬───────────────────────────────┘  │
│                                    │                                  │
│   ┌─ @deeplynx:push_results ──────┴───────────────────────────────┐  │
│   │ Write compliance records back to DeepLynx + tag needs-review   │  │
│   └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│   Graph image · Compliance report · Push receipt                      │
└───────────────────────────────────────────────────────────────────────┘
```

The engineer runs one script. DeepLynx stays current. Both systems tell the same story.

## Tools Used

| Tool | Role |
|------|------|
| **Istari Platform** | Outer loop — orchestrates the workflow, stores versioned artifacts, shares results |
| **DeepLynx Pull** (`@deeplynx:pull_graph`) | Inner loop 1 — queries DeepLynx REST API, exports records + edges as structured JSON |
| **DeepLynx Graph Image** (`@deeplynx:pull_graph_image`) | Inner loop 2 — fetches graph topology, renders visual node-and-edge diagram as PNG/SVG |
| **Compliance checker** (`compliance_checks.py`) | Inner loop 3 — walks requirement → simulation edges and checks PASS/FAIL/UNCHECKED |
| **DeepLynx Push** (`@deeplynx:push_results`) | Inner loop 4 — writes compliance results back to DeepLynx as new records with `needs-review` tag |

## K-Script

| Step | Interaction / Process | Unobservable Actions or Assumptions |
|------|----------------------|-------------------------------------|
| 1 | **Systems Engineer:** Updates the Recon Drone MK-IV project in DeepLynx — changes motor power draw from 450W to 520W, adds thermal requirement "Motor temp shall not exceed 85°C" | Uses the DeepLynx UI at `localhost:3100`; creates new `SystemRequirement` record with edge to Propulsion subsystem |
| 2 | **Thermal Engineer:** Opens Istari, navigates to the "Drone Thermal Analysis" system | Wants to verify the motor assembly still meets thermal limits after the power draw update |
| 3 | **Thermal Engineer:** Runs `check_thermal_compliance.py` | Script orchestrates all four modules in sequence — no manual steps |
| 4 | **System:** `@deeplynx:pull_graph` queries DeepLynx API — fetches all records, edges, classes, and relationships | Calls `GET /records`, `GET /edges`, `GET /classes`, `GET /relationships`; enriches records with class names; parses properties JSON strings |
| 5 | **System:** Pull complete — 65 records, 84 edges, 15 requirements exported to JSON | Artifacts: `graph_records.json`, `graph_edges.json`, `requirements.json`, `graph_summary.md` |
| 6 | **System:** `@deeplynx:pull_graph_image` fetches graph topology for the Propulsion subsystem | Calls `GET /records/20/graph?depth=2` — gets 20 nodes and 20 edges centered on Propulsion |
| 7 | **System:** Agent runs force-directed layout (networkx spring layout, 150 iterations) and renders to PNG + SVG | Colors: purple root, blue depth-1, orange depth-2; edge labels show relationship names |
| 8 | **System:** Graph image complete — shows motor, battery, propeller, requirements, risks, and trade studies all connected to Propulsion | Artifacts: `graph_Propulsion.png`, `graph_Propulsion.svg`, `graph_data.json` |
| 9 | **System:** `compliance_checks.py` walks each requirement's edges to find linked simulations | For each requirement, checks if a Thermal Analysis, FEA Result, or CFD Result record is connected via `validates`/`satisfies`/`analyzes` edges |
| 10 | **System:** Compliance check results: 4 PASS, 1 FAIL, 10 UNCHECKED | PERF-007 (Thermal Envelope) FAILS — simulation shows max junction temp 82°C with status MARGINAL; other sims (FEA, CFD) PASS |
| 11 | **Thermal Engineer:** Reviews `compliance_report.md` — sees PERF-007 flagged | Report shows: ANSYS Icepak simulation at 50°C ambient → 82°C hotspot on flight controller CPU, margin only 3°C |
| 12 | **Thermal Engineer:** Opens `graph_Propulsion.png` — sees the full context | Motor, battery, propulsion system, thermal requirement, risk items all visible in one diagram |
| 13 | **System:** `@deeplynx:push_results` creates two records in DeepLynx — one for the failed check and one compliance summary | Both tagged `needs-review`; creates via `POST /records` with tag names in the body |
| 14 | **Systems Engineer:** Sees `needs-review` tag in DeepLynx — opens the compliance check record | Sees: PERF-007 FAIL, ANSYS Icepak, hotspot at flight controller CPU, 82°C junction temp |
| 15 | **Systems Engineer:** Decides to add a heat sink to the avionics bay — creates new component in DeepLynx | Design change captured in the graph immediately |
| 16 | **Thermal Engineer:** Re-runs `check_thermal_compliance.py` after the re-simulation | New pull captures the updated graph; compliance report versioned in Istari alongside the old one |

## Expected Results

### Compliance Check Results

| Requirement | ID | Priority | Simulation | Status |
|-------------|-----|----------|------------|--------|
| PERF-007: Thermal Envelope | PERF-007 | normal | THERM-001: Electronics Bay Summer | **FAIL** |
| PERF-001: Structural Load Factor | PERF-001 | normal | FEA-001: Wing Spar 4g Load | PASS |
| PERF-004: Drag Coefficient | PERF-004 | normal | CFD-001: Cruise Aerodynamics | PASS |
| SYS-003: Maximum Speed | SYS-003 | high | CFD-002: Max Speed Run | PASS |
| SYS-007: Wind Resistance | SYS-007 | medium | CFD-003: 40 km/h Crosswind | PASS |
| SYS-001: Maximum Takeoff Weight | SYS-001 | critical | — | UNCHECKED |
| SYS-002: Operational Range | SYS-002 | critical | — | UNCHECKED |
| SYS-004: Endurance | SYS-004 | critical | — | UNCHECKED |
| *(+ 7 more)* | | | | UNCHECKED |

### FAIL Detail: PERF-007 Thermal Envelope

| Field | Value |
|-------|-------|
| Simulation | THERM-001: Electronics Bay Summer |
| Solver | ANSYS Icepak |
| Ambient Temperature | 50°C |
| Max Junction Temperature | 82°C |
| Hotspot | Flight controller CPU |
| Margin | 3°C |
| Status | MARGINAL |

### Graph Pull Summary

| Metric | Value |
|--------|-------|
| Records pulled | 65 |
| Edges pulled | 84 |
| Classes | 19 |
| Relationship types | 15 |
| Requirements | 15 (8 system, 7 performance) |
| Tags | 6 (`critical-path`, `needs-review`, `flight-tested`, `COTS`, `custom-design`, `marginal`) |

### Graph Visualization

The Propulsion subsystem graph (20 nodes, 20 edges) rendered by `@deeplynx:pull_graph_image`:

Purple = root (Propulsion), Blue = depth 1 (motor, battery, requirements, subsystems), Orange = depth 2 (materials, components, trade studies, risks).

## Example Files

### [`example-output/`](example-output/) — what comes out

| File | Description |
|------|-------------|
| `compliance_report.json` | Machine-readable results — 15 checks with PASS/FAIL/UNCHECKED and simulation details |
| `compliance_report.md` | Human-readable report — summary + failure details + full results table |
| `graph_Propulsion.png` | Rendered graph of Propulsion subsystem (20 nodes, depth-colored, edge-labeled) |
| `push_receipt.json` | Confirmation of records pushed to DeepLynx — record IDs and tags applied |

## DeepLynx Data Model

The Recon Drone MK-IV project uses this graph structure:

```
Requirements (15)          Subsystems (6)           Components (12)
├── SYS-001: MTOW          ├── Airframe              ├── Wing Spar
├── SYS-002: Range          ├── Propulsion            ├── T-Motor U8 II
├── SYS-003: Speed          ├── Power System          ├── Main Battery Pack
├── SYS-004: Endurance      ├── Payload Bay           ├── Folding Prop
├── ...                     ├── Avionics              ├── ...
│                           └── Communications        │
│                                                     │
Simulations (8)            Materials (3)             Risks (3)
├── FEA-001: Wing Spar      ├── Toray T700           ├── RISK-001: Battery
├── CFD-001: Cruise Aero    ├── Ti-6Al-4V            ├── RISK-002: GPS Jam
├── CFD-002: Max Speed      └── Al 6061-T6           └── RISK-003: Motor
├── THERM-001: Elec Bay
└── ...
```

Connected by 84 edges: `contains`, `validates`, `satisfies`, `analyzed_by`, `decomposes_to`, `made_of`, `mitigated_by`, `depends_on`, `powered_by`, `tested_by`, `selected_by`, etc.

## Check Script

The compliance checks live in [`compliance_checks.py`](compliance_checks.py) and can be imported:

```python
from compliance_checks import run_compliance_checks, format_report

results = run_compliance_checks(requirements, records, edges)
print(format_report(results))

# Output:
#   # Thermal Compliance Report: Recon Drone MK-IV
#   **Summary:** 4 PASS / 1 FAIL / 10 UNCHECKED out of 15 checks
#
#   ## FAILURES
#   - **PERF-007: Thermal Envelope** (PERF-007)
#     - Simulation: THERM-001: Electronics Bay Summer
#     - Result: MARGINAL
#     - max_junction_temp: 82 C
```

## Try It

```bash
# Prerequisites: DeepLynx running at localhost:5000 with sample data loaded
pip install requests networkx matplotlib Pillow

# Run the full compliance check
python check_thermal_compliance.py

# With custom settings
python check_thermal_compliance.py --deeplynx-url http://my-deeplynx:5000 --org-id 1 --project-id 2
```
