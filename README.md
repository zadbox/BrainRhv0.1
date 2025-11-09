# 🎯 Brain RH - Système de Matching CV/RH

Système intelligent de matching entre CVs et offres d'emploi avec API FastAPI et interface React moderne.

## ✨ Fonctionnalités

### Architecture Moderne
- **Backend FastAPI** : API REST avec endpoints pour CVs, Projets, Entreprises, et Matching
- **Frontend React** : Interface utilisateur moderne avec TypeScript, TailwindCSS, et React Router
- **Server-Sent Events (SSE)** : Streaming en temps réel pour parsing et matching
- **Gestion multi-projets** : Organisation par entreprises et projets

### Fonctionnalités Core

- **📄 Parsing automatique de CVs** : Extraction structurée depuis PDF/DOCX via OpenAI
- **🏢 Gestion d'entreprises** : Création et organisation des clients
- **📁 Gestion de projets** : Projets rattachés aux entreprises avec offres d'emploi
- **🔍 Matching intelligent** : Analyse sémantique CV-offre avec scoring avancé
- **📊 Résultats détaillés** : Visualisation des scores, historique des matchings
- **⚡ Traitement parallèle** : Parsing de CVs haute performance (500 concurrents, 100 QPS)

## 🚀 Installation

### Backend (API FastAPI)

1. **Prérequis**
   - Python 3.11+
   - Clé API OpenAI

2. **Installation**
   ```bash
   # Installer les dépendances
   pip install -r requirements.txt

   # Configurer l'environnement
   cp .env.example .env
   # Éditer .env et ajouter votre OPENAI_API_KEY
   ```

3. **Lancer le backend**
   ```bash
   cd /path/to/Brain\ RH\ migration
   python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   API disponible sur `http://localhost:8000`
   Documentation interactive : `http://localhost:8000/docs`

### Frontend (React + Vite)

1. **Prérequis**
   - Node.js 18+
   - npm

2. **Installation**
   ```bash
   cd frontend
   npm install
   ```

3. **Lancer le frontend**
   ```bash
   npm run dev
   ```

   Interface disponible sur `http://localhost:5173`

## 📁 Structure du projet

```
Brain RH migration/
├── api/                        # Backend FastAPI
│   ├── main.py                 # Point d'entrée de l'API
│   ├── routers/                # Endpoints REST
│   │   ├── cvs.py              # Parsing et gestion des CVs
│   │   ├── enterprises.py      # Gestion des entreprises
│   │   ├── projects.py         # Gestion des projets
│   │   ├── matching.py         # Moteur de matching
│   │   └── offres.py           # Parsing et gestion des offres
│   ├── middleware/             # Middlewares (logging, etc.)
│   └── examples/               # Exemples de requêtes/réponses
│
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/         # Composants UI réutilisables
│   │   ├── pages/              # Pages principales
│   │   ├── api/                # Clients API
│   │   ├── stores/             # State management (Zustand)
│   │   └── hooks/              # Hooks React personnalisés
│   ├── package.json
│   └── vite.config.ts
│
├── lib/                        # Bibliothèques partagées
│   ├── models.py               # Modèles Pydantic
│   ├── parallel_engine.py      # Moteur de parsing parallèle
│   └── cv_parsing.py           # Parsing de CVs
│
├── enterprises/                # Données : entreprises et projets
├── projects/                   # Données : anciens projets
├── requirements.txt            # Dépendances Python
└── README.md
```

## 🎮 Utilisation

### Workflow typique

1. **Créer une entreprise**
   - Aller dans "Entreprises" → "Créer une entreprise"
   - Remplir les informations (nom, contacts, etc.)

2. **Créer un projet**
   - Depuis la page de l'entreprise, créer un nouveau projet
   - Ajouter une offre d'emploi (parsing automatique depuis texte brut)

3. **Parser des CVs**
   - Aller dans "Base CVs" → Sélectionner le projet
   - Uploader des fichiers PDF/DOCX
   - Lancer le parsing (streaming en temps réel)

4. **Lancer le matching**
   - Depuis la page du projet, aller dans "Matching"
   - Configurer les paramètres (modèle LLM, top N, etc.)
   - Visualiser les résultats en temps réel

5. **Consulter les résultats**
   - Voir les scores détaillés par CV
   - Consulter l'historique des matchings
   - Exporter les résultats

## 🔧 Configuration

### Backend

Configuration dans `.env`:
```env
OPENAI_API_KEY=your-api-key-here
```

Configuration dans `config.yaml` (optionnel):
```yaml
llm:
  model: "gpt-5-mini"  # ou "gpt-4o-mini"
  temperature_extraction: 0.1
  temperature_reranking: 0.2

scoring:
  top_k: 50
  top_rerank: 10
```

### Frontend

Configuration dans `frontend/src/api/client.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

## 📊 API Endpoints

### CVs
- `POST /api/v1/cvs/parse/stream` - Parser des CVs (SSE)
- `GET /api/v1/cvs/all` - Liste tous les CVs
- `GET /api/v1/cvs/projects/{project_id}/cvs` - CVs d'un projet

### Entreprises
- `GET /api/v1/enterprises` - Liste des entreprises
- `POST /api/v1/enterprises` - Créer une entreprise
- `PUT /api/v1/enterprises/{id}` - Modifier une entreprise

### Projets
- `GET /api/v1/projects` - Liste des projets
- `POST /api/v1/projects` - Créer un projet
- `GET /api/v1/projects/{id}` - Détails d'un projet

### Matching
- `POST /api/v1/matching/run/stream` - Lancer un matching (SSE)
- `GET /api/v1/matching/{project_id}/history` - Historique des matchings

## 🐛 Troubleshooting

### Backend ne démarre pas

Vérifier que `.env` contient `OPENAI_API_KEY`:
```bash
cat .env
```

### Frontend ne se connecte pas à l'API

Vérifier que le backend tourne sur le port 8000:
```bash
curl http://localhost:8000/health
```

### Erreur "gpt-5-mini not found"

Dans `config.yaml`, changer le modèle:
```yaml
llm:
  model: "gpt-4o-mini"
```

## 📈 Performance

- **Parsing parallèle** : 500 CVs simultanés avec rate limiting 100 QPS
- **Streaming SSE** : Feedback en temps réel du traitement
- **Caching** : Embeddings mis en cache pour éviter les recalculs

## 🔐 Sécurité

- ✅ Clés API via variables d'environnement
- ✅ Validation des entrées avec Pydantic
- ✅ CORS configuré pour localhost en développement
- ✅ Dépôt privé GitHub

## 📝 Licence

Projet interne - Usage confidentiel

## 🤝 Support

Pour toute question, contactez l'équipe projet.

## 📚 Documentation

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
