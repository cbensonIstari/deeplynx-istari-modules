#!/usr/bin/env python3
"""@deeplynx:pull_graph_image — Pull graph from DeepLynx and render as PNG/SVG."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared import DeepLynxClient, read_input, write_output, write_artifact
from rendering import render_graph


def main(work_dir: str = "."):
    input_data = read_input(work_dir)

    client = DeepLynxClient(
        base_url=input_data["deeplynx_url"],
        org_id=input_data["organization_id"],
        project_id=input_data["project_id"],
        bearer_token=input_data.get("bearer_token"),
    )

    root_id = input_data["root_record_id"]
    depth = input_data.get("depth", 2)

    # Fetch graph topology from DeepLynx
    graph_data = client.get_record_graph(root_id, depth)

    # Write raw graph data as artifact
    write_artifact("graph_data.json", json.dumps(graph_data, indent=2), work_dir)

    # Determine root label for filenames
    root_label = next(
        (n["label"] for n in graph_data.get("nodes", []) if n.get("type") == "root"),
        f"record_{root_id}",
    )
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", root_label)[:50]

    # Determine output formats
    fmt = input_data.get("format", "both")
    formats = ["png", "svg"] if fmt == "both" else [fmt]

    # Render
    saved = render_graph(
        graph_data=graph_data,
        output_prefix=f"graph_{safe_name}",
        work_dir=work_dir,
        width=input_data.get("width", 1600),
        height=input_data.get("height", 1200),
        dpi=input_data.get("dpi", 150),
        layout_algo=input_data.get("layout", "spring"),
        show_edge_labels=input_data.get("show_edge_labels", True),
        formats=formats,
    )

    artifacts = saved + ["graph_data.json"]

    write_output({
        "node_count": len(graph_data.get("nodes", [])),
        "edge_count": len(graph_data.get("links", [])),
        "root_label": root_label,
        "artifacts": artifacts,
    }, work_dir)

    print(f"pull_graph_image complete: {len(graph_data.get('nodes', []))} nodes, "
          f"{len(graph_data.get('links', []))} links → {', '.join(saved)}")


if __name__ == "__main__":
    work_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    main(work_dir)
