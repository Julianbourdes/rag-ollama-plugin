---
name: chunking-strategies
description: Guide complet des stratégies de découpage de texte pour les applications RAG
allowed-tools: Read, Grep, Glob
---

# Stratégies de Chunking pour RAG

Guide complet des stratégies de découpage de texte pour les applications RAG.

## Vue d'ensemble

Le chunking est une étape critique du pipeline RAG. Un mauvais chunking peut:
- Perdre le contexte sémantique
- Fragmenter les informations importantes
- Produire des chunks trop petits (bruit) ou trop grands (dilution)

## Service de Chunking

Le template backend inclut un service de chunking complet avec toutes les stratégies :

```python
from app.services.chunking_service import get_chunking_service

chunking = get_chunking_service()

# Split avec stratégie automatique
docs = chunking.split_text(text, strategy="recursive")

# Obtenir une recommandation
rec = chunking.get_optimal_strategy("markdown", avg_doc_length=2000)
```

## 1. RecursiveCharacterTextSplitter (Documents longs)

**Meilleur pour:** Articles, documentation, rapports, blogs

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # Taille cible en caractères
    chunk_overlap=200,       # Chevauchement pour préserver le contexte
    separators=[
        "\n\n",             # Paragraphes
        "\n",               # Lignes
        ". ",               # Phrases
        " ",                # Mots
        ""                  # Caractères (fallback)
    ],
    length_function=len
)

chunks = splitter.split_text(document)
```

### Paramètres recommandés

| Type de contenu | chunk_size | chunk_overlap |
|-----------------|------------|---------------|
| Articles courts | 500-800 | 100 |
| Documentation | 1000-1500 | 200 |
| Rapports longs | 1500-2000 | 300 |
| Livres | 800-1000 | 150 |

## 2. SemanticChunker (Objets structurés)

**Meilleur pour:** Produits, recettes, profils, fiches

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import json

class SemanticObjectChunker:
    """Un objet structuré = un chunk"""

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens

    def chunk_objects(self, objects: List[dict]) -> List[str]:
        chunks = []
        for obj in objects:
            chunk = self._format_object(obj)
            if len(chunk) <= self.max_tokens:
                chunks.append(chunk)
            else:
                # Objet trop grand: découper intelligemment
                chunks.extend(self._split_large_object(obj))
        return chunks

    def _format_object(self, obj: dict) -> str:
        """Formate un objet en texte structuré"""
        lines = []
        for key, value in obj.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _split_large_object(self, obj: dict) -> List[str]:
        """Découpe un objet trop grand"""
        # Garder les champs essentiels dans chaque chunk
        essential_fields = ['id', 'name', 'title', 'type']
        base = {k: v for k, v in obj.items() if k in essential_fields}

        # Découper les autres champs
        chunks = []
        current_chunk = base.copy()
        current_size = len(self._format_object(current_chunk))

        for key, value in obj.items():
            if key in essential_fields:
                continue

            field_size = len(f"{key}: {value}")
            if current_size + field_size > self.max_tokens:
                chunks.append(self._format_object(current_chunk))
                current_chunk = base.copy()
                current_size = len(self._format_object(current_chunk))

            current_chunk[key] = value
            current_size += field_size

        if len(current_chunk) > len(base):
            chunks.append(self._format_object(current_chunk))

        return chunks
```

## 3. ConversationAwareChunker (Dialogues)

**Meilleur pour:** Transcriptions, logs de chat, support client

```python
class ConversationChunker:
    """Préserve les tours de parole"""

    def __init__(
        self,
        max_turns: int = 5,
        max_tokens: int = 1000,
        speaker_pattern: str = r"^(User|Assistant|Human|AI):"
    ):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.speaker_pattern = speaker_pattern

    def chunk_conversation(self, text: str) -> List[str]:
        import re

        # Diviser par tours de parole
        turns = re.split(f"({self.speaker_pattern})", text, flags=re.MULTILINE)

        # Reconstruire les tours
        parsed_turns = []
        current_speaker = None
        current_text = []

        for part in turns:
            if re.match(self.speaker_pattern, part):
                if current_speaker:
                    parsed_turns.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_text).strip()
                    })
                current_speaker = part.strip()
                current_text = []
            else:
                current_text.append(part.strip())

        if current_speaker:
            parsed_turns.append({
                "speaker": current_speaker,
                "text": " ".join(current_text).strip()
            })

        # Grouper en chunks
        chunks = []
        current_chunk = []
        current_size = 0

        for turn in parsed_turns:
            turn_text = f"{turn['speaker']} {turn['text']}"
            turn_size = len(turn_text)

            if (len(current_chunk) >= self.max_turns or
                current_size + turn_size > self.max_tokens):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(turn_text)
            current_size += turn_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks
```

## 4. CodeAwareChunker (Code source)

**Meilleur pour:** Repositories, documentation technique

```python
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)

# Splitters par langage
LANGUAGE_SPLITTERS = {
    "python": RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=500,
        chunk_overlap=50
    ),
    "javascript": RecursiveCharacterTextSplitter.from_language(
        language=Language.JS,
        chunk_size=500,
        chunk_overlap=50
    ),
    "typescript": RecursiveCharacterTextSplitter.from_language(
        language=Language.TS,
        chunk_size=500,
        chunk_overlap=50
    ),
    "markdown": RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=1000,
        chunk_overlap=100
    )
}

def chunk_code(code: str, language: str) -> List[str]:
    splitter = LANGUAGE_SPLITTERS.get(
        language.lower(),
        RecursiveCharacterTextSplitter(chunk_size=500)
    )
    return splitter.split_text(code)
```

## 5. Parent Document Retriever

**Meilleur pour:** Documents hiérarchiques avec contexte parent important

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Splitter pour les chunks enfants (petits, précis)
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50
)

# Splitter pour les documents parents (plus grands, contexte)
parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)

# Store pour les documents parents
store = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter
)

# Ajouter des documents
retriever.add_documents(documents)

# Recherche: récupère les parents des chunks pertinents
results = retriever.get_relevant_documents("query")
```

## Sélection automatique

```python
def auto_select_chunker(data_sample: str, data_type: str):
    """Sélectionne automatiquement la meilleure stratégie"""

    if data_type == "structured" or data_sample.startswith("{"):
        return SemanticObjectChunker()

    if data_type == "conversation" or re.match(r"^(User|Human):", data_sample):
        return ConversationChunker()

    if data_type == "code" or data_sample.startswith(("def ", "class ", "function")):
        return LANGUAGE_SPLITTERS.get("python")

    # Default: documents
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
```

## Bonnes pratiques

1. **Tester sur un échantillon** - Vérifiez visuellement que les chunks sont cohérents
2. **Préserver les métadonnées** - Gardez la référence au document source
3. **Éviter les chunks trop petits** - Minimum ~200 caractères
4. **Ajuster l'overlap** - 10-20% de la taille du chunk
5. **Considérer les tokens** - Un embedding model a une limite de tokens

## Métriques de qualité

```python
def analyze_chunks(chunks: List[str]):
    """Analyse la qualité des chunks"""
    sizes = [len(c) for c in chunks]

    return {
        "count": len(chunks),
        "avg_size": sum(sizes) / len(sizes),
        "min_size": min(sizes),
        "max_size": max(sizes),
        "std_dev": (sum((s - sum(sizes)/len(sizes))**2 for s in sizes) / len(sizes)) ** 0.5,
        "too_small": sum(1 for s in sizes if s < 100),
        "too_large": sum(1 for s in sizes if s > 2000)
    }
```
