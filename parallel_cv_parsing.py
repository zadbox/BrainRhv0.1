"""
⚠️ WARNING - MODULE LEGACY

Module de parsing parallèle des CVs
Utilise asyncio + Semaphore pour traiter plusieurs CVs simultanément

Ce module écrit dans des dossiers arbitraires et ne suit pas la nouvelle architecture.

Pour la nouvelle architecture, utilisez:
- API: POST /api/v1/projects/{project_id}/cvs/upload (upload avec parsing automatique)
- Service: brainrh.services.cv_service.CVService

Les CVs sont maintenant stockés dans: enterprises/{id}/projects/{id}/cvs_parsed/
Ce module est conservé uniquement pour tests/développement.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import json
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import parseur_cv
import time
from datetime import datetime

load_dotenv()

# Client OpenAI async
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logger pour tracking des performances
def log_performance(message: str, level: str = "INFO"):
    """Log avec timestamp pour tracking des performances"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_message = f"[{timestamp}] [{level}] {message}"

    # Afficher dans la console
    print(log_message)

    # Écrire dans un fichier de log
    log_file = Path("logs/parsing_performance.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


async def parse_single_cv_async(
    cv_text: str,
    cv_filename: str,
    model: str = "gpt-5-mini",
    semaphore: asyncio.Semaphore = None
) -> Dict[str, Any]:
    """
    Parse un CV de manière asynchrone avec GPT

    Args:
        cv_text: Texte extrait du CV
        cv_filename: Nom du fichier CV
        model: Modèle LLM à utiliser
        temperature: Température (0.1 pour extraction structurée)
        semaphore: Semaphore pour limiter la concurrence

    Returns:
        Dict avec données parsées ou erreur + timing détaillé
    """
    # Timer global pour ce CV
    cv_start_time = time.time()
    timings = {}

    async with semaphore if semaphore else asyncio.Semaphore(5):
        try:
            log_performance(f"🔄 [DÉBUT] Parsing de {cv_filename}")

            # PHASE 1: Appel API
            api_start = time.time()
            log_performance(f"  📤 [API START] Envoi requête LLM pour {cv_filename}")

            response = await client.chat.completions.create(
                model=model,
                # NE PAS passer temperature pour gpt-5-mini (seule valeur 1.0 supportée)
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui analyse des CV. Tu réponds UNIQUEMENT en JSON valide."},
                    {"role": "user", "content": f"{parseur_cv.PROMPT_CV_EXTRACTION}\n\n{cv_text}"}
                ],
                response_format={"type": "json_object"}
            )

            api_duration = time.time() - api_start
            timings['api_call'] = round(api_duration, 3)
            log_performance(f"  📥 [API END] Réponse reçue pour {cv_filename} ({api_duration:.3f}s)")

            # PHASE 2: Extraction réponse
            extract_start = time.time()
            result_text = response.choices[0].message.content
            extract_duration = time.time() - extract_start
            timings['extract_response'] = round(extract_duration, 3)
            log_performance(f"  📄 [EXTRACT] Réponse extraite ({extract_duration:.3f}s)")

            # PHASE 3: Nettoyage JSON
            clean_start = time.time()
            cleaned_result = parseur_cv.clean_json_text(result_text)
            clean_duration = time.time() - clean_start
            timings['clean_json'] = round(clean_duration, 3)
            log_performance(f"  🧹 [CLEAN] JSON nettoyé ({clean_duration:.3f}s)")

            # PHASE 4: Parsing JSON
            parse_start = time.time()
            parsed_data = json.loads(cleaned_result)
            parse_duration = time.time() - parse_start
            timings['parse_json'] = round(parse_duration, 3)
            log_performance(f"  ✓ [PARSE] JSON parsé ({parse_duration:.3f}s)")

            # Temps total
            total_duration = time.time() - cv_start_time
            timings['total'] = round(total_duration, 3)

            log_performance(f"✅ [FIN] {cv_filename} parsé avec succès | TOTAL: {total_duration:.3f}s", "SUCCESS")
            log_performance(f"  📊 Détail: API={api_duration:.3f}s | Clean={clean_duration:.3f}s | Parse={parse_duration:.3f}s")

            return {
                "filename": cv_filename,
                "success": True,
                "data": parsed_data,
                "timings": timings  # Ajout des timings
            }

        except Exception as e:
            total_duration = time.time() - cv_start_time
            log_performance(f"❌ [ERREUR] {cv_filename}: {str(e)[:100]} | Temps écoulé: {total_duration:.3f}s", "ERROR")
            return {
                "filename": cv_filename,
                "success": False,
                "error": str(e),
                "timings": {"total": round(total_duration, 3), "error": True}
            }


async def parse_cvs_parallel(
    cv_files: List[Path],
    cv_json_folder: Path,
    model: str = "gpt-5-mini",
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """
    Parse plusieurs CVs en parallèle avec contrôle de concurrence

    Args:
        cv_files: Liste de Path vers les fichiers CVs (PDF/DOCX)
        cv_json_folder: Dossier de sortie pour les JSONs
        model: Modèle LLM à utiliser
        temperature: Température (0.1 pour extraction)
        max_concurrent: Nombre max d'appels LLM simultanés

    Returns:
        Dict avec statistiques (success_count, failed_count, results)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []

    # Créer le dossier de sortie
    cv_json_folder.mkdir(parents=True, exist_ok=True)

    # Marqueur de début de session
    log_performance("")
    log_performance("=" * 100)
    log_performance(f"🚀 NOUVELLE SESSION DE PARSING - {len(cv_files)} fichiers à traiter")
    log_performance(f"   Configuration: max_concurrent={max_concurrent}, model={model}")
    log_performance("=" * 100)

    # Extraction du texte (synchrone) avec tracking
    log_performance(f"📂 [EXTRACTION TEXTE] Début extraction de {len(cv_files)} fichiers")
    extraction_start = time.time()

    cv_texts = []
    extraction_timings = []

    for idx, cv_file in enumerate(cv_files, 1):
        ext = cv_file.suffix.lower()
        file_start = time.time()

        try:
            log_performance(f"  📄 [{idx}/{len(cv_files)}] Extraction de {cv_file.name} (format: {ext})")

            if ext == ".pdf":
                cv_text = parseur_cv.extract_text_from_pdf(str(cv_file))
            elif ext == ".docx":
                cv_text = parseur_cv.extract_text_from_docx(str(cv_file))
            else:
                log_performance(f"  ⚠️ Format non supporté: {cv_file.name}", "WARNING")
                continue

            file_duration = time.time() - file_start
            extraction_timings.append({
                "filename": cv_file.name,
                "duration": round(file_duration, 3),
                "text_length": len(cv_text)
            })

            log_performance(f"  ✅ {cv_file.name} extrait ({file_duration:.3f}s, {len(cv_text)} chars)")

            cv_texts.append({
                "filename": cv_file.name,
                "text": cv_text
            })
        except Exception as e:
            file_duration = time.time() - file_start
            log_performance(f"  ❌ Erreur extraction {cv_file.name}: {e} ({file_duration:.3f}s)", "ERROR")

    extraction_total = time.time() - extraction_start
    log_performance(f"📂 [FIN EXTRACTION] {len(cv_texts)}/{len(cv_files)} fichiers extraits en {extraction_total:.3f}s")

    if extraction_timings:
        avg_extraction = sum(t['duration'] for t in extraction_timings) / len(extraction_timings)
        log_performance(f"  📊 Temps moyen extraction: {avg_extraction:.3f}s par fichier")

    # Parsing parallèle avec LLM
    log_performance(f"🤖 [PARSING LLM] Début parsing de {len(cv_texts)} CVs (max {max_concurrent} simultanés)")
    parsing_start = time.time()

    for cv_info in cv_texts:
        task = parse_single_cv_async(
            cv_text=cv_info["text"],
            cv_filename=cv_info["filename"],
            model=model,
            semaphore=semaphore
        )
        tasks.append(task)

    # Exécuter toutes les tâches en parallèle
    results = await asyncio.gather(*tasks)

    parsing_total = time.time() - parsing_start
    log_performance(f"🤖 [FIN PARSING] {len(results)} CVs traités en {parsing_total:.3f}s")

    # Sauvegarder les résultats et calculer les stats
    save_start = time.time()
    success_count = 0
    failed_count = 0
    saved_files = []
    llm_timings = []

    for result in results:
        if result["success"]:
            # Sauvegarder le JSON
            json_filename = Path(result["filename"]).stem + ".json"
            json_path = cv_json_folder / json_filename

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result["data"], f, ensure_ascii=False, indent=4)

            saved_files.append(json_filename)
            success_count += 1

            # Collecter les timings LLM
            if "timings" in result:
                llm_timings.append(result["timings"])
        else:
            failed_count += 1

    save_duration = time.time() - save_start

    # STATISTIQUES FINALES
    log_performance("=" * 80)
    log_performance("📊 [RAPPORT FINAL DE PERFORMANCE]")
    log_performance("=" * 80)
    log_performance(f"  ✅ Succès: {success_count}/{len(results)}")
    log_performance(f"  ❌ Échecs: {failed_count}/{len(results)}")
    log_performance(f"  💾 Sauvegarde: {save_duration:.3f}s")
    log_performance("")

    # Stats extraction
    if extraction_timings:
        total_extract_time = sum(t['duration'] for t in extraction_timings)
        avg_extract_time = total_extract_time / len(extraction_timings)
        min_extract = min(t['duration'] for t in extraction_timings)
        max_extract = max(t['duration'] for t in extraction_timings)

        log_performance(f"📂 EXTRACTION DE TEXTE:")
        log_performance(f"  • Temps total: {extraction_total:.3f}s")
        log_performance(f"  • Temps moyen: {avg_extract_time:.3f}s/CV")
        log_performance(f"  • Min: {min_extract:.3f}s | Max: {max_extract:.3f}s")
        log_performance("")

    # Stats LLM
    if llm_timings:
        avg_api = sum(t.get('api_call', 0) for t in llm_timings) / len(llm_timings)
        avg_total_llm = sum(t.get('total', 0) for t in llm_timings) / len(llm_timings)
        min_api = min(t.get('api_call', 0) for t in llm_timings)
        max_api = max(t.get('api_call', 0) for t in llm_timings)

        log_performance(f"🤖 PARSING LLM:")
        log_performance(f"  • Temps total: {parsing_total:.3f}s")
        log_performance(f"  • Temps moyen par CV: {avg_total_llm:.3f}s")
        log_performance(f"  • Temps API moyen: {avg_api:.3f}s")
        log_performance(f"  • API Min: {min_api:.3f}s | Max: {max_api:.3f}s")
        log_performance("")

    # Temps total global
    total_global = extraction_total + parsing_total + save_duration
    log_performance(f"⏱️ TEMPS TOTAL: {total_global:.3f}s")
    log_performance(f"  • Extraction: {extraction_total:.3f}s ({extraction_total/total_global*100:.1f}%)")
    log_performance(f"  • Parsing LLM: {parsing_total:.3f}s ({parsing_total/total_global*100:.1f}%)")
    log_performance(f"  • Sauvegarde: {save_duration:.3f}s ({save_duration/total_global*100:.1f}%)")
    log_performance("=" * 80)

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total": len(results),
        "saved_files": saved_files,
        "results": results,
        "timings": {
            "extraction_total": round(extraction_total, 3),
            "extraction_details": extraction_timings,
            "parsing_total": round(parsing_total, 3),
            "llm_details": llm_timings,
            "save_duration": round(save_duration, 3),
            "total": round(total_global, 3)
        }
    }


# Fonction wrapper pour Streamlit (contexte synchrone)
def parse_cvs_parallel_sync(
    cv_files: List[Path],
    cv_json_folder: Path,
    model: str = "gpt-5-mini",
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """
    Wrapper synchrone pour Streamlit

    Usage:
        from parallel_cv_parsing import parse_cvs_parallel_sync

        results = parse_cvs_parallel_sync(
            cv_files=[Path("cv1.pdf"), Path("cv2.pdf")],
            cv_json_folder=Path("cv_json"),
            max_concurrent=5
        )

        st.success(f"✅ {results['success_count']} CVs parsés")
    """
    return asyncio.run(parse_cvs_parallel(
        cv_files=cv_files,
        cv_json_folder=cv_json_folder,
        model=model,
        max_concurrent=max_concurrent
    ))


# Test si exécuté directement
if __name__ == "__main__":
    async def test():
        """
        ⚠️ DEPRECATED - Ce script écrit dans cv_json/ (structure legacy)

        Pour la nouvelle architecture, utilisez l'API:
        POST /api/v1/projects/{project_id}/cvs/upload
        """
        print("⚠️  WARNING: Script legacy - Utilisez l'API pour uploader les CVs")
        print("   Nouvelle structure: enterprises/{id}/projects/{id}/cvs_parsed/")
        print()

        # Exemple de test
        test_folder = Path("cv_input")
        output_folder = Path("cv_json")

        if not test_folder.exists():
            print("⚠️ Créez d'abord un dossier cv_input avec des CVs")
            return

        cv_files = list(test_folder.glob("*.pdf")) + list(test_folder.glob("*.docx"))

        if not cv_files:
            print("⚠️ Aucun fichier CV trouvé dans cv_input/")
            return

        print(f"📁 {len(cv_files)} CV(s) trouvés")

        results = await parse_cvs_parallel(
            cv_files=cv_files,
            cv_json_folder=output_folder,
            max_concurrent=5
        )

        print(f"\n✅ Parsing terminé: {results['success_count']}/{results['total']} succès")

    asyncio.run(test())
