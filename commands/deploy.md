---
description: Build & deploy Docker (local ou production)
---

# Deploy - Build & Deploy Docker

Cette commande génère et déploie les containers Docker pour le projet RAG.

## Instructions

1. **Vérifie qu'un projet RAG existe** (présence de `project-profile.json`)

2. **Vérifie que Docker et Docker Compose sont disponibles**:
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Demande la cible de déploiement**:
   - **Local (développement)**: Docker Compose local
   - **Local (production)**: Build de production en local
   - **Docker Hub**: Push vers Docker Hub
   - **GitHub Container Registry**: Push vers ghcr.io

4. **Si push vers registry**, demande:
   - Namespace (username Docker Hub ou GitHub)
   - Tag (latest, v1.0.0, etc.)

5. **Vérifie les prérequis**:
   - package.json frontend existe
   - requirements.txt backend existe
   - .env existe
   - Ollama accessible (pour local)
   - Docker login OK (pour push)

6. **Génère les Dockerfiles**:

   **docker/Dockerfile.backend**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   RUN apt-get update && apt-get install -y gcc
   COPY apps/backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY apps/backend/app ./app
   ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
   EXPOSE 8000
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

   **docker/Dockerfile.frontend**:
   ```dockerfile
   FROM node:20-alpine AS builder
   WORKDIR /app
   RUN corepack enable && corepack prepare pnpm@latest --activate
   COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
   COPY apps/frontend/package.json ./apps/frontend/
   RUN pnpm install --frozen-lockfile
   COPY apps/frontend ./apps/frontend
   COPY packages ./packages
   WORKDIR /app/apps/frontend
   RUN pnpm build

   FROM node:20-alpine AS runner
   WORKDIR /app
   ENV NODE_ENV=production
   COPY --from=builder /app/apps/frontend/.next/standalone ./
   COPY --from=builder /app/apps/frontend/.next/static ./apps/frontend/.next/static
   COPY --from=builder /app/apps/frontend/public ./apps/frontend/public
   EXPOSE 3000
   CMD ["node", "apps/frontend/server.js"]
   ```

   **docker/docker-compose.yml**:
   ```yaml
   services:
     backend:
       build: {context: .., dockerfile: docker/Dockerfile.backend}
       ports: ["8000:8000"]
       environment:
         - OLLAMA_BASE_URL=http://host.docker.internal:11434
         - QDRANT_HOST=qdrant
       depends_on: [qdrant]

     frontend:
       build: {context: .., dockerfile: docker/Dockerfile.frontend}
       ports: ["3000:3000"]
       environment:
         - NEXT_PUBLIC_API_URL=http://localhost:8000
       depends_on: [backend]

     qdrant:
       image: qdrant/qdrant:latest
       ports: ["6333:6333", "6334:6334"]
       volumes: [qdrant-data:/qdrant/storage]

   volumes:
     qdrant-data:
   ```

7. **Build les images**:
   ```bash
   docker build -f docker/Dockerfile.backend -t {project}-backend:latest .
   docker build -f docker/Dockerfile.frontend -t {project}-frontend:latest .
   ```

8. **Tests de santé** (pour local):
   - Démarre les services
   - Attend 10 secondes
   - Teste les endpoints health
   - Affiche les résultats

9. **Démarre ou push**:
   - Local: `docker-compose up -d`
   - Registry: Tag et push les images

10. **Affiche le résumé**:

    Pour local:
    ```
    🌐 Services disponibles :
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000
    - API Docs: http://localhost:8000/docs
    - Qdrant: http://localhost:6333/dashboard

    📋 Commandes utiles :
    - docker-compose logs -f
    - docker-compose ps
    - docker-compose down
    ```

    Pour registry:
    ```
    🐳 Images publiées :
    - ghcr.io/{namespace}/{project}-backend:latest
    - ghcr.io/{namespace}/{project}-frontend:latest
    ```

## Configuration Docker pour M1

- `OLLAMA_BASE_URL=http://host.docker.internal:11434` pour accéder à Ollama sur l'hôte
- Volumes persistants pour Qdrant
- Restart policy: `unless-stopped`
