---
description: Teste la pipeline RAG end-to-end
---

# Test RAG - Test Pipeline End-to-End

Cette commande vérifie que tous les composants de la pipeline RAG fonctionnent correctement.

## Instructions

1. **Vérifie qu'un projet RAG existe** (présence de `project-profile.json`)

2. **Exécute les tests de santé**:

   ### Test 1: Connexion Qdrant
   ```bash
   curl http://localhost:6333/collections
   ```
   - Vérifie que Qdrant est accessible
   - Compte le nombre de collections

   ### Test 2: Modèle LLM Ollama
   ```bash
   curl http://localhost:11434/api/tags
   ```
   - Vérifie qu'Ollama est accessible
   - Vérifie que le modèle LLM configuré est disponible
   - Teste une génération rapide: "Réponds par OK uniquement"

   ### Test 3: Modèle Embeddings Ollama
   ```bash
   curl -X POST http://localhost:11434/api/embeddings \
     -d '{"model": "nomic-embed-text", "prompt": "Test"}'
   ```
   - Vérifie que le modèle d'embeddings est disponible
   - Affiche le nombre de dimensions

   ### Test 4: Pipeline RAG complète
   - Seulement si les tests 1-3 passent
   - Teste une query via l'API backend

3. **Affiche le résumé des tests**:
   ```
   ✓ Qdrant: Connecté, X collection(s)
   ✓ LLM: mistral:7b-instruct-q4_0 opérationnel
   ✓ Embeddings: nomic-embed-text (768 dimensions)
   ✓ Pipeline RAG: Fonctionnelle
   ```

4. **En cas d'échec, affiche les suggestions**:

   | Composant | Suggestions |
   |-----------|-------------|
   | Qdrant | Vérifier Docker, `docker-compose ps`, variables QDRANT_HOST/PORT |
   | Ollama LLM | Vérifier Ollama installé, `ollama pull {model}`, variable OLLAMA_BASE_URL |
   | Ollama Embeddings | Idem LLM, vérifier le modèle d'embeddings |
   | Pipeline | Vérifier le backend FastAPI, les logs |

5. **Propose un test interactif** (optionnel):
   - Demande une query à l'utilisateur
   - Exécute la query via l'API
   - Affiche la réponse et les sources utilisées
   - Affiche le temps de réponse

## Endpoints à tester

| Service | URL | Description |
|---------|-----|-------------|
| Qdrant REST | http://localhost:6333 | Vector database |
| Ollama | http://localhost:11434 | LLM server |
| Backend | http://localhost:8000 | FastAPI |
| Frontend | http://localhost:3000 | Next.js |

## Variables d'environnement vérifiées

- `QDRANT_HOST` (default: localhost)
- `QDRANT_PORT` (default: 6333)
- `OLLAMA_BASE_URL` (default: http://localhost:11434)
- `OLLAMA_MODEL`
- `OLLAMA_EMBEDDINGS_MODEL`
- `BACKEND_URL` (default: http://localhost:8000)
