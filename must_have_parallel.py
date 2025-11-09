"""
Module de filtrage must-have parallélisé
- Parallélisation avec asyncio + ThreadPoolExecutor pour vraie parallélisation API
- Rate limiting (QPS)
- Timeout et retries
- Compatible avec le format existant
"""

import asyncio
import time
import random
import json
import functools
from typing import Dict, List, Tuple, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

# Configuration par défaut
DEFAULT_CONCURRENCY = 500    # CVs traités en parallèle (max threads)
DEFAULT_QPS = 100.0          # Requêtes/seconde max (limite OpenAI)
DEFAULT_TIMEOUT_S = 20       # Timeout par appel LLM
DEFAULT_RETRIES = 2          # Nombre de retries
DEFAULT_BACKOFF_S = 1.0      # Backoff initial (exponentiel)


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


def _is_empty(xs: Optional[List[str]]) -> bool:
    """Vérifie si une liste est vide ou ne contient que des chaînes vides"""
    return not xs or all((not s) or (not s.strip()) for s in xs)


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


async def _run_one(
    cv: Dict[str, Any],
    must_haves: List[str],
    job_description: str,
    *,
    decide_fn: Callable[[Dict[str,Any], List[str], str, int], Tuple[bool, str, Any]],
    timeout_s: int,
    retries: int,
    backoff_s: float,
    limiter: RateLimiter,
    executor: ThreadPoolExecutor,
) -> Tuple[Dict[str,Any], bool, str, Any]:
    """
    Appelle la fonction de décision avec protection QPS/timeout/retries + vraie parallélisation

    Args:
        cv: CV à analyser
        must_haves: Liste des critères indispensables
        job_description: Description de l'offre
        decide_fn: Fonction de décision (prompt + LLM + parsing)
        timeout_s: Timeout en secondes
        retries: Nombre de tentatives
        backoff_s: Backoff initial
        limiter: Rate limiter
        executor: ThreadPoolExecutor pour vraie parallélisation

    Returns:
        Tuple (cv, accepted, rationale, raw_trace)
    """
    delay = backoff_s
    last_err = None
    loop = asyncio.get_running_loop()

    for attempt in range(retries + 1):
        try:
            # Respecter le rate limit
            await limiter.acquire()

            # TRACKING: Marquer début appel API
            await _track_inflight_start()

            # Appel avec timeout + vraie parallélisation
            decide_partial = functools.partial(decide_fn, cv, must_haves, job_description, timeout_s)
            accepted, rationale, raw = await asyncio.wait_for(
                loop.run_in_executor(executor, decide_partial),
                timeout=timeout_s + 5,  # Garde-fou externe
            )

            # TRACKING: Marquer fin appel API
            await _track_inflight_end()

            return cv, accepted, rationale, raw

        except asyncio.TimeoutError as e:
            await _track_inflight_end()
            last_err = f"Timeout après {timeout_s}s (tentative {attempt + 1}/{retries + 1})"
            print(f"⚠️ {last_err} - CV: {cv.get('cv', 'inconnu')}")

        except Exception as e:
            await _track_inflight_end()
            last_err = str(e)
            print(f"⚠️ Erreur tentative {attempt + 1}/{retries + 1}: {last_err} - CV: {cv.get('cv', 'inconnu')}")

        # Backoff exponentiel avec jitter
        if attempt < retries:
            jitter = random.uniform(0, delay / 4)
            await asyncio.sleep(delay + jitter)
            delay *= 2

    # Échec après toutes les tentatives: rejet prudent
    cv_name = cv.get('cv', 'inconnu')
    print(f"❌ CV {cv_name} ÉLIMINÉ après {retries + 1} tentatives: {last_err}")
    return cv, False, f"[ERREUR après {retries + 1} tentatives] {last_err}", {"error": str(last_err)}


async def filter_cvs_by_must_have_parallel(
    cvs: List[Dict[str,Any]],
    must_haves: List[str],
    job_description: str,
    *,
    decide_fn: Callable[[Dict[str,Any], List[str], str, int], Tuple[bool, str, Any]],
    concurrency: int = DEFAULT_CONCURRENCY,
    qps: float = DEFAULT_QPS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    retries: int = DEFAULT_RETRIES,
    backoff_s: float = DEFAULT_BACKOFF_S,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[Dict[str,Any]], List[Dict[str,Any]], Dict[str, Dict[str, Any]]]:
    """
    Filtre les CVs en parallèle selon les must-have avec vraie parallélisation API

    Args:
        cvs: Liste des CVs à filtrer
        must_haves: Liste des critères indispensables
        job_description: Description de l'offre
        decide_fn: Fonction de décision (prompt + LLM + parsing)
        concurrency: Nombre de CVs traités en parallèle
        qps: Requêtes par seconde max
        timeout_s: Timeout par appel
        retries: Nombre de retries
        backoff_s: Backoff initial
        progress_callback: Callback(current, total) pour suivre la progression

    Returns:
        Tuple (accepted_list, rejected_list, traces_dict)
    """
    # Si pas de must-haves, accepter tous les CVs
    if _is_empty(must_haves):
        print("ℹ️ Aucun must-have défini → tous les CVs acceptés")
        return list(cvs), [], {}

    # Reset tracking avant le filtrage
    reset_inflight_tracking()

    print(f"\n🔄 Filtrage parallèle: {len(cvs)} CVs, concurrence={concurrency}, QPS={qps}")

    # ThreadPoolExecutor dimensionné selon la concurrence
    max_workers = max(4, min(concurrency, 128))

    limiter = RateLimiter(qps)
    sem = asyncio.Semaphore(max(1, concurrency))

    async def one(cv):
        async with sem:
            return await _run_one(
                cv, must_haves, job_description,
                decide_fn=decide_fn,
                timeout_s=timeout_s,
                retries=retries,
                backoff_s=backoff_s,
                limiter=limiter,
                executor=executor
            )

    # Créer le ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Lancer toutes les tâches
        tasks = [asyncio.create_task(one(cv)) for cv in cvs]

        accepted, rejected, traces = [], [], {}
        completed = 0
        total = len(tasks)

        # Traiter les résultats au fur et à mesure
        for fut in asyncio.as_completed(tasks):
            cv, ok, rationale, raw = await fut
            completed += 1

            # Mise à jour de la progression
            if progress_callback:
                progress_callback(completed, total)

            # Identifier le CV
            cv_id = cv.get("cv") or cv.get("id") or cv.get("filename") or cv.get("nom") or f"cv_{len(traces)+1}"

            # Stocker la trace
            traces[cv_id] = {
                "accepted": ok,
                "rationale": rationale,
                "raw": raw
            }

            # Classifier
            (accepted if ok else rejected).append(cv)

            # Log en temps réel
            status = "✅ ACCEPTÉ" if ok else "❌ ÉLIMINÉ"
            print(f"  [{completed}/{total}] {status} - {cv_id}")

    peak = get_peak_inflight()
    print(f"\n📊 Résultat: {len(accepted)} acceptés, {len(rejected)} éliminés")
    print(f"⚡ Pic d'appels API simultanés: {peak}")

    return accepted, rejected, traces


# Fonction wrapper synchrone pour compatibilité avec Streamlit
def filter_cvs_by_must_have_parallel_sync(
    cvs: List[Dict[str,Any]],
    must_haves: List[str],
    job_description: str,
    *,
    decide_fn: Callable[[Dict[str,Any], List[str], str, int], Tuple[bool, str, Any]],
    concurrency: int = DEFAULT_CONCURRENCY,
    qps: float = DEFAULT_QPS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    retries: int = DEFAULT_RETRIES,
    backoff_s: float = DEFAULT_BACKOFF_S,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[Dict[str,Any]], List[Dict[str,Any]], Dict[str, Dict[str, Any]]]:
    """Version synchrone pour compatibilité avec Streamlit"""
    return asyncio.run(
        filter_cvs_by_must_have_parallel(
            cvs, must_haves, job_description,
            decide_fn=decide_fn,
            concurrency=concurrency,
            qps=qps,
            timeout_s=timeout_s,
            retries=retries,
            backoff_s=backoff_s,
            progress_callback=progress_callback
        )
    )
