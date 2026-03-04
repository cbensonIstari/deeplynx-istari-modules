#!/usr/bin/env python3
"""@deeplynx:push_results — Push analysis results back to DeepLynx."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared import DeepLynxClient, read_input, write_output, write_artifact


def main(work_dir: str = "."):
    input_data = read_input(work_dir)

    client = DeepLynxClient(
        base_url=input_data["deeplynx_url"],
        org_id=input_data["organization_id"],
        project_id=input_data["project_id"],
        bearer_token=input_data.get("bearer_token"),
    )
    ds_id = input_data["data_source_id"]

    receipt = {
        "created_records": [],
        "created_edges": [],
        "errors": [],
    }

    for record_spec in input_data["records"]:
        try:
            # Build the create request body
            create_body = {
                "name": record_spec["name"],
                "description": record_spec["description"],
                "original_id": record_spec["original_id"],
                "properties": record_spec["properties"],
            }
            if record_spec.get("class_name"):
                create_body["class_name"] = record_spec["class_name"]
            if record_spec.get("tags"):
                create_body["tags"] = record_spec["tags"]

            # Create the record
            created = client.create_record(ds_id, create_body)
            new_id = created["id"]
            receipt["created_records"].append({
                "name": record_spec["name"],
                "record_id": new_id,
                "original_id": record_spec["original_id"],
            })
            print(f"  Created record: {record_spec['name']} (id={new_id})")

            # Create edges
            for link in record_spec.get("link_to", []):
                direction = link.get("direction", "outgoing")
                if direction == "outgoing":
                    origin, dest = new_id, link["record_id"]
                else:
                    origin, dest = link["record_id"], new_id

                edge_body = {
                    "origin_id": origin,
                    "destination_id": dest,
                    "relationship_name": link["relationship_name"],
                }
                created_edge = client.create_edge(ds_id, edge_body)
                receipt["created_edges"].append({
                    "edge_id": created_edge["id"],
                    "origin_id": origin,
                    "destination_id": dest,
                    "relationship": link["relationship_name"],
                })
                print(f"    Edge: {origin} --{link['relationship_name']}--> {dest} (id={created_edge['id']})")

        except Exception as e:
            receipt["errors"].append({
                "record": record_spec.get("name", "?"),
                "error": str(e),
            })
            print(f"  ERROR creating {record_spec.get('name', '?')}: {e}")

    # Write receipt artifact
    write_artifact("push_receipt.json", json.dumps(receipt, indent=2), work_dir)

    write_output({
        "records_created": len(receipt["created_records"]),
        "edges_created": len(receipt["created_edges"]),
        "errors": len(receipt["errors"]),
        "artifacts": ["push_receipt.json"],
    }, work_dir)

    print(f"push_results complete: {len(receipt['created_records'])} records, "
          f"{len(receipt['created_edges'])} edges, {len(receipt['errors'])} errors")


if __name__ == "__main__":
    work_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    main(work_dir)
