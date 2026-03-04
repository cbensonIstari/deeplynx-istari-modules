"""Graph layout and rendering engine using networkx + matplotlib."""

from __future__ import annotations

import os
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


# Depth-based colors matching DeepLynx UI conventions
DEPTH_COLORS = {
    0: "#7C3AED",  # purple  (root)
    1: "#3B82F6",  # blue    (depth 1)
    2: "#F97316",  # orange  (depth 2)
    3: "#9CA3AF",  # gray    (depth 3+)
}

DEPTH_LABELS = {
    0: "Root",
    1: "Depth 1",
    2: "Depth 2",
    3: "Depth 3+",
}


def _compute_depths(nodes: list[dict], links: list[dict], root_id: int) -> dict[int, int]:
    """BFS from root to assign depth to each node."""
    adj: dict[int, list[int]] = {}
    for link in links:
        s, t = link["source"], link["target"]
        adj.setdefault(s, []).append(t)
        adj.setdefault(t, []).append(s)

    depths = {root_id: 0}
    queue = deque([root_id])
    while queue:
        current = queue.popleft()
        for neighbor in adj.get(current, []):
            if neighbor not in depths:
                depths[neighbor] = depths[current] + 1
                queue.append(neighbor)
    return depths


def render_graph(
    graph_data: dict,
    output_prefix: str,
    work_dir: str,
    width: int = 1600,
    height: int = 1200,
    dpi: int = 150,
    layout_algo: str = "spring",
    show_edge_labels: bool = True,
    formats: list[str] | None = None,
) -> list[str]:
    """Build networkx graph from DeepLynx GraphResponse, render to PNG/SVG."""

    if formats is None:
        formats = ["png", "svg"]

    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    if not nodes:
        return []

    # Find root node
    root_node = next((n for n in nodes if n.get("type") == "root"), nodes[0])
    root_id = root_node["id"]

    # Build networkx graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"], label=node["label"], type=node.get("type", ""))
    for link in links:
        G.add_edge(
            link["source"], link["target"],
            relationship=link.get("relationshipName", ""),
        )

    # Compute layout
    if layout_algo == "kamada_kawai" and len(G.nodes) > 2:
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, k=2.5, iterations=150, seed=42)

    # Compute depths for coloring
    depths = _compute_depths(nodes, links, root_id)
    node_ids = list(G.nodes())
    node_colors = [DEPTH_COLORS.get(min(depths.get(n, 3), 3), "#9CA3AF") for n in node_ids]
    node_sizes = [900 if n == root_id else 450 for n in node_ids]

    # Render
    fig_w = width / dpi
    fig_h = height / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FAFAFA")

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#B0B0B0", width=1.2, alpha=0.7,
        arrows=True, arrowstyle="-|>", arrowsize=12,
        connectionstyle="arc3,rad=0.1",
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        nodelist=node_ids, node_color=node_colors,
        node_size=node_sizes, edgecolors="#333333", linewidths=0.8,
    )

    # Draw node labels (wrapped for readability)
    labels = {}
    for n in node_ids:
        raw = G.nodes[n].get("label", str(n))
        # Wrap long labels
        if len(raw) > 20:
            mid = len(raw) // 2
            # Find nearest space to midpoint
            space_idx = raw.rfind(" ", 0, mid + 5)
            if space_idx > 0:
                raw = raw[:space_idx] + "\n" + raw[space_idx + 1:]
        labels[n] = raw
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=6, font_weight="bold")

    # Draw edge labels
    if show_edge_labels:
        edge_labels = {(u, v): d.get("relationship", "") for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels, ax=ax,
            font_size=5, font_color="#666666",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7),
        )

    # Title and legend
    ax.set_title(
        f"DeepLynx Graph: {root_node['label']}",
        fontsize=12, fontweight="bold", pad=15,
    )

    # Add depth legend
    used_depths = sorted(set(min(d, 3) for d in depths.values()))
    legend_patches = [
        mpatches.Patch(color=DEPTH_COLORS[d], label=DEPTH_LABELS[d])
        for d in used_depths
    ]
    ax.legend(handles=legend_patches, loc="upper left", fontsize=7, framealpha=0.8)

    ax.axis("off")
    plt.tight_layout()

    # Save
    saved = []
    for fmt in formats:
        filepath = os.path.join(work_dir, f"{output_prefix}.{fmt}")
        fig.savefig(filepath, format=fmt, dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        saved.append(f"{output_prefix}.{fmt}")

    plt.close(fig)
    return saved
