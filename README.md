# NASA Space Apps Maceió - Document Analysis with Neo4j

Este projeto é uma aplicação web que analisa documentos PDF, extrai entidades e relacionamentos usando processamento de linguagem natural (NLP), e visualiza os dados em um grafo usando Neo4j.

## 🚀 Instalação

### Instalação das Dependências
```bash
# 1. Atualizar pip
python -m pip install --upgrade pip

# 2. Instalar dependências Python
pip install Flask Flask-CORS PyMuPDF neo4j python-dotenv spacy

# 3. Baixar modelo de linguagem spaCy
python -m spacy download en_core_web_lg

# 4. Criar diretório de uploads
mkdir uploads
```

## 📋 Pré-requisitos

### Python
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Neo4j
- Neo4j Desktop ou Neo4j Community Edition
- Banco de dados rodando em `localhost:7687`
- Credenciais padrão: `neo4j` / `12345678`

### Download do Neo4j
1. Acesse: https://neo4j.com/download/
2. Baixe a versão Community Edition
3. Instale e configure uma nova instância
4. Defina a senha como `12345678` (ou atualize as credenciais em `app.py`)

## 🛠️ Dependências

O projeto utiliza as seguintes bibliotecas Python:

- **Flask** (2.3.3) - Framework web
- **Flask-CORS** (4.0.0) - CORS para requisições cross-origin
- **spaCy** (3.7.2) - Processamento de linguagem natural
- **PyMuPDF** (1.23.8) - Extração de texto de PDFs
- **neo4j** (5.14.1) - Driver para banco de dados Neo4j
- **python-dotenv** (1.0.0) - Gerenciamento de variáveis de ambiente

## 🎯 Como Usar

### 1. Iniciar a Aplicação
```bash
python app.py
```

### 2. Acessar a Interface
Abra seu navegador e acesse: `http://localhost:5000`

### 3. Upload e Processamento
1. Faça upload de um arquivo PDF
2. A aplicação irá:
   - Extrair o texto do PDF
   - Processar com spaCy para identificar entidades
   - Criar relacionamentos entre entidades
   - Salvar no banco Neo4j
   - Visualizar no grafo interativo

### 4. Visualização
- **Grafo Interativo**: Visualize entidades e relacionamentos
- **Clique nos Nós**: Abre pesquisa no Google para a entidade
- **Lista de Nós**: Veja todas as entidades extraídas

## 🔧 Configuração

### Neo4j
Para alterar as configurações do Neo4j, edite as variáveis em `app.py`:

```python
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")  # Altere aqui se necessário
```

### Modelo de Linguagem
O projeto usa o modelo `en_core_web_lg` do spaCy. Para usar outro idioma:

1. Baixe o modelo desejado:
```bash
python -m spacy download pt_core_news_lg  # Para português
```

2. Atualize o código em `app.py`:
```python
NLP_MODEL = spacy.load("pt_core_news_lg")
```

## 📁 Estrutura do Projeto

```
nasa-space-apps-maceio/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
├── templates/
│   └── index.html        # Interface web
├── uploads/              # Diretório para arquivos PDF (criado automaticamente)
└── SB_publication_PMC.csv # Dados de exemplo
```

## 🐛 Solução de Problemas

### Erro: "spaCy model not found"
```bash
python -m spacy download en_core_web_lg
```

### Erro: "Neo4j connection failed"
1. Verifique se o Neo4j está rodando
2. Confirme as credenciais em `app.py`
3. Teste a conexão: `http://localhost:7474`


### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

## 🚀 Funcionalidades

- ✅ Upload de PDFs
- ✅ Extração de texto
- ✅ Processamento NLP com spaCy
- ✅ Identificação de entidades (PERSON, ORG, LOC, DATE, etc.)
- ✅ Criação de relacionamentos
- ✅ Armazenamento em Neo4j
- ✅ Visualização interativa de grafos
- ✅ Interface web moderna com tema escuro
- ✅ Pesquisa automática no Google ao clicar em entidades

## 📊 API Endpoints

- `GET /` - Interface principal
- `GET /api/data` - Dados do grafo para visualização
- `GET /api/nodes` - Lista de todos os nós
- `POST /upload` - Upload e processamento de PDF

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto foi desenvolvido para o NASA Space Apps Challenge 2024 em Maceió.

---

**Desenvolvido com ❤️ para o NASA Space Apps Challenge**
