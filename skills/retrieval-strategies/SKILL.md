---
name: retrieval-strategies
description: Guide des différentes stratégies de recherche pour optimiser la qualité des réponses RAG
allowed-tools: Read, Grep, Glob
---

# Stratégies de Retrieval pour RAG

Guide des différentes stratégies de recherche pour optimiser la qualité des réponses RAG.

## Vue d'ensemble

Le retrieval est le cœur du RAG. La qualité de la réponse dépend directement de la pertinence des documents récupérés.

## Services RAG du template

Le template backend inclut un service RAG complet avec toutes les stratégies :

```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()

# Retriever avec stratégie
retriever = rag.get_retriever(search_type="mmr", k=5)

# Query avec streaming
async for chunk in rag.query("Ma question", search_type="similarity"):
    print(chunk)
```

## 1. Similarity Search (Défaut)

**Description:** Recherche par similarité cosinus simple

**Quand l'utiliser:**
- Corpus petit à moyen (< 10K docs)
- Requêtes simples et directes
- Besoin de rapidité

```python
from langchain_qdrant import QdrantVectorStore

# Configuration de base
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 5  # Nombre de documents à retourner
    }
)

# Recherche
docs = retriever.get_relevant_documents("Comment configurer le système ?")
```

### Paramètres clés

| Paramètre | Description | Recommandation |
|-----------|-------------|----------------|
| k | Nombre de résultats | 3-10 selon le contexte LLM |

## 2. MMR (Maximal Marginal Relevance)

**Description:** Équilibre entre pertinence et diversité

**Quand l'utiliser:**
- Éviter les réponses redondantes
- Couvrir plusieurs aspects d'une question
- Grand corpus avec documents similaires

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,           # Documents finaux
        "fetch_k": 20,    # Candidats à filtrer
        "lambda_mult": 0.5  # 0=diversité max, 1=pertinence max
    }
)
```

### Comprendre lambda_mult

```
lambda_mult = 0.0  → Maximum de diversité (risque de perdre en pertinence)
lambda_mult = 0.5  → Équilibre recommandé
lambda_mult = 0.7  → Priorité pertinence avec un peu de diversité
lambda_mult = 1.0  → Équivalent à similarity search
```

### Exemple pratique

```python
# Pour un chatbot de recommandation produits
# On veut des suggestions diverses, pas 5 fois le même produit
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 30,      # Plus de candidats = meilleure diversité
        "lambda_mult": 0.4  # Favoriser la diversité
    }
)
```

## 3. Similarity Score Threshold

**Description:** Ne retourne que les résultats au-dessus d'un seuil de confiance

**Quand l'utiliser:**
- Domaines critiques (médical, légal)
- Éviter les hallucinations
- Préférer "je ne sais pas" à une mauvaise réponse

```python
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.7,  # Seuil de similarité (0-1)
        "k": 5  # Maximum de documents
    }
)

# Peut retourner 0-5 documents selon la pertinence
docs = retriever.get_relevant_documents("question très spécifique")

if not docs:
    response = "Je n'ai pas trouvé d'information pertinente à ce sujet."
```

### Calibration du seuil

```python
def calibrate_threshold(vectorstore, test_queries, expected_docs):
    """Trouve le seuil optimal"""
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    results = []

    for threshold in thresholds:
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": threshold, "k": 10}
        )

        precision = 0
        recall = 0

        for query, expected in zip(test_queries, expected_docs):
            docs = retriever.get_relevant_documents(query)
            found_ids = {d.metadata["id"] for d in docs}

            if expected:
                precision += len(found_ids & expected) / len(found_ids) if found_ids else 0
                recall += len(found_ids & expected) / len(expected)

        results.append({
            "threshold": threshold,
            "precision": precision / len(test_queries),
            "recall": recall / len(test_queries)
        })

    return results
```

## 4. Hybrid Search (BM25 + Vector)

**Description:** Combine recherche lexicale et sémantique

**Quand l'utiliser:**
- Requêtes avec mots-clés importants
- Termes techniques ou acronymes
- Besoin de précision sur des termes exacts

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_qdrant import QdrantVectorStore

# BM25 pour la recherche lexicale
bm25_retriever = BM25Retriever.from_texts(
    texts,
    metadatas=metadatas
)
bm25_retriever.k = 5

# Retriever vectoriel
vector_retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}
)

# Combinaison avec pondération
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]  # 30% BM25, 70% vecteurs
)
```

### Ajuster les poids

```
[0.5, 0.5]  → Équilibre (usage général)
[0.3, 0.7]  → Favorise la sémantique (recommandé pour RAG)
[0.7, 0.3]  → Favorise les mots-clés (recherche technique)
[0.2, 0.8]  → Presque tout sémantique avec safety net lexical
```

## 5. Contextual Compression

**Description:** Compresse les documents après retrieval pour ne garder que le pertinent

**Quand l'utiliser:**
- Documents longs avec peu d'information pertinente
- Réduire la taille du contexte LLM
- Améliorer la précision

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Compresseur basé sur LLM
compressor = LLMChainExtractor.from_llm(llm)

# Retriever de base
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Retriever avec compression
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# Les documents sont filtrés et compressés
docs = compression_retriever.get_relevant_documents("question")
```

## 6. Self-Query Retriever

**Description:** Extrait automatiquement les filtres depuis la requête

**Quand l'utiliser:**
- Données avec métadonnées riches
- Requêtes incluant des critères (date, catégorie, etc.)
- Interface conversationnelle naturelle

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# Définir les métadonnées filtrables
metadata_field_info = [
    AttributeInfo(
        name="category",
        description="La catégorie du document (article, guide, faq)",
        type="string"
    ),
    AttributeInfo(
        name="date",
        description="Date de publication",
        type="date"
    ),
    AttributeInfo(
        name="author",
        description="Auteur du document",
        type="string"
    )
]

# Créer le retriever
self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="Documentation technique",
    metadata_field_info=metadata_field_info
)

# Requête avec filtres implicites
docs = self_query_retriever.get_relevant_documents(
    "Montre-moi les guides de 2024 écrits par Marie"
)
# → Filtre automatiquement: category="guide", date>=2024, author="Marie"
```

## 7. Multi-Query Retriever

**Description:** Génère plusieurs variantes de la requête pour améliorer le recall

**Quand l'utiliser:**
- Requêtes ambiguës
- Améliorer la couverture
- Questions complexes

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

# Génère automatiquement des variantes
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

# Une requête devient plusieurs
docs = multi_query_retriever.get_relevant_documents(
    "Comment améliorer les performances ?"
)
# Génère: "optimisation de la performance", "accélérer le système", etc.
```

## Sélection automatique

```python
def select_retrieval_strategy(
    corpus_size: int,
    query_type: str,
    domain: str,
    has_metadata: bool
) -> dict:
    """Recommande la stratégie optimale"""

    if domain in ["medical", "legal", "finance"]:
        return {
            "strategy": "similarity_score_threshold",
            "config": {"score_threshold": 0.8, "k": 5},
            "reason": "Domaine critique - éviter les fausses réponses"
        }

    if has_metadata and query_type == "filtered":
        return {
            "strategy": "self_query",
            "reason": "Requêtes avec critères de filtrage"
        }

    if corpus_size > 100000:
        return {
            "strategy": "mmr",
            "config": {"k": 5, "fetch_k": 30, "lambda_mult": 0.6},
            "reason": "Grand corpus - besoin de diversité"
        }

    if query_type == "technical":
        return {
            "strategy": "hybrid",
            "config": {"weights": [0.4, 0.6]},
            "reason": "Termes techniques - BM25 pour mots-clés"
        }

    # Default
    return {
        "strategy": "similarity",
        "config": {"k": 5},
        "reason": "Configuration standard efficace"
    }
```

## Métriques de qualité

```python
def evaluate_retrieval(
    retriever,
    test_queries: list,
    ground_truth: list
) -> dict:
    """Évalue la qualité du retrieval"""

    metrics = {
        "mrr": 0,           # Mean Reciprocal Rank
        "recall_at_5": 0,
        "precision_at_5": 0,
        "ndcg": 0
    }

    for query, relevant_ids in zip(test_queries, ground_truth):
        docs = retriever.get_relevant_documents(query)
        retrieved_ids = [d.metadata.get("id") for d in docs]

        # MRR
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_ids:
                metrics["mrr"] += 1 / (i + 1)
                break

        # Recall@5
        relevant_in_top5 = len(set(retrieved_ids[:5]) & set(relevant_ids))
        metrics["recall_at_5"] += relevant_in_top5 / len(relevant_ids)

        # Precision@5
        metrics["precision_at_5"] += relevant_in_top5 / 5

    n = len(test_queries)
    return {k: v/n for k, v in metrics.items()}
```
