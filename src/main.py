import argparse
import sys
import os
from scraper import get_celebrity_info
from extractor import extract_relationships
from graph import create_graph, visualize_graph

def main():
    parser = argparse.ArgumentParser(description="Generate a relationship graph for a celebrity.")
    parser.add_argument("--name", type=str, required=True, help="Name of the celebrity")
    parser.add_argument("--output", type=str, default="output/graph.html", help="Output path for the HTML graph")
    
    args = parser.parse_args()
    
    print(f"Step 1: Fetching information for '{args.name}'...")
    text = get_celebrity_info(args.name)
    
    if not text:
        print("Error: Could not fetch information. Please check the name and try again.")
        sys.exit(1)
        
    print(f"Successfully fetched {len(text)} characters.")
    
    print("Step 2: Extracting relationships (this may take a moment)...")
    relationships = extract_relationships(text, args.name)
    
    if not relationships:
        print("Warning: No relationships extracted. This might be due to an API error or empty response.")
        # Create a dummy relationship to show the graph works even if empty
        # relationships = [(args.name, "No Data", "Unknown")]
    else:
        print(f"Extracted {len(relationships)} relationships.")
        
    print("Step 3: Generating graph...")
    G = create_graph(relationships)
    visualize_graph(G, args.output)
    
    print("Done!")

if __name__ == "__main__":
    main()
