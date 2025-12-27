# 🚀 RAG Ollama Plugin

Plugin Claude Code **générique et adaptatif** pour créer N'IMPORTE QUELLE application RAG (Retrieval-Augmented Generation) avec FastAPI, LangChain, Qdrant, Ollama et Next.js.

## ✨ Caractéristiques

- **🧠 Profiling Intelligent**: Pose des questions pour comprendre votre projet et génère l'architecture optimale
- **⚡ Optimisé M1 Pro 16GB**: Configuration pré-optimisée pour Apple Silicon
- **🔧 Adaptatif**: S'adapte à tout type de projet RAG (chatbot, recommandation, Q&A, etc.)
- **📦 Monorepo**: Structure moderne avec pnpm workspaces et Turborepo
- **🐳 Docker Ready**: Déploiement local et production simplifié

## 🛠️ Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python 3.10+) |
| Frontend | Next.js 14+ (template ai-chatbot Vercel) |
| RAG | LangChain |
| Vector DB | Qdrant |
| LLM | Ollama (local) |
| Architecture | Monorepo (pnpm + Turborepo) |

## 📥 Installation

```bash
# Via le marketplace Claude Code
/plugin install rag-ollama

# Ou manuellement
git clone <repo> ~/.claude/plugins/rag-ollama
```

## 🚀 Quick Start

### 1. Créer un nouveau projet

```bash
/rag-ollama:init-project
```

Le plugin vous posera des questions pour comprendre votre projet:
- Type de projet (chatbot, recommandation, Q&A...)
- Sources de données (API, fichiers, base de données...)
- Features nécessaires (profiling, multimodal, widgets...)

### 2. Configurer l'environnement

```bash
cd mon-projet-rag
cp .env.example .env
# Éditer .env avec vos configurations
```

### 3. Démarrer les services

```bash
# Démarrer Qdrant
pnpm docker:up

# Installer Ollama et télécharger les modèles
ollama pull mistral:7b-instruct-q4_0
ollama pull nomic-embed-text

# Lancer le développement
pnpm dev
```

## 📋 Commands Disponibles

| Command | Description |
|---------|-------------|
| `/rag-ollama:init-project` | Crée un nouveau projet via profiling interactif |
| `/rag-ollama:init-monorepo` | Setup monorepo sans profiling |
| `/rag-ollama:add-data-source` | Configure une nouvelle source de données |
| `/rag-ollama:add-feature` | Ajoute une feature optionnelle |
| `/rag-ollama:test-rag` | Teste la pipeline RAG end-to-end |
| `/rag-ollama:benchmark-embeddings` | Compare les modèles d'embeddings |
| `/rag-ollama:index-incremental` | Indexation incrémentale des données |
| `/rag-ollama:deploy` | Build et deploy Docker |

## 🤖 Agents Disponibles

| Agent | Description |
|-------|-------------|
| `project-profiler` | Comprend votre projet via questions intelligentes |
| `architecture-designer` | Design l'architecture RAG optimale |
| `data-modeler` | Génère les schemas (Pydantic, TypeScript, Qdrant) |
| `api-integrator` | Intégration API REST générique |
| `ollama-optimizer` | Optimisation pour M1 Pro 16GB |
| `qdrant-tuner` | Configuration Qdrant optimale |
| `frontend-customizer` | Personnalisation du template ai-chatbot |
| `feature-generator` | Génère des features custom |

## 📚 Skills (Documentation)

| Skill | Description |
|-------|-------------|
| `chunking-strategies` | Stratégies de découpage de texte |
| `retrieval-strategies` | Patterns de recherche RAG |
| `ollama-m1-optimization` | Optimisations Apple Silicon |
| `fastapi-async-patterns` | Best practices FastAPI async |
| `vercel-ai-sdk-rag` | Intégration Vercel AI SDK |

## 🎯 Exemples de Projets

Le plugin s'adapte à tout type de projet RAG:

### Assistant de cuisine saine
```
Type: Recommandation
Data: API recettes
Features: Profiling nutritionnel, widgets cartes recettes
```

### Documentation interne
```
Type: Q&A
Data: Confluence/Notion API
Features: Citations, recherche avancée
```

### Coach linguistique
```
Type: Assistant spécialisé
Data: Contenus pédagogiques
Features: STT/TTS, feedback temps réel
```

## ⚙️ Architecture Adaptative

Le plugin analyse votre projet et choisit automatiquement:

| Critère | Options |
|---------|---------|
| **Chunking** | Recursive (docs) / Semantic (objets) / Code-aware |
| **Retrieval** | Similarity / MMR / Hybrid / Score Threshold |
| **LLM** | llama3.2:3b (rapide) / mistral:7b (équilibré) / llama3.1:8b (qualité) |
| **Embeddings** | nomic-embed-text / mxbai-embed-large / bge-m3 |

## 💻 Optimisations M1 Pro 16GB

Configuration optimisée pour Apple Silicon:

```bash
# Variables d'environnement recommandées
export OLLAMA_USE_METAL=1
export OLLAMA_NUM_THREAD=8
export OLLAMA_NUM_GPU=999
export OLLAMA_CONTEXT_SIZE=4096
```

### Combinaisons recommandées

| Combo | LLM | Embeddings | RAM Total |
|-------|-----|------------|-----------|
| Fast | llama3.2:3b | nomic-embed-text | ~4GB |
| **Balanced** ⭐ | mistral:7b-q4 | nomic-embed-text | ~6GB |
| Quality | llama3.1:8b-q4 | mxbai-embed-large | ~8GB |

## 🔧 Structure du projet généré

```
mon-projet-rag/
├── apps/
│   ├── backend/           # FastAPI
│   │   ├── app/
│   │   │   ├── api/routes/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   └── schemas/
│   │   └── requirements.txt
│   └── frontend/          # Next.js
│       ├── app/
│       ├── components/
│       └── lib/
├── packages/
│   └── shared/            # Code partagé
├── docker/
│   └── docker-compose.yml
├── project-profile.json   # Configuration du projet
└── .env
```

## 🐳 Déploiement

### Local (Docker Compose)

```bash
/rag-ollama:deploy
# Choisir "Local (développement)" ou "Local (production)"
```

### Production

```bash
/rag-ollama:deploy
# Choisir "Docker Hub" ou "GitHub Container Registry"
```

## 🔍 Troubleshooting

### Ollama non accessible

```bash
# Vérifier qu'Ollama est lancé
ollama list

# Si nécessaire, redémarrer
killall ollama && ollama serve
```

### Qdrant connection error

```bash
# Vérifier que Docker est lancé
docker ps

# Redémarrer Qdrant
pnpm docker:down && pnpm docker:up
```

### Out of memory

1. Réduire `OLLAMA_CONTEXT_SIZE` à 2048
2. Utiliser un modèle plus petit (llama3.2:3b)
3. Fermer les applications gourmandes

## 🤝 Contributing

Contributions bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT

---

Généré avec ❤️ par [Claude Code](https://claude.ai/claude-code)
