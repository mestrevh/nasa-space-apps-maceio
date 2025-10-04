import json
from neo4j import GraphDatabase

# --- 1. CONFIGURAÇÕES DE CONEXÃO ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # TROQUE PELA SUA SENHA

# --- 2. FUNÇÃO PARA BUSCAR DADOS NO NEO4J E FORMATAR ---


def buscar_dados_do_grafo(driver):
    print("Buscando dados no Neo4j...")
    nodes = []
    edges = []
    node_ids = set()  # Usado para não duplicar nós

    with driver.session(database="neo4j") as session:
        # Query para buscar uma parte do grafo (limite a 50 para não sobrecarregar)
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")

        for record in result:
            # Processa o nó de origem (n)
            node_n = record["n"]
            node_n_id = node_n.element_id
            if node_n_id not in node_ids:
                node_ids.add(node_n_id)
                # O primeiro rótulo do nó será usado como grupo/cor
                label = list(node_n.labels)[0] if node_n.labels else "Node"
                nodes.append({
                    "id": node_n_id,
                    # Usa a propriedade 'name' como label
                    "label": node_n.get("name", "Unnamed"),
                    "group": label
                })

            # Processa o nó de destino (m)
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

            # Processa a relação (r)
            rel = record["r"]
            edges.append({
                "from": rel.start_node.element_id,
                "to": rel.end_node.element_id,
                "label": type(rel).__name__  # Usa o tipo da relação como label
            })

    print(f"Encontrados {len(nodes)} nós e {len(edges)} relações.")
    return {"nodes": nodes, "edges": edges}


# --- 3. TEMPLATE HTML COM VIS.JS ---
# Este é o "molde" da nossa página web
# --- 3. TEMPLATE HTML COM VIS.JS (VERSÃO CORRIGIDA) ---
html_template = """
<!doctype html>
<html>
<head>
    <title>Visualização do Grafo Neo4j</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        #mynetwork {
            width: 100%;
            height: 95vh;
            border: 1px solid lightgray;
        }
    </style>
</head>
<body>

<div id="mynetwork"></div>

<script type="text/javascript">
    // Os dados do grafo serão inseridos aqui pelo Python
    // CORREÇÃO: Removemos os {} em volta dos placeholders
    var nodesArray = {nodes_json};
    var edgesArray = {edges_json};

    var nodes = new vis.DataSet(nodesArray);
    var edges = new vis.DataSet(edgesArray);

    // Cria a visualização
    var container = document.getElementById('mynetwork');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        nodes: {
            shape: 'dot',
            size: 16
        },
        physics: {
            forceAtlas2Based: {
                gravitationalConstant: -26,
                centralGravity: 0.005,
                springLength: 230,
                springConstant: 0.18
            },
            maxVelocity: 146,
            solver: 'forceAtlas2Based',
            timestep: 0.35,
            stabilization: {iterations: 150}
        },
        layout: {
            improvedLayout: false
        }
    };
    var network = new vis.Network(container, data, options);
</script>

</body>
</html>
"""

# --- 4. SCRIPT PRINCIPAL ---
if __name__ == "__main__":
    driver = None
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        dados_do_grafo = buscar_dados_do_grafo(driver)

        # Converte os dados para o formato JSON
        nodes_json_string = json.dumps(dados_do_grafo["nodes"], indent=4)
        edges_json_string = json.dumps(dados_do_grafo["edges"], indent=4)

        # Preenche o template HTML com os dados
        # --- CORREÇÃO FINAL ---
        # Garanta que os placeholders não tenham aspas em volta

        # Preenche o template HTML com os dados
        html_final = html_template.replace("{nodes_json}", nodes_json_string)
        html_final = html_final.replace("{edges_json}", edges_json_string)

        # Salva o resultado em um arquivo
        with open("grafo_visualizacao.html", "w", encoding="utf-8") as f:
            f.write(html_final)

        print("\nArquivo 'grafo_visualizacao.html' gerado com sucesso!")
        print("Abra este arquivo em seu navegador para ver o grafo.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if driver:
            driver.close()
