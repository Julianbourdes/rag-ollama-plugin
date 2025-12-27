---
name: ollama-m1-optimization
description: Guide complet pour optimiser les performances d'Ollama sur Apple Silicon M1 Pro 16GB
allowed-tools: Read, Bash, Grep
---

# Optimisation Ollama pour MacBook M1 Pro 16GB

Guide complet pour optimiser les performances d'Ollama sur Apple Silicon.

## Spécificités M1 Pro

### Architecture
- **CPU:** 8-10 cores (performance + efficiency)
- **GPU:** 16 cores GPU intégrés
- **RAM:** Mémoire unifiée partagée CPU/GPU
- **Neural Engine:** 16 cores (non utilisés par Ollama actuellement)

### Contraintes
- 16GB partagés entre système, apps, GPU et LLM
- Pas de mémoire GPU dédiée
- Bande passante mémoire: 200 GB/s

## Configuration optimale

### Variables d'environnement

```bash
# Activer Metal (GPU Apple) - CRITIQUE
export OLLAMA_USE_METAL=1

# Nombre de threads CPU optimal pour M1 Pro
export OLLAMA_NUM_THREAD=8

# Layers à mettre sur GPU (max = tout sur GPU)
export OLLAMA_NUM_GPU=999

# Taille du contexte (impact RAM)
export OLLAMA_CONTEXT_SIZE=4096

# Taille du batch pour génération
export OLLAMA_BATCH_SIZE=512

# Garder les modèles en mémoire
export OLLAMA_KEEP_ALIVE=5m
```

### Ajouter au profil shell

```bash
# ~/.zshrc ou ~/.bash_profile
cat >> ~/.zshrc << 'EOF'
# Ollama M1 Optimizations
export OLLAMA_USE_METAL=1
export OLLAMA_NUM_THREAD=8
export OLLAMA_NUM_GPU=999
export OLLAMA_CONTEXT_SIZE=4096
export OLLAMA_BATCH_SIZE=512
export OLLAMA_KEEP_ALIVE=5m
EOF

source ~/.zshrc
```

## Modèles recommandés

### Budget RAM: ~14GB disponible (16GB - 2GB système)

| Modèle | Taille | RAM Usage | Tokens/s | Qualité | Use Case |
|--------|--------|-----------|----------|---------|----------|
| `llama3.2:3b` | 2.0GB | ~2.5GB | ~50 | Bon | Chatbot simple |
| `mistral:7b-instruct-q4_0` | 4.1GB | ~5GB | ~25 | Excellent | **Recommandé** |
| `llama3.1:8b-instruct-q4_0` | 4.7GB | ~6GB | ~20 | Excellent+ | Q&A complexe |
| `codellama:7b-instruct-q4_0` | 3.8GB | ~4.5GB | ~28 | Excellent | Code |

### Embeddings

| Modèle | Taille | RAM | Dims | Speed | Use Case |
|--------|--------|-----|------|-------|----------|
| `nomic-embed-text` | 274MB | ~400MB | 768 | ~500/s | **Recommandé** |
| `mxbai-embed-large` | 670MB | ~800MB | 1024 | ~200/s | Haute qualité |
| `all-minilm` | 46MB | ~150MB | 384 | ~1000/s | Très rapide |

### Vision

| Modèle | Taille | RAM | Speed | Use Case |
|--------|--------|-----|-------|----------|
| `llava:7b-v1.6-mistral-q4_0` | 4.5GB | ~6GB | ~10 img/min | Analyse images |

## Combinaisons testées

### 1. Fast & Light (~4GB RAM)
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
# Reste ~10GB pour Qdrant + apps
```

### 2. Balanced (~6GB RAM) - Recommandé
```bash
ollama pull mistral:7b-instruct-q4_0
ollama pull nomic-embed-text
# Reste ~8GB pour Qdrant + apps
```

### 3. Quality Focus (~8GB RAM)
```bash
ollama pull llama3.1:8b-instruct-q4_0
ollama pull mxbai-embed-large
# Reste ~6GB (attention si gros corpus Qdrant)
```

### 4. Multimodal (~8GB RAM)
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama pull llava:7b-v1.6-mistral-q4_0
# Vision model chargé à la demande
```

## Optimisations avancées

### 1. Quantization

Les modèles Q4 (4-bit quantization) offrent le meilleur ratio qualité/RAM:

```bash
# Préférer les versions q4_0 ou q4_K_M
ollama pull mistral:7b-instruct-q4_0     # Meilleur compression
ollama pull mistral:7b-instruct-q4_K_M   # Meilleure qualité
```

### 2. Préchargement

```python
# Préchauffer le modèle au démarrage de l'app
async def warmup_ollama():
    await ollama.generate(
        model="mistral:7b-instruct-q4_0",
        prompt="Hello",
        stream=False
    )
```

### 3. Streaming

Toujours utiliser le streaming pour réduire la latence perçue:

```python
async def stream_response(prompt: str):
    async for chunk in ollama.generate(
        model="mistral:7b-instruct-q4_0",
        prompt=prompt,
        stream=True
    ):
        yield chunk["response"]
```

### 4. Contexte dynamique

```python
def adjust_context_size(query_length: int, max_response: int) -> int:
    """Ajuste la taille du contexte selon le besoin"""
    needed = query_length + max_response + 500  # Marge
    return min(needed, 4096)  # Cap pour économiser RAM

# Utilisation
response = await ollama.generate(
    model="mistral:7b-instruct-q4_0",
    prompt=prompt,
    options={
        "num_ctx": adjust_context_size(len(prompt), 1000)
    }
)
```

## Monitoring

### Activity Monitor

```bash
# Surveiller l'utilisation mémoire
while true; do
    memory_pressure=$(memory_pressure | grep -oP '\d+%' | head -1)
    echo "Memory Pressure: $memory_pressure"
    sleep 5
done
```

### Ollama stats

```python
async def get_ollama_stats():
    """Récupère les stats Ollama"""
    response = await httpx.get("http://localhost:11434/api/ps")
    return response.json()

# Affiche les modèles chargés
stats = await get_ollama_stats()
for model in stats.get("models", []):
    print(f"{model['name']}: {model['size'] / 1e9:.1f}GB")
```

## Gestion de la mémoire

### Décharger les modèles inutilisés

```python
async def unload_model(model_name: str):
    """Décharge un modèle de la mémoire"""
    await httpx.post(
        "http://localhost:11434/api/generate",
        json={"model": model_name, "keep_alive": 0}
    )
```

### Script de nettoyage

```bash
#!/bin/bash
# cleanup-ollama.sh

# Liste des modèles à garder
KEEP_MODELS=("mistral:7b-instruct-q4_0" "nomic-embed-text")

# Décharger tous les autres
curl -s http://localhost:11434/api/ps | jq -r '.models[].name' | while read model; do
    if [[ ! " ${KEEP_MODELS[@]} " =~ " ${model} " ]]; then
        curl -X POST http://localhost:11434/api/generate \
            -d "{\"model\": \"$model\", \"keep_alive\": 0}"
        echo "Unloaded: $model"
    fi
done
```

## Benchmarking

### Script de benchmark

```python
import time
import statistics
import ollama

async def benchmark_model(model: str, prompts: list, num_runs: int = 3):
    """Benchmark un modèle Ollama"""
    results = {
        "model": model,
        "tokens_per_second": [],
        "first_token_latency": [],
        "total_time": []
    }

    for prompt in prompts:
        for _ in range(num_runs):
            start = time.perf_counter()
            first_token_time = None
            total_tokens = 0

            async for chunk in ollama.generate(
                model=model,
                prompt=prompt,
                stream=True
            ):
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start

                if "response" in chunk:
                    total_tokens += len(chunk["response"].split())

            total_time = time.perf_counter() - start

            results["first_token_latency"].append(first_token_time)
            results["total_time"].append(total_time)
            results["tokens_per_second"].append(total_tokens / total_time)

    return {
        "model": model,
        "avg_tokens_per_second": statistics.mean(results["tokens_per_second"]),
        "avg_first_token_latency": statistics.mean(results["first_token_latency"]),
        "avg_total_time": statistics.mean(results["total_time"])
    }
```

## Troubleshooting

### "Out of memory"

1. Réduire `OLLAMA_CONTEXT_SIZE` à 2048
2. Utiliser un modèle plus petit
3. Fermer les applications gourmandes
4. Redémarrer Ollama

```bash
killall ollama && ollama serve
```

### Lenteur

1. Vérifier `OLLAMA_USE_METAL=1`
2. Vérifier `OLLAMA_NUM_GPU=999`
3. Fermer Chrome et autres apps GPU-heavy

### Haute latence premier token

1. Configurer `OLLAMA_KEEP_ALIVE=5m` ou plus
2. Préchauffer le modèle au démarrage
