from flask import Flask, render_template, request, jsonify, send_from_directory
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
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    try:
        # Step 1: Scrape
        text = get_celebrity_info(name)
        if not text:
            return jsonify({'error': 'Could not find information for this celebrity.'}), 404
            
        # Step 2: Extract
        relationships = extract_relationships(text, name)
        if not relationships:
            # Fallback for demo purposes if API fails or no relations found
            # relationships = [(name, "Example Person", "Example Relation")]
             return jsonify({'error': 'No relationships found or API error.'}), 500

        # Step 3: Visualize
        G = create_graph(relationships)
        
        # Save to static folder for serving
        filename = f"{name.replace(' ', '_')}_{int(time.time())}.html"
        output_path = os.path.join(OUTPUT_DIR, filename)
        visualize_graph(G, output_path)
        
        return jsonify({'graph_url': f"/static/output/{filename}"})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
