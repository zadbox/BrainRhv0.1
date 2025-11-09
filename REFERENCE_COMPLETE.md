# 🗺️ BRAIN RH - CARTE DE RÉFÉRENCE COMPLÈTE

**Dernière MAJ:** 18 octobre 2025
**Version:** 2.6.4
**Pour:** Claude Code (navigation rapide)

> ⚠️ **RÈGLE:** Lire ce fichier EN PREMIER avant toute modification de code
> 📘 **RÈGLE:** Consulter CODING_RULES.md pour connaître les patterns obligatoires

---

## 🎯 VUE D'ENSEMBLE

**Stack:** React 18 + TypeScript + FastAPI + Python 3.11
**Architecture:** API REST + SSE (streaming) + Frontend découplé
**Logique métier:** `lib/` (réutilisable backend + API)
**Base de données:** Système de fichiers (migration PostgreSQL prévue v2.0)

**Structures de stockage:**
- Ancienne: `projects/{project_id}/`
- Nouvelle: `enterprises/{enterprise_id}/{project_id}/`
- ⚠️ **Jamais hardcoder les chemins !** Utiliser `ProjectManager.get_project_path()`

---

## 📂 STRUCTURE PROJET

### Backend (Python)

```
📦 Root
├── matching_engine.py             # ⭐ Moteur matching principal (classe MatchingEngine)
├── parseur_cv.py                  # Parsing CVs PDF/DOCX via OpenAI LLM
├── offer_enrichment.py            # Extraction must-have/nice-have LLM
├── parallel_cv_parsing.py         # Parsing parallèle (500 CVs max, QPS 10)
├── must_have_parallel.py          # Filtrage must-have parallèle
├── nice_have_parallel.py          # Détection nice-have parallèle
├── parallel_processing.py         # Pipeline parallèle générique
├── config_loader.py               # ⭐ Configuration centralisée (singleton)
├── project_manager.py             # ⭐ Gestionnaire projets (multi-structure)
├── enterprise_manager.py          # Gestionnaire entreprises clientes
├── mapper_offre.py                # Normalisation formats CV/Offre
├── validation.py                  # Validation/réparation JSON CVs
├── rome_api.py                    # API France Travail (ROME) - optionnel
│
├── 📁 lib/                        # ⭐ Logique métier pure (prioritaire)
│   ├── __init__.py
│   ├── models.py                  # ⭐ Pydantic schemas (CV, Offre, ResultatMatching)
│   ├── cv_parsing.py              # Fonctions parsing pures
│   ├── matching_core.py           # Fonctions matching pures
│   ├── offer_processing.py        # Fonctions offres pures
│   ├── parallel_engine.py         # Moteur parallèle générique
│   └── config.py                  # Config helpers
│
├── 📁 api/                        # ⭐ API FastAPI
│   ├── main.py                    # Point d'entrée FastAPI
│   └── routers/
│       ├── cvs.py                 # Routes CVs (parse, list, get, delete)
│       ├── offres.py              # Routes Offres (create, enrich, get)
│       ├── matching.py            # ⭐ Routes Matching (run, stream, export)
│       ├── projects.py            # Routes Projets (CRUD)
│       └── enterprises.py         # Routes Entreprises (CRUD)
│
├── 📁 tests/                      # Tests automatiques
│   ├── __init__.py
│   ├── test_palier0_extraction.py
│   └── fixtures/                  # Fixtures de test
│
├── config.yaml                    # ⭐ Configuration système
├── .env                           # Variables secrètes (API keys)
├── requirements.txt               # Dépendances Python
└── openapi.yaml                   # ⭐ Contrat API (950+ lignes)
```

### Frontend (React + TypeScript)

```
📁 frontend/
├── src/
│   ├── pages/                     # Pages principales
│   │   ├── CVsPage.tsx            # Upload + parsing CVs
│   │   ├── MatchingPage.tsx       # Configuration + lancement matching
│   │   ├── OffresPage.tsx         # Création + enrichissement offres
│   │   ├── ProjectsPage.tsx       # Gestion projets
│   │   └── EnterprisesPage.tsx    # Gestion entreprises
│   │
│   ├── components/                # Composants réutilisables
│   │   ├── ui/                    # Composants shadcn/ui
│   │   ├── CVUploader.tsx
│   │   ├── MatchingResults.tsx
│   │   └── ...
│   │
│   ├── hooks/                     # Hooks custom
│   │   ├── useSSE.ts              # ⭐ Hook SSE streaming
│   │   ├── useMatching.ts         # Hook logique matching
│   │   └── useCVParsing.ts        # Hook parsing CVs
│   │
│   ├── api/                       # Client API TypeScript
│   │   ├── client.ts              # Axios client configuré
│   │   ├── types.ts               # Types générés depuis OpenAPI
│   │   └── endpoints/
│   │       ├── cvs.ts
│   │       ├── matching.ts
│   │       └── ...
│   │
│   └── App.tsx                    # Point d'entrée React
│
├── public/                        # Assets statiques
├── package.json
└── vite.config.ts
```

### Stockage (Fichiers)

```
📁 projects/                       # Ancienne structure (legacy)
└── {project_id}/
    ├── projet.json                # Métadonnées projet
    ├── offre.json                 # Offre parsée + must-have/nice-have
    ├── cvs_parsed/                # CVs parsés (JSON)
    │   ├── cv1.json
    │   └── cv2.json
    ├── matchings/                 # Historique matchings
    │   └── {timestamp}/
    │       ├── results.json
    │       └── metadata.json
    └── historique/                # Archives

📁 enterprises/                    # Nouvelle structure (multi-tenant)
└── {enterprise_id}/
    └── {project_id}/              # Même structure que ci-dessus
```

---

## 🔍 TROUVER UNE FONCTIONNALITÉ

### 🔹 Parsing CVs

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Upload + parsing batch** | `parseur_cv.py` | 120-180 | Utilise OpenAI LLM |
| **Parsing parallèle** | `parallel_cv_parsing.py` | 45-150 | 500 CVs max, QPS 10 |
| **Extraction sections LLM** | `parseur_cv.py` | 200-280 | Prompt structuré |
| **Normalisation format** | `mapper_offre.py` | 60-120 | Ancien → nouveau format |
| **Validation JSON** | `validation.py` | 50-200 | Validation + réparation auto |
| **API endpoint (batch)** | `api/routers/cvs.py` | 25-60 | POST `/cvs/parse` |
| **API endpoint (stream)** | `api/routers/cvs.py` | 80-150 | POST `/cvs/parse/stream` (SSE) |

**Prompt LLM parsing:** `parseur_cv.py:200-280`

---

### 🔹 Enrichissement Offre

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Extraction must-have/nice-have** | `offer_enrichment.py` | 80-200 | LLM contextuel |
| **Parsing offre brute** | `parseur_cv.py` | (fonction partagée) | PDF/DOCX → JSON |
| **Normalisation offre** | `mapper_offre.py` | 150-220 | Format sections{} |
| **API endpoint** | `api/routers/offres.py` | 35-80 | POST `/offres/enrich` |

**Prompt extraction critères:** `offer_enrichment.py:80-150`

---

### 🔹 Filtrage Must-have

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Analyse LLM contextuelle** | `matching_engine.py` | 450-580 | Méthode `filter_must_have()` |
| **Parallélisation 500 CVs** | `must_have_parallel.py` | 80-200 | QPS 10 |
| **Prompt must-have** | `matching_engine.py` | 460-510 | Analyse binaire Oui/Non |
| **Gestion négations** | `matching_engine.py` | 520-550 | "Pas de Python" → élimine si Python présent |

**Docs prompt:** `PROMPT_MUST_HAVE_V2.md`

---

### 🔹 Scoring & Nice-to-have

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Calcul similarité (embeddings)** | `matching_engine.py` | 650-720 | SentenceTransformer |
| **Cache embeddings** | `matching_engine.py` | 680-700 | SHA-256 hash |
| **Détection nice-have LLM** | `matching_engine.py` | 800-900 | Analyse candidat par candidat |
| **Parallélisation nice-have** | `nice_have_parallel.py` | 60-180 | 500 CVs max |
| **Malus nice-have (0.95^n)** | `matching_engine.py` | 920-950 | Formula: `score_base * (0.95 ** nb_manquants)` |
| **Bonus expérience** | `matching_engine.py` | 960-1020 | Exacte: +15%, Proche: +10%, Similaire: +5% |
| **Capping [0,1]** | `matching_engine.py` | 1030-1050 | min/max final |

**Configuration:** `config.yaml:scoring`

---

### 🔹 Re-ranking Top-N

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Re-ranking LLM top-10** | `matching_engine.py` | 1100-1250 | Méthode `rerank_top()` |
| **Génération commentaires RH** | `matching_engine.py` | 1180-1220 | Prompt dédié |
| **Tri final par score** | `matching_engine.py` | 1260-1280 | Tri décroissant |

**Logique top_k/top_rerank:** `EXPLICATION_TOP_K.md`

---

### 🔹 Exports

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Export CSV** | `matching_engine.py` | 1350-1450 | Colonnes: cv, score_final, commentaire, etc. |
| **Export JSON** | `matching_engine.py` | 1480-1520 | Structure complète |
| **API endpoint CSV** | `api/routers/matching.py` | 210-250 | GET `/matching/{id}/export/csv` |
| **API endpoint JSON** | `api/routers/matching.py` | 260-290 | GET `/matching/{id}/export/json` |

---

### 🔹 Gestion Projets

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Créer projet** | `project_manager.py` | 84-127 | Génère ID unique |
| **⭐ Obtenir chemin projet** | `project_manager.py` | 200-240 | `get_project_path(project_id)` |
| **Lister projets** | `project_manager.py` | 44-70 | Filtrable par statut |
| **Supprimer projet** | `project_manager.py` | 180-195 | Archive ou suppression |
| **API CRUD** | `api/routers/projects.py` | Toutes | GET/POST/PUT/DELETE |

**⚠️ IMPORTANT:** Toujours utiliser `get_project_path()` pour gérer `projects/` ET `enterprises/`

---

### 🔹 Gestion Entreprises

| Feature | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
| **Créer entreprise** | `enterprise_manager.py` | 40-80 | Structure multi-tenant |
| **Lister entreprises** | `enterprise_manager.py` | 90-120 | Avec comptage projets |
| **API CRUD** | `api/routers/enterprises.py` | Toutes | GET/POST/PUT/DELETE |

---

## 🌐 API REST (FastAPI)

### Endpoints disponibles

| Endpoint | Méthode | Description | Fichier | Lignes |
|----------|---------|-------------|---------|--------|
| **CVs** |
| `/api/v1/cvs/parse` | POST | Parse CVs (batch) | `api/routers/cvs.py` | 25-60 |
| `/api/v1/cvs/parse/stream` | POST | Parse CVs (SSE) | `api/routers/cvs.py` | 80-200 |
| `/api/v1/cvs` | GET | Liste CVs projet | `api/routers/cvs.py` | 220-250 |
| `/api/v1/cvs/{filename}` | GET | Récupère un CV | `api/routers/cvs.py` | 260-290 |
| `/api/v1/cvs/{filename}` | DELETE | Supprime un CV | `api/routers/cvs.py` | 300-320 |
| **Offres** |
| `/api/v1/offres/parse` | POST | Parse offre brute | `api/routers/offres.py` | 30-60 |
| `/api/v1/offres/enrich` | POST | Enrichir offre LLM | `api/routers/offres.py` | 70-150 |
| `/api/v1/offres` | GET | Récupère offre projet | `api/routers/offres.py` | 160-190 |
| `/api/v1/offres` | PUT | Met à jour offre | `api/routers/offres.py` | 200-230 |
| `/api/v1/offres` | DELETE | Supprime offre | `api/routers/offres.py` | 240-260 |
| **Matching** |
| `/api/v1/matching/run` | POST | Lancer matching (batch) | `api/routers/matching.py` | 45-120 |
| `/api/v1/matching/run/stream` | POST | Matching (SSE) | `api/routers/matching.py` | 130-350 |
| `/api/v1/matching/results` | GET | Récupère résultats | `api/routers/matching.py` | 360-390 |
| `/api/v1/matching/{id}/export/csv` | GET | Export CSV | `api/routers/matching.py` | 210-250 |
| `/api/v1/matching/{id}/export/json` | GET | Export JSON | `api/routers/matching.py` | 260-290 |
| **Projets** |
| `/api/v1/projects` | GET | Liste projets | `api/routers/projects.py` | 25-50 |
| `/api/v1/projects` | POST | Crée projet | `api/routers/projects.py` | 60-90 |
| `/api/v1/projects/{id}` | GET | Récupère projet | `api/routers/projects.py` | 100-120 |
| `/api/v1/projects/{id}` | PUT | Met à jour projet | `api/routers/projects.py` | 130-160 |
| `/api/v1/projects/{id}` | DELETE | Supprime projet | `api/routers/projects.py` | 170-190 |
| `/api/v1/projects/{id}/history` | GET | Historique matchings | `api/routers/projects.py` | 200-230 |
| **Entreprises** |
| `/api/v1/enterprises` | GET | Liste entreprises | `api/routers/enterprises.py` | 25-50 |
| `/api/v1/enterprises` | POST | Crée entreprise | `api/routers/enterprises.py` | 60-90 |
| `/api/v1/enterprises/{id}` | GET | Récupère entreprise | `api/routers/enterprises.py` | 100-130 |
| `/api/v1/enterprises/{id}` | PUT | Met à jour entreprise | `api/routers/enterprises.py` | 140-170 |
| `/api/v1/enterprises/{id}` | DELETE | Supprime entreprise | `api/routers/enterprises.py` | 180-200 |

**Docs OpenAPI complète:** `openapi.yaml` (950+ lignes)
**Swagger UI:** `http://localhost:8000/docs` (auto-généré)

---

## 📊 SCHEMAS PYDANTIC (lib/models.py)

### Schemas principaux

| Schema | Fichier | Lignes | Usage |
|--------|---------|--------|-------|
| **CV** | `lib/models.py` | 40-57 | CV parsé structuré |
| **Identite** | `lib/models.py` | 14-23 | Infos candidat |
| **Experience** | `lib/models.py` | 27-36 | Expérience professionnelle |
| **Offre** | `lib/models.py` | 80-88 | Offre avec must-have/nice-have |
| **OffreSection** | `lib/models.py` | 61-78 | Sections offre |
| **ResultatMatching** | `lib/models.py` | 92-129 | Résultat matching d'un CV |
| **MatchingResponse** | `lib/models.py` | 140-143 | Réponse complète matching |
| **CVParseResult** | `lib/models.py` | 148-155 | Résultat parsing d'un CV |
| **Project** | `lib/models.py` | 201-211 | Métadonnées projet |
| **Enterprise** | `lib/models.py` | 214-224 | Métadonnées entreprise |
| **SSE*Event** | `lib/models.py` | 168-197 | Événements SSE typés |
| **APIError** | `lib/models.py` | 229-234 | Erreur API normalisée |

**Validation automatique:** Pydantic valide tous les payloads entrants/sortants

---

## 📡 STREAMING SSE (Server-Sent Events)

### Format événements

```
event: <type>
data: <json>

```

### Types d'événements

| Event | Émis par | Structure JSON | Fichier émetteur |
|-------|----------|----------------|------------------|
| **progress** | Parsing CVs, Matching | `{event:"progress", step:str, current:int, total:int, progress:float}` | `api/routers/cvs.py:95`, `api/routers/matching.py:180` |
| **result** | Parsing CVs, Matching | `{event:"result", data:{...}}` | `api/routers/cvs.py:120`, `api/routers/matching.py:280` |
| **done** | Tous | `{event:"done", summary:{...}}` | `api/routers/cvs.py:160`, `api/routers/matching.py:330` |
| **error** | Tous | `{event:"error", code:str, message:str, details:{}}` | `api/routers/cvs.py:180`, `api/routers/matching.py:200` |

**Docs détaillée:** `api/examples/sse_events.md`

### Étapes streaming matching

| Step | Description | Duration estimée |
|------|-------------|------------------|
| `must_have_filtering` | Filtrage éliminatoire LLM | 1-2 min (32 CVs) |
| `similarity_scoring` | Calcul embeddings + similarité | 5-10s |
| `nice_have_detection` | Détection nice-have LLM | 1-2 min |
| `reranking` | Re-ranking top-N LLM | 30-60s |

---

## ⚙️ CONFIGURATION

### Fichiers config

| Fichier | Usage | Chargé par | Variables clés |
|---------|-------|------------|----------------|
| **`.env`** | API keys secrètes | `config_loader.py` | `OPENAI_API_KEY`, `FRANCE_TRAVAIL_*` |
| **`config.yaml`** | Paramètres système | `config_loader.py` | `llm.model`, `scoring.*`, `parallel.*` |

### Variables importantes (config.yaml)

```yaml
llm:
  model: gpt-4o-mini              # Modèle LLM (gpt-4o-mini, gpt-5-mini)
  temperature: 0.0                # Déterminisme (0.0-1.0)
  fallback_models: [...]          # Modèles de secours

scoring:
  top_k: 50                       # Candidats avant filtrage must-have
  top_rerank: 10                  # Top-N pour re-ranking final
  nice_have_malus_factor: 0.95    # Malus par nice-have manquant
  bonus_experience_exacte: 0.15   # Bonus expérience exacte
  bonus_experience_proche: 0.10   # Bonus expérience proche
  bonus_experience_similaire: 0.05  # Bonus expérience similaire
  score_min: 0.0                  # Capping minimum
  score_max: 1.0                  # Capping maximum

parallel:
  file_workers: 4                 # Workers pour fichiers I/O
  llm_concurrent: 5               # Requêtes LLM concurrentes
  max_workers: 500                # Max workers parallèles
  qps: 10                         # Queries/sec OpenAI (rate limit)

embeddings:
  model: all-MiniLM-L6-v2         # Modèle SentenceTransformer
  cache_enabled: true             # Cache embeddings

paths:
  cache_folder: cache             # Cache embeddings
  cv_input: cv_input              # CVs bruts uploadés temporairement
  # cv_json: SUPPRIMÉ             # Legacy - utiliser enterprises/{id}/projects/{id}/cvs_parsed/
  offres: offres                  # Offres (legacy - sera migré)
  output: output                  # Exports
  # projects: SUPPRIMÉ            # Legacy - utiliser enterprises/{id}/projects/
  enterprises: enterprises        # Structure hiérarchique entreprises/projets

validation:
  enabled: true                   # Validation JSONs
  max_repair_attempts: 3          # Tentatives réparation auto
```

**Accès config:** `from config_loader import load_config`

---

## 🧪 TESTS

### Tests automatiques

| Test | Fichier | Description | Durée |
|------|---------|-------------|-------|
| **2 CVs intégration** | `test_2cv_matching.py` | Test complet end-to-end | 30s |
| **Parsing performance** | `test_parsing_performance.py` | Benchmarks parsing | 1 min |
| **Must-have négation** | `test_negation_must_have.py` | Logique "Pas de X" | 20s |
| **Parité séq/parallel** | `test_parite_seq_parallel.py` | Vérifie résultats identiques | 2 min |
| **Migration API** | `test_api_migration.py` | Tests API routes | 1 min |
| **E2E complet** | `test_e2e.py` | Parsing → Matching → Export | 5 min |

**Lancer tests:**
```bash
python test_2cv_matching.py           # Test rapide
pytest backend/tests/                 # Suite complète
```

### Guide de test manuel

**Fichier:** `GUIDE_TEST_UTILISATEUR.md`

---

## 🔧 COMMANDES UTILES

```bash
# Backend (Python)
streamlit run app.py                          # UI Streamlit (legacy)
uvicorn api.main:app --reload --port 8000     # API FastAPI (nouveau)
python -m api.main                            # Alternative API

# Frontend (React)
cd frontend && npm run dev                    # Dev server (Vite)
cd frontend && npm run build                  # Build production

# Tests
python test_2cv_matching.py                   # Test rapide
pytest backend/tests/ -v                      # Tests unitaires
python test_e2e.py                            # Test end-to-end

# Configuration
python -c "from config_loader import load_config; import json; print(json.dumps(load_config(), indent=2))"

# Vérifier structure projet
python -c "from project_manager import ProjectManager; pm = ProjectManager(); print(pm.list_projects())"

# Nettoyer cache
rm -rf cache/*
```

---

## 📚 DOCUMENTATION TECHNIQUE

### Guides principaux (LIRE EN PRIORITÉ)

| Doc | Usage | Dernière MAJ |
|-----|-------|--------------|
| **REFERENCE_COMPLETE.md** ⭐ | Ce fichier - carte du projet | 18/10/2025 |
| **CODING_RULES.md** ⭐ | Règles & patterns obligatoires | 18/10/2025 |
| **MAINTENANCE_GUIDE.md** ⭐ | Règles de maintenance des docs | 18/10/2025 |
| **QUICKSTART.md** | Démarrage rapide (installation, premier test) | 13/10/2025 |
| **FRONT_STANDARDS.md** | Standards React/TypeScript/UX | 11/10/2025 |
| **API_DECISIONS.md** | Décisions architecture API | 11/10/2025 |
| **GUIDE_TEST_UTILISATEUR.md** | Tests manuels complets | 03/10/2025 |

### Docs spécialisées

| Doc | Sujet | Pertinence |
|-----|-------|------------|
| `PROMPT_MUST_HAVE_V2.md` | Prompts LLM must-have | Haute |
| `EXPLICATION_TOP_K.md` | Logique top_k/top_rerank | Haute |
| `CHARTE_GRAPHIQUE_BRAIN_RH.md` | Design system | Moyenne |
| `PLAN_MIGRATION_PALIERS.md` | Plan migration Legacy → API | Faible (historique) |
| `TESTING_METHODOLOGY.md` | Méthodologie tests | Moyenne |

### Archives (historique corrections)

⚠️ **Ne pas utiliser pour référence actuelle**

`FIX_*.md`, `RECAP_*.md`, `VERIFICATION_*.md`, `PALIER*.md`
→ Voir code actuel à la place

---

## 🚨 PIÈGES COURANTS

### 1. ❌ Hardcoding chemins projets

**Problème:** `Path("projects") / project_id`
**Solution:** Utiliser `ProjectManager.get_project_path(project_id)`
**Voir:** `CODING_RULES.md` section "Chemins projets"

### 2. ❌ Exception dans générateur SSE

**Problème:** `raise HTTPException(...)` dans une fonction SSE
**Solution:** `yield "event: error\n" + data + return`
**Voir:** `CODING_RULES.md` section "Gestion erreurs SSE"

### 3. ❌ Import depuis racine

**Problème:** `from matching_engine import ...`
**Solution:** `from lib.matching_core import ...`
**Voir:** `CODING_RULES.md` section "Imports"

### 4. ❌ Duplication schemas

**Problème:** Redéfinir `CV`, `Offre` dans plusieurs fichiers
**Solution:** Toujours importer depuis `lib/models.py`
**Voir:** `CODING_RULES.md` section "Schemas Pydantic"

### 5. ❌ Format CSV export incorrect

**Problème:** Colonnes manquantes, score_map vide
**Solution:** Vérifier que `ResultatMatching` contient tous les champs
**Fichier:** `matching_engine.py:1350-1450`

### 6. ❌ Température LLM incorrecte

**Problème:** Certains modèles (gpt-5-mini) ne supportent pas `temperature`
**Solution:** Vérifier config + fallback models
**Fichier:** `config.yaml:llm.temperature`

---

## 🆘 DIAGNOSTICS (EN CAS DE PROBLÈME)

| Symptôme | Cause probable | Fichier à vérifier | Action |
|----------|----------------|-------------------|--------|
| **CVs non scorés après matching** | Filtrage must-have trop strict | `matching_engine.py:450-580` | Réduire must-have indispensables |
| **Export CSV vide** | `score_map` manquant dans résultats | `matching_engine.py:1350-1450` | Vérifier génération score_map |
| **Parsing échoue** | Format PDF non standard | `parseur_cv.py:200-280` | Vérifier logs LLM |
| **SSE se déconnecte** | Timeout backend ou client | `api/routers/*.py` | Vérifier keep-alive |
| **Nice-have non détectés** | Prompt LLM à ajuster | `matching_engine.py:800-900` | Tester prompt manuellement |
| **Projet introuvable** | Chemin hardcodé au lieu de `get_project_path()` | Routes API | Utiliser `ProjectManager` |
| **Erreur 404 API** | Route mal définie ou CORS | `api/main.py`, `api/routers/` | Vérifier Swagger UI |
| **Frontend ne reçoit pas SSE** | Content-Type incorrect | `api/routers/*.py` (routes stream) | Vérifier `text/event-stream` |

---

## 🔄 MAINTENANCE DE CE FICHIER

### ⚠️ RÈGLE OBLIGATOIRE

Ce fichier DOIT être mis à jour à chaque modification significative :

✅ **Mettre à jour si :**
- Ajout d'une nouvelle route API
- Ajout d'un nouveau fichier Python important
- Modification d'une fonction clé (changement signature, emplacement)
- Ajout/suppression d'un schema Pydantic
- Changement de configuration importante (`config.yaml`)
- Nouveau pattern de code obligatoire

❌ **NE PAS mettre à jour pour :**
- Corrections mineures (typos, commentaires)
- Refactoring interne sans changement d'interface
- Modifications de documentation secondaire

### 🔧 Comment mettre à jour

1. **Modifier la section concernée** (ex: ajout route API → section "API REST")
2. **Mettre à jour la date** : `**Dernière MAJ:** JJ/MM/AAAA`
3. **Ajouter un commentaire** en haut du fichier (optionnel si changement majeur)

**Voir détails complets :** `MAINTENANCE_GUIDE.md`

---

## 📞 SUPPORT & RESSOURCES

**En cas de doute :**
1. Lire ce fichier (`REFERENCE_COMPLETE.md`)
2. Consulter `CODING_RULES.md` pour les patterns
3. Vérifier le code source directement
4. Consulter les tests pour exemples d'usage

**Fichiers de log :**
- Terminal API : stdout FastAPI
- Terminal frontend : stdout Vite
- Fichier `logs/` (si configuré)

---

**🔄 Ce fichier est LA source de vérité pour la structure du projet**
**📖 Toujours consulter EN PREMIER avant toute modification**

---

_Dernière modification: 18 octobre 2025 - Version 2.6.4_
