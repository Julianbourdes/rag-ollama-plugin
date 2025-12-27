# Guide d'utilisation du plugin RAG Ollama

Ce document explique comment utiliser le plugin et ce que vous devez fournir au démarrage d'un projet.

## Prérequis

### 1. Configuration des variables d'environnement

Créez un fichier `.env` à la racine de votre projet avec :

```bash
# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-q4_0
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text

# Qdrant (vector database)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# PostgreSQL (optionnel - pour conversations/metadata)
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# GitHub (pour MCP server)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Chemin du projet (pour MCP filesystem)
PROJECT_PATH=/chemin/vers/votre/projet
```

### 2. Services requis

```bash
# Installer et démarrer Ollama
brew install ollama
ollama serve

# Télécharger les modèles recommandés
ollama pull mistral:7b-instruct-q4_0
ollama pull nomic-embed-text

# Démarrer Qdrant (via Docker)
docker run -d -p 6333:6333 qdrant/qdrant
```

---

## Démarrage d'un nouveau projet

### Méthode 1 : Brief initial (recommandé)

Décrivez simplement votre projet, le plugin analysera et posera uniquement les questions complémentaires :

```bash
/rag-ollama:init-project

Je veux créer un assistant de recommandation de recettes saines.
J'ai une API Spoonacular avec ~5000 recettes en JSON.
Les utilisateurs ont des allergies et préférences alimentaires à respecter.
Je voudrais afficher des cartes recettes dans le chat.
```

**Réponse du plugin :**

```
📊 Analyse de ton projet :

✅ Identifié :
   - Type : Système de recommandation
   - Source : API REST (Spoonacular)
   - Format : Objets structurés (recettes JSON)
   - Volume : ~5000 documents (petit)

🔍 Inféré :
   - Personnalisation : Profiling (allergies/préférences mentionnées)
   - UI : Cartes riches (cartes recettes demandées)

❓ Questions complémentaires :
```

Le plugin posera ensuite uniquement les questions manquantes (nom du projet, fréquence de mise à jour, citations, langue).

### Méthode 2 : Questionnaire guidé

Si vous préférez être guidé, lancez simplement la commande sans description :

```bash
/rag-ollama:init-project
```

Le plugin posera alors toutes les questions :
- Type de projet
- Sources de données
- Format des données
- Volume
- Personnalisation
- Widgets UI
- etc.

### Exemples de descriptions initiales

**Assistant documentation :**
```
Un chatbot pour notre documentation technique interne.
200 pages de docs Markdown sur Notion.
Équipe francophone, besoin de citer les sources.
```

**Système de recommandation produits :**
```
Recommander des produits e-commerce basé sur les préférences.
API catalogue avec 50K produits, mise à jour quotidienne.
Filtrage par catégorie, prix, disponibilité.
Afficher des cartes produits avec images.
```

**Q&A support client :**
```
Répondre aux questions fréquentes des clients.
Base de tickets Zendesk + FAQ existante.
Besoin de précision, éviter les mauvaises réponses.
```

---

## Structure du projet généré

Après le profiling, le plugin génère :

```
mon-projet-rag/
├── apps/
│   ├── backend/                    # FastAPI + LangChain
│   │   ├── app/
│   │   │   ├── api/routes/
│   │   │   │   ├── chat.py         # Endpoint chat RAG
│   │   │   │   ├── rag.py          # Endpoints indexation
│   │   │   │   └── health.py       # Health checks
│   │   │   ├── services/
│   │   │   │   ├── rag_service.py      # LangChain chains (LCEL)
│   │   │   │   ├── ollama_service.py   # ChatOllama + OllamaEmbeddings
│   │   │   │   ├── qdrant_service.py   # QdrantVectorStore + retrievers
│   │   │   │   └── chunking_service.py # Text splitters
│   │   │   ├── core/
│   │   │   │   └── config.py       # Settings Pydantic
│   │   │   ├── models/
│   │   │   └── schemas/
│   │   └── requirements.txt        # LangChain packages inclus
│   │
│   └── frontend/                   # Next.js (ai-chatbot Vercel)
│       ├── app/(chat)/page.tsx     # Page chat principale
│       ├── components/
│       │   ├── sources-panel.tsx   # Affichage sources RAG
│       │   └── ...
│       └── lib/hooks/
│
├── docker/
│   └── docker-compose.yml          # Qdrant + backend + frontend
│
├── project-profile.json            # Configuration du projet
├── .env.example
├── .mcp.json                       # Config MCP servers
└── pnpm-workspace.yaml
```

---

## Fichier project-profile.json

Ce fichier est généré automatiquement et contient toute la configuration :

```json
{
  "name": "mon-assistant-recettes",
  "type": "recommendation",
  "description": "Assistant de recommandation de recettes saines",

  "dataSources": [
    {
      "name": "recettes",
      "type": "api",
      "endpoint": "https://api.example.com/recipes",
      "auth": "api_key",
      "refreshInterval": "daily"
    }
  ],

  "architecture": {
    "chunking": "semantic_object",
    "retrieval": "mmr",
    "llm": "mistral:7b-instruct-q4_0",
    "embeddings": "nomic-embed-text"
  },

  "features": {
    "userProfiling": true,
    "multimodal": false,
    "customWidgets": ["recipe-card", "ingredient-list"],
    "voiceInput": false,
    "citations": true
  },

  "constraints": {
    "ramBudget": "8GB",
    "platform": "m1-pro-16gb"
  }
}
```

---

## Commandes disponibles après init

```bash
# Ajouter une nouvelle source de données
/rag-ollama:add-data-source

# Ajouter une feature optionnelle
/rag-ollama:add-feature

# Tester la pipeline RAG
/rag-ollama:test-rag

# Indexation incrémentale
/rag-ollama:index-incremental

# Déployer
/rag-ollama:deploy
```

---

## MCP Servers disponibles

Les serveurs MCP sont configurés dans `.mcp.json` :

| Serveur | Utilité pour RAG |
|---------|------------------|
| `docs-langchain` | Documentation LangChain pour RAG |
| `postgres` | Accès direct PostgreSQL pour metadata |
| `memory` | Mémoire persistante du contexte projet |
| `fetch` | Récupérer docs Ollama, Qdrant |
| `sequential-thinking` | Raisonnement complexe architecture |
| `shadcn` | Composants UI pour frontend |

---

## Hooks configurés

Les hooks dans `.claude/settings.json` s'exécutent automatiquement :

| Hook | Déclencheur | Action |
|------|-------------|--------|
| `lint-python.sh` | Write/Edit fichier .py | Ruff lint + format |
| `lint-typescript.sh` | Write/Edit fichier .ts/.tsx | ESLint + Prettier |

---

## Exemple complet : Assistant de recettes

### 1. Lancer le profiling

```bash
/rag-ollama:init-project
```

### 2. Répondre aux questions

```
Type: Recommandation de recettes saines
Source: API REST (Spoonacular ou similar)
Volume: ~5,000 recettes
Features: Profiling nutritionnel, cartes recettes, citations
Critères: Respecter allergies, temps de préparation < 30min
```

### 3. Résultat

Le plugin génère automatiquement :
- Backend FastAPI avec **LangChain chains** pour le RAG
- Chunking configurable via `chunking_service.py`
- Retrieval MMR via `qdrant.get_retriever(search_type="mmr")`
- Frontend avec composant RecipeCard
- Filtres Qdrant sur allergies et temps de préparation

### Services LangChain générés

```python
# Exemple d'utilisation des services
from app.services.rag_service import get_rag_service
from app.services.chunking_service import get_chunking_service

# RAG avec streaming
rag = get_rag_service()
async for chunk in rag.query("Recettes végétariennes rapides"):
    print(chunk)

# Ou via chain complète
chain = rag.create_rag_chain(search_type="mmr", k=5)
result = chain.invoke({"input": "Recettes sans gluten"})

# Chunking des documents
chunking = get_chunking_service()
docs = chunking.split_text(
    recipe_text,
    strategy="semantic",
    chunk_size=500
)
```

### 4. Tester

```bash
pnpm dev
# Ouvrir http://localhost:3000
# Taper: "Suggère-moi des recettes végétariennes rapides"
```

---

## FAQ

### Q: Dois-je fournir un schéma de données ?

**R:** Non, le plugin analyse un échantillon de vos données et génère le schéma automatiquement (Pydantic, TypeScript, Qdrant payload).

### Q: Puis-je modifier la configuration après init ?

**R:** Oui, modifiez `project-profile.json` ou utilisez les commandes :
- `/rag-ollama:add-data-source` pour ajouter des sources
- `/rag-ollama:add-feature` pour activer des features

### Q: Comment ajouter des filtres métier ?

**R:** Décrivez vos critères lors du profiling. L'agent `data-modeler` créera les indexes Qdrant appropriés.

### Q: Le frontend est-il personnalisable ?

**R:** Oui, l'agent `frontend-customizer` modifie le template ai-chatbot Vercel existant sans créer de nouvelles pages.
