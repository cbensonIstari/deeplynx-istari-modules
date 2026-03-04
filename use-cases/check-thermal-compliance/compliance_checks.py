"""Compliance checker — compares component properties against requirement thresholds."""

from __future__ import annotations

import json


# Map requirement original_id prefixes to the property checks we can perform
THERMAL_CHECKS = {
    "SYS-001": {
        "name": "Maximum Takeoff Weight",
        "property": "threshold",
        "parse_target": lambda t: float(t.split()[0]),  # "25 kg" -> 25.0
        "unit": "kg",
        "operator": "<=",
    },
    "SYS-002": {
        "name": "Operational Range",
        "property": "threshold",
        "parse_target": lambda t: float(t.split()[0]),
        "unit": "km",
        "operator": ">=",
    },
    "SYS-004": {
        "name": "Endurance",
        "property": "threshold",
        "parse_target": lambda t: float(t.split()[0]),
        "unit": "hours",
        "operator": ">=",
    },
}


def run_compliance_checks(
    requirements: list[dict],
    records: list[dict],
    edges: list[dict],
) -> list[dict]:
    """Run all compliance checks, returning a list of results."""
    results = []

    # Build lookups
    record_by_id = {r["id"]: r for r in records}
    record_by_oid = {r.get("originalId", ""): r for r in records}

    # Find thermal analysis records (simulations) and their results
    thermal_sims = [r for r in records if r.get("class_name") == "Thermal Analysis"]
    fea_results = [r for r in records if r.get("class_name") == "FEA Result"]
    cfd_results = [r for r in records if r.get("class_name") == "CFD Result"]

    # Check each requirement
    for req in requirements:
        props = req.get("properties", {})
        if isinstance(props, str):
            props = json.loads(props)

        req_name = req.get("name", "?")
        oid = req.get("originalId", "")
        threshold_str = props.get("threshold", "")
        status_val = props.get("status", "active")
        priority = props.get("priority", "normal")

        # Try to find a simulation that validates this requirement
        # Walk edges to find: requirement <-- satisfies/validates -- simulation
        related_sims = []
        for e in edges:
            if e.get("destinationId") == req["id"] or e.get("originId") == req["id"]:
                other_id = e["originId"] if e["destinationId"] == req["id"] else e["destinationId"]
                other = record_by_id.get(other_id)
                if other and other.get("class_name") in ("Thermal Analysis", "FEA Result", "CFD Result"):
                    related_sims.append(other)

        if related_sims:
            for sim in related_sims:
                sim_props = sim.get("properties", {})
                if isinstance(sim_props, str):
                    sim_props = json.loads(sim_props)

                sim_status = sim_props.get("status", "unknown")
                results.append({
                    "requirement": req_name,
                    "requirement_id": oid,
                    "priority": priority,
                    "threshold": threshold_str,
                    "simulation": sim.get("name", "?"),
                    "simulation_status": sim_status,
                    "status": "PASS" if sim_status.lower() in ("pass", "passed", "nominal") else "FAIL",
                    "details": sim_props,
                })
        else:
            # No simulation linked — report as unchecked
            results.append({
                "requirement": req_name,
                "requirement_id": oid,
                "priority": priority,
                "threshold": threshold_str,
                "simulation": None,
                "simulation_status": "no_simulation_linked",
                "status": "UNCHECKED",
                "details": {},
            })

    return results


def format_report(results: list[dict], project_name: str = "Recon Drone MK-IV") -> str:
    """Generate a Markdown compliance report."""
    lines = [
        f"# Thermal Compliance Report: {project_name}\n",
    ]

    passing = sum(1 for r in results if r["status"] == "PASS")
    failing = sum(1 for r in results if r["status"] == "FAIL")
    unchecked = sum(1 for r in results if r["status"] == "UNCHECKED")
    total = len(results)

    lines.append(f"**Summary:** {passing} PASS / {failing} FAIL / {unchecked} UNCHECKED out of {total} checks\n")

    if failing > 0:
        lines.append("## FAILURES\n")
        for r in results:
            if r["status"] == "FAIL":
                lines.append(f"- **{r['requirement']}** ({r['requirement_id']})")
                lines.append(f"  - Priority: {r['priority']}")
                lines.append(f"  - Threshold: {r['threshold']}")
                lines.append(f"  - Simulation: {r['simulation']}")
                lines.append(f"  - Result: {r['simulation_status']}")
                if r.get("details"):
                    for k, v in r["details"].items():
                        lines.append(f"  - {k}: {v}")
                lines.append("")

    lines.append("## All Results\n")
    lines.append("| Requirement | ID | Priority | Threshold | Simulation | Status |")
    lines.append("|------------|-----|----------|-----------|------------|--------|")
    for r in sorted(results, key=lambda x: (x["status"] != "FAIL", x["status"] != "UNCHECKED", x["requirement"])):
        sim_name = r["simulation"] or "—"
        icon = {"PASS": "PASS", "FAIL": "**FAIL**", "UNCHECKED": "—"}[r["status"]]
        lines.append(f"| {r['requirement'][:40]} | {r['requirement_id']} | {r['priority']} | {r['threshold'][:20]} | {sim_name[:30]} | {icon} |")

    return "\n".join(lines) + "\n"
