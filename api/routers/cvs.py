"""
Router CVs - Parsing et gestion des CVs
"""

import json
import asyncio
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import logging

from lib.models import CVParseResponse, CVParseResult, CV
from lib.parallel_engine import parse_cvs_parallel_sync
from lib.cv_parsing import parse_cv_from_file, get_openai_client
from brainrh.paths import PROJECT_ROOT

import sys
sys.path.insert(0, str(PROJECT_ROOT))
from unified_project_manager import UnifiedProjectManager
from brainrh.services import CVService, EnterpriseService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialiser unified project manager
project_manager = UnifiedProjectManager(enterprises_folder="enterprises")


@router.post("/parse", response_model=CVParseResponse)
async def parse_cvs(
    files: List[UploadFile] = File(...),
    model: str = Query(default="gpt-4o-mini", description="Modèle LLM à utiliser"),
    concurrency: int = Query(default=500, ge=1, le=1000, description="CVs traités en parallèle"),
    qps: float = Query(default=100.0, ge=0.1, le=100.0, description="Requêtes/seconde max")
):
    """
    Parse plusieurs CVs en mode batch

    Retourne les résultats une fois tous les CVs traités.
    Pour un feedback temps-réel, utiliser `/cvs/parse/stream`

    **Paramètres:**
    - `files`: Fichiers CVs (PDF ou DOCX)
    - `model`: Modèle LLM (default: gpt-5-mini)
    - `concurrency`: Nombre max de CVs traités en parallèle (default: 500)
    - `qps`: Requêtes par seconde max vers OpenAI (default: 10.0)

    **Retourne:**
    - `success_count`: Nombre de CVs parsés avec succès
    - `failed_count`: Nombre de CVs en échec
    - `total`: Nombre total de CVs
    - `results`: Liste des résultats (CVParseResult)
    """
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    # Sauvegarder les fichiers temporairement
    temp_dir = Path(tempfile.mkdtemp(prefix="brainrh-cvs-"))
    temp_files = []
    try:
        for upload in files:
            suffix = Path(upload.filename or "").suffix or ".pdf"
            fd, raw_path = tempfile.mkstemp(dir=temp_dir, suffix=suffix)
            tmp_path = Path(raw_path)
            with os.fdopen(fd, "wb") as buffer:
                await upload.seek(0)
                shutil.copyfileobj(upload.file, buffer)
            temp_files.append(tmp_path)

        # Parsing parallèle avec lib/
        results = parse_cvs_parallel_sync(
            cv_files=temp_files,
            model=model,
            concurrency=concurrency,
            qps=qps
        )

        return CVParseResponse(**results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du parsing: {str(e)}")

    finally:
        # Nettoyer fichiers temporaires
        for tmp_file in temp_files:
            try:
                tmp_file.unlink(missing_ok=True)
            except:
                pass
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/parse/stream")
async def parse_cvs_stream(
    files: List[UploadFile] = File(...),
    project_id: str = Query(default=None, description="ID du projet (optionnel)"),
    model: str = Query(default="gpt-4o-mini"),
    concurrency: int = Query(default=500, ge=1, le=1000),
    qps: float = Query(default=100.0, ge=0.1, le=100.0)
):
    """
    Parse plusieurs CVs avec streaming SSE (Server-Sent Events)

    Envoie des événements en temps réel pendant le traitement:
    - `progress`: Progression (current, total, progress)
    - `result`: CV parsé (success, data, error)
    - `done`: Fin du traitement (summary)
    - `error`: Erreur globale

    **Consommation côté client (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/api/v1/cvs/parse/stream');

    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      console.log(`${data.current}/${data.total}`);
    });

    eventSource.addEventListener('result', (e) => {
      const data = JSON.parse(e.data);
      console.log('CV parsé:', data);
    });

    eventSource.addEventListener('done', (e) => {
      const data = JSON.parse(e.data);
      console.log('Terminé:', data.summary);
      eventSource.close();
    });
    ```
    """
    if not files:
        async def error_stream():
            yield f"event: error\n"
            yield f"data: {json.dumps({'code': 'NO_FILES', 'message': 'Aucun fichier fourni'})}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    # LIRE TOUS LES FICHIERS AVANT LE GÉNÉRATEUR
    # (FastAPI ferme les UploadFile dès que l'endpoint retourne avec StreamingResponse)
    logger.info(f"📥 Réception de {len(files)} fichiers pour parsing")
    files_data = []
    for upload in files:
        logger.info(f"  📖 Lecture de {upload.filename}...")
        content = await upload.read()
        logger.info(f"  ✅ {len(content)} bytes lus")
        files_data.append({
            'filename': upload.filename,
            'content': content,
            'content_type': upload.content_type
        })

    async def event_generator():
        temp_dir = Path(tempfile.mkdtemp(prefix="brainrh-cvs-"))
        temp_files = []
        original_filenames = {}  # Mapping: temp_path -> original_filename
        file_hashes: Dict[str, str] = {}  # Mapping: temp_path -> sha256_digest

        try:
            # Sauvegarder fichiers temporairement EN GARDANT le nom original
            for file_data in files_data:
                logger.info(f"🔍 Traitement de {file_data['filename']}...")
                suffix = Path(file_data['filename'] or "").suffix or ".pdf"
                fd, raw_path = tempfile.mkstemp(dir=temp_dir, suffix=suffix)
                tmp_path = Path(raw_path)

                content = file_data['content']
                logger.info(f"  📝 Contenu récupéré: {len(content)} bytes")

                # Écrire le fichier
                with os.fdopen(fd, "wb") as buffer:
                    buffer.write(content)
                    buffer.flush()
                
                # Vérifier que le fichier existe et est lisible
                if tmp_path.exists():
                    file_size = tmp_path.stat().st_size
                    logger.info(f"  ✅ Fichier temporaire créé: {tmp_path.name} ({file_size} bytes)")
                else:
                    logger.error(f"  ❌ Le fichier temporaire n'existe pas: {tmp_path}")
                    raise FileNotFoundError(f"Impossible de créer le fichier temporaire: {tmp_path}")

                temp_files.append(tmp_path)
                # Garder le mapping
                original_filenames[str(tmp_path)] = file_data['filename']

                # Calculer le hash SHA256 du fichier
                file_hash = hashlib.sha256(content).hexdigest()
                file_hashes[str(tmp_path)] = file_hash

            total = len(temp_files)
            success_count = 0
            failed_count = 0

            # Queue pour communiquer entre threads
            progress_queue = asyncio.Queue()

            # Callback de progression (appelé depuis le thread de parsing)
            def progress_callback(current, total_cvs):
                # Utiliser call_soon_threadsafe pour émettre depuis un thread
                asyncio.get_event_loop().call_soon_threadsafe(
                    progress_queue.put_nowait,
                    {'current': current, 'total': total_cvs}
                )

            # Lancer le parsing dans un thread séparé
            parse_task = asyncio.create_task(
                asyncio.to_thread(
                    parse_cvs_parallel_sync,
                    cv_files=temp_files,
                    model=model,
                    concurrency=concurrency,
                    qps=qps,
                    progress_callback=progress_callback
                )
            )

            # Émettre les événements progress au fur et à mesure
            while not parse_task.done():
                try:
                    # Attendre un événement progress avec timeout
                    progress_data = await asyncio.wait_for(progress_queue.get(), timeout=0.1)

                    # Émettre événement progress
                    current = progress_data['current']
                    total_cvs = progress_data['total']
                    progress = current / total_cvs if total_cvs > 0 else 0.0

                    yield f"event: progress\n"
                    yield f"data: {json.dumps({'step': 'parsing', 'current': current, 'total': total_cvs, 'progress': progress, 'message': f'Parsing {current}/{total_cvs} CVs...'})}\n\n"

                except asyncio.TimeoutError:
                    # Pas de nouvel événement, continuer à attendre
                    continue

            # Récupérer les résultats finaux
            results = await parse_task

            # Remplacer les noms temporaires par les noms originaux
            for result in results['results']:
                temp_filename = result.filename
                # Chercher dans le mapping (avec ou sans extension)
                for temp_path, original_name in original_filenames.items():
                    if Path(temp_path).name == temp_filename or str(temp_path) == temp_filename:
                        result.filename = original_name
                        if result.data:
                            result.data.cv = original_name
                        break

            # Sauvegarder les CVs dans le projet si project_id fourni
            if project_id:
                try:
                    project = project_manager.get_project(project_id)
                    if project:
                        # Utiliser get_project_path pour trouver le bon chemin
                        project_path = project_manager.get_project_path(project_id)
                        if project_path:
                            # Créer le dossier cvs_parsed s'il n'existe pas
                            cvs_parsed_dir = project_path / "cvs_parsed"
                            cvs_parsed_dir.mkdir(parents=True, exist_ok=True)

                            # Créer le dossier cvs_original/ pour stocker les fichiers sources
                            cvs_original_dir = project_path / "cvs_original"
                            cvs_original_dir.mkdir(parents=True, exist_ok=True)

                            # Construire le référentiel des hash existants
                            existing_hashes: Dict[str, str] = {}  # hash -> filename
                            try:
                                existing_cvs = CVService.list_by_project(project_id)
                                for cv_meta in existing_cvs:
                                    file_path = cv_meta.get("file_path")
                                    if file_path:
                                        # Construire le chemin absolu
                                        abs_path = PROJECT_ROOT / file_path
                                        if abs_path.exists():
                                            # Calculer le hash du fichier existant
                                            with open(abs_path, 'rb') as f:
                                                existing_hash = hashlib.sha256(f.read()).hexdigest()
                                                existing_hashes[existing_hash] = cv_meta.get("filename")
                                logger.info(f"📋 Référentiel construit: {len(existing_hashes)} hash existants")
                            except Exception as hash_err:
                                logger.warning(f"⚠️ Erreur construction référentiel hash: {hash_err}")

                            # Cache local pour éviter les collisions dans le même batch
                            used_filenames_in_batch = set()
                            # Cache pour détecter les doublons dans le batch actuel
                            batch_hashes: Dict[str, str] = {}  # hash -> filename

                            # Sauvegarder chaque CV parsé avec succès
                            for result in results['results']:
                                if result.success and result.data:
                                    # Garder en mémoire le nom fourni par l'utilisateur
                                    original_filename = result.filename

                                    # DÉTECTION DE DOUBLON PAR HASH
                                    # Retrouver le hash du fichier uploadé
                                    current_hash = None
                                    source_temp_file = None
                                    for temp_path_str, original_name in original_filenames.items():
                                        if original_name == original_filename:
                                            current_hash = file_hashes.get(temp_path_str)
                                            source_temp_file = Path(temp_path_str)
                                            break

                                    # Vérifier si doublon existant dans le projet
                                    if current_hash and current_hash in existing_hashes:
                                        existing_filename = existing_hashes[current_hash]
                                        logger.info(
                                            f"🛑 CV dupliqué détecté : '{original_filename}' "
                                            f"identique à '{existing_filename}' (hash={current_hash[:8]}...)"
                                        )
                                        # Émettre événement SSE pour informer le frontend
                                        duplicate_event = {
                                            "type": "duplicate",
                                            "filename": original_filename,
                                            "existing_filename": existing_filename,
                                            "reason": "Fichier identique déjà présent dans le projet"
                                        }
                                        yield f"event: duplicate\n"
                                        yield f"data: {json.dumps(duplicate_event)}\n\n"
                                        continue  # Skip save/indexation

                                    # Vérifier si doublon dans le batch actuel
                                    if current_hash and current_hash in batch_hashes:
                                        first_filename = batch_hashes[current_hash]
                                        logger.info(
                                            f"🛑 CV dupliqué détecté dans le batch : '{original_filename}' "
                                            f"identique à '{first_filename}' (hash={current_hash[:8]}...)"
                                        )
                                        # Émettre événement SSE pour informer le frontend
                                        duplicate_event = {
                                            "type": "duplicate",
                                            "filename": original_filename,
                                            "existing_filename": first_filename,
                                            "reason": "Fichier dupliqué dans le même batch"
                                        }
                                        yield f"event: duplicate\n"
                                        yield f"data: {json.dumps(duplicate_event)}\n\n"
                                        continue  # Skip save/indexation

                                    # Pas de doublon → ajouter au cache batch
                                    if current_hash:
                                        batch_hashes[current_hash] = original_filename

                                    # DÉTECTION DE COLLISION - Générer nom unique si nécessaire
                                    final_filename, collision_detected = CVService.get_unique_filename(
                                        project_id=project_id,
                                        original_filename=original_filename
                                    )

                                    # Vérifier collision dans le batch en cours (race condition)
                                    path = Path(final_filename)
                                    base = path.stem
                                    ext = path.suffix
                                    json_name = f"{base}.json"
                                    counter = 0

                                    while json_name in used_filenames_in_batch:
                                        counter += 1
                                        final_filename = f"{base}_{counter}{ext}"
                                        json_name = f"{base}_{counter}.json"
                                        collision_detected = True

                                    # Marquer ce nom comme utilisé dans le batch
                                    used_filenames_in_batch.add(json_name)

                                    if collision_detected:
                                        logger.warning(
                                            "🔄 Collision détectée pour '%s' → renommé en '%s'",
                                            original_filename,
                                            final_filename
                                        )

                                    # Utiliser le nom final (original ou avec suffixe)
                                    result.filename = final_filename
                                    if result.data:
                                        result.data.cv = final_filename

                                    cv_filename = Path(final_filename).stem + ".json"
                                    cv_path = cvs_parsed_dir / cv_filename
                                    with open(cv_path, 'w', encoding='utf-8') as f:
                                        json.dump(result.data.model_dump(), f, ensure_ascii=False, indent=2)
                                    logger.info(f"✅ CV sauvegardé: {cv_filename}")

                                    # Copier le fichier source (PDF/DOCX) dans cvs_original/
                                    original_file_path_rel = None
                                    try:
                                        # Retrouver le fichier temp correspondant à ce CV
                                        source_temp_file = None
                                        temp_key_to_remove = None
                                        for temp_path_str, original_name in original_filenames.items():
                                            if original_name == original_filename:
                                                source_temp_file = Path(temp_path_str)
                                                temp_key_to_remove = temp_path_str
                                                break

                                        if temp_key_to_remove is not None:
                                            original_filenames.pop(temp_key_to_remove, None)

                                        if source_temp_file and source_temp_file.exists():
                                            # Copier vers cvs_original/ avec le nom original
                                            original_dest = cvs_original_dir / result.filename
                                            shutil.copy2(source_temp_file, original_dest)
                                            logger.info(f"📄 Fichier original copié: {result.filename}")

                                            # Calculer le chemin relatif pour file_path
                                            original_file_path_abs = original_dest if original_dest.is_absolute() else (PROJECT_ROOT / original_dest)
                                            original_file_path_rel = str(original_file_path_abs.relative_to(PROJECT_ROOT))
                                    except Exception as copy_err:
                                        logger.warning(f"⚠️ Impossible de copier le fichier original pour {result.filename}: {copy_err}")

                                    # Indexer dans cv_meta
                                    try:
                                        cv_data = result.data.model_dump()
                                        identite = cv_data.get("identite", {})
                                        candidat_nom = identite.get("nom")
                                        if identite.get("prenom"):
                                            candidat_nom = f"{identite.get('nom')} {identite.get('prenom')}" if candidat_nom else identite.get("prenom")

                                        # Chemin relatif : absolu si nécessaire, puis relatif à PROJECT_ROOT
                                        json_path_abs = cv_path if cv_path.is_absolute() else (PROJECT_ROOT / cv_path)
                                        json_path_rel = str(json_path_abs.relative_to(PROJECT_ROOT))

                                        CVService.create_or_update_cv({
                                            "filename": cv_filename,
                                            "project_id": project_id,
                                            "json_path": json_path_rel,
                                            "file_path": original_file_path_rel,  # Chemin relatif du PDF/DOCX original
                                            "candidat_nom": candidat_nom,
                                            "candidat_titre": cv_data.get("titre")
                                        })
                                        logger.info(f"📇 CV indexé: {candidat_nom or cv_filename}")
                                    except Exception as idx_err:
                                        logger.info(f"❌ Erreur indexation CV {cv_filename}: {idx_err}")
                except Exception as e:
                    logger.info(f"Erreur lors de la sauvegarde des CVs dans le projet: {e}")

            # Émettre les résultats
            for result in results['results']:
                if result.success:
                    success_count += 1
                else:
                    failed_count += 1

                # Événement result
                yield f"event: result\n"
                yield f"data: {result.model_dump_json()}\n\n"

            # Événement done
            yield f"event: done\n"
            yield f"data: {json.dumps({'summary': {'success_count': success_count, 'failed_count': failed_count, 'total': total}})}\n\n"

        except Exception as e:
            # Log détaillé de l'erreur avec traceback complet
            import traceback
            full_traceback = traceback.format_exc()
            logger.exception("❌ ERREUR PARSING SSE - Trace complète:")
            logger.error(f"❌ PARSING ERROR:\n{full_traceback}")
            logger.error(f"Type d'erreur: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            logger.error(f"Nombre de fichiers traités: {len(temp_files)}")
            logger.error(f"Fichiers temp: {[str(f) for f in temp_files]}")

            # Événement error
            yield f"event: error\n"
            yield f"data: {json.dumps({'code': 'PARSING_ERROR', 'message': str(e)})}\n\n"

        finally:
            # Nettoyer fichiers temporaires
            for tmp_file in temp_files:
                try:
                    tmp_file.unlink(missing_ok=True)
                except Exception:
                    pass
            shutil.rmtree(temp_dir, ignore_errors=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/all", response_model=List[CV])
async def list_all_cvs():
    """
    Liste tous les CVs parsés de tous les projets

    **Retourne:**
    - Liste de tous les CVs parsés avec leurs métadonnées complètes
    """
    try:
        # Utiliser CVService pour lister tous les CVs (indexés dans cv_meta)
        cv_metas = CVService.list_all()

        # Récupérer tous les projets et entreprises
        projects_map = {}
        enterprises_map = {}
        try:
            # Charger toutes les entreprises
            all_enterprises = EnterpriseService.list_enterprises()
            for ent in all_enterprises:
                enterprises_map[ent["id"]] = ent["nom"]

            # Charger tous les projets
            all_projects = project_manager.list_projects()
            for proj in all_projects:
                ent_id = proj.get("enterprise_id")
                projects_map[proj["id"]] = {
                    "enterprise_id": ent_id,
                    "enterprise_nom": enterprises_map.get(ent_id) if ent_id else None
                }
        except Exception as e:
            logger.warning(f"Impossible de charger les projets: {e}")

        cvs = []
        for cv_meta in cv_metas:
            try:
                # Charger le JSON complet depuis le json_path
                cv_path = PROJECT_ROOT / cv_meta["json_path"]
                if cv_path.exists():
                    with open(cv_path, 'r', encoding='utf-8') as f:
                        cv_data = json.load(f)

                        # Ajouter les métadonnées projet/entreprise
                        project_id = cv_meta.get("project_id")
                        if project_id and project_id in projects_map:
                            cv_data["project_id"] = project_id
                            cv_data["enterprise_id"] = projects_map[project_id].get("enterprise_id")
                            cv_data["enterprise_nom"] = projects_map[project_id].get("enterprise_nom")

                        cvs.append(CV(**cv_data))
            except Exception as e:
                logger.info(f"Erreur lecture CV {cv_meta['filename']}: {e}")
                continue

        # Trier par nom de fichier
        cvs.sort(key=lambda x: x.cv)

        return cvs

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des CVs: {str(e)}"
        )


@router.get("/projects/{project_id}/cvs", response_model=List[CV])
async def list_project_cvs(project_id: str):
    """
    Liste tous les CVs parsés d'un projet

    **Paramètres:**
    - `project_id`: ID du projet

    **Retourne:**
    - Liste des CVs parsés avec leurs métadonnées complètes
    """
    try:
        # Vérifier que le projet existe
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Projet {project_id} introuvable"
            )

        # Récupérer enterprise_id et enterprise_nom du projet
        enterprise_id = project.get("enterprise_id")
        enterprise_nom = None
        if enterprise_id:
            try:
                enterprise_data = EnterpriseService.get_enterprise(enterprise_id)
                if enterprise_data:
                    enterprise_nom = enterprise_data["nom"]
            except Exception as e:
                logger.warning(f"Impossible de charger l'entreprise {enterprise_id}: {e}")

        # Utiliser CVService pour lister les CVs du projet
        cv_metas = CVService.list_by_project(project_id)

        cvs = []
        for cv_meta in cv_metas:
            try:
                # Charger le JSON complet depuis le json_path
                cv_path = PROJECT_ROOT / cv_meta["json_path"]
                if cv_path.exists():
                    with open(cv_path, 'r', encoding='utf-8') as f:
                        cv_data = json.load(f)

                        # Ajouter les métadonnées projet/entreprise
                        cv_data["project_id"] = project_id
                        cv_data["enterprise_id"] = enterprise_id
                        cv_data["enterprise_nom"] = enterprise_nom

                        cvs.append(CV(**cv_data))
            except Exception as e:
                logger.info(f"Erreur lecture CV {cv_meta['filename']}: {e}")
                continue

        # Trier par nom de fichier
        cvs.sort(key=lambda x: x.cv)

        return cvs

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des CVs: {str(e)}"
        )


@router.get("/{cv_id}", response_model=CV)
async def get_cv(cv_id: str):
    """
    Récupère un CV parsé par son ID (nom de fichier)

    **Note:** Cette route nécessite un système de stockage persistant.
    Pour l'instant, non implémentée (fichiers temporaires seulement).
    """
    raise HTTPException(status_code=501, detail="Endpoint non implémenté (stockage persistant requis)")


@router.delete("/{cv_id}")
async def delete_cv(cv_id: str):
    """
    Supprime un CV parsé (fichier JSON + entrée DB)

    **Paramètres:**
    - `cv_id`: Nom du fichier CV (identifiant unique)

    **Retourne:**
    - Message de confirmation
    """
    try:
        # cv_id = filename du CV
        success = CVService.delete_cv(filename=cv_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"CV '{cv_id}' introuvable")

        logger.info(f"✅ CV supprimé: {cv_id}")
        return {"message": f"CV '{cv_id}' supprimé avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression CV {cv_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du CV: {str(e)}"
        )
