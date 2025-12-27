---
description: Ajoute une feature optionnelle (profiling, multimodal, widgets, etc.)
---

# Add Feature - Ajout de Feature Optionnelle

Cette commande ajoute des fonctionnalités optionnelles au projet RAG.

## Instructions

1. **Vérifie qu'un projet RAG existe** (présence de `project-profile.json`)

2. **Liste les features disponibles** (filtre celles déjà installées):

   | Feature | Description | Fichiers Backend | Fichiers Frontend |
   |---------|-------------|------------------|-------------------|
   | **user-profiling** | Apprentissage progressif des préférences | models/profile.py, services/profiling_service.py, api/routes/profile.py | components/profile-widget.tsx, lib/hooks/use-profile.ts |
   | **multimodal-stt** | Speech-to-Text avec Whisper | services/stt_service.py, api/routes/audio.py | components/voice-input.tsx, lib/hooks/use-voice-input.ts |
   | **multimodal-tts** | Text-to-Speech | services/tts_service.py, api/routes/speech.py | components/audio-player.tsx, lib/hooks/use-tts.ts |
   | **multimodal-images** | Analyse d'images avec LLaVA | services/vision_service.py, api/routes/images.py | components/image-upload.tsx |
   | **custom-widget-cards** | Affichage en cartes riches | - | components/rich-card.tsx, components/card-gallery.tsx |
   | **custom-widget-forms** | Formulaires dynamiques dans le chat | schemas/dynamic_form.py | components/dynamic-form.tsx |
   | **advanced-search** | Filtres, facettes, tri des résultats | services/advanced_search_service.py, api/routes/search.py | components/search-filters.tsx, components/facets-panel.tsx |
   | **feedback-system** | Thumbs up/down, ratings | models/feedback.py, services/feedback_service.py | components/feedback-buttons.tsx |
   | **analytics** | Tracking usage, métriques | models/analytics.py, services/analytics_service.py | components/analytics-dashboard.tsx |
   | **conversation-export** | Export PDF/Markdown | services/export_service.py, api/routes/export.py | components/export-button.tsx |

3. **Demande quelle feature installer**

4. **Génère les fichiers** dans les dossiers appropriés:
   - Backend: `apps/backend/app/{path}`
   - Frontend: `apps/frontend/{path}`

5. **Affiche les dépendances à installer**:

   | Feature | Backend (pip) | Frontend (pnpm) |
   |---------|---------------|-----------------|
   | multimodal-stt | openai-whisper | - |
   | multimodal-tts | edge-tts | - |
   | multimodal-images | pillow | - |
   | custom-widget-forms | - | @hookform/resolvers, zod |
   | analytics | prometheus-client | recharts |
   | conversation-export | weasyprint | - |

6. **Indique le modèle Ollama requis** si applicable:
   - multimodal-images: `ollama pull llava:7b`

7. **Met à jour project-profile.json** avec la nouvelle feature

8. **Affiche les prochaines étapes**:
   - Installer les dépendances
   - Adapter les fichiers générés
   - Redémarrer le serveur de développement

## Templates de code

Génère du code fonctionnel basé sur les patterns suivants:

### User Profiling Service
```python
class ProfilingService:
    async def get_or_create_profile(self, user_id: str) -> UserProfile
    async def analyze_interaction(self, user_id, message, response) -> Dict
    async def get_personalization_context(self, user_id: str) -> str
```

### STT Service
```python
class STTService:
    def __init__(self, model_size="small"):  # small pour M1 16GB
    async def transcribe(self, audio_data: bytes, language="fr") -> dict
    async def detect_language(self, audio_data: bytes) -> str
```

### Feedback System
```python
class Feedback(Base):
    id, message_id, user_id, rating, comment, created_at
```
