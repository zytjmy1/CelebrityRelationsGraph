import networkx as nx
from pyvis.network import Network
import os

def create_graph(relationships):
    """
    Creates a NetworkX graph from a list of relationships.
    
    Args:
        relationships (list): List of tuples (source, target, relation).
        
    Returns:
        nx.Graph: The generated graph.
    """
    G = nx.Graph()
    
    # Calculate node sizes based on max intimacy
    node_sizes = {}
    
    for source, target, relation, intimacy in relationships:
        # Default size for source if not set (will be overwritten if it's a target elsewhere with higher intimacy)
        if source not in node_sizes:
            node_sizes[source] = 25 # Base size
            
        # Target size based on intimacy
        # Formula: Base (10) + Intimacy * 3. Range: 13 (Intimacy 1) to 40 (Intimacy 10)
        target_size = 10 + (intimacy * 3)
        if target not in node_sizes or target_size > node_sizes[target]:
            node_sizes[target] = target_size

    for source, target, relation, intimacy in relationships:
        # Add nodes with calculated sizes
        G.add_node(source, title=source, group=1, size=node_sizes[source])
        G.add_node(target, title=target, group=2, size=node_sizes[target])
        
        # Calculate visual properties based on intimacy (1-10)
        # Higher intimacy = shorter length, thicker line
        # element: Length: 10 -> 50, 1 -> 300 (Previous)
        # Tighter clustering: 10 -> 30, 1 -> 200
        edge_length = (11 - intimacy) * 20
        # Thicker edges: 1 -> ~1.8, 10 -> ~9
        edge_width = 1 + (intimacy * 0.8)
        
        G.add_edge(source, target, title=f"{relation} (Intimacy: {intimacy})", label=relation, length=edge_length, width=edge_width)
        
    return G

def visualize_graph(G, output_file="graph.html"):
    """
    Generates an interactive HTML graph using Pyvis.
    
    Args:
        G (nx.Graph): The graph to visualize.
        output_file (str): The path to save the HTML file.
    """
    net = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(G)
    
    # Set options for a premium, dark-themed UI
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 0,
        "color": {
          "background": "#64b5f6",
          "border": "#2b2b2b",
          "highlight": {
            "background": "#90caf9",
            "border": "#2b2b2b"
          }
        },
        "font": {
          "color": "#f0f0f0",
          "size": 16,
          "face": "Segoe UI"
        },
        "shadow": {
          "enabled": true,
          "color": "rgba(0,0,0,0.5)",
          "size": 10,
          "x": 5,
          "y": 5
        },
        "shape": "dot",
        "size": 25
      },
      "edges": {
        "color": {
          "color": "#555",
          "highlight": "#accent-color"
        },
        "font": {
          "color": "#888",
          "size": 12,
          "align": "middle"
        },
        "smooth": {
          "enabled": true,
          "type": "dynamic",
          "roundness": 0.5
        },
        "width": 2
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.05,
          "damping": 0.4
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "stabilization": {
          "enabled": true,
          "iterations": 1000,
          "updateInterval": 100,
          "onlyDynamicEdges": false,
          "fit": true
        }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Save the graph
    # Check if we assume 'src/static/output' or just 'output' relative to script
    # For main.py it was just 'output', but for app.py we passed absolute path.
    # The visualization function handles the path passed to it.
    
    net.save_graph(output_file)
    print(f"Graph saved to {output_file}")

if __name__ == "__main__":
    # Test with dummy data
    rels = [
        ("Taylor Swift", "Travis Kelce", "dating", 10),
        ("Taylor Swift", "Scott Swift", "father", 10),
        ("Taylor Swift", "Andrea Swift", "mother", 10),
        ("Travis Kelce", "Jason Kelce", "brother", 9)
    ]
    G = create_graph(rels)
    visualize_graph(G, "output/test_graph.html")
