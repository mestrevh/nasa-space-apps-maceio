import os
import spacy
import fitz  # PyMuPDF
from collections import defaultdict
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from neo4j import GraphDatabase

# --- GENERAL SETTINGS ---
# Create the Flask application
app = Flask(__name__)
CORS(app)

# Define the folder for file uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the spaCy model ONCE when the application starts (improves performance)
print("Loading spaCy model...")
NLP_MODEL = spacy.load("en_core_web_lg")
print("Model loaded.")

# --- NEO4J SETTINGS ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # Remember to use your password
driver = GraphDatabase.driver(URI, auth=AUTH)

# Clear database on startup
def clear_database():
    """Clear all data from Neo4j database"""
    try:
        with driver.session(database="neo4j") as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared successfully!")
            return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False

# Load sample data after clearing
def load_sample_data():
    """Load the sample data from both articles"""
    try:
        # Import and run the sample data loader
        import subprocess
        import sys
        result = subprocess.run([sys.executable, "load_sample_data.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Sample data loaded successfully!")
            return True
        else:
            print(f"Error loading sample data: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error loading sample data: {e}")
        return False

# Try to clear and load data, but continue if Neo4j is not available
if clear_database():
    load_sample_data()
else:
    print("Neo4j not available - running in demo mode without database")


# --- PROCESSING FUNCTIONS (Original script logic) ---

def extract_content_from_pdf(pdf_path):
    """Extracts text content from a PDF file."""
    print(f"Extracting text from: {pdf_path}")
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                full_text += page.get_text("text") + "\n\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    return full_text


def process_text_to_graph(text):
    """Processes text to extract entities (nodes) and relationships (edges)."""
    print("Starting NLP processing...")
    doc = NLP_MODEL(text)
    entities = set()
    relationships = set()

    for ent in doc.ents:
        entities.add((ent.text.strip(), ent.label_))

    for sent in doc.sents:
        entities_in_sentence = [(ent.text.strip(), ent.label_) for ent in sent.ents]
        if len(entities_in_sentence) > 1:
            for i in range(len(entities_in_sentence)):
                for j in range(i + 1, len(entities_in_sentence)):
                    ent1 = entities_in_sentence[i]
                    ent2 = entities_in_sentence[j]
                    if ent1 != ent2:
                        relationships.add((ent1, "RELATED_TO", ent2))

    print(f"Processing complete. Entities: {len(entities)}, Relationships: {len(relationships)}")
    return entities, relationships


def load_data_into_neo4j(entities, relationships):
    """Connects to Neo4j and loads the nodes and relationships."""
    print("Loading data into Neo4j...")
    with driver.session(database="neo4j") as session:
        # We use MERGE to avoid creating duplicate nodes
        for name, entity_type in entities:
            session.run(f"MERGE (n:{entity_type} {{name: $name}})", name=name)

        for (ent1, rel_type, ent2) in relationships:
            name1, type1 = ent1
            name2, type2 = ent2
            session.run(
                f"MATCH (a:{type1} {{name: $name1}}), (b:{type2} {{name: $name2}}) "
                f"MERGE (a)-[r:{rel_type}]->(b)",
                name1=name1, name2=name2
            )
    print("Loading into Neo4j complete.")


def fetch_graph_data():
    """Fetches nodes and relationships from Neo4j for visualization."""
    try:
        nodes = []
        edges = []
        node_ids = set()
        with driver.session(database="neo4j") as session:
            result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100")
            for record in result:
                node_n, rel, node_m = record["n"], record["r"], record["m"]

                if node_n.element_id not in node_ids:
                    node_ids.add(node_n.element_id)
                    label = get_node_label(node_n)
                    full_label = get_full_node_label(node_n)
                    article_group = get_article_group(node_n)
                    nodes.append({
                        "id": node_n.element_id, 
                        "label": label, 
                        "fullLabel": full_label,
                        "group": list(node_n.labels)[0],
                        "articleGroup": article_group
                    })

                if node_m.element_id not in node_ids:
                    node_ids.add(node_m.element_id)
                    label = get_node_label(node_m)
                    full_label = get_full_node_label(node_m)
                    article_group = get_article_group(node_m)
                    nodes.append({
                        "id": node_m.element_id, 
                        "label": label, 
                        "fullLabel": full_label,
                        "group": list(node_m.labels)[0],
                        "articleGroup": article_group
                    })

                edges.append({"from": rel.start_node.element_id, "to": rel.end_node.element_id, "label": type(rel).__name__})
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"Neo4j not available, returning demo data: {e}")
        return get_demo_data()

def get_demo_data():
    """Returns demo data when Neo4j is not available"""
    return {
        "nodes": [
            {"id": "1", "label": "NASA Space Apps", "fullLabel": "NASA Space Apps Challenge 2024", "group": "Paper"},
            {"id": "2", "label": "Microgravity Research", "fullLabel": "Microgravity and Cellular Biology Research", "group": "Keyword"},
            {"id": "3", "label": "ISS", "fullLabel": "International Space Station", "group": "Mission"},
            {"id": "4", "label": "Stem Cells", "fullLabel": "Adipose-Derived Stem Cells", "group": "CellType"},
            {"id": "5", "label": "qPCR", "fullLabel": "Quantitative Polymerase Chain Reaction", "group": "Method"}
        ],
        "edges": [
            {"from": "1", "to": "2", "label": "STUDIES"},
            {"from": "1", "to": "3", "label": "USED_IN"},
            {"from": "2", "to": "4", "label": "AFFECTS"},
            {"from": "3", "to": "5", "label": "VALIDATES"}
        ]
    }

def get_node_label(node):
    """Get the appropriate label for a node based on its properties."""
    # Try different possible label fields based on node type
    if "title" in node:
        label = node["title"]
    elif "name" in node:
        label = node["name"]
    elif "term" in node:
        label = node["term"]
    elif "paper_id" in node:
        label = node["paper_id"]
    elif "author_id" in node:
        label = node["author_id"]
    elif "institution_id" in node:
        label = node["institution_id"]
    elif "keyword_id" in node:
        label = node["keyword_id"]
    elif "cell_type_id" in node:
        label = node["cell_type_id"]
    elif "gene_id" in node:
        label = node["gene_id"]
    elif "method_id" in node:
        label = node["method_id"]
    elif "material_id" in node:
        label = node["material_id"]
    elif "funder_id" in node:
        label = node["funder_id"]
    elif "mission_id" in node:
        label = node["mission_id"]
    else:
        # Fallback: use the first available property
        properties = dict(node)
        if properties:
            label = str(list(properties.values())[0])
        else:
            label = "Unnamed"
    
    # Truncate long labels to prevent node stretching
    if len(label) > 50:
        return label[:47] + "..."
    return label

def get_full_node_label(node):
    """Get the full label for a node without truncation (for tooltips)."""
    # Try different possible label fields based on node type
    if "title" in node:
        return node["title"]
    elif "name" in node:
        return node["name"]
    elif "term" in node:
        return node["term"]
    elif "paper_id" in node:
        return node["paper_id"]
    elif "author_id" in node:
        return node["author_id"]
    elif "institution_id" in node:
        return node["institution_id"]
    elif "keyword_id" in node:
        return node["keyword_id"]
    elif "cell_type_id" in node:
        return node["cell_type_id"]
    elif "gene_id" in node:
        return node["gene_id"]
    elif "method_id" in node:
        return node["method_id"]
    elif "material_id" in node:
        return node["material_id"]
    elif "funder_id" in node:
        return node["funder_id"]
    elif "mission_id" in node:
        return node["mission_id"]
    else:
        # Fallback: use the first available property
        properties = dict(node)
        if properties:
            return str(list(properties.values())[0])
        return "Unnamed"

def get_article_group(node):
    """Determine which article group a node belongs to based on its properties."""
    # Check if this is a Paper node
    if "paper_id" in node:
        paper_id = node["paper_id"]
        if "10.3390/cells10030560" in paper_id:
            return "article1"
        elif "10.1371/journal.pone.0183480" in paper_id:
            return "article2"
        else:
            return "unknown"
    
    # For other nodes, we need to check their relationships to papers
    # This is a simplified approach - in a real scenario, you'd query the relationships
    # For now, we'll use a heuristic based on node properties
    
    # Check if node has properties that suggest it belongs to a specific article
    if "name" in node:
        name = node["name"].lower()
        # Keywords and terms that are more specific to article 1 (adipose stem cells)
        article1_keywords = ["adipose", "stem", "cell", "proliferation", "microgravity", "stirred", "microspheres"]
        # Keywords and terms that are more specific to article 2 (RNA isolation, ISS)
        article2_keywords = ["rna", "isolation", "pcr", "quantitative", "real", "time", "iss", "space", "station"]
        
        if any(keyword in name for keyword in article1_keywords):
            return "article1"
        elif any(keyword in name for keyword in article2_keywords):
            return "article2"
    
    # Default to shared/unknown for nodes that could belong to both articles
    return "shared"


# --- WEB APPLICATION ROUTES (Endpoints) ---

@app.route('/')
def main_page():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/systematic-review')
def systematic_review():
    """Serves the systematic review page."""
    return render_template('systematic_review.html')


@app.route('/api/data')
def get_graph_data():
    """API endpoint that returns the graph data for visualization."""
    return jsonify(fetch_graph_data())


@app.route('/api/nodes')
def get_node_list():
    """API endpoint that returns a simplified list of all nodes."""
    try:
        nodes = []
        with driver.session(database="neo4j") as session:
            # This query fetches all nodes with their properties
            query = """
            MATCH (n) 
            RETURN n, elementId(n) AS id, labels(n)[0] AS group
            ORDER BY id(n)
            """
            result = session.run(query)
            # Convert the result into a list of dictionaries
            for record in result:
                node = record["n"]
                label = get_node_label(node)
                full_label = get_full_node_label(node)
                nodes.append({
                    "name": label,
                    "fullName": full_label,
                    "id": record["id"],
                    "group": record["group"]
                })
        return jsonify(nodes)
    except Exception as e:
        print(f"Neo4j not available, returning demo node list: {e}")
        demo_data = get_demo_data()
        demo_nodes = []
        for node in demo_data["nodes"]:
            demo_nodes.append({
                "name": node["label"],
                "fullName": node["fullLabel"],
                "id": node["id"],
                "group": node["group"]
            })
        return jsonify(demo_nodes)


@app.route('/upload', methods=['POST'])
def upload_and_process_pdf():
    """Endpoint to receive the PDF upload and execute the full pipeline."""
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file sent"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if file and file.filename.endswith('.pdf'):
        # Save the file to the 'uploads' folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # --- Execute the full pipeline ---
        text = extract_content_from_pdf(filepath)
        if text:
            entities, relationships = process_text_to_graph(text)
            if entities:
                load_data_into_neo4j(entities, relationships)
                return jsonify({
                    "message": f"File '{file.filename}' processed successfully!",
                    "entities_found": len(entities),
                    "relationships_found": len(relationships)
                })

    return jsonify({"error": "Processing failed or invalid file"}), 500


# --- SERVER INITIALIZATION ---
if __name__ == '__main__':
    # The if __name__ == '__main__' block now only starts the web server.
    app.run(debug=True)