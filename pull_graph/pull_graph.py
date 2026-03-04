#!/usr/bin/env python3
"""@deeplynx:pull_graph — Pull records and edges from DeepLynx into structured JSON."""

import json
import os
import sys

# Allow imports from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared import DeepLynxClient, read_input, write_output, write_artifact


REQUIREMENT_CLASSES = {"System Requirement", "Performance Requirement"}


def enrich_records(records: list[dict], class_lookup: dict[int, str]) -> list[dict]:
    """Add class_name and parse properties JSON string into dict."""
    enriched = []
    for r in records:
        r["class_name"] = class_lookup.get(r.get("classId"), "Unknown")
        props = r.get("properties")
        if isinstance(props, str):
            try:
                r["properties"] = json.loads(props)
            except json.JSONDecodeError:
                r["properties"] = {}
        enriched.append(r)
    return enriched


def enrich_edges(edges: list[dict], rel_lookup: dict[int, str], name_lookup: dict[int, str]) -> list[dict]:
    """Add relationship_name and origin/destination record names."""
    for e in edges:
        e["relationship_name"] = rel_lookup.get(e.get("relationshipId"), "unknown")
        e["origin_name"] = name_lookup.get(e.get("originId"), "?")
        e["destination_name"] = name_lookup.get(e.get("destinationId"), "?")
    return edges


def generate_summary(records: list[dict], edges: list[dict],
                     classes: list[dict], relationships: list[dict]) -> str:
    """Build a Markdown summary of the pulled graph data."""
    lines = ["# DeepLynx Graph Pull Summary\n"]

    lines.append(f"- **Records:** {len(records)}")
    lines.append(f"- **Edges:** {len(edges)}")
    lines.append(f"- **Classes:** {len(classes)}")
    lines.append(f"- **Relationship types:** {len(relationships)}\n")

    # Records by class
    lines.append("## Records by Class\n")
    lines.append("| Class | Count |")
    lines.append("|-------|-------|")
    class_counts: dict[str, int] = {}
    for r in records:
        cn = r.get("class_name", "Unknown")
        class_counts[cn] = class_counts.get(cn, 0) + 1
    for cn, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {cn} | {count} |")

    # Edge breakdown
    lines.append("\n## Edges by Relationship\n")
    lines.append("| Relationship | Count |")
    lines.append("|-------------|-------|")
    rel_counts: dict[str, int] = {}
    for e in edges:
        rn = e.get("relationship_name", "unknown")
        rel_counts[rn] = rel_counts.get(rn, 0) + 1
    for rn, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {rn} | {count} |")

    # Tags
    all_tags = set()
    for r in records:
        for t in r.get("tags", []):
            all_tags.add(t.get("name", ""))
    if all_tags:
        lines.append("\n## Tags Found\n")
        for tag in sorted(all_tags):
            lines.append(f"- `{tag}`")

    return "\n".join(lines) + "\n"


def main(work_dir: str = "."):
    input_data = read_input(work_dir)

    client = DeepLynxClient(
        base_url=input_data["deeplynx_url"],
        org_id=input_data["organization_id"],
        project_id=input_data["project_id"],
        bearer_token=input_data.get("bearer_token"),
    )

    # Fetch ontology lookups
    classes = client.get_classes()
    relationships = client.get_relationships()
    class_lookup = {c["id"]: c["name"] for c in classes}
    rel_lookup = {r["id"]: r["name"] for r in relationships}

    # Fetch all records and edges
    records = client.get_all_records()
    edges = client.get_all_edges()

    # Enrich
    records = enrich_records(records, class_lookup)
    name_lookup = {r["id"]: r["name"] for r in records}
    edges = enrich_edges(edges, rel_lookup, name_lookup)

    # Filter by record_types if specified
    record_types = input_data.get("record_types")
    if record_types:
        filtered = [r for r in records if r.get("class_name") in record_types]
    else:
        filtered = records

    # Extract requirements
    requirements = [r for r in records if r.get("class_name") in REQUIREMENT_CLASSES]

    # Write artifacts
    write_artifact("graph_records.json", json.dumps(filtered, indent=2, default=str), work_dir)
    write_artifact("graph_edges.json", json.dumps(edges, indent=2, default=str), work_dir)
    write_artifact("requirements.json", json.dumps(requirements, indent=2, default=str), work_dir)
    write_artifact("graph_summary.md", generate_summary(records, edges, classes, relationships), work_dir)

    write_output({
        "record_count": len(filtered),
        "edge_count": len(edges),
        "class_count": len(classes),
        "requirement_count": len(requirements),
        "artifacts": ["graph_records.json", "graph_edges.json", "requirements.json", "graph_summary.md"],
    }, work_dir)

    print(f"pull_graph complete: {len(filtered)} records, {len(edges)} edges, {len(requirements)} requirements")


if __name__ == "__main__":
    work_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    main(work_dir)
