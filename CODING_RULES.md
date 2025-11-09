# 🛡️ BRAIN RH - RÈGLES DE CODE (OBLIGATOIRES)

**Pour:** Claude Code
**Usage:** Consulter SYSTÉMATIQUEMENT avant toute modification

> ⚠️ **RÈGLE ABSOLUE:** Lire ce fichier AVANT d'écrire ou modifier du code
> 📘 **RÈGLE:** Consulter REFERENCE_COMPLETE.md pour localiser les fichiers

---

## ⚠️ RÈGLES CRITIQUES (NE JAMAIS VIOLER)

### 1. 🚨 Chemins de projets : TOUJOURS utiliser `get_project_path()`

#### ❌ INTERDIT - Hardcoder "projects/"

```python
# ❌ NE JAMAIS FAIRE ÇA
cvs_dir = Path("projects") / project_id / "cvs_parsed"
matchings_dir = Path("projects") / project_id / "matchings"
offre_path = Path("projects") / project_id / "offre.json"

# ❌ MÊME PAS AVEC os.path
cvs_dir = os.path.join("projects", project_id, "cvs_parsed")
```

**Pourquoi ?**
Le projet gère **2 structures de stockage** :
- `projects/{project_id}/` (ancienne structure, legacy)
- `enterprises/{enterprise_id}/{project_id}/` (nouvelle structure multi-tenant)

Hardcoder `"projects"` casse les projets dans `enterprises/`.

#### ✅ OBLIGATOIRE - Utiliser `get_project_path()`

```python
# ✅ TOUJOURS FAIRE ÇA
from project_manager import ProjectManager

pm = ProjectManager()
project_path = pm.get_project_path(project_id)

# Vérifier que le chemin existe (IMPORTANT)
if not project_path:
    # En route API : raise HTTPException
    raise HTTPException(404, f"Projet {project_id} introuvable")

    # En route SSE : yield error event
    yield "event: error\n"
    error_data = {'code': 'PROJECT_NOT_FOUND', 'message': f'Projet {project_id} introuvable'}
    yield f"data: {json.dumps(error_data)}\n\n"
    return

# Construire les sous-chemins
cvs_dir = project_path / "cvs_parsed"
matchings_dir = project_path / "matchings"
offre_path = project_path / "offre.json"
```

**Fichiers concernés (TOUS) :**
- `api/routers/matching.py` (routes matching)
- `api/routers/cvs.py` (routes CVs)
- `api/routers/offres.py` (routes offres)
- Tout code backend qui accède aux fichiers projet

**Fonction de référence :**
- **Fichier :** `project_manager.py`
- **Fonction :** `get_project_path(project_id: str) -> Path | None`
- **Lignes :** 200-240

**Comportement :**
1. Cherche d'abord dans `projects/{project_id}/`
2. Si absent, cherche dans `enterprises/*/{{project_id}/`
3. Retourne `None` si introuvable

---

### 2. 🚨 Gestion des erreurs dans SSE (Server-Sent Events)

#### ❌ INTERDIT - Raise d'exception dans un générateur SSE

```python
# ❌ NE JAMAIS FAIRE ÇA
def stream_matching(project_id: str):
    if not project_exists(project_id):
        raise HTTPException(404, "Projet introuvable")  # ❌ CRASH SSE COMPLET

    for cv in cvs:
        if error:
            raise ValueError("Erreur")  # ❌ CRASH ÉGALEMENT

# ❌ MÊME PAS AVEC try/except EXTERNE
async def endpoint():
    try:
        return StreamingResponse(stream_matching())
    except Exception:
        # Trop tard, le stream est déjà ouvert!
        return JSONResponse({"error": "..."})
```

**Pourquoi ?**
Une fois le stream SSE ouvert (headers HTTP envoyés), on ne peut plus envoyer de status code HTTP. L'exception crash le stream sans notification au client.

#### ✅ OBLIGATOIRE - Yield error event puis return

```python
# ✅ TOUJOURS FAIRE ÇA
def stream_matching(project_id: str):
    # Validation initiale
    if not project_exists(project_id):
        yield "event: error\n"
        yield f"data: {json.dumps({'code': 'PROJECT_NOT_FOUND', 'message': 'Projet introuvable'})}\n\n"
        return  # ⭐ IMPORTANT: return après l'erreur

    # Logique métier avec try/except
    try:
        for cv in cvs:
            # ... traitement ...
            if error_condition:
                yield "event: error\n"
                yield f"data: {json.dumps({'code': 'PROCESSING_ERROR', 'message': 'Erreur traitement CV'})}\n\n"
                return

            # Success
            yield "event: result\n"
            yield f"data: {json.dumps(result)}\n\n"

        # Done
        yield "event: done\n"
        yield f"data: {json.dumps({'summary': 'OK'})}\n\n"

    except Exception as e:
        # Erreur inattendue
        yield "event: error\n"
        yield f"data: {json.dumps({'code': 'INTERNAL_ERROR', 'message': str(e)})}\n\n"
        return
```

**Format erreur SSE standard :**

```python
yield "event: error\n"
error_data = {
    'code': 'ERROR_CODE',              # SNAKE_CASE_MAJUSCULE
    'message': 'Message utilisateur',  # Français, clair, actionnable
    'details': {}                      # Optionnel (dict avec contexte)
}
yield f"data: {json.dumps(error_data)}\n\n"
return  # ⭐ TOUJOURS return après erreur
```

**Codes d'erreur standards :**
- `PROJECT_NOT_FOUND` : Projet introuvable
- `NO_CVS` : Aucun CV parsé
- `NO_OFFRE` : Aucune offre définie
- `PROCESSING_ERROR` : Erreur traitement
- `LLM_ERROR` : Erreur appel LLM
- `INTERNAL_ERROR` : Erreur inattendue

**Fichiers concernés :**
- `api/routers/matching.py` (routes `/stream`)
- `api/routers/cvs.py` (routes `/stream`)

---

### 3. 🚨 Imports : Toujours utiliser `lib/` en priorité

#### ❌ INTERDIT - Importer depuis la racine

```python
# ❌ NE JAMAIS FAIRE ÇA
from matching_engine import MatchingEngine  # Fichier racine (legacy)
from parseur_cv import parse_cv              # Fichier racine (legacy)
```

**Pourquoi ?**
Les fichiers à la racine sont des versions legacy ou des orchestrateurs. La logique métier pure est dans `lib/`.

#### ✅ OBLIGATOIRE - Importer depuis `lib/`

```python
# ✅ TOUJOURS FAIRE ÇA
from lib.matching_core import run_matching_pipeline
from lib.cv_parsing import parse_cv_to_json
from lib.models import CV, Offre, ResultatMatching
from lib.parallel_engine import process_batch_parallel
```

**Hiérarchie des imports :**

1. **`lib/`** → Code métier pur, fonctions réutilisables (PRIORITÉ)
2. **Fichiers racine** → Orchestrateurs, points d'entrée (OK si nécessaire)

**Exceptions (autorisées à la racine) :**
- `config_loader.py` : Singleton de configuration
- `project_manager.py` : Gestion projets multi-structure
- `enterprise_manager.py` : Gestion entreprises
- `matching_engine.py` : Classe orchestratrice (mais préférer `lib/matching_core` pour la logique)

**Mapping racine → lib :**

| Racine (legacy) | lib/ (prioritaire) | Notes |
|----------------|-------------------|-------|
| `matching_engine.py` | `lib/matching_core.py` | Fonctions pures matching |
| `parseur_cv.py` | `lib/cv_parsing.py` | Fonctions parsing |
| `offer_enrichment.py` | `lib/offer_processing.py` | Fonctions offres |
| N/A | `lib/models.py` | ⭐ Schemas Pydantic (UNIQUE) |
| `parallel_processing.py` | `lib/parallel_engine.py` | Moteur parallèle |

---

### 4. 🚨 Configuration : Toujours passer via `config_loader`

#### ❌ INTERDIT - Lire directement .env ou config.yaml

```python
# ❌ NE JAMAIS FAIRE ÇA
import os
api_key = os.getenv("OPENAI_API_KEY")  # Pas de validation
model = os.getenv("LLM_MODEL")          # Pas de default

# ❌ NE JAMAIS FAIRE ÇA NON PLUS
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)  # Pas de validation, pas de defaults
    top_k = config["scoring"]["top_k"]  # KeyError si manquant
```

**Pourquoi ?**
- Pas de validation des variables
- Pas de valeurs par défaut
- Pas de gestion d'erreur
- Duplication de logique

#### ✅ OBLIGATOIRE - Utiliser `config_loader`

```python
# ✅ TOUJOURS FAIRE ÇA
from config_loader import load_config

config = load_config()  # Singleton, chargé une seule fois

# Accès type-safe avec defaults
api_key = config["openai"]["api_key"]       # Valide ou raise
model = config["llm"]["model"]              # Default: gpt-4o-mini
top_k = config["matching"]["top_k"]         # Default: 50
top_rerank = config["matching"]["top_rerank"]  # Default: 10
```

**Avantages :**
- ✅ Validation automatique (raise si clé manquante critique)
- ✅ Valeurs par défaut pour paramètres optionnels
- ✅ Singleton (chargé une seule fois)
- ✅ Création automatique des dossiers (`cache/`, `logs/`, etc.)

**Configuration disponible :**

```python
config = {
    "openai": {
        "api_key": str  # De .env
    },
    "llm": {
        "model": str,              # Default: gpt-4o-mini
        "temperature": float,      # Default: 0.0
        "fallback_models": List[str]
    },
    "matching": {
        "top_k": int,              # Default: 50
        "top_rerank": int,         # Default: 10
        ...
    },
    "scoring": {
        "nice_have_malus_factor": float,  # Default: 0.95
        "bonus_experience_exacte": float,  # Default: 0.15
        ...
    },
    "parallel": {
        "max_workers": int,        # Default: 500
        "qps": int,                # Default: 10
        ...
    },
    "paths": {
        "cache_folder": str,       # Default: cache
        "projects": str,           # Default: projects
        "enterprises": str,        # Default: enterprises
        ...
    }
}
```

**Fichier de référence :** `config_loader.py:45-150`

---

### 5. 🚨 Schemas Pydantic : Source unique dans `lib/models.py`

#### ❌ INTERDIT - Redéfinir des schemas

```python
# ❌ NE JAMAIS FAIRE ÇA (dans api/schemas.py ou autre)
class CV(BaseModel):  # ❌ Duplication !
    nom: str
    titre: str
    # ...

class ResultatMatching(BaseModel):  # ❌ Duplication !
    cv: str
    score: float
    # ...
```

**Pourquoi ?**
- Duplication de code
- Désynchronisation des schemas
- Validation incohérente

#### ✅ OBLIGATOIRE - Importer depuis `lib/models.py`

```python
# ✅ TOUJOURS FAIRE ÇA
from lib.models import (
    CV,
    Offre,
    ResultatMatching,
    MatchingResponse,
    CVParseResult,
    Project,
    Enterprise,
    SSEProgressEvent,
    SSEErrorEvent,
    APIError
)

# Si besoin d'un schema API-only (rare)
class CVResponse(BaseModel):
    cv: CV  # ✅ Réutilise le schema de base
    parsed_at: datetime
    project_id: str
```

**Schemas disponibles (`lib/models.py`) :**

| Schema | Usage | Lignes |
|--------|-------|--------|
| `CV` | CV parsé structuré | 40-57 |
| `Identite` | Infos candidat | 14-23 |
| `Experience` | Expérience pro | 27-36 |
| `Offre` | Offre + must-have/nice-have | 80-88 |
| `OffreSection` | Sections offre | 61-78 |
| `ResultatMatching` | Résultat matching d'un CV | 92-129 |
| `MatchingResponse` | Réponse complète matching | 140-143 |
| `CVParseResult` | Résultat parsing | 148-155 |
| `Project` | Métadonnées projet | 201-211 |
| `Enterprise` | Métadonnées entreprise | 214-224 |
| `SSE*Event` | Événements SSE | 168-197 |
| `APIError` | Erreur API | 229-234 |

**Validation automatique :**
Pydantic valide tous les payloads entrants/sortants. Si erreur → `ValidationError` explicite.

---

### 6. 🚨 Parallélisation : Utiliser `parallel_engine.py`

#### ❌ INTERDIT - Créer un ProcessPoolExecutor à la main

```python
# ❌ NE JAMAIS FAIRE ÇA
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_cv, cvs))
    # Pas de rate limiting
    # Pas de progress
    # Pas de gestion erreurs
```

**Pourquoi ?**
- Pas de rate limiting (QPS OpenAI)
- Pas de progress bar
- Gestion erreurs manuelle
- Duplication de logique

#### ✅ OBLIGATOIRE - Utiliser `parallel_engine`

```python
# ✅ TOUJOURS FAIRE ÇA
from lib.parallel_engine import process_batch_parallel

results = process_batch_parallel(
    items=cvs,
    process_func=process_cv,
    max_workers=500,           # Max workers
    qps=10,                    # Rate limit OpenAI (queries/sec)
    description="Processing CVs",  # Pour progress bar
    show_progress=True         # Afficher progress (optional)
)
```

**Avantages :**
- ✅ Gestion automatique QPS (rate limiting)
- ✅ Progress bar automatique
- ✅ Retry automatique sur erreur
- ✅ Gestion erreurs robuste
- ✅ Logging uniforme

**Fichier de référence :** `lib/parallel_engine.py:60-200`

**Signature complète :**

```python
def process_batch_parallel(
    items: List[Any],
    process_func: Callable,
    max_workers: int = 500,
    qps: int = 10,
    description: str = "Processing",
    show_progress: bool = True,
    timeout: float = 300.0
) -> List[Any]:
    """
    Traite un batch d'items en parallèle avec rate limiting

    Args:
        items: Liste d'items à traiter
        process_func: Fonction de traitement (doit accepter 1 item)
        max_workers: Nombre max de workers parallèles
        qps: Queries per second (rate limit)
        description: Description pour progress bar
        show_progress: Afficher progress bar
        timeout: Timeout par item (secondes)

    Returns:
        Liste des résultats (même ordre que items)
    """
```

---

## 📋 PATTERNS OBLIGATOIRES

### Pattern 1 : Route API standard avec projet

```python
from fastapi import APIRouter, HTTPException
from project_manager import ProjectManager
from lib.models import MatchingRequest, MatchingResponse

router = APIRouter()

@router.post("/matching/run")
async def run_matching(project_id: str, request: MatchingRequest) -> MatchingResponse:
    """Lance un matching complet"""

    # 1. Charger le ProjectManager
    pm = ProjectManager()

    # 2. Vérifier que le projet existe
    if not pm.project_exists(project_id):
        raise HTTPException(404, f"Projet {project_id} introuvable")

    # 3. ⭐ Obtenir le chemin du projet (NE JAMAIS hardcoder!)
    project_path = pm.get_project_path(project_id)
    if not project_path:
        raise HTTPException(500, "Impossible de déterminer le chemin du projet")

    # 4. Construire les sous-chemins
    cvs_dir = project_path / "cvs_parsed"
    offre_path = project_path / "offre.json"

    # 5. Vérifier que les ressources existent
    if not cvs_dir.exists():
        raise HTTPException(400, "Aucun CV parsé pour ce projet")

    if not offre_path.exists():
        raise HTTPException(400, "Aucune offre définie pour ce projet")

    # 6. Logique métier (utiliser lib/)
    from lib.matching_core import run_matching_pipeline

    results = run_matching_pipeline(
        cvs_dir=cvs_dir,
        offre_path=offre_path,
        config=request.dict()
    )

    # 7. Sauvegarder résultats dans le projet
    matchings_dir = project_path / "matchings" / timestamp
    matchings_dir.mkdir(parents=True, exist_ok=True)

    with open(matchings_dir / "results.json", 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 8. Retourner réponse validée
    return MatchingResponse(**results)
```

**Points clés :**
1. ProjectManager pour gérer les chemins
2. `get_project_path()` au lieu de hardcoder
3. Validation existence ressources
4. Imports depuis `lib/`
5. Pydantic pour validation

---

### Pattern 2 : Route SSE avec gestion erreurs

```python
from fastapi.responses import StreamingResponse
import json

@router.post("/cvs/parse/stream")
async def parse_cvs_stream(project_id: str, files: List[UploadFile]):
    """Parse CVs avec streaming SSE"""

    def event_generator():
        try:
            # Validation initiale
            pm = ProjectManager()
            project_path = pm.get_project_path(project_id)

            if not project_path:
                yield "event: error\n"
                yield f"data: {json.dumps({'code': 'PROJECT_NOT_FOUND', 'message': 'Projet introuvable'})}\n\n"
                return  # ⭐ IMPORTANT

            cvs_dir = project_path / "cvs_parsed"
            cvs_dir.mkdir(parents=True, exist_ok=True)

            # Logique métier avec yields réguliers
            total = len(files)
            for i, file in enumerate(files):
                # Progress event
                yield "event: progress\n"
                progress_data = {
                    'step': 'parsing',
                    'current': i + 1,
                    'total': total,
                    'progress': (i + 1) / total,
                    'filename': file.filename
                }
                yield f"data: {json.dumps(progress_data)}\n\n"

                # Traitement (avec gestion erreur par fichier)
                try:
                    result = parse_cv(file)

                    # Result event
                    yield "event: result\n"
                    yield f"data: {json.dumps(result)}\n\n"

                except Exception as e:
                    # Erreur sur un fichier (continuer les autres)
                    yield "event: result\n"
                    error_result = {
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    }
                    yield f"data: {json.dumps(error_result)}\n\n"

            # Done event
            yield "event: done\n"
            summary = {'total': total, 'success': success_count, 'failed': failed_count}
            yield f"data: {json.dumps(summary)}\n\n"

        except Exception as e:
            # Erreur fatale
            yield "event: error\n"
            yield f"data: {json.dumps({'code': 'INTERNAL_ERROR', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx
        }
    )
```

**Points clés :**
1. Générateur avec try/except global
2. Validation initiale avant boucle
3. Yield error + return sur erreur fatale
4. Progress réguliers
5. Headers SSE corrects

---

### Pattern 3 : Chargement CVs d'un projet

```python
from pathlib import Path
import json
from typing import List
from lib.models import CV
from project_manager import ProjectManager

def load_cvs_from_project(project_id: str) -> List[CV]:
    """Charge tous les CVs parsés d'un projet"""

    # 1. ProjectManager
    pm = ProjectManager()
    project_path = pm.get_project_path(project_id)

    if not project_path:
        raise ValueError(f"Projet {project_id} introuvable")

    # 2. Chemin CVs
    cvs_dir = project_path / "cvs_parsed"

    if not cvs_dir.exists():
        return []  # Pas d'erreur, juste liste vide

    # 3. Charger tous les JSONs
    cvs = []
    for json_file in sorted(cvs_dir.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cv = CV(**data)  # Validation Pydantic
                cvs.append(cv)
        except Exception as e:
            # Logger l'erreur mais continuer
            print(f"⚠️ Erreur chargement {json_file.name}: {e}")
            continue

    return cvs
```

**Points clés :**
1. `get_project_path()` obligatoire
2. Vérification existence dossier
3. Validation Pydantic pour chaque CV
4. Gestion erreurs robuste (continue sur erreur)

---

## 🔍 CHECKLIST AVANT COMMIT

Avant chaque modification, vérifier :

### ✅ Chemins projets
- [ ] Aucun `Path("projects")` hardcodé
- [ ] Utilise `pm.get_project_path(project_id)`
- [ ] Vérifie que `project_path is not None`

### ✅ SSE
- [ ] Aucun `raise` dans un générateur SSE
- [ ] Yield `event: error` + `return` sur erreur
- [ ] Headers SSE corrects (`text/event-stream`, `no-cache`)

### ✅ Imports
- [ ] Imports depuis `lib/` en priorité
- [ ] Schemas depuis `lib/models.py` uniquement
- [ ] Config via `config_loader.load_config()`

### ✅ Parallélisation
- [ ] Utilise `process_batch_parallel()` si applicable
- [ ] Pas de `ProcessPoolExecutor` manuel

### ✅ Code quality
- [ ] Types Pydantic pour payloads API
- [ ] Validation existence ressources (fichiers, projets)
- [ ] Gestion erreurs robuste (try/except)
- [ ] Logs clairs pour debug

---

## 📞 EN CAS DE DOUTE

| Question | Réponse | Fichier référence |
|----------|---------|------------------|
| "Comment accéder aux fichiers d'un projet ?" | `pm.get_project_path(project_id)` | `project_manager.py:200-240` |
| "Comment gérer une erreur dans SSE ?" | `yield "event: error\n"` + `return` | Ce fichier, section 2 |
| "Où importer CV/Offre ?" | `from lib.models import CV, Offre` | `lib/models.py` |
| "Comment paralléliser du traitement ?" | `process_batch_parallel()` | `lib/parallel_engine.py` |
| "Comment lire la config ?" | `from config_loader import load_config` | `config_loader.py` |
| "Où trouver une fonctionnalité ?" | Lire `REFERENCE_COMPLETE.md` | `REFERENCE_COMPLETE.md` |

---

## 🚨 EXEMPLES D'ERREURS FRÉQUENTES (CORRIGÉES)

### Erreur 1 : Hardcoding "projects/"

```python
# ❌ AVANT (MAUVAIS)
cvs_parsed_dir = Path("projects") / project_id / "cvs_parsed"
matchings_dir = Path("projects") / project_id / "matchings" / timestamp_str

# ✅ APRÈS (BON)
from project_manager import ProjectManager

pm = ProjectManager()
project_path = pm.get_project_path(project_id)

if not project_path:
    yield "event: error\n"
    error_data = {'code': 'PROJECT_PATH_ERROR', 'message': f'Impossible de trouver le chemin du projet {project_id}'}
    yield f"data: {json.dumps(error_data)}\n\n"
    return

cvs_parsed_dir = project_path / "cvs_parsed"
matchings_dir = project_path / "matchings" / timestamp_str
```

**Fichier corrigé :** `api/routers/matching.py:153-162`, `api/routers/matching.py:337-342`

---

### Erreur 2 : Exception dans SSE

```python
# ❌ AVANT (MAUVAIS)
def stream():
    if not project_exists:
        raise HTTPException(404, "Projet introuvable")  # Crash SSE

    for cv in cvs:
        process(cv)  # Si erreur → crash

# ✅ APRÈS (BON)
def stream():
    try:
        if not project_exists:
            yield "event: error\n"
            yield f"data: {json.dumps({'code': 'PROJECT_NOT_FOUND', 'message': 'Projet introuvable'})}\n\n"
            return

        for cv in cvs:
            try:
                process(cv)
            except Exception as e:
                yield "event: error\n"
                yield f"data: {json.dumps({'code': 'PROCESSING_ERROR', 'message': str(e)})}\n\n"
                return

    except Exception as e:
        yield "event: error\n"
        yield f"data: {json.dumps({'code': 'INTERNAL_ERROR', 'message': str(e)})}\n\n"
```

---

### Erreur 3 : Import depuis racine

```python
# ❌ AVANT (MAUVAIS)
from matching_engine import MatchingEngine
from parseur_cv import parse_cv

# ✅ APRÈS (BON)
from lib.matching_core import run_matching_pipeline
from lib.cv_parsing import parse_cv_to_json
from lib.models import CV, Offre, ResultatMatching
```

---

### Erreur 4 : Schema dupliqué

```python
# ❌ AVANT (MAUVAIS - dans api/schemas.py)
class ResultatMatching(BaseModel):
    cv: str
    score_final: float
    # ... redéfinition complète

# ✅ APRÈS (BON)
from lib.models import ResultatMatching  # Import unique

# Si vraiment besoin d'étendre (rare)
class ResultatMatchingAPI(BaseModel):
    resultat: ResultatMatching  # Réutilise le schema de base
    api_metadata: dict
```

---

## 🔄 MAINTENANCE DE CE FICHIER

### ⚠️ RÈGLE OBLIGATOIRE

Ce fichier DOIT être mis à jour à chaque nouveau pattern ou règle critique.

✅ **Mettre à jour si :**
- Nouvelle règle critique identifiée (ex: nouveau piège récurrent)
- Nouveau pattern obligatoire (ex: nouvelle structure de route)
- Changement de convention (ex: nouveau format erreur SSE)
- Nouvelle fonction utilitaire critique (ex: nouveau helper dans `lib/`)

❌ **NE PAS mettre à jour pour :**
- Corrections mineures de code
- Ajout de fonctionnalités (sauf si nouveau pattern)
- Refactoring interne

### 🔧 Comment mettre à jour

1. **Ajouter la règle** dans la section appropriée
2. **Fournir exemples** ❌ AVANT / ✅ APRÈS
3. **Référencer fichiers** concernés
4. **Mettre à jour la date** en haut

**Voir détails complets :** `MAINTENANCE_GUIDE.md`

---

**🔄 Ce fichier contient LES RÈGLES ABSOLUES du projet**
**📖 LIRE SYSTÉMATIQUEMENT avant toute modification**

---

_Dernière modification: 18 octobre 2025 - Version 2.6.4_
