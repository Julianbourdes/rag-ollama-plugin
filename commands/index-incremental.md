---
description: Indexation incrémentale des données
---

# Index Incremental - Indexation Incrémentale

Cette commande met à jour l'index Qdrant avec les nouvelles données ou modifications sans réindexer tout le corpus.

## Instructions

1. **Vérifie qu'un projet RAG existe** (présence de `project-profile.json`)

2. **Vérifie les sources de données configurées**

3. **Demande quelle source indexer**:
   - Toutes les sources
   - Ou une source spécifique

4. **Demande le mode d'indexation**:
   - **Nouveaux uniquement**: Indexe seulement les documents jamais vus
   - **Nouveaux + Modifiés**: Indexe les nouveaux et met à jour les modifiés
   - **Réindexation complète**: Supprime et réindexe tout
   - **Delta depuis timestamp**: Indexe les changements depuis une date

5. **Si mode Delta**, demande la date:
   - Format: YYYY-MM-DD
   - Ou raccourcis: `yesterday`, `last_week`, `last_month`

6. **Demande la taille des batchs** (recommandé: 50-100)

7. **Affiche le récapitulatif** et demande confirmation

8. **Exécute l'indexation**:

   Pour chaque source:

   a. **Récupère les documents** selon le type de source:
      - API REST: Fetch via le client généré
      - Fichiers: Lecture du dossier avec filtrage par date si delta
      - Base de données: Query SQL/MongoDB

   b. **Compare avec l'index existant** (via hash des contenus):
      - Documents nouveaux → à indexer
      - Documents modifiés (hash différent) → à mettre à jour
      - Documents supprimés (plus dans la source) → à supprimer

   c. **Génère les embeddings** par batch:
      ```bash
      curl -X POST http://localhost:11434/api/embeddings \
        -d '{"model": "nomic-embed-text", "prompt": "..."}'
      ```

   d. **Upsert dans Qdrant**:
      ```bash
      curl -X PUT http://localhost:6333/collections/{collection}/points \
        -d '{"points": [...]}'
      ```

   e. **Supprime les documents obsolètes** (si mode approprié)

9. **Affiche le résumé**:
   ```
   📊 Résumé de l'indexation :
   - Documents indexés: 150
   - Documents mis à jour: 23
   - Documents supprimés: 5
   - Erreurs: 0
   - Durée totale: 45s
   ```

10. **Met à jour project-profile.json** avec le timestamp de dernière indexation

11. **Propose un test rapide** de query sur l'index mis à jour

## Détection des modifications

Chaque document est hashé (contenu + metadata) pour détecter les changements:

```python
hash = hashlib.md5(json.dumps({
    "content": doc.content,
    "metadata": doc.metadata
}).encode()).hexdigest()
```

Le hash est stocké dans les metadata Qdrant pour comparaison future.

## Endpoints Qdrant utilisés

| Action | Endpoint |
|--------|----------|
| Scroll existing | POST /collections/{name}/points/scroll |
| Upsert | PUT /collections/{name}/points |
| Delete | POST /collections/{name}/points/delete |
| Create collection | PUT /collections/{name} |

## Optimisations M1 Pro

- Batch size: 50-100 pour équilibrer mémoire et vitesse
- Parallélisme: 4 requêtes embeddings simultanées max
- Timeout: 30s par requête embedding
