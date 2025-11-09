"""
Module de traitement parallèle pour le matching CV/RH
Implémente async/await pour les appels LLM et ThreadPool pour l'I/O fichiers
"""

import asyncio
import time
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import os


# ==================== EXTRACTION PARALLÈLE DE FICHIERS ====================

def extract_single_file(file_path: str, extract_fn: Callable) -> Dict[str, Any]:
    """
    Extrait un seul fichier avec gestion d'erreur

    Args:
        file_path: Chemin du fichier
        extract_fn: Fonction d'extraction (ex: extract_cv_text)

    Returns:
        {"file": path, "success": bool, "data": ..., "error": ...}
    """
    try:
        start = time.time()
        data = extract_fn(file_path)
        duration = time.time() - start

        return {
            "file": file_path,
            "success": True,
            "data": data,
            "error": None,
            "duration": duration
        }
    except Exception as e:
        return {
            "file": file_path,
            "success": False,
            "data": None,
            "error": str(e),
            "duration": 0
        }


def parallel_extract_files(
    file_paths: List[str],
    extract_fn: Callable,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict[str, Any]]:
    """
    Extrait plusieurs fichiers en parallèle avec ThreadPoolExecutor

    Args:
        file_paths: Liste des chemins de fichiers
        extract_fn: Fonction d'extraction
        max_workers: Nombre de threads (défaut: 4)
        progress_callback: Callback(current, total) pour progression

    Returns:
        Liste de résultats [{file, success, data, error, duration}, ...]
    """
    results = []
    total = len(file_paths)

    print(f"🔄 Extraction parallèle de {total} fichiers ({max_workers} workers)")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les jobs
        future_to_file = {
            executor.submit(extract_single_file, fp, extract_fn): fp
            for fp in file_paths
        }

        # Collecter les résultats au fur et à mesure
        completed = 0
        for future in as_completed(future_to_file):
            result = future.result()
            results.append(result)

            completed += 1
            if progress_callback:
                progress_callback(completed, total)

            status = "✅" if result["success"] else "❌"
            filename = os.path.basename(result["file"])
            print(f"  {status} {filename} ({result['duration']:.2f}s)")

    # Trier par ordre original
    results.sort(key=lambda r: file_paths.index(r["file"]))

    successes = sum(1 for r in results if r["success"])
    print(f"✅ {successes}/{total} fichiers extraits avec succès")

    return results


# ==================== APPELS LLM PARALLÈLES AVEC ASYNC ====================

async def async_llm_call(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    response_format: Dict[str, str],
    temperature: float,
    semaphore: asyncio.Semaphore,
    call_id: str
) -> Dict[str, Any]:
    """
    Appel LLM asynchrone avec semaphore (rate limiting)

    Args:
        client: Client OpenAI
        model: Modèle (ex: gpt-5-mini)
        messages: Messages du prompt
        response_format: Format de réponse {"type": "json_object"}
        temperature: Température
        semaphore: Semaphore pour limiter la concurrence
        call_id: ID de l'appel (pour debug)

    Returns:
        {"call_id": ..., "success": bool, "response": ..., "error": ...}
    """
    async with semaphore:  # Limite le nombre d'appels simultanés
        try:
            start = time.time()

            # Appel synchrone dans un thread (OpenAI n'a pas d'API async native)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    client.chat.completions.create,
                    model=model,
                    messages=messages,
                    response_format=response_format,
                        )
            )

            duration = time.time() - start
            content = response.choices[0].message.content

            return {
                "call_id": call_id,
                "success": True,
                "response": content,
                "error": None,
                "duration": duration
            }

        except Exception as e:
            return {
                "call_id": call_id,
                "success": False,
                "response": None,
                "error": str(e),
                "duration": 0
            }


async def parallel_llm_calls(
    client: Any,
    calls: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Effectue plusieurs appels LLM en parallèle avec rate limiting

    Args:
        client: Client OpenAI
        calls: Liste de dicts avec:
            - call_id: Identifiant unique
            - model: Modèle
            - messages: Messages
            - response_format: Format réponse
            - temperature: Température
        max_concurrent: Nombre max d'appels simultanés (défaut: 5)

    Returns:
        Liste de résultats [{call_id, success, response, error, duration}, ...]
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    print(f"🔄 Appels LLM parallèles: {len(calls)} appels ({max_concurrent} max concurrent)")

    tasks = [
        async_llm_call(
            client=client,
            model=call["model"],
            messages=call["messages"],
            response_format=call.get("response_format", {"type": "json_object"}),
            semaphore=semaphore,
            call_id=call["call_id"]
        )
        for call in calls
    ]

    results = await asyncio.gather(*tasks)

    successes = sum(1 for r in results if r["success"])
    total_duration = sum(r["duration"] for r in results)
    avg_duration = total_duration / len(results) if results else 0

    print(f"✅ {successes}/{len(calls)} appels réussis (durée moy: {avg_duration:.2f}s)")

    return results


def run_parallel_llm_calls(
    client: Any,
    calls: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Version synchrone wrapper pour parallel_llm_calls

    Args:
        client: Client OpenAI
        calls: Liste de calls (voir parallel_llm_calls)
        max_concurrent: Nombre max d'appels simultanés

    Returns:
        Liste de résultats
    """
    return asyncio.run(parallel_llm_calls(client, calls, max_concurrent))


# ==================== VALIDATION BATCH AVEC LLM RETRY ====================

async def validate_with_retry(
    data: Any,
    schema_type: str,
    llm_repair_fn: Optional[Callable] = None,
    max_attempts: int = 3
) -> Dict[str, Any]:
    """
    Valide des données avec retry automatique (LLM si fourni)

    Args:
        data: Données à valider
        schema_type: Type de schéma ("cv", "must_have", "reranking")
        llm_repair_fn: Fonction de réparation LLM optionnelle
        max_attempts: Nombre max de tentatives

    Returns:
        {"success": bool, "data": ..., "attempts": int, "errors": [...]}
    """
    from validation import validate_and_repair

    for attempt in range(max_attempts):
        result = validate_and_repair(data, schema_type, max_attempts=1)

        if result.valid:
            return {
                "success": True,
                "data": result.data,
                "attempts": attempt + 1,
                "errors": [],
                "warnings": result.warnings
            }

        # Si réparation automatique a échoué et qu'on a une fonction LLM
        if llm_repair_fn and attempt < max_attempts - 1:
            print(f"  ⚠️ Tentative {attempt + 1}/{max_attempts} échouée, réparation LLM...")
            try:
                data = await llm_repair_fn(data, result.errors)
            except Exception as e:
                print(f"  ❌ Réparation LLM échouée: {e}")
                continue

    # Échec après max_attempts
    return {
        "success": False,
        "data": data,
        "attempts": max_attempts,
        "errors": result.errors,
        "warnings": result.warnings if result else []
    }


# ==================== PIPELINE COMPLET ====================

class ParallelPipeline:
    """Pipeline de traitement parallèle pour le matching"""

    def __init__(
        self,
        max_file_workers: int = 4,
        max_llm_concurrent: int = 5,
        openai_client: Any = None
    ):
        """
        Initialise le pipeline

        Args:
            max_file_workers: Threads pour extraction fichiers
            max_llm_concurrent: Appels LLM simultanés max
            openai_client: Client OpenAI
        """
        self.max_file_workers = max_file_workers
        self.max_llm_concurrent = max_llm_concurrent
        self.openai_client = openai_client

    def extract_files(
        self,
        file_paths: List[str],
        extract_fn: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """Extrait des fichiers en parallèle"""
        return parallel_extract_files(
            file_paths,
            extract_fn,
            max_workers=self.max_file_workers,
            progress_callback=progress_callback
        )

    def process_llm_batch(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Traite un batch d'appels LLM en parallèle"""
        if not self.openai_client:
            raise ValueError("OpenAI client non configuré")

        return run_parallel_llm_calls(
            self.openai_client,
            calls,
            max_concurrent=self.max_llm_concurrent
        )

    async def validate_batch(
        self,
        data_list: List[Any],
        schema_type: str,
        max_attempts: int = 3
    ) -> List[Dict[str, Any]]:
        """Valide un batch de données avec retry"""
        tasks = [
            validate_with_retry(data, schema_type, max_attempts=max_attempts)
            for data in data_list
        ]

        return await asyncio.gather(*tasks)


# ==================== TESTS ====================

if __name__ == "__main__":
    print("🧪 Tests du module de parallélisation\n")
    print("=" * 60)

    # Test 1: Extraction parallèle (simulation)
    print("\n📁 Test 1: Extraction parallèle de fichiers")

    def fake_extract(file_path: str) -> str:
        """Simule une extraction lente"""
        time.sleep(0.5)
        return f"Contenu de {os.path.basename(file_path)}"

    fake_files = [f"cv_{i}.pdf" for i in range(8)]

    start = time.time()
    results = parallel_extract_files(
        fake_files,
        fake_extract,
        max_workers=4
    )
    duration = time.time() - start

    print(f"✅ {len(results)} fichiers traités en {duration:.2f}s")
    print(f"   (séquentiel aurait pris {len(fake_files) * 0.5:.1f}s)")

    # Test 2: Appels LLM parallèles (mock)
    print("\n🤖 Test 2: Appels LLM parallèles (simulés)")

    class MockClient:
        class MockResponse:
            def __init__(self):
                self.choices = [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': '{"result": "success"}'
                    })()
                })()]

        class MockCompletions:
            def create(self, **kwargs):
                time.sleep(0.3)  # Simule latence API
                return MockClient.MockResponse()

        def __init__(self):
            self.chat = type('obj', (object,), {
                'completions': self.MockCompletions()
            })()

    mock_client = MockClient()

    calls = [
        {
            "call_id": f"call_{i}",
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": "Test"}],
            "response_format": {"type": "json_object"},
            "temperature": 1
        }
        for i in range(10)
    ]

    start = time.time()
    results = run_parallel_llm_calls(mock_client, calls, max_concurrent=5)
    duration = time.time() - start

    print(f"✅ {len(results)} appels traités en {duration:.2f}s")
    print(f"   (séquentiel aurait pris {len(calls) * 0.3:.1f}s)")

    # Test 3: Pipeline complet
    print("\n🔄 Test 3: Pipeline complet")

    pipeline = ParallelPipeline(
        max_file_workers=4,
        max_llm_concurrent=5,
        openai_client=mock_client
    )

    print("✅ Pipeline initialisé")
    print(f"   - {pipeline.max_file_workers} workers fichiers")
    print(f"   - {pipeline.max_llm_concurrent} appels LLM simultanés")

    print("\n✅ Tous les tests terminés!")
