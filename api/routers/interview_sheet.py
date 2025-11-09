"""
Router Interview Sheets - Génération et gestion des fiches d'entretien
"""

import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brainrh.services.interview_sheet_service import InterviewSheetService
from brainrh.services.cv_service import CVService
from brainrh.services.project_service import ProjectService
from brainrh.services.file_storage import FileStorage
from brainrh.paths import PROJECT_ROOT, get_relative_path
from unified_project_manager import UnifiedProjectManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Configuration xAI
XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    logger.warning("⚠️ XAI_API_KEY non trouvée - Les fiches d'entretien ne seront pas disponibles")

XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-4-fast-reasoning"

# Initialiser UnifiedProjectManager
project_manager = UnifiedProjectManager(enterprises_folder="enterprises")


class GenerateInterviewSheetInput(BaseModel):
    """Input pour génération de fiche d'entretien"""
    candidate_id: str  # Nom fichier CV
    job_id: str  # ID projet
    matching_id: str  # ID matching (timestamp)
    interviewer_id: str = "default_interviewer"  # ID recruteur
    weights: Optional[Dict[str, float]] = None  # Pondérations personnalisées (optionnel)


class UpdateInterviewSheetInput(BaseModel):
    """Input pour mise à jour partielle de fiche d'entretien"""
    scorecard: Optional[Any] = None  # Grille d'évaluation remplie (liste ou dict)
    questions: Optional[Any] = None  # Questions modifiées/enrichies
    free_notes: Optional[str] = None  # Notes libres du recruteur
    recommendation: Optional[str] = None  # Recommandation finale
    status: Optional[str] = None  # Status (draft, in_progress)
    verdict: Optional[str] = None  # Verdict final
    verdict_detail: Optional[str] = None  # Justification verdict
    additional_tests: Optional[bool] = None  # Tests complémentaires requis
    residual_risks: Optional[str] = None  # Risques résiduels


@router.post("/generate", status_code=201)
async def generate_interview_sheet(input_data: GenerateInterviewSheetInput):
    """
    Génère une fiche d'entretien structurée via LLM

    **Étapes:**
    1. Charger CV + Offre depuis les données existantes
    2. Construire le prompt avec contexte matching
    3. Appeler LLM (OpenAI) pour génération JSON
    4. Sauvegarder le fichier JSON dans interviews/<candidate>/
    5. Créer un enregistrement draft dans interview_sheets
    6. Retourner la fiche générée

    **Body:**
    - `candidate_id`: Nom fichier CV (ex: "CV_John_Doe.pdf")
    - `job_id`: ID du projet/offre
    - `matching_id`: ID du matching (timestamp)
    - `interviewer_id`: ID recruteur (optionnel, default: "default_interviewer")
    - `weights`: Pondérations personnalisées pour grille eval (optionnel)

    **Retourne:** Fiche d'entretien générée (JSON)
    """

    # ==========================================
    # 0. RÉCUPÉRER LE PROJET ET SON ENTERPRISE_ID
    # ==========================================

    try:
        project = ProjectService.get_project(input_data.job_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Projet {input_data.job_id} introuvable")

        enterprise_id = project.get("enterprise_id")
        if not enterprise_id:
            raise HTTPException(status_code=500, detail=f"Projet {input_data.job_id} sans enterprise_id")

        # Obtenir le chemin du projet via UnifiedProjectManager
        project_dir = project_manager._get_project_dir(input_data.job_id, enterprise_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération projet: {str(e)}")

    # ==========================================
    # 0.5. VÉRIFIER SI UNE FICHE EXISTE DÉJÀ
    # ==========================================

    existing_sheet = InterviewSheetService.find_existing(
        candidate_id=input_data.candidate_id,
        job_id=input_data.job_id,
        matching_id=input_data.matching_id
    )

    if existing_sheet:
        logger.info(
            f"♻️ Fiche existante trouvée (id={existing_sheet['id']}, status={existing_sheet['status']}) "
            f"pour trio ({input_data.candidate_id}, {input_data.job_id}, {input_data.matching_id})"
        )
        # Charger le JSON complet depuis le fichier
        json_path_abs = PROJECT_ROOT / existing_sheet["json_path"]
        if json_path_abs.exists():
            existing_data = FileStorage.load_json(str(json_path_abs))
            return {
                "interview_sheet_id": existing_sheet["id"],
                "status": existing_sheet["status"],
                "data": existing_data,
                "json_path": existing_sheet["json_path"],
                "created_at": existing_sheet["created_at"],
                "updated_at": existing_sheet["updated_at"],
                "existing": True
            }

    # ==========================================
    # 1. CHARGER LES DONNÉES (CV + OFFRE)
    # ==========================================

    # Charger le CV (gérer mapping .pdf vs .json)
    try:
        cv_metas = CVService.list_by_project(input_data.job_id)

        # Essayer plusieurs variantes du nom de fichier
        cv_meta = None
        candidate_variants = [
            input_data.candidate_id,  # Ex: CV X.pdf
            input_data.candidate_id.replace('.pdf', '.json'),  # CV X.json
            input_data.candidate_id.replace('.docx', '.json')  # CV X.json
        ]

        for variant in candidate_variants:
            cv_meta = next((cv for cv in cv_metas if cv["filename"] == variant), None)
            if cv_meta:
                break

        if not cv_meta:
            raise HTTPException(
                status_code=404,
                detail=f"CV {input_data.candidate_id} introuvable (testé: {', '.join(candidate_variants)})"
            )

        cv_data_path = PROJECT_ROOT / cv_meta["json_path"]
        cv_data = FileStorage.load_json(str(cv_data_path))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur chargement CV: {str(e)}")

    # Charger l'offre (offre.json ou offre_parsed.json)
    try:
        offre_path = project_dir / "offre.json"
        if not offre_path.exists():
            offre_path = project_dir / "offre_parsed.json"

        if not offre_path.exists():
            raise HTTPException(status_code=404, detail=f"Offre introuvable pour projet {input_data.job_id}")

        offre_data = FileStorage.load_json(str(offre_path))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur chargement offre: {str(e)}")

    # Charger les résultats du matching (optionnel, pour contexte)
    matching_data = None
    try:
        matching_results_path = project_dir / "matchings" / input_data.matching_id / "results.json"

        if matching_results_path.exists():
            matching_full = FileStorage.load_json(str(matching_results_path))
            # Trouver le résultat du candidat spécifique (tester les variantes)
            for variant in candidate_variants:
                matching_data = next(
                    (r for r in matching_full.get("results", []) if r["cv"] == variant),
                    None
                )
                if matching_data:
                    break
    except Exception:
        # Pas grave si matching introuvable, on continue sans contexte
        pass

    # ==========================================
    # 2. CONSTRUIRE LE PROMPT
    # ==========================================

    # Charger le template de prompt
    prompt_path = PROJECT_ROOT / "prompts" / "prompt_fiche_entretien.txt"
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail="Template prompt fiche d'entretien introuvable")

    prompt_template = prompt_path.read_text(encoding="utf-8")

    # Construire le contexte pour le LLM
    context = f"""
# DONNÉES DU CANDIDAT

**Nom:** {cv_data.get('informations_personnelles', {}).get('nom_complet', 'N/A')}
**Compétences:** {', '.join(cv_data.get('competences', {}).get('techniques', [])[:10])}
**Expériences:** {len(cv_data.get('experiences_professionnelles', []))} expérience(s)
**Formations:** {len(cv_data.get('formations', []))} formation(s)

# OFFRE D'EMPLOI

**Poste:** {offre_data.get('intitule', 'N/A')}
**Missions:** {offre_data.get('missions', 'N/A')[:300]}...
**Must-have:** {', '.join(offre_data.get('must_have', [])[:5])}
**Nice-have:** {', '.join(offre_data.get('nice_have', [])[:5])}

# RÉSULTATS DU MATCHING (si disponible)

"""
    if matching_data:
        context += f"""
**Score final:** {matching_data.get('score_final', 0):.2f}
**Appréciation:** {matching_data.get('appreciation_globale', 'N/A')[:200]}...
**Nice-have manquants:** {', '.join(matching_data.get('nice_have_manquants', []))}
"""
    else:
        context += "_(Données de matching non disponibles)_\n"

    # Prompt final
    full_prompt = prompt_template + "\n\n" + context

    # ==========================================
    # 3. APPELER LE LLM (xAI Grok)
    # ==========================================

    try:
        # Construire le payload xAI
        payload = {
            "model": XAI_MODEL,
            "messages": [
                {"role": "system", "content": "Tu es un expert RH. Réponds uniquement avec du JSON valide."},
                {"role": "user", "content": full_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.15,  # Factuel et peu créatif
            "max_tokens": 8000,  # Large pour fiches détaillées
            "stream": False
        }

        # Appel HTTP xAI
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{XAI_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=90
        )
        response.raise_for_status()
        response_json = response.json()

        # Parser la réponse (format OpenAI-compatible)
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            raise ValueError(f"Réponse xAI invalide: {response_json}")

        llm_output = response_json["choices"][0]["message"]["content"]
        generated_data = json.loads(llm_output)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Erreur parsing JSON LLM: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur appel xAI: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur LLM: {str(e)}")

    # ==========================================
    # 4. SAUVEGARDER LE FICHIER JSON
    # ==========================================

    try:
        # Créer le dossier interviews/<candidate-id>/
        # Utiliser un identifiant sûr basé sur le nom du CV (sans extension)
        candidate_safe_id = Path(input_data.candidate_id).stem.replace(' ', '_')
        interviews_dir = project_dir / "interviews" / candidate_safe_id
        interviews_dir.mkdir(parents=True, exist_ok=True)

        # Nom fichier avec timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_filename = f"{timestamp}.json"
        json_filepath = interviews_dir / json_filename

        # Sauvegarder le JSON (atomique)
        tmp_file = json_filepath.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(generated_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(json_filepath)

        # Chemin relatif pour la DB
        json_path_relative = get_relative_path(json_filepath)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde fichier JSON: {str(e)}")

    # ==========================================
    # 5. CRÉER L'ENREGISTREMENT EN BASE
    # ==========================================

    try:
        interview_sheet = InterviewSheetService.create(
            candidate_id=input_data.candidate_id,
            job_id=input_data.job_id,
            matching_id=input_data.matching_id,
            interviewer_id=input_data.interviewer_id,
            data=generated_data,
            json_path=json_path_relative
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création fiche: {str(e)}")

    # ==========================================
    # 6. RETOURNER LA FICHE
    # ==========================================

    return {
        "interview_sheet_id": interview_sheet["id"],
        "status": interview_sheet["status"],
        "data": interview_sheet["data"],
        "json_path": interview_sheet["json_path"],
        "created_at": interview_sheet["created_at"],
        "existing": False
    }


@router.get("/")
async def list_interview_sheets(
    job_id: Optional[str] = None,
    limit: Optional[int] = None
):
    """
    Liste toutes les fiches d'entretien avec filtres optionnels

    **Query params:**
    - `job_id`: Filtrer par projet (optionnel)
    - `limit`: Limiter le nombre de résultats (optionnel)

    **Retourne:** Liste des fiches d'entretien
    """
    try:
        sheets = InterviewSheetService.list_all(
            job_id=job_id,
            limit=limit
        )
        return {"sheets": sheets, "total": len(sheets)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des fiches: {str(e)}"
        )


@router.get("/{interview_sheet_id}")
async def get_interview_sheet(interview_sheet_id: str):
    """
    Récupère une fiche d'entretien par son ID

    **Étapes:**
    1. Charger les métadonnées depuis la DB
    2. Recharger le JSON complet depuis json_path (source de vérité)
    3. Retourner la fiche complète

    **Path:**
    - `interview_sheet_id`: UUID de la fiche

    **Retourne:** Fiche d'entretien complète
    """

    # ==========================================
    # 1. CHARGER LES MÉTADONNÉES DB
    # ==========================================

    interview_sheet = InterviewSheetService.get(interview_sheet_id)

    if not interview_sheet:
        raise HTTPException(
            status_code=404,
            detail=f"Fiche d'entretien {interview_sheet_id} introuvable"
        )

    # ==========================================
    # 2. RECHARGER LE JSON COMPLET
    # ==========================================

    try:
        json_path_absolute = PROJECT_ROOT / interview_sheet["json_path"]

        if not json_path_absolute.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Fichier JSON introuvable: {interview_sheet['json_path']}"
            )

        # Recharger les données depuis le fichier (source de vérité)
        data = FileStorage.load_json(str(json_path_absolute))

        print(f"📥 [GET] Fiche {interview_sheet_id}")
        print(f"   Verdict dans JSON: {data.get('verdict', 'NON DÉFINI')}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lecture fichier JSON: {str(e)}"
        )

    # ==========================================
    # 3. RETOURNER LA FICHE COMPLÈTE
    # ==========================================

    return {
        "id": interview_sheet["id"],
        "candidate_id": interview_sheet["candidate_id"],
        "job_id": interview_sheet["job_id"],
        "matching_id": interview_sheet["matching_id"],
        "interviewer_id": interview_sheet["interviewer_id"],
        "status": interview_sheet["status"],
        "data": data,  # Données rechargées depuis le fichier
        "json_path": interview_sheet["json_path"],
        "created_at": interview_sheet["created_at"],
        "updated_at": interview_sheet["updated_at"],
        "completed_at": interview_sheet["completed_at"],
        "pdf_url": interview_sheet["pdf_url"]
    }


@router.patch("/{interview_sheet_id}")
async def update_interview_sheet(
    interview_sheet_id: str,
    updates: UpdateInterviewSheetInput
):
    """
    Met à jour partiellement une fiche d'entretien

    **Étapes:**
    1. Charger les métadonnées depuis la DB
    2. Lire le JSON complet depuis json_path
    3. Fusionner les nouveaux champs dans le JSON
    4. Réécrire le fichier JSON (atomique)
    5. Mettre à jour la DB (data + status + updated_at)

    **Path:**
    - `interview_sheet_id`: UUID de la fiche

    **Body:**
    - `scorecard`: Grille d'évaluation remplie (optionnel)
    - `questions`: Questions modifiées (optionnel)
    - `free_notes`: Notes libres (optionnel)
    - `recommendation`: Recommandation finale (optionnel)
    - `status`: Nouveau statut (draft/in_progress) (optionnel)

    **Retourne:** {"success": true, "updated_at": ...}
    """

    # ==========================================
    # 1. VÉRIFIER QUE LA FICHE EXISTE
    # ==========================================

    interview_sheet = InterviewSheetService.get(interview_sheet_id)

    if not interview_sheet:
        raise HTTPException(
            status_code=404,
            detail=f"Fiche d'entretien {interview_sheet_id} introuvable"
        )

    # ==========================================
    # 2. LIRE LE JSON COMPLET
    # ==========================================

    try:
        json_path_absolute = PROJECT_ROOT / interview_sheet["json_path"]

        if not json_path_absolute.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Fichier JSON introuvable: {interview_sheet['json_path']}"
            )

        # Charger les données actuelles
        current_data = FileStorage.load_json(str(json_path_absolute))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lecture fichier JSON: {str(e)}"
        )

    # ==========================================
    # 3. FUSIONNER LES NOUVEAUX CHAMPS
    # ==========================================

    # Construire le dictionnaire des mises à jour (seulement les champs fournis)
    updates_dict = updates.model_dump(exclude_unset=True)

    print(f"💾 [PATCH] Fiche {interview_sheet_id}")
    print(f"   Champs à mettre à jour: {list(updates_dict.keys())}")
    if 'verdict' in updates_dict:
        print(f"   ⚖️  Verdict: {updates_dict['verdict']}")

    # Fusionner dans current_data
    for key, value in updates_dict.items():
        if key != "status":  # Le status est géré séparément en DB
            current_data[key] = value

    # ==========================================
    # 4. RÉÉCRIRE LE FICHIER JSON (ATOMIQUE)
    # ==========================================

    try:
        # Écriture atomique
        tmp_file = json_path_absolute.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(json_path_absolute)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur écriture fichier JSON: {str(e)}"
        )

    # ==========================================
    # 5. METTRE À JOUR LA DB
    # ==========================================

    try:
        db_updates = {
            "data": current_data
        }

        # Si le status est fourni, le mettre à jour
        if "status" in updates_dict:
            db_updates["status"] = updates_dict["status"]

        updated_sheet = InterviewSheetService.update_partial(
            interview_sheet_id,
            db_updates
        )

        if not updated_sheet:
            raise HTTPException(
                status_code=500,
                detail="Erreur mise à jour base de données"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur mise à jour DB: {str(e)}"
        )

    # ==========================================
    # 6. RETOURNER LE SUCCÈS
    # ==========================================

    return {
        "success": True,
        "updated_at": updated_sheet["updated_at"]
    }


@router.post("/{interview_sheet_id}/finalize")
async def finalize_interview_sheet(interview_sheet_id: str):
    """
    Finalise une fiche d'entretien (marque comme completed)

    **Étapes:**
    1. Vérifier que la fiche existe
    2. Marquer status = completed, completed_at, updated_at
    3. Retourner le succès avec statut actualisé

    **Path:**
    - `interview_sheet_id`: UUID de la fiche

    **Retourne:** {"success": true, "status": "completed", "completed_at": ...}
    """

    # ==========================================
    # 1. VÉRIFIER QUE LA FICHE EXISTE
    # ==========================================

    interview_sheet = InterviewSheetService.get(interview_sheet_id)

    if not interview_sheet:
        raise HTTPException(
            status_code=404,
            detail=f"Fiche d'entretien {interview_sheet_id} introuvable"
        )

    # ==========================================
    # 2. FINALISER LA FICHE
    # ==========================================

    try:
        finalized_sheet = InterviewSheetService.finalize(interview_sheet_id)

        if not finalized_sheet:
            raise HTTPException(
                status_code=500,
                detail="Erreur finalisation fiche"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur finalisation: {str(e)}"
        )

    # ==========================================
    # 3. RETOURNER LE SUCCÈS
    # ==========================================

    return {
        "success": True,
        "status": finalized_sheet["status"],
        "completed_at": finalized_sheet["completed_at"],
        "updated_at": finalized_sheet["updated_at"]
    }
