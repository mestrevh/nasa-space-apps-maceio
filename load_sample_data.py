#!/usr/bin/env python3
"""
Script para carregar dados estruturados de artigo científico no Neo4j
Baseado na estrutura de dados fornecida pelo usuário
"""

from neo4j import GraphDatabase
import json

# Configurações do Neo4j
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

def connect_to_neo4j():
    """Conecta ao banco Neo4j"""
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        print("[OK] Conectado ao Neo4j com sucesso!")
        return driver
    except Exception as e:
        print(f"[ERROR] Erro ao conectar ao Neo4j: {e}")
        return None

def clear_database(driver):
    """Limpa o banco de dados (opcional)"""
    with driver.session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("[INFO] Banco de dados limpo!")

def create_paper_nodes(driver):
    """Cria os nós dos artigos científicos"""
    papers = [
        {
            "paper_id": "10.3390/cells10030560",
            "title": "Selective Proliferation of Highly Functional Adipose-Derived Stem Cells in Microgravity Culture with Stirred Microspheres",
            "journal": "Cells",
            "publication_date": "2021-03-04",
            "doi": "10.3390/cells10030560"
        },
        {
            "paper_id": "10.1371/journal.pone.0183480",
            "title": "Microgravity validation of a novel system for RNA isolation and multiplex quantitative real time PCR analysis of gene expression on the International Space Station",
            "journal": "PLOS ONE",
            "publication_date": "2017-09-06",
            "doi": "10.1371/journal.pone.0183480"
        }
    ]
    
    with driver.session(database="neo4j") as session:
        for paper in papers:
            session.run("""
                CREATE (p:Paper {
                    paper_id: $paper_id,
                    title: $title,
                    journal: $journal,
                    publication_date: $publication_date,
                    doi: $doi
                })
            """, **paper)
        print(f"[INFO] Criados {len(papers)} nós de artigos")

def create_author_nodes(driver):
    """Cria os nós dos autores"""
    authors = [
        # Autores do primeiro artigo (Cells)
        {"author_id": "Takanobu Mashiko", "name": "Takanobu Mashiko", "is_corresponding": False},
        {"author_id": "Koji Kanayama", "name": "Koji Kanayama", "is_corresponding": False},
        {"author_id": "Natsumi Saito", "name": "Natsumi Saito", "is_corresponding": False},
        {"author_id": "Takako Shirado", "name": "Takako Shirado", "is_corresponding": False},
        {"author_id": "Rintaro Asahi", "name": "Rintaro Asahi", "is_corresponding": False},
        {"author_id": "Masanori Mori", "name": "Masanori Mori", "is_corresponding": False},
        {"author_id": "Kotaro Yoshimura", "name": "Kotaro Yoshimura", "is_corresponding": True},
        
        # Autores do segundo artigo (PLOS ONE)
        {"author_id": "Macarena Parra", "name": "Macarena Parra", "is_corresponding": False},
        {"author_id": "Jimmy Jung", "name": "Jimmy Jung", "is_corresponding": False},
        {"author_id": "Travis D. Boone", "name": "Travis D. Boone", "is_corresponding": False},
        {"author_id": "Luan Tran", "name": "Luan Tran", "is_corresponding": False},
        {"author_id": "Elizabeth A. Blaber", "name": "Elizabeth A. Blaber", "is_corresponding": False},
        {"author_id": "Kathleen Rubins", "name": "Kathleen Rubins", "is_corresponding": False, "role": "Astronaut"},
        {"author_id": "Jeffrey Williams", "name": "Jeffrey Williams", "is_corresponding": False, "role": "Astronaut"},
        {"author_id": "Eduardo A. C. Almeida", "name": "Eduardo A. C. Almeida", "is_corresponding": True}
    ]
    
    with driver.session(database="neo4j") as session:
        for author in authors:
            # Verificar se tem role (astronaut)
            if "role" in author:
                session.run("""
                    CREATE (a:Author {
                        author_id: $author_id,
                        name: $name,
                        is_corresponding: $is_corresponding,
                        role: $role
                    })
                """, **author)
            else:
                session.run("""
                    CREATE (a:Author {
                        author_id: $author_id,
                        name: $name,
                        is_corresponding: $is_corresponding
                    })
                """, **author)
        print(f"[INFO] Criados {len(authors)} nós de autores")

def create_institution_nodes(driver):
    """Cria os nós das instituições"""
    institutions = [
        # Instituições do primeiro artigo (Cells)
        {"institution_id": "Jichi Medical University", "name": "Jichi Medical University"},
        {"institution_id": "Toranomon Hospital", "name": "Toranomon Hospital"},
        
        # Instituições do segundo artigo (PLOS ONE)
        {"institution_id": "NASA Ames Research Center", "name": "NASA Ames Research Center"},
        {"institution_id": "KBRWyle", "name": "KBRWyle"},
        {"institution_id": "Millenium Engineering & Integration Co", "name": "Millenium Engineering & Integration Co"},
        {"institution_id": "Universities Space Research Association", "name": "Universities Space Research Association"},
        {"institution_id": "Claremont Biosolutions", "name": "Claremont Biosolutions"},
        {"institution_id": "Stanford University", "name": "Stanford University"},
        {"institution_id": "NASA Johnson Space Center", "name": "NASA Johnson Space Center"}
    ]
    
    with driver.session(database="neo4j") as session:
        for institution in institutions:
            session.run("""
                CREATE (i:Institution {
                    institution_id: $institution_id,
                    name: $name
                })
            """, **institution)
        print(f"[INFO] Criados {len(institutions)} nós de instituições")

def create_keyword_nodes(driver):
    """Cria os nós das palavras-chave"""
    keywords = [
        # Palavras-chave do primeiro artigo (Cells)
        {"keyword_id": "adipose-derived stem cell", "term": "adipose-derived stem cell"},
        {"keyword_id": "microgravity culture", "term": "microgravity culture"},
        {"keyword_id": "polystyrene microsphere", "term": "polystyrene microsphere"},
        {"keyword_id": "collagen microsphere", "term": "collagen microsphere"},
        {"keyword_id": "multilineage-differentiating stress-enduring cell", "term": "multilineage-differentiating stress-enduring cell"},
        
        # Palavras-chave do segundo artigo (PLOS ONE)
        {"keyword_id": "RNA isolation", "term": "RNA isolation"},
        {"keyword_id": "qPCR", "term": "quantitative PCR"},
        {"keyword_id": "ISS", "term": "International Space Station"},
        {"keyword_id": "microgravity validation", "term": "microgravity validation"},
        {"keyword_id": "gene expression", "term": "gene expression"}
    ]
    
    with driver.session(database="neo4j") as session:
        for keyword in keywords:
            session.run("""
                CREATE (k:Keyword {
                    keyword_id: $keyword_id,
                    term: $term
                })
            """, **keyword)
        print(f"[INFO] Criados {len(keywords)} nós de palavras-chave")

def create_cell_type_nodes(driver):
    """Cria os nós dos tipos de células"""
    cell_types = [
        # Tipos de células do primeiro artigo (Cells)
        {"cell_type_id": "hASC", "name": "Human Adipose-Derived Stem Cells (hASCs)"},
        {"cell_type_id": "Muse Cell", "name": "Multilineage-Differentiating Stress-Enduring (Muse) Cell"},
        {"cell_type_id": "Embryonic Stem Cell", "name": "Embryonic Stem Cells"},
        
        # Organismos do segundo artigo (PLOS ONE)
        {"cell_type_id": "E. coli", "name": "Escherichia coli", "type": "Prokaryote"},
        {"cell_type_id": "Mouse", "name": "Mouse (Mus musculus)", "type": "Mammal"}
    ]
    
    with driver.session(database="neo4j") as session:
        for cell_type in cell_types:
            if "type" in cell_type:
                session.run("""
                    CREATE (c:CellType {
                        cell_type_id: $cell_type_id,
                        name: $name,
                        organism_type: $type
                    })
                """, **cell_type)
            else:
                session.run("""
                    CREATE (c:CellType {
                        cell_type_id: $cell_type_id,
                        name: $name
                    })
                """, **cell_type)
        print(f"[INFO] Criados {len(cell_types)} nós de tipos de células/organismos")

def create_gene_nodes(driver):
    """Cria os nós dos genes/marcadores"""
    genes = [
        # Genes do primeiro artigo (Cells)
        {"gene_id": "SSEA-3", "name": "Stage-Specific Embryonic Antigen-3 (SSEA-3)"},
        {"gene_id": "OCT4", "name": "Octamer-Binding Transcription Factor 4 (OCT4)"},
        {"gene_id": "SOX2", "name": "(Sex Determining Region Y)-Box 2 (SOX2)"},
        {"gene_id": "NANOG", "name": "NANOG"},
        {"gene_id": "MYC", "name": "MYC"},
        {"gene_id": "KLF4", "name": "Kruppel-Like Factor 4 (KLF4)"},
        {"gene_id": "CD34", "name": "CD34"},
        {"gene_id": "ACTB", "name": "B-actin (ACTB)"},
        
        # Genes do segundo artigo (PLOS ONE)
        {"gene_id": "dnaK", "name": "dnaK (Hsp70)", "organism": "E. coli"},
        {"gene_id": "rpoA", "name": "rpoA", "organism": "E. coli"},
        {"gene_id": "srlR", "name": "srlR", "organism": "E. coli"},
        {"gene_id": "gapdh", "name": "gapdh", "organism": "Mouse"},
        {"gene_id": "rpl19", "name": "rpl19", "organism": "Mouse"},
        {"gene_id": "fn1", "name": "fn1", "organism": "Mouse"}
    ]
    
    with driver.session(database="neo4j") as session:
        for gene in genes:
            if "organism" in gene:
                session.run("""
                    CREATE (g:Gene {
                        gene_id: $gene_id,
                        name: $name,
                        organism: $organism
                    })
                """, **gene)
            else:
                session.run("""
                    CREATE (g:Gene {
                        gene_id: $gene_id,
                        name: $name
                    })
                """, **gene)
        print(f"[INFO] Criados {len(genes)} nós de genes/marcadores")

def create_method_nodes(driver):
    """Cria os nós dos métodos"""
    methods = [
        # Métodos do primeiro artigo (Cells)
        {"method_id": "Microgravity Culture", "name": "Microgravity Culture with Stirred Microspheres"},
        {"method_id": "Flow Cytometry", "name": "Flow Cytometry"},
        {"method_id": "RT-PCR", "name": "Quantitative Real-Time Polymerase Chain Reaction (RT-PCR)"},
        {"method_id": "Immunocytochemistry", "name": "Immunocytochemistry"},
        {"method_id": "Colony-Forming Assay", "name": "Colony-Forming Assay"},
        {"method_id": "Angiogenesis Assay", "name": "In Vitro Angiogenesis (Network Formation) Assay"},
        {"method_id": "Multilineage Differentiation Assay", "name": "Multilineage Differentiation Assay"},
        
        # Métodos do segundo artigo (PLOS ONE)
        {"method_id": "On-Orbit RNA Isolation", "name": "On-Orbit RNA Isolation", "description": "Protocol to extract and purify RNA from samples aboard the ISS"},
        {"method_id": "On-Orbit RT-qPCR", "name": "On-Orbit RT-qPCR", "description": "Real-time gene expression analysis performed in microgravity"},
        {"method_id": "Lyophilized Assays", "name": "Lyophilized Reagents", "description": "Use of freeze-dried, room-temperature stable reagents"}
    ]
    
    with driver.session(database="neo4j") as session:
        for method in methods:
            if "description" in method:
                session.run("""
                    CREATE (m:Method {
                        method_id: $method_id,
                        name: $name,
                        description: $description
                    })
                """, **method)
            else:
                session.run("""
                    CREATE (m:Method {
                        method_id: $method_id,
                        name: $name
                    })
                """, **method)
        print(f"[INFO] Criados {len(methods)} nós de métodos")

def create_material_nodes(driver):
    """Cria os nós dos materiais"""
    materials = [
        # Materiais do primeiro artigo (Cells)
        {"material_id": "Polystyrene Microspheres", "name": "Polystyrene Microspheres"},
        {"material_id": "Collagen Microspheres", "name": "Collagen Microspheres"},
        
        # Hardware do segundo artigo (PLOS ONE)
        {"material_id": "WetLab-2", "name": "WetLab-2 System", "description": "A suite of molecular biology tools for on-orbit gene expression analysis"},
        {"material_id": "SPM", "name": "Sample Preparation Module (SPM)", "description": "An enclosed module for RNA isolation from biological samples in microgravity"},
        {"material_id": "SmartCycler", "name": "Cepheid SmartCycler", "description": "A microgravity-compatible thermal cycler for qPCR"},
        {"material_id": "Pipette Loader", "name": "Pipette Loader (PL)", "description": "A tool for bubble-free fluid transfer in microgravity"},
        {"material_id": "STT", "name": "Sample Transfer Tool (STT)", "description": "Tools like ACT2 or Finger Loop syringes for sample handling"}
    ]
    
    with driver.session(database="neo4j") as session:
        for material in materials:
            if "description" in material:
                session.run("""
                    CREATE (mat:Material {
                        material_id: $material_id,
                        name: $name,
                        description: $description
                    })
                """, **material)
            else:
                session.run("""
                    CREATE (mat:Material {
                        material_id: $material_id,
                        name: $name
                    })
                """, **material)
        print(f"[INFO] Criados {len(materials)} nós de materiais/hardware")

def create_funder_nodes(driver):
    """Cria os nós dos financiadores e colaboradores"""
    funders = [
        # Financiadores do primeiro artigo (Cells)
        {"funder_id": "MHLW Japan", "name": "Ministry of Health, Labour and Welfare of Japan"},
        {"funder_id": "Cell Source Inc", "name": "Cell Source, Inc."},
        
        # Financiadores e colaboradores do segundo artigo (PLOS ONE)
        {"funder_id": "NASA ISS Program", "name": "NASA International Space Station Program", "type": "Funder"},
        {"funder_id": "CASIS", "name": "Center for the Advancement of Science in Space, Inc. (CASIS)", "type": "Collaborator"},
        {"funder_id": "TechShot", "name": "TechShot", "type": "Commercial Collaborator"},
        {"funder_id": "BioGX LLC", "name": "BioGX LLC", "type": "Commercial Collaborator"},
        {"funder_id": "ClaremontBiosolutions", "name": "ClaremontBiosolutions", "type": "Commercial Collaborator"}
    ]
    
    with driver.session(database="neo4j") as session:
        for funder in funders:
            if "type" in funder:
                session.run("""
                    CREATE (f:Funder {
                        funder_id: $funder_id,
                        name: $name,
                        entity_type: $type
                    })
                """, **funder)
            else:
                session.run("""
                    CREATE (f:Funder {
                        funder_id: $funder_id,
                        name: $name
                    })
                """, **funder)
        print(f"[INFO] Criados {len(funders)} nós de financiadores/colaboradores")

def create_mission_nodes(driver):
    """Cria os nós das missões espaciais"""
    missions = [
        {"mission_id": "ISS_SPX-8", "name": "ISS Increment 47 / SpaceX CRS-8", "location": "International Space Station"}
    ]
    
    with driver.session(database="neo4j") as session:
        for mission in missions:
            session.run("""
                CREATE (m:Mission {
                    mission_id: $mission_id,
                    name: $name,
                    location: $location
                })
            """, **mission)
        print(f"[INFO] Criados {len(missions)} nós de missões")

def create_relationships(driver):
    """Cria todos os relacionamentos"""
    with driver.session(database="neo4j") as session:
        
        # Relacionamentos Autor -> Artigo (Primeiro artigo - Cells)
        authors_article1 = ["Takanobu Mashiko", "Koji Kanayama", "Natsumi Saito", "Takako Shirado", 
                           "Rintaro Asahi", "Masanori Mori", "Kotaro Yoshimura"]
        
        for author in authors_article1:
            session.run("""
                MATCH (a:Author {author_id: $author_id})
                MATCH (p:Paper {paper_id: $paper_id})
                CREATE (a)-[:WROTE]->(p)
            """, author_id=author, paper_id="10.3390/cells10030560")
        
        # Relacionamentos Autor -> Artigo (Segundo artigo - PLOS ONE)
        authors_article2 = ["Macarena Parra", "Jimmy Jung", "Travis D. Boone", "Luan Tran", 
                           "Elizabeth A. Blaber", "Kathleen Rubins", "Jeffrey Williams", "Eduardo A. C. Almeida"]
        
        for author in authors_article2:
            session.run("""
                MATCH (a:Author {author_id: $author_id})
                MATCH (p:Paper {paper_id: $paper_id})
                CREATE (a)-[:WROTE]->(p)
            """, author_id=author, paper_id="10.1371/journal.pone.0183480")
        
        # Relacionamentos Autor -> Instituição (Primeiro artigo)
        author_institutions_article1 = [
            ("Takanobu Mashiko", "Jichi Medical University"),
            ("Takanobu Mashiko", "Toranomon Hospital"),
            ("Koji Kanayama", "Jichi Medical University"),
            ("Natsumi Saito", "Jichi Medical University"),
            ("Takako Shirado", "Jichi Medical University"),
            ("Rintaro Asahi", "Jichi Medical University"),
            ("Masanori Mori", "Jichi Medical University"),
            ("Kotaro Yoshimura", "Jichi Medical University")
        ]
        
        for author, institution in author_institutions_article1:
            session.run("""
                MATCH (a:Author {author_id: $author_id})
                MATCH (i:Institution {institution_id: $institution_id})
                CREATE (a)-[:AFFILIATED_WITH]->(i)
            """, author_id=author, institution_id=institution)
        
        # Relacionamentos Autor -> Instituição (Segundo artigo)
        author_institutions_article2 = [
            ("Macarena Parra", "NASA Ames Research Center"),
            ("Kathleen Rubins", "NASA Johnson Space Center"),
            ("Jeffrey Williams", "NASA Johnson Space Center"),
            ("Eduardo A. C. Almeida", "NASA Ames Research Center")
        ]
        
        for author, institution in author_institutions_article2:
            session.run("""
                MATCH (a:Author {author_id: $author_id})
                MATCH (i:Institution {institution_id: $institution_id})
                CREATE (a)-[:AFFILIATED_WITH]->(i)
            """, author_id=author, institution_id=institution)
        
        # Relacionamentos Artigo -> Palavras-chave (Primeiro artigo)
        keywords_article1 = ["adipose-derived stem cell", "microgravity culture", "polystyrene microsphere", 
                            "collagen microsphere", "multilineage-differentiating stress-enduring cell"]
        
        for keyword in keywords_article1:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (k:Keyword {keyword_id: $keyword_id})
                CREATE (p)-[:HAS_KEYWORD]->(k)
            """, paper_id="10.3390/cells10030560", keyword_id=keyword)
        
        # Relacionamentos Artigo -> Palavras-chave (Segundo artigo)
        keywords_article2 = ["RNA isolation", "qPCR", "ISS", "microgravity validation", "gene expression"]
        
        for keyword in keywords_article2:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (k:Keyword {keyword_id: $keyword_id})
                CREATE (p)-[:HAS_KEYWORD]->(k)
            """, paper_id="10.1371/journal.pone.0183480", keyword_id=keyword)
        
        # Relacionamentos Artigo -> Tipos de Células
        session.run("""
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (c:CellType {cell_type_id: $cell_type_id})
            CREATE (p)-[:STUDIES_CELL_TYPE]->(c)
        """, paper_id="10.3390/cells10030560", cell_type_id="hASC")
        
        # Relacionamentos Artigo -> Métodos
        methods = ["Microgravity Culture", "Flow Cytometry", "RT-PCR", "Immunocytochemistry", 
                  "Colony-Forming Assay", "Angiogenesis Assay", "Multilineage Differentiation Assay"]
        
        for method in methods:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (m:Method {method_id: $method_id})
                CREATE (p)-[:USES_METHOD]->(m)
            """, paper_id="10.3390/cells10030560", method_id=method)
        
        # Relacionamentos Artigo -> Materiais
        materials = ["Polystyrene Microspheres", "Collagen Microspheres"]
        
        for material in materials:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (mat:Material {material_id: $material_id})
                CREATE (p)-[:USES_MATERIAL]->(mat)
            """, paper_id="10.3390/cells10030560", material_id=material)
        
        # Relacionamentos Artigo -> Genes/Marcadores
        genes = ["SSEA-3", "OCT4", "SOX2", "NANOG", "MYC", "KLF4", "CD34", "ACTB"]
        
        for gene in genes:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (g:Gene {gene_id: $gene_id})
                CREATE (p)-[:ANALYZES_GENE_MARKER]->(g)
            """, paper_id="10.3390/cells10030560", gene_id=gene)
        
        # Relacionamentos Financiador -> Artigo (Primeiro artigo)
        funders_article1 = ["MHLW Japan", "Cell Source Inc"]
        
        for funder in funders_article1:
            session.run("""
                MATCH (f:Funder {funder_id: $funder_id})
                MATCH (p:Paper {paper_id: $paper_id})
                CREATE (f)-[:FUNDED]->(p)
            """, funder_id=funder, paper_id="10.3390/cells10030560")
        
        # Relacionamentos específicos do segundo artigo (PLOS ONE)
        # Artigo valida hardware/métodos
        session.run("""
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (h:Material {material_id: $hardware_id})
            CREATE (p)-[:VALIDATES]->(h)
        """, paper_id="10.1371/journal.pone.0183480", hardware_id="WetLab-2")
        
        session.run("""
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (m:Method {method_id: $method_id})
            CREATE (p)-[:VALIDATES]->(m)
        """, paper_id="10.1371/journal.pone.0183480", method_id="On-Orbit RNA Isolation")
        
        session.run("""
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (m:Method {method_id: $method_id})
            CREATE (p)-[:VALIDATES]->(m)
        """, paper_id="10.1371/journal.pone.0183480", method_id="On-Orbit RT-qPCR")
        
        # Hardware usado na missão
        session.run("""
            MATCH (h:Material {material_id: $hardware_id})
            MATCH (m:Mission {mission_id: $mission_id})
            CREATE (h)-[:USED_IN]->(m)
        """, hardware_id="WetLab-2", mission_id="ISS_SPX-8")
        
        # Métodos aplicados a organismos
        session.run("""
            MATCH (m:Method {method_id: $method_id})
            MATCH (o:CellType {cell_type_id: $organism_id})
            CREATE (m)-[:APPLIED_TO]->(o)
        """, method_id="On-Orbit RNA Isolation", organism_id="E. coli")
        
        session.run("""
            MATCH (m:Method {method_id: $method_id})
            MATCH (o:CellType {cell_type_id: $organism_id})
            CREATE (m)-[:APPLIED_TO]->(o)
        """, method_id="On-Orbit RNA Isolation", organism_id="Mouse")
        
        # Financiamento do segundo artigo
        session.run("""
            MATCH (f:Funder {funder_id: $funder_id})
            MATCH (p:Paper {paper_id: $paper_id})
            CREATE (f)-[:FUNDED]->(p)
        """, funder_id="NASA ISS Program", paper_id="10.1371/journal.pone.0183480")
        
        print("[INFO] Criados todos os relacionamentos!")

def main():
    """Função principal"""
    print("Iniciando carregamento de dados estruturados no Neo4j...")
    print("=" * 60)
    
    # Conectar ao Neo4j
    driver = connect_to_neo4j()
    if not driver:
        return
    
    try:
        # Limpar banco (opcional - descomente se quiser limpar)
        # clear_database(driver)
        
        # Criar todos os nós
        create_paper_nodes(driver)
        create_author_nodes(driver)
        create_institution_nodes(driver)
        create_keyword_nodes(driver)
        create_cell_type_nodes(driver)
        create_gene_nodes(driver)
        create_method_nodes(driver)
        create_material_nodes(driver)
        create_funder_nodes(driver)
        create_mission_nodes(driver)
        
        # Criar relacionamentos
        create_relationships(driver)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Dados carregados com sucesso no Neo4j!")
        print("\nResumo dos dados carregados:")
        print("- 2 Artigos científicos (Cells + PLOS ONE)")
        print("- 15 Autores (incluindo astronautas)")
        print("- 9 Instituições (universidades, NASA, etc.)")
        print("- 10 Palavras-chave")
        print("- 5 Tipos de células/organismos")
        print("- 14 Genes/Marcadores")
        print("- 10 Métodos")
        print("- 7 Materiais/Hardware")
        print("- 7 Financiadores/Colaboradores")
        print("- 1 Missão espacial (ISS)")
        print("- Múltiplos relacionamentos entre entidades")
        
        print("\nAcesse http://localhost:5000 para visualizar o grafo!")
        
    except Exception as e:
        print(f"[ERROR] Erro durante o carregamento: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
