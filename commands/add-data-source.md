---
description: Configure une nouvelle source de données (API REST, fichiers, DB)
---

# Add Data Source - Ajout de Source de Données

Cette commande configure une nouvelle source de données pour le projet RAG.

## Instructions

1. **Vérifie qu'un projet RAG existe** (présence de `project-profile.json`)

2. **Demande les informations de la source**:

   - **Nom de la source** (kebab-case)

   - **Type de source**:
     - API REST (JSON)
     - API GraphQL
     - Fichiers locaux (PDF, DOCX, TXT, MD)
     - Fichiers S3/Cloud
     - Base SQL (PostgreSQL, MySQL, SQLite)
     - MongoDB
     - Notion
     - Confluence
     - CSV / Excel

3. **Questions spécifiques par type**:

   ### API REST
   - URL de base de l'API
   - Endpoint(s) à indexer (ex: `/items, /categories`)
   - Type d'authentification: Aucune, API Key Header, API Key Query, Bearer Token, Basic Auth, OAuth2
   - Type de pagination: Aucune, Offset/Limit, Page Number, Cursor, Link Header
   - Rate limit (requêtes/seconde)
   - Chemin JSON vers les données (ex: `data.items`)
   - Champ ID unique
   - Champs texte à indexer
   - Champs metadata à conserver

   ### Fichiers Locaux
   - Chemin du dossier
   - Patterns de fichiers (glob): `**/*.pdf,**/*.docx,**/*.txt,**/*.md`
   - Inclure sous-dossiers: Oui/Non

   ### Base SQL
   - Connection string (stocké dans .env)
   - Nom de la table
   - Colonne ID
   - Colonnes texte à indexer
   - Clause WHERE optionnelle

   ### CSV/Excel
   - Chemin du fichier
   - Délimiteur
   - Colonne ID (ou 'auto')
   - Colonnes texte à indexer

   ### Notion
   - Token d'intégration
   - ID(s) de base de données
   - Inclure les pages individuelles: Oui/Non

4. **Génère les fichiers**:

   Pour API REST, crée dans `apps/backend/app/services/data_sources/`:

   **{nom}_client.py**:
   ```python
   class {NomPascalCase}Client:
       def __init__(self):
           self.base_url = "{base_url}"
           self.rate_limit = {rate_limit}
           # Auth config

       async def fetch_all(self) -> AsyncGenerator[dict, None]:
           # Pagination logic

       async def fetch_by_id(self, item_id: str) -> Optional[dict]:
           # Single item fetch
   ```

   **{nom}_indexer.py**:
   ```python
   class {NomPascalCase}Indexer:
       def __init__(self):
           self.client = get_client()
           self.text_fields = [...]
           self.metadata_fields = [...]

       async def index_all(self, batch_size: int = 100) -> int:
           # Index all documents

       async def index_incremental(self, since_timestamp: str = None) -> int:
           # Incremental indexing
   ```

5. **Met à jour project-profile.json** avec la nouvelle source

6. **Affiche les variables d'environnement à ajouter** dans `.env`:
   - `{NOM}_BASE_URL`
   - `{NOM}_API_KEY` / `{NOM}_TOKEN` / `{NOM}_USERNAME` + `{NOM}_PASSWORD`

7. **Affiche les prochaines étapes**:
   - Configurer les variables d'environnement
   - Tester le client
   - Lancer l'indexation: `pnpm db:index --source={nom}`
   - Tester la pipeline: `/rag-ollama:test-rag`
