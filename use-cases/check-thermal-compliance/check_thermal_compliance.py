#!/usr/bin/env python3
"""
End-to-end use case: Check Thermal Compliance Against DeepLynx Requirements.

This script orchestrates the full workflow:
1. Pull records and edges from DeepLynx (@deeplynx:pull_graph)
2. Render the Propulsion subsystem graph (@deeplynx:pull_graph_image)
3. Run compliance checks against thermal requirements
4. Push results back to DeepLynx (@deeplynx:push_results)

Usage:
    python check_thermal_compliance.py [--deeplynx-url URL] [--org-id N] [--project-id N]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import shutil
from datetime import datetime

# Add parent paths for module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, MODULES_DIR)
sys.path.insert(0, os.path.join(MODULES_DIR, "pull_graph"))
sys.path.insert(0, os.path.join(MODULES_DIR, "pull_graph_image"))
sys.path.insert(0, os.path.join(MODULES_DIR, "push_results"))

from shared import write_artifact
from compliance_checks import run_compliance_checks, format_report


def step_pull_graph(work_dir, config):
    """Step 1: Pull all records and edges from DeepLynx."""
    print("\n" + "=" * 60)
    print("STEP 1: Pulling graph data from DeepLynx")
    print("=" * 60)

    from pull_graph import main as pull_graph_main

    # Write input for pull_graph
    with open(os.path.join(work_dir, "input.json"), "w") as f:
        json.dump({
            "deeplynx_url": config["deeplynx_url"],
            "organization_id": config["org_id"],
            "project_id": config["project_id"],
        }, f)

    pull_graph_main(work_dir)

    # Read the output
    with open(os.path.join(work_dir, "output.json")) as f:
        output = json.load(f)
    print(f"  -> {output['record_count']} records, {output['edge_count']} edges, "
          f"{output['requirement_count']} requirements")
    return output


def step_pull_graph_image(work_dir, config, root_record_id):
    """Step 2: Render graph image centered on a subsystem."""
    print("\n" + "=" * 60)
    print("STEP 2: Rendering graph image")
    print("=" * 60)

    from pull_graph_image import main as pull_graph_image_main

    # Write input for pull_graph_image
    with open(os.path.join(work_dir, "input.json"), "w") as f:
        json.dump({
            "deeplynx_url": config["deeplynx_url"],
            "organization_id": config["org_id"],
            "project_id": config["project_id"],
            "root_record_id": root_record_id,
            "depth": 2,
            "format": "both",
            "show_edge_labels": True,
        }, f)

    pull_graph_image_main(work_dir)

    with open(os.path.join(work_dir, "output.json")) as f:
        output = json.load(f)
    print(f"  -> Rendered graph: {output['root_label']} ({output['node_count']} nodes)")
    return output


def step_compliance_check(work_dir):
    """Step 3: Run compliance checks against requirements."""
    print("\n" + "=" * 60)
    print("STEP 3: Running compliance checks")
    print("=" * 60)

    # Load the data pulled in step 1
    with open(os.path.join(work_dir, "graph_records.json")) as f:
        records = json.load(f)
    with open(os.path.join(work_dir, "graph_edges.json")) as f:
        edges = json.load(f)
    with open(os.path.join(work_dir, "requirements.json")) as f:
        requirements = json.load(f)

    # Run checks
    results = run_compliance_checks(requirements, records, edges)

    # Generate report
    report_md = format_report(results)

    # Write artifacts
    write_artifact("compliance_report.json", json.dumps(results, indent=2, default=str), work_dir)
    write_artifact("compliance_report.md", report_md, work_dir)

    passing = sum(1 for r in results if r["status"] == "PASS")
    failing = sum(1 for r in results if r["status"] == "FAIL")
    unchecked = sum(1 for r in results if r["status"] == "UNCHECKED")
    print(f"  -> {passing} PASS / {failing} FAIL / {unchecked} UNCHECKED")

    return results


def step_push_results(work_dir, config, compliance_results):
    """Step 4: Push compliance results back to DeepLynx."""
    print("\n" + "=" * 60)
    print("STEP 4: Pushing results to DeepLynx")
    print("=" * 60)

    from push_results import main as push_results_main

    # Build records to push — one per FAIL result
    records_to_push = []
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    for result in compliance_results:
        if result["status"] == "FAIL":
            records_to_push.append({
                "name": f"Compliance Check: {result['requirement'][:40]}",
                "description": (
                    f"Automated compliance check for {result['requirement']} "
                    f"({result['requirement_id']}) — {result['status']}"
                ),
                "original_id": f"COMPLIANCE-{result['requirement_id']}-{timestamp}",
                "class_name": "Thermal Analysis",
                "properties": {
                    "check_type": "thermal_compliance",
                    "requirement_id": result["requirement_id"],
                    "requirement_name": result["requirement"],
                    "threshold": result["threshold"],
                    "simulation_used": result["simulation"],
                    "simulation_status": result["simulation_status"],
                    "compliance_status": result["status"],
                    "checked_at": timestamp,
                    "tool": "Istari check-thermal-compliance",
                },
                "tags": ["needs-review"],
                "link_to": [],
            })

    # Also push a summary record
    passing = sum(1 for r in compliance_results if r["status"] == "PASS")
    failing = sum(1 for r in compliance_results if r["status"] == "FAIL")
    unchecked = sum(1 for r in compliance_results if r["status"] == "UNCHECKED")
    records_to_push.append({
        "name": f"Compliance Summary ({timestamp[:10]})",
        "description": (
            f"Automated compliance run: {passing} PASS, {failing} FAIL, {unchecked} UNCHECKED "
            f"out of {len(compliance_results)} checks"
        ),
        "original_id": f"COMPLIANCE-SUMMARY-{timestamp}",
        "class_name": "Thermal Analysis",
        "properties": {
            "check_type": "compliance_summary",
            "total_checks": len(compliance_results),
            "passing": passing,
            "failing": failing,
            "unchecked": unchecked,
            "checked_at": timestamp,
            "tool": "Istari check-thermal-compliance",
        },
        "tags": ["needs-review"] if failing > 0 else [],
        "link_to": [],
    })

    # Write input for push_results
    with open(os.path.join(work_dir, "input.json"), "w") as f:
        json.dump({
            "deeplynx_url": config["deeplynx_url"],
            "organization_id": config["org_id"],
            "project_id": config["project_id"],
            "data_source_id": 2,
            "records": records_to_push,
        }, f)

    push_results_main(work_dir)

    with open(os.path.join(work_dir, "output.json")) as f:
        output = json.load(f)
    print(f"  -> Pushed {output['records_created']} records to DeepLynx")
    return output


def find_propulsion_record(records):
    """Find the Propulsion subsystem record for graph rendering."""
    # Prefer the actual Propulsion Subsystem class record
    for r in records:
        if r.get("class_name") == "Subsystem" and "Propulsion" in r.get("name", ""):
            return r["id"]
    # Fallback: any subsystem
    for r in records:
        if r.get("class_name") == "Subsystem":
            return r["id"]
    return records[0]["id"]


def main():
    parser = argparse.ArgumentParser(description="Check thermal compliance against DeepLynx")
    parser.add_argument("--deeplynx-url", default="http://localhost:5000")
    parser.add_argument("--org-id", type=int, default=1)
    parser.add_argument("--project-id", type=int, default=2)
    parser.add_argument("--output-dir", default=os.path.join(SCRIPT_DIR, "output"))
    args = parser.parse_args()

    config = {
        "deeplynx_url": args.deeplynx_url,
        "org_id": args.org_id,
        "project_id": args.project_id,
    }

    # Create output directory
    work_dir = args.output_dir
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    print("=" * 60)
    print("  DeepLynx Thermal Compliance Check")
    print(f"  Target: {config['deeplynx_url']} (org={config['org_id']}, project={config['project_id']})")
    print("=" * 60)

    # Step 1: Pull graph data
    pull_output = step_pull_graph(work_dir, config)

    # Load records to find Propulsion subsystem
    with open(os.path.join(work_dir, "graph_records.json")) as f:
        records = json.load(f)
    propulsion_id = find_propulsion_record(records)

    # Step 2: Render graph image
    image_output = step_pull_graph_image(work_dir, config, propulsion_id)

    # Step 3: Run compliance checks
    compliance_results = step_compliance_check(work_dir)

    # Step 4: Push results back to DeepLynx
    push_output = step_push_results(work_dir, config, compliance_results)

    # Final summary
    print("\n" + "=" * 60)
    print("  COMPLETE")
    print("=" * 60)
    print(f"  Output directory: {work_dir}")
    print(f"  Artifacts:")
    for f in sorted(os.listdir(work_dir)):
        if f != "input.json":
            size = os.path.getsize(os.path.join(work_dir, f))
            print(f"    {f:40s} {size:>8,} bytes")

    failing = sum(1 for r in compliance_results if r["status"] == "FAIL")
    if failing > 0:
        print(f"\n  WARNING: {failing} compliance check(s) FAILED")
        print("  Review compliance_report.md for details")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
