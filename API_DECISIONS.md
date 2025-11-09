# BRAIN RH API - DÉCISIONS D'ARCHITECTURE

**Date:** 11 octobre 2025
**Version:** 1.0.0
**Statut:** ✅ Validé (Palier 1)

---

## 🎯 OBJECTIFS DE L'API

### Objectif principal
Exposer toutes les fonctionnalités de Brain RH via une API REST moderne pour permettre la création d'un frontend React découplé.

### Objectifs secondaires
1. **Performance:** Supporter le streaming SSE pour les traitements longs (parsing 32 CVs ~5-8 min)
2. **Scalabilité:** Architecture stateless permettant le déploiement multi-instances
3. **Maintenabilité:** Contrat OpenAPI complet pour génération de clients TypeScript
4. **Compatibilité:** Réutiliser 100% de la logique métier existante (`lib/`)

---

## 📐 PRINCIPES D'ARCHITECTURE

### 1. RESTful Design
- **Ressources:** CVs, Offres, Matchings, Projets, Entreprises
- **Verbes HTTP standards:** GET (lecture), POST (création), PUT (modification complète), DELETE (suppression)
- **Status codes:** 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 404 (Not Found), 500 (Internal Error)

### 2. Versioning
- **Format:** `/api/v1/`
- **Rationale:** Permet évolutions futures sans casser clients existants
- **Plan:** v1 = parité Streamlit, v2+ = nouvelles fonctionnalités

### 3. Stateless
- **Aucune session côté serveur**
- **Stockage:** Fichiers locaux (projets, CVs parsés, résultats matchings)
- **Future:** Migration vers base de données relationnelle (PostgreSQL) prévue

### 4. Async First
- **FastAPI** avec support async natif
- **Réutilisation** du code parallèle existant (`lib/parallel_engine.py`)
- **Non-blocking I/O** pour appels OpenAI

---

## 🔌 ENDPOINTS

### Groupes d'endpoints

| Groupe | Nombre | Description |
|--------|--------|-------------|
| **CVs** | 4 | Upload, parsing, récupération, suppression |
| **Offres** | 5 | CRUD + enrichissement LLM |
| **Matching** | 5 | Lancement, résultats, exports CSV/JSON |
| **Projets** | 6 | CRUD + historique matchings |
| **Entreprises** | 5 | CRUD entreprises clientes |
| **TOTAL** | **25** | |

### Endpoints critiques

#### 1. `/cvs/parse/stream` (POST)
- **Pourquoi:** Parsing de 32 CVs = 2-5 minutes → besoin de feedback temps-réel
- **SSE events:** `progress`, `result`, `done`, `error`
- **Alternative batch:** `/cvs/parse` sans streaming

#### 2. `/matching/run/stream` (POST)
- **Pourquoi:** Matching complet = 5-8 minutes (must-have + embeddings + nice-have + re-ranking)
- **SSE events:** `progress` (4 étapes), `result` (CVs filtrés/scorés), `done`
- **Alternative batch:** `/matching/run` sans streaming

#### 3. `/offres/enrich` (POST)
- **Pourquoi:** Génération must-have/nice-have via LLM (30-60s)
- **Option:** Intégration France Travail API (ROME)
- **Mode:** Synchrone (pas de streaming nécessaire car < 1 min)

---

## 📊 SERVER-SENT EVENTS (SSE)

### Choix SSE vs WebSocket

| Critère | SSE | WebSocket |
|---------|-----|-----------|
| **Complexité** | Simple (HTTP) | Complexe (protocole custom) |
| **Direction** | Serveur → Client | Bidirectionnel |
| **Reconnexion auto** | ✅ Oui (natif navigateur) | ❌ Non (à implémenter) |
| **Use case Brain RH** | ✅ Parfait (progression unidirectionnelle) | ❌ Overkill (pas besoin bidirectionnel) |

**Décision:** SSE pour tous les traitements longs (parsing, matching)

### Format événements

```
event: progress
data: {"event":"progress","step":"parsing","current":5,"total":10,"progress":0.5}

event: result
data: {"event":"result","data":{...}}

event: done
data: {"event":"done","summary":{...}}

event: error
data: {"event":"error","code":"...","message":"..."}
```

**Rationale:** Format JSON dans `data:` pour faciliter parsing côté client JavaScript.

---

## 🗂️ SCHEMAS (PYDANTIC)

### Réutilisation modèles existants

**Tous les schemas OpenAPI** sont basés sur les Pydantic models de `lib/models.py`:

- `CV` → `lib/models.py:CV`
- `Offre` → `lib/models.py:Offre`
- `ResultatMatching` → `lib/models.py:ResultatMatching`
- `CVParseResult` → `lib/models.py:CVParseResult`

**Avantage:** Validation automatique + génération OpenAPI via FastAPI.

### Schemas additionnels

Créés spécifiquement pour l'API:

- `MatchingRequest`: Payload pour `/matching/run`
- `ProjectInput`: Payload pour création/modification projet
- `EnterpriseInput`: Payload pour création/modification entreprise
- `SSE*Event`: Événements SSE typés

---

## 💾 STOCKAGE

### État actuel (v1.0)

**Système de fichiers local** (compatible avec code existant):

```
projects/
├── {enterprise_id}/
│   └── {project_id}/
│       ├── cvs_parsed/
│       │   └── *.json
│       ├── offres/
│       │   └── *.json
│       └── historique/
│           └── {timestamp}_matching.json
```

### Migration future (v2.0)

**PostgreSQL** avec:
- Table `enterprises`
- Table `projects` (FK → enterprises)
- Table `cvs` (FK → projects)
- Table `offres` (FK → projects)
- Table `matchings` (FK → projects)
- Table `matching_results` (FK → matchings)

**Rationale:** Requêtes complexes, pagination, recherche full-text, multi-tenancy.

---

## 🔐 SÉCURITÉ

### V1.0 (développement local)

- **Aucune authentification** (API ouverte)
- **CORS:** Permissif (`*`) pour développement
- **Validation:** Pydantic sur tous les payloads

### V2.0 (production)

**Plan:**
- **API Keys** (header `X-API-Key`)
- **CORS:** Whitelist domaines autorisés
- **Rate limiting:** 100 req/min par IP
- **HTTPS:** Obligatoire (Let's Encrypt)

---

## 📤 EXPORTS

### Formats supportés

1. **JSON** (`/matching/{id}/export/json`)
   - Structure complète
   - Facile à réimporter
   - Idéal pour archivage

2. **CSV** (`/matching/{id}/export/csv`)
   - Colonnes: cv, score_final, score_base, nice_have_manquants, commentaire_scoring
   - Compatible Excel
   - Idéal pour analyse business

### Rationale

Les 2 formats répondent à des besoins différents:
- **JSON:** Développeurs, intégrations, archivage
- **CSV:** RH, managers, analyse Excel

---

## 🚀 PERFORMANCE

### Optimisations prévues

1. **Parallélisation** (déjà implémentée dans `lib/`)
   - Parsing: 500 CVs max simultanés, QPS 10
   - Must-have filtering: 500 CVs max simultanés
   - Nice-have detection: 500 CVs max simultanés

2. **Caching** (à implémenter)
   - Cache embeddings (hash texte → vecteur)
   - Cache résultats enrichissement offres
   - TTL: 24h

3. **Streaming** (SSE)
   - Feedback temps-réel (UX)
   - Pas de timeout côté client

### Métriques cibles (32 CVs)

| Étape | Temps actuel | Cible v2.0 |
|-------|--------------|------------|
| Parsing | 2 min | 1 min (cache) |
| Must-have | 1-2 min | 1 min |
| Embeddings | 5s | 2s (GPU) |
| Nice-have | 1-2 min | 1 min |
| Re-ranking | 30-60s | 30s |
| **TOTAL** | **5-8 min** | **3-4 min** |

---

## 🧪 TESTS

### Stratégie de test (Palier 2)

1. **Tests unitaires FastAPI**
   - Routes: pytest + TestClient
   - Validation payloads: exemples JSON
   - SSE: test événements émis

2. **Tests d'intégration**
   - Parsing bout-en-bout (avec vraies CVs)
   - Matching complet (offre + 10 CVs)
   - Exports CSV/JSON

3. **Tests de charge**
   - 100 CVs en parallèle
   - 10 requêtes simultanées
   - Timeout SSE

---

## 📝 DOCUMENTATION

### OpenAPI (Swagger)

- **Fichier:** `openapi.yaml` (950+ lignes)
- **Génération auto docs:** FastAPI → `/docs` (Swagger UI)
- **Génération client TypeScript:** `openapi-generator-cli`

### Exemples

- **Dossier:** `api/examples/`
- **Fichiers:**
  - `cv_example.json`: CV parsé complet
  - `offre_example.json`: Offre avec must-have/nice-have
  - `matching_request.json`: Payload matching
  - `matching_response.json`: Résultats matching
  - `sse_events.md`: Documentation SSE avec exemples JS

---

## 🎯 COMPATIBILITÉ STREAMLIT

### Principe

**L'API réutilise 100% de `lib/`** → garantie parité fonctionnelle.

### Vérification

| Fonctionnalité Streamlit | Endpoint API | Status |
|---------------------------|--------------|--------|
| Upload CVs | `POST /cvs/parse` | ✅ Mappé |
| Parsing parallèle | `POST /cvs/parse/stream` | ✅ Mappé |
| Enrichir offre | `POST /offres/enrich` | ✅ Mappé |
| Lancer matching | `POST /matching/run` | ✅ Mappé |
| Export CSV | `GET /matching/{id}/export/csv` | ✅ Mappé |
| Export JSON | `GET /matching/{id}/export/json` | ✅ Mappé |
| Gestion projets | `GET/POST/PUT/DELETE /projects` | ✅ Mappé |
| Gestion entreprises | `GET/POST/PUT/DELETE /enterprises` | ✅ Mappé |
| Historique | `GET /projects/{id}/history` | ✅ Mappé |

---

## ⚠️ LIMITATIONS CONNUES

### V1.0

1. **Pas de pagination** (GET /projects, /enterprises)
   - Retourne toutes les ressources
   - À implémenter en v2.0 avec `?limit=50&offset=0`

2. **Pas d'authentification**
   - API ouverte (développement uniquement)
   - À sécuriser avant production

3. **Stockage fichiers local**
   - Pas de concurrent access
   - Pas de recherche full-text
   - Migration PostgreSQL prévue v2.0

4. **Pas de gestion uploads volumineux**
   - Limite taille fichier: défaut FastAPI (10 MB)
   - À augmenter si nécessaire

---

## 📅 ROADMAP

### Palier 2 (API Backend FastAPI)
- [ ] Implémenter tous les endpoints
- [ ] Tests unitaires + intégration
- [ ] Vérifier parité Streamlit

### Palier 3 (Frontend React)
- [ ] Générer client TypeScript depuis OpenAPI
- [ ] Implémenter pages P0 (parsing, matching)
- [ ] Intégrer SSE pour feedback temps-réel

### Palier 4 (Streaming complet)
- [ ] SSE pour parsing
- [ ] SSE pour matching
- [ ] Gestion reconnexions

### Palier 5 (Parité complète)
- [ ] Toutes les fonctionnalités Streamlit
- [ ] Tests E2E Playwright
- [ ] Documentation complète

### V2.0 (Production)
- [ ] Migration PostgreSQL
- [ ] Authentification API Keys
- [ ] Rate limiting
- [ ] HTTPS
- [ ] Monitoring (Sentry, logs)

---

## ✅ VALIDATION PALIER 1

### Critères de succès

- [x] `openapi.yaml` complet et valide
- [x] 25 endpoints définis
- [x] 22 schemas documentés
- [x] SSE events spécifiés
- [x] Exemples JSON créés
- [x] Documentation décisions architecture

### Livrable

Contrat d'API figé prêt pour implémentation FastAPI (Palier 2).

**Status:** ✅ **VALIDÉ**
