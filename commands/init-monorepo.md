---
description: Setup monorepo complet (Turborepo/pnpm workspace) sans profiling interactif
---

# Init Monorepo - Setup Monorepo RAG

Cette commande crée rapidement la structure monorepo de base sans le profiling interactif complet.

## Instructions

1. **Demande le nom du projet** (kebab-case uniquement)

2. **Crée la structure de dossiers**:
   ```
   {nom-projet}/
   ├── apps/
   │   ├── backend/
   │   └── frontend/
   ├── packages/
   │   ├── shared/
   │   └── types/
   ├── docker/
   ├── scripts/
   └── docs/
   ```

3. **Génère les fichiers de configuration**:

   **package.json** (root):
   ```json
   {
     "name": "{nom-projet}",
     "version": "0.1.0",
     "private": true,
     "packageManager": "pnpm@8.15.0",
     "engines": { "node": ">=20.0.0" },
     "scripts": {
       "dev": "turbo dev",
       "build": "turbo build",
       "docker:up": "docker-compose -f docker/docker-compose.yml up -d",
       "docker:down": "docker-compose -f docker/docker-compose.yml down",
       "db:index": "pnpm --filter backend run index"
     },
     "devDependencies": {
       "turbo": "^2.0.0",
       "typescript": "^5.3.0"
     }
   }
   ```

   **pnpm-workspace.yaml**:
   ```yaml
   packages:
     - 'apps/*'
     - 'packages/*'
   ```

   **turbo.json**:
   ```json
   {
     "$schema": "https://turbo.build/schema.json",
     "globalDependencies": [".env"],
     "pipeline": {
       "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] },
       "dev": { "cache": false, "persistent": true },
       "lint": { "dependsOn": ["^build"] },
       "test": { "dependsOn": ["build"], "outputs": ["coverage/**"] }
     }
   }
   ```

   **.gitignore**: Node, Python, IDE, Docker, Qdrant ignores

   **.env.example**: Variables pour Ollama, Qdrant, RAG config

   **.nvmrc**: `20`

   **README.md**: Documentation du projet

4. **Initialise Git** si non présent

5. **Affiche les prochaines étapes**:
   - `cd {nom-projet}`
   - `/rag-ollama:init-project` pour le profiling complet
   - Ou configurer manuellement `apps/backend` et `apps/frontend`

## Configuration par défaut

| Paramètre | Valeur |
|-----------|--------|
| LLM Model | mistral:7b-instruct-q4_0 |
| Embeddings | nomic-embed-text |
| Chunk Size | 1000 |
| Chunk Overlap | 200 |
| Retrieval Strategy | mmr |
