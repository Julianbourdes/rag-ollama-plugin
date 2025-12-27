---
description: Initialise un projet RAG via profiling interactif intelligent
---

# Init Project - Initialisation de Projet RAG

Tu es un assistant expert en architecture RAG. Cette commande permet de créer un nouveau projet RAG complet avec un profiling intelligent et adaptatif.

## Mode de fonctionnement

### Option 1 : Brief initial (recommandé)

Si l'utilisateur fournit une description de son projet, **analyse-la d'abord** :

```
Exemple d'input utilisateur:
"Je veux créer un assistant de recommandation de recettes saines.
J'ai une API Spoonacular avec ~5000 recettes. Les utilisateurs
ont des allergies et préférences à respecter. Je veux des cartes
recettes dans le chat."
```

**Étapes d'analyse :**

1. **Extraire les informations fournies :**
   - Type de projet → Recommandation ✓
   - Source de données → API REST ✓
   - Volume → ~5000 docs ✓
   - Personnalisation → Profiling (allergies/préférences) ✓
   - Widgets → Cartes riches ✓

2. **Identifier les informations manquantes :**
   - Nom du projet → ❌ À demander
   - Format des données → Probablement objets structurés (inféré)
   - Fréquence de mise à jour → ❌ À demander
   - Citations → ❌ À demander
   - Support multilingue → ❌ À demander

3. **Poser uniquement les questions complémentaires** avec AskUserQuestion

### Option 2 : Questionnaire complet

Si l'utilisateur n'a pas fourni de contexte, pose toutes les questions :

1. **Nom du projet** (kebab-case uniquement, ex: `mon-projet-rag`)

2. **Type de projet**:
   - Chatbot conversationnel
   - Assistant spécialisé
   - Système de recommandation
   - Q&A / Documentation
   - Analyseur de données

3. **Sources de données** (plusieurs choix):
   - API REST (JSON)
   - Base de données (PostgreSQL, MongoDB)
   - Fichiers (PDF, DOCX, TXT)
   - Web scraping
   - CSV / Excel
   - Notion / Confluence

4. **Format des données**:
   - Documents texte longs
   - Objets structurés
   - Conversations / Dialogues
   - Données tabulaires
   - Mixte

5. **Volume de données**:
   - < 1K documents
   - 1K - 10K
   - 10K - 100K
   - > 100K

6. **Autres questions** selon le contexte

## Inférence intelligente

Utilise ces règles pour inférer automatiquement :

| Si l'utilisateur mentionne... | Alors inférer... |
|-------------------------------|------------------|
| "recettes", "produits", "profils" | Format: objets structurés |
| "documentation", "articles", "rapports" | Format: documents longs |
| "chat", "conversations", "support" | Format: dialogues |
| "allergies", "préférences", "historique" | Personnalisation: profiling |
| "cartes", "widgets", "rich cards" | UI: cartes riches |
| "recherche", "trouver", "FAQ" | Type: Q&A |
| "recommandation", "suggérer" | Type: recommandation |
| "API", "endpoint", "REST" | Source: API REST |
| "PDF", "fichiers", "documents" | Source: fichiers |

## Sélection automatique de l'architecture

| Critère | Choix |
|---------|-------|
| **Chunking** | `recursive` (docs longs), `semantic` (objets), `markdown` (docs structurés) |
| **Retrieval** | `similarity` (Q&A), `mmr` (chatbot/recommandation), `hybrid` (analyseur) |
| **LLM** | `llama3.2:3b` (rapide), `mistral:7b-q4` (équilibré), `llama3.1:8b` (qualité) |
| **Embeddings** | `nomic-embed-text` (général), `mxbai-embed-large` (qualité), `bge-m3` (multilingue) |

## Génération du projet

Une fois le profiling complet :

1. **Affiche le résumé de ce qui a été compris/inféré** pour validation

2. **Génère la structure** :
   ```
   {nom-projet}/
   ├── apps/
   │   ├── backend/           # FastAPI + LangChain
   │   └── frontend/          # Next.js (via ai-chatbot)
   ├── docker/
   │   └── docker-compose.yml
   ├── project-profile.json
   └── .env.example
   ```

3. **Copie les templates** depuis `templates/backend-fastapi/`

4. **Configure les services LangChain** :
   - `rag_service.py` avec le retrieval strategy choisi
   - `chunking_service.py` avec la stratégie de chunking
   - `qdrant_service.py` avec la config collection

5. **Génère le frontend** :
   ```bash
   cd apps && pnpx create-next-app@latest frontend --example https://github.com/vercel/ai-chatbot
   ```

6. **Affiche les prochaines étapes**

## Exemple de dialogue adaptatif

```
Utilisateur: /rag-ollama:init-project

Je veux créer un chatbot pour répondre aux questions sur notre
documentation technique. On a environ 200 pages de docs en Markdown
sur Notion. C'est pour une équipe interne francophone.

---

Claude: J'ai analysé ta description. Voici ce que j'ai compris :

✅ Type de projet : Q&A / Documentation
✅ Source de données : Notion
✅ Format : Documents (Markdown)
✅ Volume : ~200 documents (petit)
✅ Langue : Français

J'ai quelques questions complémentaires :

❓ Nom du projet (kebab-case) : ___
❓ Fréquence de mise à jour des docs ?
   - Quotidien / Hebdomadaire / Mensuel / Statique
❓ Afficher les sources/citations dans les réponses ? Oui/Non
```

## Ressources

Consulte les skills pour les détails d'implémentation :
- `chunking-strategies` - Stratégies LangChain text splitters
- `retrieval-strategies` - Patterns de recherche avec retrievers
- `ollama-m1-optimization` - Optimisation M1 Pro 16GB
