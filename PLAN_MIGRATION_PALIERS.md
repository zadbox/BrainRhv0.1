# 🚀 PLAN DE MIGRATION PAR PALIERS — Brain RH
**Streamlit → FastAPI + React TypeScript**

**Principe directeur:** ZÉRO régression. Chaque palier doit être validé par toi avant de passer au suivant.

---

## 📋 RÈGLES D'OR

### ✅ À FAIRE
- **Extraire** la logique métier dans des modules Python purs (aucune dépendance Streamlit)
- **Geler** le contrat d'API (OpenAPI) dès le début
- **Tester** chaque palier avec des cas de référence Streamlit
- **Valider** avec toi avant de continuer
- **Conserver** tous les prompts LLM existants (mot pour mot)
- **Préserver** la parallélisation (asyncio + Semaphore)

### ❌ À NE JAMAIS FAIRE
- ❌ Modifier la logique de `matching_engine.py` (formules, prompts, pipeline)
- ❌ Changer les prompts LLM sans validation explicite
- ❌ Passer au palier suivant sans ton OK
- ❌ Réécrire les algorithmes (extraction, scoring, re-ranking)
- ❌ Ajouter des dépendances lourdes (pas de Celery/Redis pour MVP)
- ❌ Toucher à la parallélisation asyncio (prouvée performante)

---

## 🎯 VUE D'ENSEMBLE DES PALIERS

| Palier | Objectif | Livrables | Validation requise |
|--------|----------|-----------|-------------------|
| **0** | Audit & extraction logique | Modules purs Python | Tests unitaires passent |
| **1** | Contrat API figé | `openapi.yaml` + mocks | Tu valides le contrat |
| **2** | API FastAPI mince | Endpoints fonctionnels | Postman/curl = résultats Streamlit |
| **3** | Front P0 (sync) | Page parsing CVs | UX identique à Streamlit |
| **4** | Streaming SSE | Feedback progressif | Pas de freeze, reconnection OK |
| **5** | Parité complète | Toutes les pages | A/B Streamlit vs React = identique |

**Durée estimée:** 3-4 semaines avec validations
**Point de non-retour:** Aucun (Streamlit reste opérationnel en parallèle)

---

## 🔬 PALIER 0 — AUDIT & EXTRACTION LOGIQUE MÉTIER
**Durée:** 2-3 jours
**Objectif:** Rendre le code testable sans Streamlit

### Tâches
1. **Créer structure `lib/`**
   ```
   lib/
   ├── __init__.py
   ├── cv_parsing.py          # Extraction de parseur_cv.py
   ├── matching_core.py       # Extraction de matching_engine.py
   ├── offer_processing.py    # Extraction de offer_enrichment.py
   ├── parallel_engine.py     # Extraction parallélisation
   ├── models.py              # Pydantic models (CV, Offre, Résultat)
   └── config.py              # Config sans Streamlit
   ```

2. **Extraire fonctions pures**
   - `parseur_cv.py` → `lib/cv_parsing.py` (extraction texte + prompt LLM)
   - `matching_engine.py` → `lib/matching_core.py` (vectorisation, scoring, re-ranking)
   - `offer_enrichment.py` → `lib/offer_processing.py` (enrichissement)
   - `parallel_cv_parsing.py` + `must_have_parallel.py` + `nice_have_parallel.py` → `lib/parallel_engine.py`

3. **Créer Pydantic models** (`lib/models.py`)
   ```python
   from pydantic import BaseModel, Field
   from typing import List, Optional, Dict, Any

   class Identite(BaseModel):
       nom: str = ""
       prenom: str = ""
       email: str = ""
       telephone: str = ""
       adresse: str = ""
       linkedin: str = ""

   class Experience(BaseModel):
       poste: str = ""
       entreprise: str = ""
       lieu: str = ""
       date_debut: str = ""
       date_fin: str = ""
       duree: str = ""
       missions: List[str] = []

   class CV(BaseModel):
       identite: Identite
       titre: str = ""
       resume_professionnel: str = ""
       competences_techniques: List[str] = []
       competences_transversales: List[str] = []
       langues: List[str] = []
       experiences_professionnelles: List[Experience] = []
       formations: List[Dict[str, Any]] = []
       certifications: List[str] = []
       cv: str = ""  # filename

   class Offre(BaseModel):
       titre: str
       competences_techniques: List[str] = []
       competences_transversales: List[str] = []
       langues: List[str] = []
       experiences_professionnelles: List[Dict[str, Any]] = []
       formations: List[Dict[str, Any]] = []
       certifications: List[str] = []
       must_have: List[str] = []
       nice_have: List[str] = []

   class ResultatMatching(BaseModel):
       cv: str
       score_final: float
       score_base: float
       bonus_nice_have_multiplicateur: float
       coefficient_qualite_experience: float
       nice_have_manquants: List[str] = []
       commentaire_scoring: Optional[str] = None
       appreciation_globale: Optional[str] = None
   ```

4. **Tests unitaires de non-régression**
   ```python
   # tests/test_palier0_extraction.py
   import pytest
   from lib.cv_parsing import extract_text_from_pdf, parse_cv_with_llm
   from lib.matching_core import calculate_similarity, calculate_final_score

   def test_pdf_extraction_identique():
       # Utiliser un CV de référence
       cv_path = "tests/fixtures/cv_reference.pdf"

       # Extraction actuelle (parseur_cv.py)
       import parseur_cv
       texte_ancien = parseur_cv.extract_text_from_pdf(cv_path)

       # Extraction nouvelle (lib/cv_parsing.py)
       from lib.cv_parsing import extract_text_from_pdf
       texte_nouveau = extract_text_from_pdf(cv_path)

       assert texte_ancien == texte_nouveau

   def test_scoring_formula_identique():
       # Cas de référence
       score_base = 0.75
       bonus_nice_have = 0.95
       coef_xp = 1.2

       # Formule actuelle (matching_engine.py)
       score_attendu = score_base * bonus_nice_have * coef_xp

       # Formule nouvelle (lib/matching_core.py)
       from lib.matching_core import calculate_final_score
       score_nouveau = calculate_final_score(score_base, bonus_nice_have, coef_xp)

       assert abs(score_attendu - score_nouveau) < 0.0001
   ```

### Livrables Palier 0
- [ ] Dossier `lib/` avec modules purs
- [ ] `lib/models.py` avec Pydantic models complets
- [ ] `tests/test_palier0_extraction.py` avec 5+ tests de non-régression
- [ ] Tous les tests VERTS

### Validation Palier 0
**TOI:** Exécuter `pytest tests/test_palier0_extraction.py -v` et vérifier que tous les tests passent
**Critère GO:** 100% des tests verts, aucune modification de logique

---

## 📝 PALIER 1 — CONTRAT API FIGÉ (OpenAPI)
**Durée:** 1-2 jours
**Objectif:** Définir le contrat d'API complet AVANT d'écrire du code

### Tâches
1. **Créer `openapi.yaml`** (contrat complet)
   ```yaml
   openapi: 3.1.0
   info:
     title: Brain RH API
     version: 1.0.0
     description: API de matching CV/Offre

   servers:
     - url: http://localhost:8000/api/v1

   paths:
     /cvs/parse:
       post:
         summary: Parser un ou plusieurs CVs
         operationId: parseCVs
         requestBody:
           required: true
           content:
             multipart/form-data:
               schema:
                 type: object
                 properties:
                   files:
                     type: array
                     items:
                       type: string
                       format: binary
         responses:
           200:
             description: CVs parsés
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     success_count: { type: integer }
                     failed_count: { type: integer }
                     results:
                       type: array
                       items:
                         $ref: '#/components/schemas/CV'

     /cvs/parse/stream:
       post:
         summary: Parser CVs avec streaming SSE
         operationId: parseCVsStream
         requestBody:
           required: true
           content:
             multipart/form-data:
               schema:
                 type: object
                 properties:
                   files:
                     type: array
                     items:
                       type: string
                       format: binary
         responses:
           200:
             description: Stream d'événements de parsing
             content:
               text/event-stream:
                 schema:
                   type: string

     /matching/run:
       post:
         summary: Lancer un matching
         operationId: runMatching
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   offre:
                     $ref: '#/components/schemas/Offre'
                   cvs:
                     type: array
                     items:
                       $ref: '#/components/schemas/CV'
                   top_rerank:
                     type: integer
                     default: 10
                     minimum: 5
                     maximum: 20
         responses:
           200:
             description: Résultats du matching
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     results:
                       type: array
                       items:
                         $ref: '#/components/schemas/ResultatMatching'
                     metadata:
                       type: object
                       properties:
                         total_cvs: { type: integer }
                         filtered_must_have: { type: integer }
                         top_reranked: { type: integer }
                         duree_totale_s: { type: number }

     /matching/stream:
       post:
         summary: Matching avec streaming SSE
         operationId: runMatchingStream
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   offre:
                     $ref: '#/components/schemas/Offre'
                   cvs:
                     type: array
                     items:
                       $ref: '#/components/schemas/CV'
                   top_rerank:
                     type: integer
         responses:
           200:
             description: Stream d'événements de matching
             content:
               text/event-stream:
                 schema:
                   type: string

     /offers/enrich:
       post:
         summary: Enrichir une offre via LLM
         operationId: enrichOffer
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   offre_brute:
                     type: string
                   use_rome:
                     type: boolean
                     default: false
         responses:
           200:
             description: Offre enrichie
             content:
               application/json:
                 schema:
                   $ref: '#/components/schemas/Offre'

     /projects:
       get:
         summary: Lister les projets
         operationId: listProjects
         parameters:
           - name: enterprise_id
             in: query
             required: false
             schema:
               type: string
         responses:
           200:
             description: Liste des projets
             content:
               application/json:
                 schema:
                   type: array
                   items:
                     $ref: '#/components/schemas/Project'

       post:
         summary: Créer un projet
         operationId: createProject
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   nom: { type: string }
                   enterprise_id: { type: string }
         responses:
           201:
             description: Projet créé
             content:
               application/json:
                 schema:
                   $ref: '#/components/schemas/Project'

     /enterprises:
       get:
         summary: Lister les entreprises
         operationId: listEnterprises
         responses:
           200:
             description: Liste des entreprises
             content:
               application/json:
                 schema:
                   type: array
                   items:
                     $ref: '#/components/schemas/Enterprise'

       post:
         summary: Créer une entreprise
         operationId: createEnterprise
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   nom: { type: string }
                   secteur: { type: string }
         responses:
           201:
             description: Entreprise créée
             content:
               application/json:
                 schema:
                   $ref: '#/components/schemas/Enterprise'

   components:
     schemas:
       Identite:
         type: object
         properties:
           nom: { type: string }
           prenom: { type: string }
           email: { type: string }
           telephone: { type: string }
           adresse: { type: string }
           linkedin: { type: string }

       Experience:
         type: object
         properties:
           poste: { type: string }
           entreprise: { type: string }
           lieu: { type: string }
           date_debut: { type: string }
           date_fin: { type: string }
           duree: { type: string }
           missions:
             type: array
             items:
               type: string

       CV:
         type: object
         required: [cv]
         properties:
           cv: { type: string }
           identite: { $ref: '#/components/schemas/Identite' }
           titre: { type: string }
           resume_professionnel: { type: string }
           competences_techniques:
             type: array
             items:
               type: string
           competences_transversales:
             type: array
             items:
               type: string
           langues:
             type: array
             items:
               type: string
           experiences_professionnelles:
             type: array
             items:
               $ref: '#/components/schemas/Experience'
           formations:
             type: array
             items:
               type: object
           certifications:
             type: array
             items:
               type: string

       Offre:
         type: object
         required: [titre]
         properties:
           titre: { type: string }
           competences_techniques:
             type: array
             items:
               type: string
           competences_transversales:
             type: array
             items:
               type: string
           langues:
             type: array
             items:
               type: string
           experiences_professionnelles:
             type: array
             items:
               type: object
           formations:
             type: array
             items:
               type: object
           certifications:
             type: array
             items:
               type: string
           must_have:
             type: array
             items:
               type: string
           nice_have:
             type: array
             items:
               type: string

       ResultatMatching:
         type: object
         required: [cv, score_final]
         properties:
           cv: { type: string }
           score_final: { type: number, minimum: 0, maximum: 1 }
           score_base: { type: number, minimum: 0, maximum: 1 }
           bonus_nice_have_multiplicateur: { type: number }
           coefficient_qualite_experience: { type: number }
           nice_have_manquants:
             type: array
             items:
               type: string
           commentaire_scoring: { type: string, nullable: true }
           appreciation_globale: { type: string, nullable: true }

       Project:
         type: object
         properties:
           id: { type: string }
           nom: { type: string }
           enterprise_id: { type: string }
           created_at: { type: string, format: date-time }
           last_modified: { type: string, format: date-time }
           status: { type: string, enum: [actif, archive] }

       Enterprise:
         type: object
         properties:
           id: { type: string }
           nom: { type: string }
           secteur: { type: string }
           created_at: { type: string, format: date-time }
           projects_count: { type: integer }

       SSEEvent:
         type: object
         description: Format des événements SSE
         properties:
           event:
             type: string
             enum: [progress, result, error, done]
           data:
             type: object
   ```

2. **Créer exemples de payloads** (`api/examples/`)
   - `cv_parse_request.json`
   - `cv_parse_response.json`
   - `matching_request.json`
   - `matching_response.json`
   - `sse_events.txt` (exemples d'événements SSE)

3. **Documenter événements SSE**
   ```markdown
   # Événements SSE

   ## Parsing CVs (`/cvs/parse/stream`)

   ```
   event: progress
   data: {"current": 1, "total": 10, "filename": "cv1.pdf", "status": "extracting"}

   event: progress
   data: {"current": 1, "total": 10, "filename": "cv1.pdf", "status": "parsing"}

   event: result
   data: {"filename": "cv1.pdf", "success": true, "cv": {...}}

   event: progress
   data: {"current": 2, "total": 10, "filename": "cv2.pdf", "status": "extracting"}

   event: done
   data: {"success_count": 9, "failed_count": 1}
   ```

   ## Matching (`/matching/stream`)

   ```
   event: progress
   data: {"step": "vectorization", "progress": 0.1, "message": "Vectorisation de l'offre"}

   event: progress
   data: {"step": "must_have_filtering", "progress": 0.3, "current": 15, "total": 50}

   event: progress
   data: {"step": "nice_have_detection", "progress": 0.5, "current": 10, "total": 30}

   event: progress
   data: {"step": "scoring", "progress": 0.7, "message": "Calcul des scores"}

   event: progress
   data: {"step": "reranking", "progress": 0.9, "current": 5, "total": 10}

   event: result
   data: {"cv": "cv1.json", "score_final": 0.85, ...}

   event: done
   data: {"total_results": 10, "duree_totale_s": 125.3}
   ```
   ```

### Livrables Palier 1
- [ ] `openapi.yaml` complet et validé
- [ ] `api/examples/` avec tous les payloads
- [ ] `docs/SSE_EVENTS.md` documentant le format des événements
- [ ] Validation du contrat avec un outil (Swagger Editor)

### Validation Palier 1
**TOI:**
1. Ouvrir `openapi.yaml` dans Swagger Editor (https://editor.swagger.io/)
2. Vérifier qu'il n'y a pas d'erreurs
3. Parcourir tous les endpoints et schémas
4. Valider que ça couvre 100% des fonctionnalités Streamlit
5. **Donner ton GO explicite**

**Critère GO:** Le contrat couvre toutes les fonctionnalités, pas d'ambiguïté, pas d'erreur de syntaxe

---

## ⚙️ PALIER 2 — API FASTAPI MINCE (SANS FRONT)
**Durée:** 3-4 jours
**Objectif:** Exposer la logique métier via FastAPI, tester avec Postman/curl

### Tâches
1. **Structure API**
   ```
   api/
   ├── __init__.py
   ├── main.py                # Point d'entrée FastAPI
   ├── dependencies.py        # Dépendances (config, LLM client)
   ├── routers/
   │   ├── __init__.py
   │   ├── cvs.py            # Endpoints parsing CVs
   │   ├── matching.py       # Endpoints matching
   │   ├── offers.py         # Endpoints offres
   │   ├── projects.py       # Endpoints projets
   │   └── enterprises.py    # Endpoints entreprises
   └── middleware.py          # CORS, logging, etc.
   ```

2. **Créer `api/main.py`**
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from api.routers import cvs, matching, offers, projects, enterprises

   app = FastAPI(
       title="Brain RH API",
       version="1.0.0",
       description="API de matching CV/Offre"
   )

   # CORS pour dev local
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Routers
   app.include_router(cvs.router, prefix="/api/v1/cvs", tags=["CVs"])
   app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])
   app.include_router(offers.router, prefix="/api/v1/offers", tags=["Offres"])
   app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projets"])
   app.include_router(enterprises.router, prefix="/api/v1/enterprises", tags=["Entreprises"])

   @app.get("/health")
   def health():
       return {"status": "ok"}
   ```

3. **Implémenter routeur CVs** (`api/routers/cvs.py`)
   ```python
   from fastapi import APIRouter, UploadFile, File
   from fastapi.responses import StreamingResponse
   from typing import List
   from lib.cv_parsing import parse_cv_from_file
   from lib.parallel_engine import parse_cvs_parallel
   from lib.models import CV
   import asyncio

   router = APIRouter()

   @router.post("/parse")
   async def parse_cvs(files: List[UploadFile] = File(...)):
       """Parse CVs en mode batch (réponse d'un coup)"""
       results = await parse_cvs_parallel(files, max_concurrent=500)
       return {
           "success_count": results["success_count"],
           "failed_count": results["failed_count"],
           "results": results["results"]
       }

   @router.post("/parse/stream")
   async def parse_cvs_stream(files: List[UploadFile] = File(...)):
       """Parse CVs avec streaming SSE"""
       async def event_generator():
           total = len(files)
           success_count = 0
           failed_count = 0

           for idx, file in enumerate(files, 1):
               # Progression: extraction
               yield f"event: progress\n"
               yield f"data: {json.dumps({'current': idx, 'total': total, 'filename': file.filename, 'status': 'extracting'})}\n\n"

               try:
                   # Extraction texte
                   content = await file.read()
                   text = extract_text(content, file.filename)

                   # Progression: parsing
                   yield f"event: progress\n"
                   yield f"data: {json.dumps({'current': idx, 'total': total, 'filename': file.filename, 'status': 'parsing'})}\n\n"

                   # Parsing LLM
                   cv = await parse_cv_with_llm(text, file.filename)

                   # Résultat
                   yield f"event: result\n"
                   yield f"data: {json.dumps({'filename': file.filename, 'success': True, 'cv': cv.dict()})}\n\n"

                   success_count += 1

               except Exception as e:
                   yield f"event: result\n"
                   yield f"data: {json.dumps({'filename': file.filename, 'success': False, 'error': str(e)})}\n\n"
                   failed_count += 1

           # Fin
           yield f"event: done\n"
           yield f"data: {json.dumps({'success_count': success_count, 'failed_count': failed_count})}\n\n"

       return StreamingResponse(
           event_generator(),
           media_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"  # Disable nginx buffering
           }
       )
   ```

4. **Implémenter routeur Matching** (`api/routers/matching.py`)
   ```python
   from fastapi import APIRouter
   from fastapi.responses import StreamingResponse
   from lib.matching_core import MatchingEngine
   from lib.models import Offre, CV, ResultatMatching
   from typing import List
   import json

   router = APIRouter()

   @router.post("/run")
   async def run_matching(
       offre: Offre,
       cvs: List[CV],
       top_rerank: int = 10
   ):
       """Matching synchrone (réponse d'un coup)"""
       engine = MatchingEngine()
       results = await engine.match_cvs_with_job(
           cvs=cvs,
           job_description=offre.dict(),
           must_have_list=offre.must_have,
           nice_have_list=offre.nice_have,
           top_rerank=top_rerank
       )

       return {
           "results": results["ranked_cvs"],
           "metadata": {
               "total_cvs": len(cvs),
               "filtered_must_have": results["filtered_count"],
               "top_reranked": top_rerank,
               "duree_totale_s": results["duree_totale"]
           }
       }

   @router.post("/stream")
   async def run_matching_stream(
       offre: Offre,
       cvs: List[CV],
       top_rerank: int = 10
   ):
       """Matching avec streaming SSE"""
       async def event_generator():
           engine = MatchingEngine()

           # Callbacks pour progression
           def on_progress(step: str, current: int = None, total: int = None, progress: float = None):
               data = {"step": step}
               if current and total:
                   data.update({"current": current, "total": total})
               if progress:
                   data["progress"] = progress
               return f"event: progress\ndata: {json.dumps(data)}\n\n"

           # Lancer matching avec callbacks
           async for event in engine.match_cvs_with_job_stream(
               cvs=cvs,
               job_description=offre.dict(),
               must_have_list=offre.must_have,
               nice_have_list=offre.nice_have,
               top_rerank=top_rerank,
               progress_callback=on_progress
           ):
               yield event

           yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"

       return StreamingResponse(
           event_generator(),
           media_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"
           }
       )
   ```

5. **Tests d'API** (`tests/test_palier2_api.py`)
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from api.main import app

   client = TestClient(app)

   def test_health():
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json() == {"status": "ok"}

   def test_parse_cvs_sync():
       # Charger un CV de référence
       with open("tests/fixtures/cv_reference.pdf", "rb") as f:
           response = client.post(
               "/api/v1/cvs/parse",
               files={"files": ("cv_reference.pdf", f, "application/pdf")}
           )

       assert response.status_code == 200
       data = response.json()
       assert data["success_count"] == 1
       assert len(data["results"]) == 1

       # Comparer avec résultat Streamlit de référence
       import json
       with open("tests/fixtures/cv_reference_expected.json") as f:
           expected = json.load(f)

       # Vérifier champs critiques
       result = data["results"][0]["data"]
       assert result["identite"]["nom"] == expected["identite"]["nom"]
       assert result["competences_techniques"] == expected["competences_techniques"]

   def test_matching_sync():
       # Charger offre et CVs de référence
       with open("tests/fixtures/offre_reference.json") as f:
           offre = json.load(f)

       with open("tests/fixtures/cvs_reference.json") as f:
           cvs = json.load(f)

       response = client.post(
           "/api/v1/matching/run",
           json={
               "offre": offre,
               "cvs": cvs,
               "top_rerank": 10
           }
       )

       assert response.status_code == 200
       data = response.json()

       # Comparer avec résultat Streamlit de référence
       with open("tests/fixtures/matching_reference_result.json") as f:
           expected = json.load(f)

       # Vérifier ordre et scores (tolérance 0.01)
       for i, result in enumerate(data["results"][:5]):  # Top 5
           assert result["cv"] == expected["results"][i]["cv"]
           assert abs(result["score_final"] - expected["results"][i]["score_final"]) < 0.01
   ```

6. **Créer fixtures de référence**
   - Lancer Streamlit actuel
   - Parser 3 CVs et sauvegarder les JSONs dans `tests/fixtures/`
   - Lancer un matching et sauvegarder le résultat dans `tests/fixtures/matching_reference_result.json`

### Livrables Palier 2
- [ ] API FastAPI fonctionnelle (`api/`)
- [ ] Tous les endpoints implémentés (sync + stream)
- [ ] Tests d'API (`tests/test_palier2_api.py`) VERTS
- [ ] Fixtures de référence créées
- [ ] `README_API.md` avec exemples curl/Postman

### Validation Palier 2
**TOI:**
1. Lancer API: `uvicorn api.main:app --reload --port 8000`
2. Tester avec Postman:
   - `POST /api/v1/cvs/parse` avec un CV → comparer résultat avec Streamlit
   - `POST /api/v1/matching/run` avec offre + CVs → comparer scores avec Streamlit
   - `POST /api/v1/matching/stream` → vérifier que les événements SSE arrivent
3. Exécuter tests: `pytest tests/test_palier2_api.py -v`
4. **Critères GO:**
   - Résultats identiques à Streamlit (tolérance 0.01 sur scores)
   - SSE fonctionne sans freeze
   - Tous les tests verts

---

## 🎨 PALIER 3 — FRONT P0 (PAGE PARSING CVS)
**Durée:** 3-4 jours
**Objectif:** Page la plus simple pour valider l'intégration frontend

### Tâches
1. **Setup Vite + React TypeScript**
   ```bash
   npm create vite@latest brain-rh-frontend -- --template react-ts
   cd brain-rh-frontend
   npm install
   npm install @tanstack/react-query axios
   npm install react-dropzone
   npm install lucide-react  # Icons
   ```

2. **Structure frontend**
   ```
   src/
   ├── main.tsx
   ├── App.tsx
   ├── api/
   │   ├── client.ts          # Axios instance
   │   └── endpoints.ts       # Fonctions d'appel API
   ├── components/
   │   ├── CVUploader.tsx     # Drag & drop
   │   ├── CVParsingProgress.tsx  # Barre de progression
   │   └── CVList.tsx         # Liste CVs parsés
   ├── pages/
   │   └── CVParsingPage.tsx  # Page complète
   └── types/
       └── api.ts             # Types TypeScript depuis OpenAPI
   ```

3. **Types TypeScript** (`src/types/api.ts`)
   ```typescript
   // Générer automatiquement depuis openapi.yaml avec:
   // npx openapi-typescript openapi.yaml -o src/types/api.ts

   // Ou écrire manuellement:
   export interface Identite {
     nom: string;
     prenom: string;
     email: string;
     telephone: string;
     adresse: string;
     linkedin: string;
   }

   export interface Experience {
     poste: string;
     entreprise: string;
     lieu: string;
     date_debut: string;
     date_fin: string;
     duree: string;
     missions: string[];
   }

   export interface CV {
     cv: string;
     identite: Identite;
     titre: string;
     resume_professionnel: string;
     competences_techniques: string[];
     competences_transversales: string[];
     langues: string[];
     experiences_professionnelles: Experience[];
     formations: any[];
     certifications: string[];
   }

   export interface ParseCVsResponse {
     success_count: number;
     failed_count: number;
     results: Array<{
       filename: string;
       success: boolean;
       data?: CV;
       error?: string;
     }>;
   }
   ```

4. **Client API** (`src/api/client.ts`)
   ```typescript
   import axios from 'axios';

   export const apiClient = axios.create({
     baseURL: 'http://localhost:8000/api/v1',
     timeout: 300000, // 5 minutes
     headers: {
       'Content-Type': 'application/json',
     },
   });
   ```

5. **Endpoints** (`src/api/endpoints.ts`)
   ```typescript
   import { apiClient } from './client';
   import { ParseCVsResponse, CV } from '../types/api';

   export const parseCVs = async (files: File[]): Promise<ParseCVsResponse> => {
     const formData = new FormData();
     files.forEach(file => formData.append('files', file));

     const response = await apiClient.post<ParseCVsResponse>('/cvs/parse', formData, {
       headers: { 'Content-Type': 'multipart/form-data' }
     });

     return response.data;
   };

   export const parseCVsStream = (
     files: File[],
     onProgress: (event: any) => void,
     onResult: (result: any) => void,
     onDone: (summary: any) => void,
     onError: (error: any) => void
   ): EventSource => {
     const formData = new FormData();
     files.forEach(file => formData.append('files', file));

     // Upload files first to get stream URL
     // (Alternative: implement file upload + streaming in one endpoint)

     const eventSource = new EventSource('http://localhost:8000/api/v1/cvs/parse/stream');

     eventSource.addEventListener('progress', (e) => {
       onProgress(JSON.parse(e.data));
     });

     eventSource.addEventListener('result', (e) => {
       onResult(JSON.parse(e.data));
     });

     eventSource.addEventListener('done', (e) => {
       onDone(JSON.parse(e.data));
       eventSource.close();
     });

     eventSource.onerror = (e) => {
       onError(e);
       eventSource.close();
     };

     return eventSource;
   };
   ```

6. **Composant Upload** (`src/components/CVUploader.tsx`)
   ```typescript
   import React, { useCallback } from 'react';
   import { useDropzone } from 'react-dropzone';
   import { Upload } from 'lucide-react';

   interface CVUploaderProps {
     onFilesSelected: (files: File[]) => void;
     disabled?: boolean;
   }

   export const CVUploader: React.FC<CVUploaderProps> = ({ onFilesSelected, disabled }) => {
     const onDrop = useCallback((acceptedFiles: File[]) => {
       onFilesSelected(acceptedFiles);
     }, [onFilesSelected]);

     const { getRootProps, getInputProps, isDragActive } = useDropzone({
       onDrop,
       accept: {
         'application/pdf': ['.pdf'],
         'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
       },
       disabled
     });

     return (
       <div
         {...getRootProps()}
         className={`
           border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
           transition-colors
           ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
           ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-400'}
         `}
       >
         <input {...getInputProps()} />
         <Upload className="mx-auto mb-4 text-gray-400" size={48} />
         {isDragActive ? (
           <p className="text-blue-600">Déposez les fichiers ici...</p>
         ) : (
           <>
             <p className="text-gray-600 mb-2">
               Glissez-déposez vos CVs (PDF ou DOCX)
             </p>
             <p className="text-sm text-gray-400">
               ou cliquez pour sélectionner
             </p>
           </>
         )}
       </div>
     );
   };
   ```

7. **Page complète** (`src/pages/CVParsingPage.tsx`)
   ```typescript
   import React, { useState } from 'react';
   import { CVUploader } from '../components/CVUploader';
   import { parseCVs } from '../api/endpoints';
   import { ParseCVsResponse } from '../types/api';

   export const CVParsingPage: React.FC = () => {
     const [files, setFiles] = useState<File[]>([]);
     const [parsing, setParsing] = useState(false);
     const [results, setResults] = useState<ParseCVsResponse | null>(null);

     const handleParse = async () => {
       setParsing(true);
       try {
         const response = await parseCVs(files);
         setResults(response);
       } catch (error) {
         console.error(error);
         alert('Erreur lors du parsing');
       } finally {
         setParsing(false);
       }
     };

     return (
       <div className="max-w-6xl mx-auto p-6">
         <h1 className="text-3xl font-bold mb-8">Parser des CVs</h1>

         <div className="mb-8">
           <CVUploader
             onFilesSelected={setFiles}
             disabled={parsing}
           />
         </div>

         {files.length > 0 && (
           <div className="mb-8">
             <h2 className="text-xl font-semibold mb-4">
               {files.length} fichier(s) sélectionné(s)
             </h2>
             <ul className="space-y-2">
               {files.map((file, idx) => (
                 <li key={idx} className="flex items-center">
                   <span className="text-gray-700">{file.name}</span>
                   <span className="ml-auto text-sm text-gray-500">
                     {(file.size / 1024).toFixed(1)} KB
                   </span>
                 </li>
               ))}
             </ul>

             <button
               onClick={handleParse}
               disabled={parsing}
               className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
             >
               {parsing ? 'Parsing en cours...' : 'Lancer le parsing'}
             </button>
           </div>
         )}

         {results && (
           <div className="bg-green-50 border border-green-200 rounded-lg p-4">
             <h2 className="text-xl font-semibold mb-2">Résultats</h2>
             <p>✅ {results.success_count} CVs parsés avec succès</p>
             {results.failed_count > 0 && (
               <p>❌ {results.failed_count} CVs en erreur</p>
             )}
           </div>
         )}
       </div>
     );
   };
   ```

### Livrables Palier 3
- [ ] Frontend Vite + React TypeScript fonctionnel
- [ ] Page parsing CVs avec drag & drop
- [ ] Appels API fonctionnels (sync d'abord)
- [ ] UI ressemble à Streamlit (fonctionnellement)

### Validation Palier 3
**TOI:**
1. Lancer backend: `uvicorn api.main:app --reload --port 8000`
2. Lancer frontend: `npm run dev` (port 5173)
3. Tester upload de 3 CVs:
   - Drag & drop fonctionne
   - Clic bouton "Lancer le parsing"
   - Résultats affichés
4. Comparer résultats avec Streamlit (mêmes CVs)
5. **Critère GO:** Résultats identiques, UX fluide

---

## 📡 PALIER 4 — STREAMING SSE
**Durée:** 2-3 jours
**Objectif:** Feedback progressif pendant parsing et matching

### Tâches
1. **Composant Progress** (`src/components/CVParsingProgress.tsx`)
   ```typescript
   import React from 'react';

   interface ProgressEvent {
     current: number;
     total: number;
     filename: string;
     status: 'extracting' | 'parsing';
   }

   interface CVParsingProgressProps {
     events: ProgressEvent[];
     current: ProgressEvent | null;
   }

   export const CVParsingProgress: React.FC<CVParsingProgressProps> = ({ events, current }) => {
     if (!current) return null;

     const progress = (current.current / current.total) * 100;

     return (
       <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
         <div className="flex items-center justify-between mb-2">
           <span className="font-medium">
             {current.status === 'extracting' ? 'Extraction' : 'Parsing LLM'}
           </span>
           <span className="text-sm text-gray-600">
             {current.current} / {current.total}
           </span>
         </div>

         <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
           <div
             className="bg-blue-600 h-2 rounded-full transition-all"
             style={{ width: `${progress}%` }}
           />
         </div>

         <p className="text-sm text-gray-600">
           {current.filename}
         </p>
       </div>
     );
   };
   ```

2. **Page avec streaming** (`src/pages/CVParsingPage.tsx` - version SSE)
   ```typescript
   import React, { useState } from 'react';
   import { CVUploader } from '../components/CVUploader';
   import { CVParsingProgress } from '../components/CVParsingProgress';
   import { parseCVsStream } from '../api/endpoints';

   export const CVParsingPage: React.FC = () => {
     const [files, setFiles] = useState<File[]>([]);
     const [parsing, setParsing] = useState(false);
     const [currentEvent, setCurrentEvent] = useState<any>(null);
     const [results, setResults] = useState<any[]>([]);
     const [summary, setSummary] = useState<any>(null);

     const handleParseStream = () => {
       setParsing(true);
       setResults([]);
       setSummary(null);

       parseCVsStream(
         files,
         (progress) => {
           setCurrentEvent(progress);
         },
         (result) => {
           setResults(prev => [...prev, result]);
         },
         (done) => {
           setSummary(done);
           setParsing(false);
         },
         (error) => {
           console.error(error);
           alert('Erreur streaming');
           setParsing(false);
         }
       );
     };

     return (
       <div className="max-w-6xl mx-auto p-6">
         <h1 className="text-3xl font-bold mb-8">Parser des CVs</h1>

         <CVUploader
           onFilesSelected={setFiles}
           disabled={parsing}
         />

         {files.length > 0 && !parsing && (
           <button
             onClick={handleParseStream}
             className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
           >
             Lancer le parsing (streaming)
           </button>
         )}

         {parsing && currentEvent && (
           <div className="mt-8">
             <CVParsingProgress
               events={[]}
               current={currentEvent}
             />
           </div>
         )}

         {results.length > 0 && (
           <div className="mt-8">
             <h2 className="text-xl font-semibold mb-4">
               Résultats ({results.length})
             </h2>
             <ul className="space-y-2">
               {results.map((result, idx) => (
                 <li key={idx} className="flex items-center">
                   <span className={result.success ? 'text-green-600' : 'text-red-600'}>
                     {result.success ? '✅' : '❌'}
                   </span>
                   <span className="ml-2">{result.filename}</span>
                 </li>
               ))}
             </ul>
           </div>
         )}

         {summary && (
           <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
             <p>✅ {summary.success_count} CVs parsés</p>
             {summary.failed_count > 0 && (
               <p>❌ {summary.failed_count} CVs en erreur</p>
             )}
           </div>
         )}
       </div>
     );
   };
   ```

3. **Tester reconnection SSE**
   - Simuler perte de connexion réseau
   - Vérifier que EventSource reconnecte automatiquement
   - Ajouter logique de retry si nécessaire

### Livrables Palier 4
- [ ] Streaming SSE fonctionnel (parsing)
- [ ] Progress bar en temps réel
- [ ] Reconnection automatique testée
- [ ] Page matching avec streaming (bonus)

### Validation Palier 4
**TOI:**
1. Upload 10 CVs en mode streaming
2. Observer la progression en temps réel
3. Couper le réseau au milieu → vérifier reconnection
4. **Critère GO:** Pas de freeze, feedback fluide, résultats identiques à Streamlit

---

## 🎯 PALIER 5 — PARITÉ COMPLÈTE
**Durée:** 1 semaine
**Objectif:** Toutes les pages fonctionnelles

### Pages à migrer
1. **Accueil Entreprises**
   - Liste des entreprises (cartes)
   - Formulaire création
   - Actions: Voir projets, Modifier, Supprimer

2. **Accueil Projets**
   - Liste des projets (cartes)
   - Formulaire création
   - Actions: Ouvrir, Modifier, Archiver

3. **Préparer l'offre**
   - Textarea offre brute
   - Boutons enrichissement (LLM, ROME)
   - Classification critères (selectbox)
   - Sauvegarde

4. **Matching**
   - Slider Top N
   - Bouton lancer matching (streaming)
   - Tableau résultats
   - Cartes détaillées CVs
   - Export CSV

### Tests A/B Streamlit vs React
- Même offre, mêmes CVs, même Top N
- Comparer résultats CSV exportés
- Vérifier ordre et scores (tolérance 0.01)

### Livrables Palier 5
- [ ] Toutes les pages migrées
- [ ] Navigation complète (breadcrumb)
- [ ] Tests A/B réussis (100% parité)
- [ ] Documentation utilisateur

### Validation Palier 5
**TOI:**
1. Parcourir tout le workflow (création entreprise → projet → matching)
2. Comparer avec Streamlit étape par étape
3. Exporter CSV depuis les 2 versions → comparer ligne par ligne
4. **Critère GO:** Zéro différence fonctionnelle

---

## 📦 DÉPLOIEMENT

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ROME_CLIENT_ID=${ROME_CLIENT_ID}
      - ROME_CLIENT_SECRET=${ROME_CLIENT_SECRET}
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://backend:8000
```

### CI/CD (GitHub Actions)
```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
```

---

## 📊 SUIVI DES PALIERS

| Palier | Status | Date début | Date fin | Validé par | Remarques |
|--------|--------|------------|----------|------------|-----------|
| 0      | ⏳ TODO |            |          |            |           |
| 1      | ⏳ TODO |            |          |            |           |
| 2      | ⏳ TODO |            |          |            |           |
| 3      | ⏳ TODO |            |          |            |           |
| 4      | ⏳ TODO |            |          |            |           |
| 5      | ⏳ TODO |            |          |            |           |

**Légende:**
- ⏳ TODO - Pas commencé
- 🚧 EN COURS - En développement
- ⏸️ EN ATTENTE - Attend validation
- ✅ VALIDÉ - OK pour passer au suivant
- ❌ BLOQUÉ - Problème à résoudre

---

## 🚨 PROTOCOLE EN CAS DE RÉGRESSION

Si à n'importe quel moment un test échoue ou un résultat diffère de Streamlit:

1. **STOP** - Ne pas continuer
2. **Documenter** - Noter exactement la différence
3. **Investiguer** - Identifier la cause (prompt, formule, arrondi, etc.)
4. **Corriger** - Restaurer la parité exacte
5. **Retester** - Valider que tous les tests repassent
6. **Reprendre** - Continuer seulement si 100% vert

**Principe:** Il vaut mieux avancer lentement avec zéro régression que rapidement en cassant des choses.

---

**Prêt à commencer le Palier 0?** Dis-moi quand je peux démarrer l'extraction de la logique métier.
