from flask import Flask, jsonify, render_template
from flask_cors import CORS
from neo4j import GraphDatabase

# Inicia a aplicação Flask
app = Flask(__name__)
CORS(app)  # Permite que o frontend acesse a API

# --- Configurações de Conexão com o Neo4j ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # Lembre-se de usar sua senha
driver = GraphDatabase.driver(URI, auth=AUTH)

def buscar_dados_do_grafo():
    """Busca os nós e relações e formata para o Vis.js."""
    nodes = []
    edges = []
    node_ids = set()

    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
        for record in result:
            node_n = record["n"]
            node_n_id = node_n.element_id
            if node_n_id not in node_ids:
                node_ids.add(node_n_id)
                label = list(node_n.labels)[0] if node_n.labels else "Node"
                nodes.append({
                    "id": node_n_id,
                    "label": node_n.get("name", "Unnamed"),
                    "group": label
                })

            node_m = record["m"]
            node_m_id = node_m.element_id
            if node_m_id not in node_ids:
                node_ids.add(node_m_id)
                label = list(node_m.labels)[0] if node_m.labels else "Node"
                nodes.append({
                    "id": node_m_id,
                    "label": node_m.get("name", "Unnamed"),
                    "group": label
                })
            
            rel = record["r"]
            edges.append({
                "from": rel.start_node.element_id,
                "to": rel.end_node.element_id,
                "label": type(rel).__name__
            })
    return {"nodes": nodes, "edges": edges}

# --- Rotas (URLs) da Aplicação ---

@app.route('/')
def pagina_principal():
    """Serve o arquivo HTML principal."""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """Endpoint da API que retorna os dados do grafo em formato JSON."""
    dados_do_grafo = buscar_dados_do_grafo()
    return jsonify(dados_do_grafo)

if __name__ == '__main__':
    # Roda o servidor web
    app.run(debug=True)