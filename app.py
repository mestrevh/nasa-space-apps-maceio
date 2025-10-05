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
    nodes = []
    edges = []
    node_ids = set()
    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100")
        for record in result:
            node_n, rel, node_m = record["n"], record["r"], record["m"]

            if node_n.element_id not in node_ids:
                node_ids.add(node_n.element_id)
                nodes.append({"id": node_n.element_id, "label": node_n.get("name", "Unnamed"), "group": list(node_n.labels)[0]})

            if node_m.element_id not in node_ids:
                node_ids.add(node_m.element_id)
                nodes.append({"id": node_m.element_id, "label": node_m.get("name", "Unnamed"), "group": list(node_m.labels)[0]})

            edges.append({"from": rel.start_node.element_id, "to": rel.end_node.element_id, "label": type(rel).__name__})
    return {"nodes": nodes, "edges": edges}


# --- WEB APPLICATION ROUTES (Endpoints) ---

@app.route('/')
def main_page():
    """Serves the main HTML page."""
    return render_template('index.html')


@app.route('/api/data')
def get_graph_data():
    """API endpoint that returns the graph data for visualization."""
    return jsonify(fetch_graph_data())


@app.route('/api/nodes')
def get_node_list():
    """API endpoint that returns a simplified list of all nodes."""
    nodes = []
    with driver.session(database="neo4j") as session:
        # This query fetches the name, internal element ID, and the first label of each node
        # We order by name to keep the list alphabetized
        query = """
        MATCH (n) 
        RETURN n.name AS name, elementId(n) AS id, labels(n)[0] AS group
        ORDER BY name
        """
        result = session.run(query)
        # Convert the result into a list of dictionaries
        nodes = [record.data() for record in result]
    return jsonify(nodes)


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