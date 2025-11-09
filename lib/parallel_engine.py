# -*- coding: utf-8 -*-
"""
Module de parallélisation - Orchestration des appels LLM en parallèle
Basé sur asyncio + ThreadPoolExecutor pour vraie parallélisation API
"""

import asyncio
import time
import random
import functools
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from lib.models import CV, CVParseResult
from lib.cv_parsing import extract_text_from_file, parse_cv_with_llm, get_openai_client

# Setup logging
logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================

DEFAULT_CONCURRENCY = 500  # CVs traités en parallèle (max threads)
DEFAULT_QPS = 100.0  # Requêtes/seconde max (limite OpenAI)
DEFAULT_TIMEOUT_S = 200  # Timeout par appel LLM (3m20s)
DEFAULT_RETRIES = 2  # Nombre de retries (3 tentatives au total)
DEFAULT_BACKOFF_S = 2.0  # Backoff initial (exponentiel)


# ==================== TRACKING PARALLÉLISATION ====================

# Métriques pour prouver la vraie parallélisation
_inflight_api_calls = 0
_peak_inflight = 0
_inflight_lock = None  # Créé à la demande (lazy init)


def _get_inflight_lock():
    """Retourne le lock (lazy initialization pour éviter RuntimeError)"""
    global _inflight_lock
    if _inflight_lock is None:
        _inflight_lock = asyncio.Lock()
    return _inflight_lock


async def _track_inflight_start():
    """Incrémente le compteur d'appels API en vol"""
    global _inflight_api_calls, _peak_inflight
    lock = _get_inflight_lock()
    async with lock:
        _inflight_api_calls += 1
        if _inflight_api_calls > _peak_inflight:
            _peak_inflight = _inflight_api_calls


async def _track_inflight_end():
    """Décrémente le compteur d'appels API en vol"""
    global _inflight_api_calls
    lock = _get_inflight_lock()
    async with lock:
        _inflight_api_calls -= 1


def get_peak_inflight() -> int:
    """Retourne le pic d'appels API simultanés"""
    return _peak_inflight


def reset_inflight_tracking():
    """Reset les métriques de tracking"""
    global _inflight_api_calls, _peak_inflight
    _inflight_api_calls = 0
    _peak_inflight = 0


# ==================== RATE LIMITER ====================

class RateLimiter:
    """Rate limiter simple basé sur QPS (requêtes/seconde)"""

    def __init__(self, qps: float):
        self.min_interval = 1.0 / max(qps, 0.01)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self):
        """Attend si nécessaire pour respecter le QPS"""
        async with self._lock:
            now = time.perf_counter()
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.perf_counter()


# ==================== PARSING PARALLÈLE ====================

async def _parse_single_cv_async(
    cv_path: Path,
    model: str,
    timeout_s: int,
    retries: int,
    backoff_s: float,
    limiter: RateLimiter,
    executor: ThreadPoolExecutor
) -> CVParseResult:
    """
    Parse un CV de manière asynchrone avec vraie parallélisation API

    Args:
        cv_path: Chemin vers le fichier CV
        model: Modèle LLM à utiliser
        timeout_s: Timeout en secondes
        retries: Nombre de tentatives
        backoff_s: Backoff initial
        limiter: Rate limiter
        executor: ThreadPoolExecutor pour vraie parallélisation

    Returns:
        CVParseResult avec succès/échec
    """
    cv_start_time = time.time()
    filename = cv_path.name
    delay = backoff_s
    last_err = None

    # Client OpenAI (thread-safe)
    openai_client = get_openai_client()
    loop = asyncio.get_running_loop()

    for attempt in range(retries + 1):
        try:
            # Respecter le rate limit
            await limiter.acquire()

            # Extraction texte (synchrone, dans thread)
            extract_fn = functools.partial(extract_text_from_file, str(cv_path))
            cv_text = await loop.run_in_executor(executor, extract_fn)

            # TRACKING: Marquer début appel API
            await _track_inflight_start()

            # Parsing LLM avec timeout + vraie parallélisation
            parse_fn = functools.partial(parse_cv_with_llm, cv_text, model, openai_client)
            parsed_data = await asyncio.wait_for(
                loop.run_in_executor(executor, parse_fn),
                timeout=timeout_s
            )

            # TRACKING: Marquer fin appel API
            await _track_inflight_end()

            # Succès
            total_duration = time.time() - cv_start_time
            return CVParseResult(
                filename=filename,
                success=True,
                data=CV(cv=filename, **parsed_data),
                error=None,
                timings={"total": round(total_duration, 3)}
            )

        except asyncio.TimeoutError:
            await _track_inflight_end()
            last_err = f"Timeout après {timeout_s}s (tentative {attempt + 1}/{retries + 1})"
            logger.info(f"  {last_err} - CV: {filename}")

        except Exception as e:
            await _track_inflight_end()
            last_err = str(e)
            logger.info(f"  Erreur tentative {attempt + 1}/{retries + 1}: {last_err} - CV: {filename}")

        # Backoff exponentiel avec jitter
        if attempt < retries:
            jitter = random.uniform(0, delay / 4)
            await asyncio.sleep(delay + jitter)
            delay *= 2

    # Échec après toutes les tentatives
    total_duration = time.time() - cv_start_time
    logger.info(f"❌ CV {filename} échec parsing après {retries + 1} tentatives: {last_err}")

    return CVParseResult(
        filename=filename,
        success=False,
        data=None,
        error=last_err,
        timings={"total": round(total_duration, 3), "error": True}
    )


async def parse_cvs_parallel_async(
    cv_files: List[Path],
    model: str = "gpt-5-mini",
    concurrency: int = DEFAULT_CONCURRENCY,
    qps: float = DEFAULT_QPS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    retries: int = DEFAULT_RETRIES,
    backoff_s: float = DEFAULT_BACKOFF_S,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Parse plusieurs CVs en parallèle avec vraie parallélisation API

    Args:
        cv_files: Liste de Path vers les fichiers CVs (PDF/DOCX)
        model: Modèle LLM à utiliser
        concurrency: Nombre max d'appels LLM simultanés
        qps: Requêtes par seconde max
        timeout_s: Timeout par appel
        retries: Nombre de retries
        backoff_s: Backoff initial
        progress_callback: Callback(current, total) pour suivre la progression

    Returns:
        Dict avec statistiques (success_count, failed_count, results, timings)
    """
    if not cv_files:
        return {
            "success_count": 0,
            "failed_count": 0,
            "total": 0,
            "results": [],
            "timings": {"total": 0}
        }

    # Reset tracking avant le parsing
    reset_inflight_tracking()

    logger.info(f"\n🚀 Parsing parallèle: {len(cv_files)} CVs, concurrence={concurrency}, QPS={qps}")

    # ThreadPoolExecutor dimensionné selon la concurrence
    max_workers = max(4, min(concurrency, 128))

    limiter = RateLimiter(qps)
    sem = asyncio.Semaphore(max(1, concurrency))
    start_time = time.time()

    async def one(cv_path):
        async with sem:
            return await _parse_single_cv_async(
                cv_path=cv_path,
                model=model,
                timeout_s=timeout_s,
                retries=retries,
                backoff_s=backoff_s,
                limiter=limiter,
                executor=executor
            )

    # Créer le ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Lancer toutes les tâches
        tasks = [asyncio.create_task(one(cv_path)) for cv_path in cv_files]

        results = []
        completed = 0
        total = len(tasks)
        success_count = 0
        failed_count = 0

        # Traiter les résultats au fur et à mesure
        for fut in asyncio.as_completed(tasks):
            result = await fut
            completed += 1

            # Mise à jour de la progression
            if progress_callback:
                progress_callback(completed, total)

            # Compter succès/échecs
            if result.success:
                success_count += 1
            else:
                failed_count += 1

            results.append(result)

            # Log en temps réel
            status = "✅" if result.success else "❌"
            logger.info(f"  [{completed}/{total}] {status} {result.filename}")

    total_duration = time.time() - start_time
    peak = get_peak_inflight()

    logger.info(f"\n📊 Parsing terminé: {success_count} succès, {failed_count} échecs en {total_duration:.1f}s")
    logger.info(f"⚡ Pic d'appels API simultanés: {peak}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total": total,
        "results": results,
        "timings": {"total": round(total_duration, 3), "peak_inflight": peak}
    }


def parse_cvs_parallel_sync(
    cv_files: List[Path],
    model: str = "gpt-5-mini",
    concurrency: int = DEFAULT_CONCURRENCY,
    qps: float = DEFAULT_QPS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    retries: int = DEFAULT_RETRIES,
    backoff_s: float = DEFAULT_BACKOFF_S,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Version synchrone pour compatibilité avec Streamlit

    Args:
        cv_files: Liste de Path vers les fichiers CVs
        model: Modèle LLM
        concurrency: Concurrence max
        qps: Requêtes/seconde
        timeout_s: Timeout par appel
        retries: Nombre de retries
        backoff_s: Backoff initial
        progress_callback: Callback de progression

    Returns:
        Dict avec résultats
    """
    return asyncio.run(
        parse_cvs_parallel_async(
            cv_files=cv_files,
            model=model,
            concurrency=concurrency,
            qps=qps,
            timeout_s=timeout_s,
            retries=retries,
            backoff_s=backoff_s,
            progress_callback=progress_callback
        )
    )


# ==================== UTILITAIRES ====================

def batch_files(files: List[Path], batch_size: int = 500) -> List[List[Path]]:
    """
    Découpe une liste de fichiers en lots

    Args:
        files: Liste de fichiers
        batch_size: Taille max par lot

    Returns:
        Liste de lots
    """
    batches = []
    for i in range(0, len(files), batch_size):
        batches.append(files[i:i + batch_size])
    return batches


def process_cvs_in_batches_sync(
    cv_files: List[Path],
    batch_size: int = 500,
    model: str = "gpt-5-mini",
    concurrency: int = DEFAULT_CONCURRENCY,
    qps: float = DEFAULT_QPS,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Traite les CVs par lots de taille maximale

    Args:
        cv_files: Liste de Path vers les CVs
        batch_size: Taille max par lot
        model: Modèle LLM
        concurrency: Concurrence par lot
        qps: QPS
        progress_callback: Callback de progression globale

    Returns:
        Dict avec résultats agrégés
    """
    batches = batch_files(cv_files, batch_size)

    logger.info(f"\n📦 Traitement par lots: {len(cv_files)} CVs en {len(batches)} lot(s) de {batch_size} max")

    all_results = []
    total_success = 0
    total_failed = 0
    global_start = time.time()

    for i, batch in enumerate(batches, 1):
        logger.info(f"\n🔄 Lot {i}/{len(batches)}: {len(batch)} CVs")

        batch_result = parse_cvs_parallel_sync(
            cv_files=batch,
            model=model,
            concurrency=concurrency,
            qps=qps,
            progress_callback=None  # Progress par lot seulement
        )

        all_results.extend(batch_result["results"])
        total_success += batch_result["success_count"]
        total_failed += batch_result["failed_count"]

        # Callback global
        if progress_callback:
            completed = sum(len(b) for b in batches[:i])
            progress_callback(completed, len(cv_files))

    total_duration = time.time() - global_start

    logger.info(f"\n✅ Traitement complet: {total_success} succès, {total_failed} échecs en {total_duration:.1f}s")

    return {
        "success_count": total_success,
        "failed_count": total_failed,
        "total": len(cv_files),
        "results": all_results,
        "timings": {"total": round(total_duration, 3)}
    }
