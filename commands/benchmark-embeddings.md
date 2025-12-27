---
description: Compare les modèles d'embeddings sur vos données
---

# Benchmark Embeddings - Comparaison des Modèles

Cette commande compare les performances des différents modèles d'embeddings disponibles via Ollama.

## Instructions

1. **Liste les modèles disponibles**:

   | Modèle | Dimensions | Taille | Description | Recommandé pour |
   |--------|-----------|--------|-------------|-----------------|
   | nomic-embed-text | 768 | 274MB | Rapide, usage général | Petit corpus, indexation rapide |
   | mxbai-embed-large | 1024 | 670MB | Haute qualité | Qualité critique, recherche sémantique |
   | all-minilm | 384 | 46MB | Très rapide | Très grand corpus, temps réel |
   | bge-m3 | 1024 | 1.2GB | Multilingue | Multilingue, haute qualité |
   | snowflake-arctic-embed | 1024 | 670MB | Excellent retrieval | RAG, recherche sémantique |

2. **Demande les modèles à tester** (multiselect)

3. **Demande le mode de benchmark**:
   - **Rapide**: 10 documents, 5 queries
   - **Standard**: 100 documents, 20 queries
   - **Complet**: Tous les documents, 50 queries

4. **Vérifie que les modèles sont disponibles**:
   - Si modèles manquants, propose de les télécharger: `ollama pull {model}`

5. **Exécute le benchmark**:

   Pour chaque modèle:
   - Génère les embeddings de tous les documents
   - Mesure le temps moyen par document
   - Pour chaque query de test:
     - Génère l'embedding de la query
     - Calcule les similarités cosinus
     - Mesure le MRR (Mean Reciprocal Rank)
     - Mesure le Recall@5

6. **Affiche les résultats**:

   ```
   ┌─────────────────────┬──────────┬───────┬───────────┬──────┬───────┐
   │ Modèle              │ Temps/doc│ MRR   │ Recall@5  │ RAM  │ Score │
   ├─────────────────────┼──────────┼───────┼───────────┼──────┼───────┤
   │ nomic-embed-text    │ 45ms     │ 0.823 │ 0.876     │ 400MB│ 7.82  │
   │ mxbai-embed-large   │ 120ms    │ 0.891 │ 0.934     │ 800MB│ 8.15  │
   │ ...                 │ ...      │ ...   │ ...       │ ...  │ ...   │
   └─────────────────────┴──────────┴───────┴───────────┴──────┴───────┘
   ```

7. **Affiche les recommandations**:
   - Meilleur équilibre (score global)
   - Plus rapide (temps/doc minimal)
   - Meilleure qualité (MRR maximal)

8. **Propose de mettre à jour la configuration** du projet avec le modèle recommandé

## Métriques calculées

| Métrique | Description | Poids dans score |
|----------|-------------|------------------|
| **Temps/doc** | Temps moyen pour générer un embedding | 20% |
| **MRR** | Mean Reciprocal Rank (position du 1er résultat pertinent) | 50% |
| **Recall@5** | % de documents pertinents dans les 5 premiers | 30% |

## Score global

```
Score = (MRR * 0.5 + Recall@5 * 0.3 + SpeedScore * 0.2) * 10
SpeedScore = 1 - min(avgTime / 1000, 1)
```

## Estimation RAM par modèle

| Modèle | RAM modèle | + 100 docs | Total estimé |
|--------|-----------|------------|--------------|
| nomic-embed-text | 400MB | 10MB | ~410MB |
| mxbai-embed-large | 800MB | 10MB | ~810MB |
| all-minilm | 150MB | 5MB | ~155MB |
| bge-m3 | 1400MB | 10MB | ~1410MB |

Pour M1 Pro 16GB, garder le total < 8GB pour laisser de la marge au LLM.
