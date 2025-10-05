import os
import spacy
import fitz  # PyMuPDF
from collections import defaultdict
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from neo4j import GraphDatabase

# --- CONFIGURAÇÕES GERAIS ---
# Cria a aplicação Flask
app = Flask(__name__)
CORS(app)

# Define a pasta para onde os arquivos de upload irão
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Carrega o modelo Spacy UMA VEZ ao iniciar a aplicação (melhora o desempenho)
print("Carregando modelo spaCy...")
NLP_MODEL = spacy.load("en_core_web_lg")  # ou "pt_core_news_lg"
print("Modelo carregado.")

# --- CONFIGURAÇÕES DO NEO4J ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # Lembre-se de usar sua senha
driver = GraphDatabase.driver(URI, auth=AUTH)

# --- FUNÇÕES DE PROCESSAMENTO (Lógica do seu script original) ---


def extrair_conteudo_de_pdf(caminho_do_pdf):
    print(f"Extraindo texto e imagens de: {caminho_do_pdf}")
    # ... (O código desta função é o mesmo que você já tinha)
    texto_completo = ""
    try:
        with fitz.open(caminho_do_pdf) as doc:
            for page in doc:
                texto_completo += page.get_text("text") + "\n\n"
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return None
    return texto_completo


def processar_texto_para_grafo(texto):
    print("Iniciando processamento NLP...")
    doc = NLP_MODEL(texto)
    entidades = set()
    relacoes = set()
    entidades_por_sentenca = defaultdict(list)

    for ent in doc.ents:
        entidades.add((ent.text.strip(), ent.label_))

    for sent in doc.sents:
        entidades_na_frase = [(ent.text.strip(), ent.label_)
                              for ent in sent.ents]
        if len(entidades_na_frase) > 1:
            for i in range(len(entidades_na_frase)):
                for j in range(i + 1, len(entidades_na_frase)):
                    ent1 = entidades_na_frase[i]
                    ent2 = entidades_na_frase[j]
                    if ent1 != ent2:
                        relacoes.add((ent1, "RELATED_TO", ent2))

    print(
        f"Processamento concluído. Entidades: {len(entidades)}, Relações: {len(relacoes)}")
    return entidades, relacoes


def carregar_dados_no_neo4j(entidades, relacoes):
    print("Carregando dados no Neo4j...")
    with driver.session(database="neo4j") as session:
        # Usamos MERGE para evitar duplicatas
        for nome, tipo in entidades:
            session.run(f"MERGE (n:{tipo} {{name: $name}})", name=nome)

        for (ent1, rel_tipo, ent2) in relacoes:
            nome1, tipo1 = ent1
            nome2, tipo2 = ent2
            session.run(
                f"MATCH (a:{tipo1} {{name: $name1}}), (b:{tipo2} {{name: $name2}}) "
                f"MERGE (a)-[r:{rel_tipo}]->(b)",
                name1=nome1, name2=nome2
            )
    print("Carregamento no Neo4j concluído.")


def buscar_dados_do_grafo():
    # ... (Esta função é a mesma da resposta anterior, para buscar dados para visualização)
    nodes = []
    edges = []
    node_ids = set()
    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100")
        for record in result:
            node_n, rel, node_m = record["n"], record["r"], record["m"]

            if node_n.element_id not in node_ids:
                node_ids.add(node_n.element_id)
                nodes.append({"id": node_n.element_id, "label": node_n.get(
                    "name", "Unnamed"), "group": list(node_n.labels)[0]})

            if node_m.element_id not in node_ids:
                node_ids.add(node_m.element_id)
                nodes.append({"id": node_m.element_id, "label": node_m.get(
                    "name", "Unnamed"), "group": list(node_m.labels)[0]})

            edges.append({"from": rel.start_node.element_id,
                         "to": rel.end_node.element_id, "label": type(rel).__name__})
    return {"nodes": nodes, "edges": edges}

# --- ROTAS DA APLICAÇÃO WEB (Endpoints) ---


@app.route('/')
def pagina_principal():
    """Serve a página HTML principal."""
    return render_template('index.html')


@app.route('/api/data')
def get_graph_data():
    """Endpoint da API que retorna os dados do grafo para visualização."""
    return jsonify(buscar_dados_do_grafo())

# Adicione esta nova rota no seu app.py

@app.route('/api/nodes')
def get_node_list():
    """Endpoint que retorna uma lista simplificada de todos os nós."""
    nodes = []
    with driver.session(database="neo4j") as session:
        # A query busca o nome, o ID interno do elemento e o primeiro rótulo de cada nó
        # Ordenamos por nome para a lista ficar em ordem alfabética
        query = """
        MATCH (n) 
        RETURN n.name AS name, elementId(n) AS id, labels(n)[0] AS group
        ORDER BY name
        """
        result = session.run(query)
        # Convertemos o resultado em uma lista de dicionários
        nodes = [record.data() for record in result]
    return jsonify(nodes)

@app.route('/upload', methods=['POST'])
def upload_e_processar_pdf():
    """Endpoint para receber o upload do PDF e executar todo o pipeline."""
    if 'pdf_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400

    if file and file.filename.endswith('.pdf'):
        # Salva o arquivo na pasta 'uploads'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # --- Executa o pipeline completo ---
        texto = extrair_conteudo_de_pdf(filepath)
        if texto:
            entidades, relacoes = processar_texto_para_grafo(texto)
            if entidades:
                carregar_dados_no_neo4j(entidades, relacoes)
                return jsonify({
                    "message": f"Arquivo '{file.filename}' processado com sucesso!",
                    "entidades_encontradas": len(entidades),
                    "relacoes_encontradas": len(relacoes)
                })

    return jsonify({"error": "Falha no processamento ou arquivo inválido"}), 500


# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # O if __name__ == '__main__' agora só inicia o servidor web.
    app.run(debug=True)
