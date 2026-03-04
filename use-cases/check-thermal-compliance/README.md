# Use Case: Check Thermal Compliance Against DeepLynx Requirements

## Intent

I have a drone design stored in **DeepLynx** with system requirements, subsystems, components, and simulation results all tracked as graph records. I want to:

1. **Pull** the latest requirements and component specs from DeepLynx
2. **Visualize** the graph to see how requirements, subsystems, and components relate
3. **Run compliance checks** against the thermal requirements
4. **Push** the results back to DeepLynx so the systems team can see them

I don't want to manually export CSVs, copy data between tools, or send emails with screenshots. The full loop — pull, check, visualize, push — should run as a single workflow.

## Tools Used

| Tool | Role |
|------|------|
| **Istari Platform** | Outer loop — stores versioned artifacts, runs jobs, shares results |
| **@deeplynx:pull_graph** | Inner loop 1 — queries DeepLynx API, exports records + edges as JSON |
| **@deeplynx:pull_graph_image** | Inner loop 2 — renders graph topology as PNG/SVG diagram |
| **Compliance checker** (this script) | Inner loop 3 — compares component specs against requirement thresholds |
| **@deeplynx:push_results** | Inner loop 4 — writes compliance results back to DeepLynx |

## Inner / Outer Loop

```
┌─── Outer Loop: Istari ── store · check · visualize · share ──────────┐
│                                                                        │
│   ┌─ @deeplynx:pull_graph ────────────────────────────────────────┐   │
│   │ Query DeepLynx → records + edges + requirements as JSON        │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌─ @deeplynx:pull_graph_image ──┴───────────────────────────────┐   │
│   │ Render Propulsion subsystem graph as PNG/SVG                   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌─ compliance_checks.py ────────┴───────────────────────────────┐   │
│   │ Compare thermal specs against requirement thresholds → PASS/FAIL│  │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌─ @deeplynx:push_results ──────┴───────────────────────────────┐   │
│   │ Write compliance results back to DeepLynx as new records       │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## K-Script

| Step | Who | Interaction / Process | Unobservable Actions or Assumptions |
|------|-----|----------------------|-------------------------------------|
| 1 | **Thermal Engineer** | Opens Istari, navigates to "Drone Thermal Analysis" system | Wants to verify the motor assembly meets thermal requirements after a power draw update |
| 2 | **Thermal Engineer** | Runs `check_thermal_compliance.py` | Script orchestrates all four modules in sequence |
| 3 | **System** | `@deeplynx:pull_graph` fetches 62 records, 83 edges from DeepLynx | Includes the latest motor specs (520W power draw) and thermal requirement (85°C limit) |
| 4 | **System** | `@deeplynx:pull_graph_image` renders Propulsion subsystem graph as PNG | Shows motor, battery, propeller, and connected requirements |
| 5 | **System** | `compliance_checks.py` compares each component against its thermal limits | Reads requirements.json and graph_records.json, matches by relationship edges |
| 6 | **System** | Compliance check result: Motor FAILS at 91.3°C (limit 85°C) | Other components pass |
| 7 | **System** | `@deeplynx:push_results` creates a Thermal Analysis record in DeepLynx tagged `needs-review` | Linked to the motor component and thermal requirement via edges |
| 8 | **Thermal Engineer** | Reviews the artifacts: compliance report, graph image, and push receipt | All in one place in Istari, with the DeepLynx graph updated |
| 9 | **Systems Engineer** | Sees the `needs-review` tag in DeepLynx, opens the thermal analysis record | Full traceability from requirement to failure |

## Running the Example

```bash
# Prerequisites: DeepLynx running at localhost:5000 with sample data loaded

# Install dependencies
pip install requests networkx matplotlib Pillow

# Run the full compliance check
python check_thermal_compliance.py

# Output will be in the output/ directory:
#   output/graph_records.json      — all records from DeepLynx
#   output/graph_edges.json        — all edges
#   output/requirements.json       — filtered requirements
#   output/graph_summary.md        — summary report
#   output/graph_Propulsion.png    — visual graph of Propulsion subsystem
#   output/graph_Propulsion.svg    — vector version
#   output/compliance_report.json  — PASS/FAIL for each requirement
#   output/compliance_report.md    — human-readable report
#   output/push_receipt.json       — confirmation of records pushed to DeepLynx
```

## Expected Results

| Artifact | Contents |
|----------|----------|
| `graph_records.json` | 62 records across 16+ classes |
| `graph_edges.json` | 83 edges with relationship names |
| `requirements.json` | 15 requirements with thresholds |
| `graph_Propulsion.png` | Visual graph centered on Propulsion subsystem |
| `compliance_report.json` | Array of check results with PASS/FAIL status and margins |
| `compliance_report.md` | Formatted compliance report |
| `push_receipt.json` | IDs of records and edges created in DeepLynx |
