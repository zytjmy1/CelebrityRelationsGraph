import html
import os

import networkx as nx
from pyvis.network import Network


def create_graph(relationships, root_name=None):
    """Build a compact graph, retaining multiple facts between the same people."""
    graph = nx.Graph()
    node_sizes = {}
    for source, target, _, intimacy in relationships:
        node_sizes[source] = max(node_sizes.get(source, 28), 42 if source == root_name else 28)
        node_sizes[target] = max(node_sizes.get(target, 14), 12 + intimacy * 3)

    for source, target, relation, intimacy in relationships:
        for person in (source, target):
            is_root = person == root_name
            graph.add_node(
                person,
                title=html.escape(person),
                size=node_sizes[person],
                color="#fbbf24" if is_root else ("#34d399" if person == source else "#60a5fa"),
                borderWidth=2 if is_root else 0,
            )

        if graph.has_edge(source, target):
            edge = graph[source][target]
            edge["relations"].append((relation, intimacy))
            edge["width"] = max(edge["width"], 1 + intimacy * 0.7)
            edge["length"] = min(edge["length"], (11 - intimacy) * 18)
            edge["label"] = " · ".join(item[0] for item in edge["relations"][:3])
            edge["title"] = "<br>".join(
                f"{html.escape(label)} · 亲密度 {score}/10" for label, score in edge["relations"]
            )
            continue

        graph.add_edge(
            source,
            target,
            relations=[(relation, intimacy)],
            label=relation,
            title=f"{html.escape(relation)} · 亲密度 {intimacy}/10",
            length=(11 - intimacy) * 18,
            width=1 + intimacy * 0.7,
        )
    return graph


def visualize_graph(graph, output_file="graph.html"):
    net = Network(notebook=False, height="100vh", width="100%", bgcolor="#07111f", font_color="#dbeafe")
    net.from_nx(graph)
    net.set_options("""
    var options = {
      "nodes": {
        "shape": "dot",
        "font": {"color": "#e5eefb", "size": 15, "face": "Inter, Segoe UI, sans-serif", "strokeWidth": 3, "strokeColor": "#07111f"},
        "shadow": {"enabled": true, "color": "rgba(30, 64, 175, 0.32)", "size": 14, "x": 0, "y": 5}
      },
      "edges": {
        "color": {"color": "rgba(148, 163, 184, 0.62)", "highlight": "#fbbf24", "hover": "#93c5fd"},
        "font": {"color": "#cbd5e1", "size": 12, "align": "middle", "strokeWidth": 4, "strokeColor": "#07111f"},
        "smooth": {"enabled": true, "type": "dynamic", "roundness": 0.35}
      },
      "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {"gravitationalConstant": -85, "centralGravity": 0.012, "springLength": 135, "springConstant": 0.055, "damping": 0.42},
        "maxVelocity": 45,
        "stabilization": {"enabled": true, "iterations": 700, "updateInterval": 50, "fit": true}
      },
      "interaction": {"hover": true, "navigationButtons": true, "keyboard": true, "tooltipDelay": 120}
    }
    """)
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    net.save_graph(output_file)
    print(f"Graph saved to {output_file}")
