import os
from PIL import Image
import spacy
from collections import defaultdict
from neo4j import GraphDatabase
import fitz
import os
from PIL import Image

# Configurações da sua base de dados Neo4j
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # TROQUE PELA SUA SENHA

# Carrega o modelo de linguagem em inglês
nlp = spacy.load("en_core_web_lg")


def carregar_dados_no_neo4j(entidades, relacoes):
    """
    Conecta-se ao Neo4j e carrega os nós e relações.
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)

    with driver.session(database="neo4j") as session:
        print("\n--- Iniciando Carregamento no Neo4j ---")

        # Limpar o banco de dados antes de carregar (opcional)
        # print("  - Limpando dados antigos...")
        # session.run("MATCH (n) DETACH DELETE n")

        # 1. Criar os nós (Nodes)
        # Usamos MERGE para evitar criar nós duplicados se o script for rodado novamente.
        # MERGE procura por um nó com o rótulo e propriedades; se não encontrar, ele cria.
        print(f"  - Carregando {len(entidades)} nós...")
        for nome_entidade, tipo_entidade in entidades:
            query = (
                f"MERGE (n:{tipo_entidade} {{name: $name}})"
            )
            session.run(query, name=nome_entidade)

        # 2. Criar as relações (Relationships)
        print(f"  - Carregando {len(relacoes)} relações...")
        for (ent1, rel_tipo, ent2) in relacoes:
            nome1, tipo1 = ent1
            nome2, tipo2 = ent2

            query = (
                f"MATCH (a:{tipo1} {{name: $name1}}), (b:{tipo2} {{name: $name2}}) "
                f"MERGE (a)-[r:{rel_tipo}]->(b)"
            )
            session.run(query, name1=nome1, name2=nome2)

    print("--- Carregamento Concluído! ---")
    driver.close()

# Para executar:
# carregar_dados_no_neo4j(entidades, relacoes)


def processar_texto_para_grafo(texto):
    """
    Processa um texto para extrair entidades (nós) e relações (arestas).

    Args:
        texto (str): O texto extraído do PDF.

    Returns:
        tuple: Uma tupla contendo um set de entidades e um set de relações.
    """
    doc = nlp(texto)

    entidades = set()
    # Usaremos um defaultdict para evitar verificações de existência de chave
    entidades_por_sentenca = defaultdict(list)

    print("\n--- Iniciando Processamento NLP com spaCy ---")
    # 1. Extrair todas as entidades nomeadas (serão os nossos nós)
    for ent in doc.ents:
        # Adicionamos a entidade e seu tipo (label)
        # Ex: ('Aníbal Cavaco Silva', 'PER') - Pessoa
        # Ex: ('Portugal', 'LOC') - Localização
        entidades.add((ent.text.strip(), ent.label_))
        print(f"  - Entidade encontrada: {ent.text} ({ent.label_})")

    # 2. Identificar relações (uma abordagem simples)
    # Uma forma comum de inferir relações é assumir que entidades que aparecem
    # na mesma frase estão, de alguma forma, relacionadas.
    for sent in doc.sents:
        entidades_na_frase = []
        for ent in sent.ents:
            entidades_na_frase.append((ent.text.strip(), ent.label_))

        # Se houver mais de uma entidade na frase, criamos relações entre elas
        if len(entidades_na_frase) > 1:
            for i in range(len(entidades_na_frase)):
                for j in range(i + 1, len(entidades_na_frase)):
                    ent1 = entidades_na_frase[i]
                    ent2 = entidades_na_frase[j]
                    # Evita criar relações duplicadas em direções opostas
                    if ent1 != ent2:
                        entidades_por_sentenca[sent.text].extend([ent1, ent2])

    relacoes = set()
    for _, ents in entidades_por_sentenca.items():
        # Remove duplicatas da lista de entidades por sentença
        unique_ents = list(dict.fromkeys(ents))
        if len(unique_ents) > 1:
            for i in range(len(unique_ents)):
                for j in range(i + 1, len(unique_ents)):
                    relacoes.add(
                        (unique_ents[i], "RELATED_TO", unique_ents[j]))

    print(f"\n--- Resumo do Processamento ---")
    print(f"Total de entidades únicas encontradas: {len(entidades)}")
    print(f"Total de relações inferidas: {len(relacoes)}")

    return entidades, relacoes

# Suponha que `texto_extraido` é a variável com o texto do seu PDF
# texto_extraido = "..."
# entidades, relacoes = processar_texto_para_grafo(texto_extraido)

def extrair_conteudo_e_imagens_de_pdf(caminho_do_pdf):
    """
    Usa PyMuPDF (fitz) para extrair todo o texto e todas as imagens de um PDF.
    O texto é retornado como uma string e as imagens são salvas numa subpasta.
    """
    if not os.path.exists(caminho_do_pdf):
        return f"Erro: O ficheiro não foi encontrado em '{caminho_do_pdf}'"
    
    # --- Criação do diretório para salvar imagens (mesma lógica do seu código original) ---
    base_name = os.path.splitext(os.path.basename(caminho_do_pdf))[0]
    output_dir = os.path.join(os.path.dirname(caminho_do_pdf), f"{base_name}_imagens_pymupdf")
    os.makedirs(output_dir, exist_ok=True)
    print(f"As imagens serão guardadas em: '{output_dir}'")
    
    texto_completo = ""
    
    try:
        # Abre o documento PDF
        with fitz.open(caminho_do_pdf) as doc:
            print(f"Número de páginas: {len(doc)}\n")
            
            # Itera sobre cada página
            for i, page in enumerate(doc):
                # --- 1. Extração de TEXTO ---
                texto_da_pagina = page.get_text("text")
                if texto_da_pagina:
                    texto_completo += f"--- Texto da Página {i + 1} ---\n"
                    texto_completo += texto_da_pagina
                    texto_completo += "\n\n"

                # --- 2. Extração de IMAGENS ---
                # Pega a lista de imagens na página
                image_list = page.get_images(full=True)
                
                # Itera sobre cada imagem encontrada
                for j, img_info in enumerate(image_list):
                    # O 'xref' é o identificador da imagem no PDF
                    xref = img_info[0]
                    
                    # Extrai os dados da imagem (bytes)
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Cria um nome para o arquivo da imagem
                    nome_imagem = f"pagina_{i+1}_imagem_{j+1}.{image_ext}"
                    caminho_imagem = os.path.join(output_dir, nome_imagem)
                    
                    try:
                        # Salva os bytes da imagem no arquivo
                        with open(caminho_imagem, "wb") as f_imagem:
                            f_imagem.write(image_bytes)
                        print(f"   - Imagem guardada: {caminho_imagem}")

                    except Exception as img_e:
                        print(f"   - Erro ao salvar imagem {j+1} da página {i+1}: {img_e}")

    except Exception as e:
        return f"Ocorreu um erro ao tentar processar o PDF: {e}"
        
    return texto_completo


# --- INÍCIO DA EXECUÇÃO ---
if __name__ == "__main__":
    # Carrega o modelo spaCy (pode levar alguns segundos)
    print("Carregando modelo spaCy...")
    nlp = spacy.load("pt_core_news_lg")
    print("Modelo carregado.")

    caminho_do_pdf_exemplo = "database/pone.0104830.pdf"

    # Fase 1: Extração
    texto_extraido = extrair_conteudo_e_imagens_de_pdf(caminho_do_pdf_exemplo)

    try:
        with open("test.txt", "w", encoding='utf-8') as arquivo:
            arquivo.write(texto_extraido)
        print(f"String salva com sucesso no arquivo 'test.txt'!")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    if texto_extraido and not texto_extraido.startswith("Erro"):
        # Fase 2: Processamento NLP
        entidades, relacoes = processar_texto_para_grafo(texto_extraido)

        # Fase 3: Carregamento no Neo4j
        if entidades:
            carregar_dados_no_neo4j(entidades, relacoes)
            print("\nProcesso finalizado. Verifique seu banco de dados Neo4j!")
            print(
                "Você pode usar a query 'MATCH (n) RETURN n LIMIT 100' para ver os nós criados.")
        else:
            print("\nNenhuma entidade foi extraída para carregar no grafo.")
    else:
        print(texto_extraido)
