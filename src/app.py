from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
from collections import deque
import json
import os
import time
from scraper import get_celebrity_info
from extractor import extract_relationships
from graph import create_graph, visualize_graph

app = Flask(__name__)

# Ensure output directory exists
OUTPUT_DIR = os.path.join(app.root_path, 'static', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    root_name = data.get('name')
    search_mode = data.get('mode', 'fast') # 'fast' or 'deep'
    
    if not root_name:
        return jsonify({'error': 'Name is required'}), 400

    def generate_stream():
        try:
            # yield log
            yield json.dumps({"type": "log", "message": f"Starting analysis for {root_name}..."}) + "\n"
            
            # BFS Configuration
            MAX_DEPTH = 1
            if search_mode == 'deep':
                MAX_DEPTH = 2
                yield json.dumps({"type": "log", "message": "Deep Search enabled (Multi-hop). This may take a while."}) + "\n"
            
            BRANCH_FACTOR = 4 
            
            visited = set()
            queue = deque([(root_name, 0)])
            all_relationships = []
            
            while queue:
                current_name, depth = queue.popleft()
                
                normalized_name = current_name.lower()
                if normalized_name in visited:
                    continue
                visited.add(normalized_name)
                
                yield json.dumps({"type": "log", "message": f"Processing: {current_name} (Depth {depth})..."}) + "\n"
                
                # Step 1: Scrape
                text = get_celebrity_info(current_name)
                
                # Check for failure on ROOT node (depth 0)
                if not text and depth == 0:
                    yield json.dumps({"type": "error", "message": f"Could not find any information for '{current_name}'. Please try a different name."}) + "\n"
                    return # Stop execution immediately

                if not text:
                    yield json.dumps({"type": "log", "message": f" - Skipped {current_name}: Info not found."}) + "\n"
                    continue
                    
                if "[FALLBACK SEARCH RESULT]" in text:
                    yield json.dumps({"type": "log", "message": f" - Wikipedia not found. Using Web Search results for {current_name}."}) + "\n"
                    
                # Step 2: Extract
                yield json.dumps({"type": "log", "message": f" - Extracting relationships for {current_name}..."}) + "\n"
                
                try:
                    relationships = extract_relationships(text, current_name)
                except ValueError as e:
                    if str(e) == "Content Blocked":
                        yield json.dumps({"type": "log", "message": f" - Content filtered by AI info source. Trying search fallback..."}) + "\n"
                        # Try fallback search immediately if not already using fallback
                        if "[FALLBACK SEARCH RESULT]" not in text:
                            from scraper import search_fallback
                            fallback_text = search_fallback(current_name)
                            if fallback_text:
                                text = fallback_text
                                # Retry extraction with fallback text
                                try:
                                    relationships = extract_relationships(text, current_name)
                                except:
                                    relationships = []
                            else:
                                relationships = []
                        else:
                            relationships = []
                    else:
                        relationships = []
                
                if not relationships:
                    yield json.dumps({"type": "log", "message": f" - No relationships found for {current_name}."}) + "\n"
                    continue
                
                count = len(relationships)
                yield json.dumps({"type": "log", "message": f" - Found {count} relationships."}) + "\n"
                all_relationships.extend(relationships)
                
                # Step 3: Queue next hop
                if depth < (MAX_DEPTH - 1):
                    relationships.sort(key=lambda x: x[3] if len(x) > 3 else 0, reverse=True)
                    
                    next_nodes = []
                    for rel in relationships:
                        target = rel[1]
                        if target.lower() not in visited:
                            next_nodes.append(target)
                            
                    for next_node in next_nodes[:BRANCH_FACTOR]:
                         queue.append((next_node, depth + 1))
            
            if not all_relationships:
                 yield json.dumps({"type": "error", "message": "No relationships found."}) + "\n"
                 return

            # Step 4: Visualize
            yield json.dumps({"type": "log", "message": "Generatng graph visualization..."}) + "\n"
            G = create_graph(all_relationships)
            
            filename = f"{root_name.replace(' ', '_')}_{int(time.time())}.html"
            output_path = os.path.join(OUTPUT_DIR, filename)
            visualize_graph(G, output_path)
            
            yield json.dumps({"type": "result", "graph_url": f"/static/output/{filename}"}) + "\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return Response(stream_with_context(generate_stream()), content_type='application/x-ndjson')

if __name__ == '__main__':
    app.run(debug=True, port=8000)
