"""
Méthodes à ajouter dans matching_engine.py pour supporter xAI (Grok)
À insérer après la méthode _normalize_reranked (ligne ~1269)
"""

# === MÉTHODES À AJOUTER ===

def _rerank_with_openai(self, cvs_to_rerank, cv_summaries, prompt, cv_names, progress_callback=None):
    """
    Re-ranking avec OpenAI (code extrait de rerank_with_llm)

    Args:
        cvs_to_rerank: CVs à reranker
        cv_summaries: Résumés des CVs préparés
        prompt: Prompt complet pour le LLM
        cv_names: Noms de fichiers des CVs
        progress_callback: Callback de progression

    Returns:
        Liste des CVs rerankés avec commentaires
    """
    try:
        response = self.openai_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "Tu réponds UNIQUEMENT en JSON valide conforme au schéma demandé."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
            # GPT-5 mini: pas de paramètre temperature
        )

        result = self._safe_json_parse(response.choices[0].message.content)

        # Valider le schéma de la réponse
        if not result or "ranked_cvs" not in result:
            raise ValueError(f"Réponse LLM invalide (pas de clé 'ranked_cvs'): {result}")

        ranked_cvs_data = result.get("ranked_cvs", [])

        # Valider les noms de fichiers
        llm_cv_names = [cv.get("cv", "") for cv in ranked_cvs_data]
        missing = set(cv_names) - set(llm_cv_names)
        if missing:
            print(f"⚠️ CVs manquants dans réponse LLM: {missing}")

        # Normaliser la réponse
        normalized_result = self._normalize_reranked(result)

        # Enrichir avec coefficient, evidences et flags
        # (mapper par nom de fichier)
        cv_map_by_name = {cv.get('cv'): cv for cv in cvs_to_rerank}
        cv_summaries_by_name = {s['nom_fichier']: s for s in cv_summaries}

        enriched_result = []
        for reranked_cv in ranked_cvs_data:
            cv_name = reranked_cv.get("cv", "inconnu")
            original_cv = cv_map_by_name.get(cv_name, {})
            summary = cv_summaries_by_name.get(cv_name, {})

            # Extraire les nouveaux champs (evidences, evidence_map, coefficient)
            coefficient = reranked_cv.get("coefficient_qualite_experience", 1.0)
            evidences = reranked_cv.get("evidences", [])
            evidence_map_data = reranked_cv.get("evidence_map", {})

            # Convertir en modèles Pydantic si possible
            try:
                from lib.models import Evidence, EvidenceMap
                evidences_models = [Evidence(**ev) for ev in evidences] if evidences else []
                evidence_map = EvidenceMap(
                    commentaire_scoring=evidence_map_data.get("commentaire_scoring", []),
                    appreciation_globale=evidence_map_data.get("appreciation_globale", [])
                ) if evidence_map_data else None
            except:
                evidences_models = evidences
                evidence_map = evidence_map_data

            enriched_result.append({
                "cv": cv_name,
                "coefficient_qualite_experience": coefficient,
                "commentaire_scoring": reranked_cv.get("commentaire_scoring", ""),
                "appreciation_globale": reranked_cv.get("appreciation_globale", ""),
                "evidences": evidences_models,
                "evidence_map": evidence_map,
                "flags_raw": summary.get("flags_raw")  # Flags détectés automatiquement
            })

        print(f"✅ Re-ranking OpenAI: {len(enriched_result)} CVs retournés (validés)")
        return enriched_result

    except Exception as e:
        print(f"❌ Exception rerank OpenAI: {e}")
        raise  # Remonter l'exception pour déclencher le fallback


def _call_xai_with_retry(self, payload):
    """
    Appel xAI avec retry automatique (tenacity)

    Args:
        payload: Payload JSON pour l'API xAI

    Returns:
        Réponse JSON de l'API
    """
    XAI_BASE = "https://api.x.ai/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def _do_call():
        api_key = os.environ.get('XAI_API_KEY')
        if not api_key:
            raise ValueError("XAI_API_KEY non trouvée dans l'environnement")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        resp = requests.post(
            f"{XAI_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=90
        )
        resp.raise_for_status()
        return resp.json()

    return _do_call()


def _rerank_with_xai(self, cvs_to_rerank, cv_summaries, prompt, cv_names, progress_callback=None):
    """
    Re-ranking avec xAI (Grok-4-fast-reasoning)

    Args:
        cvs_to_rerank: CVs à reranker
        cv_summaries: Résumés des CVs préparés
        prompt: Prompt complet pour le LLM
        cv_names: Noms de fichiers des CVs
        progress_callback: Callback de progression

    Returns:
        Liste des CVs rerankés avec commentaires
    """
    try:
        XAI_MODEL = "grok-4-fast-reasoning"

        # Construire le payload (format OpenAI-compatible)
        payload = {
            "model": XAI_MODEL,
            "messages": [
                {"role": "system", "content": "Tu réponds UNIQUEMENT en JSON valide conforme au schéma demandé."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": self.temperature_reranking,
            "max_tokens": 1200,
            "stream": False
        }

        # Appel xAI avec retry
        response_json = self._call_xai_with_retry(payload)

        # Parser la réponse (format OpenAI-compatible)
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            raise ValueError(f"Réponse xAI invalide: {response_json}")

        content = response_json["choices"][0]["message"]["content"]
        result = self._safe_json_parse(content)

        # Valider le schéma de la réponse
        if not result or "ranked_cvs" not in result:
            raise ValueError(f"Réponse LLM invalide (pas de clé 'ranked_cvs'): {result}")

        ranked_cvs_data = result.get("ranked_cvs", [])

        # Valider les noms de fichiers
        llm_cv_names = [cv.get("cv", "") for cv in ranked_cvs_data]
        missing = set(cv_names) - set(llm_cv_names)
        if missing:
            print(f"⚠️ CVs manquants dans réponse LLM: {missing}")

        # Normaliser la réponse (même logique que OpenAI)
        normalized_result = self._normalize_reranked(result)

        # Enrichir avec coefficient, evidences et flags
        cv_map_by_name = {cv.get('cv'): cv for cv in cvs_to_rerank}
        cv_summaries_by_name = {s['nom_fichier']: s for s in cv_summaries}

        enriched_result = []
        for reranked_cv in ranked_cvs_data:
            cv_name = reranked_cv.get("cv", "inconnu")
            original_cv = cv_map_by_name.get(cv_name, {})
            summary = cv_summaries_by_name.get(cv_name, {})

            # Extraire les nouveaux champs (evidences, evidence_map, coefficient)
            coefficient = reranked_cv.get("coefficient_qualite_experience", 1.0)
            evidences = reranked_cv.get("evidences", [])
            evidence_map_data = reranked_cv.get("evidence_map", {})

            # Convertir en modèles Pydantic si possible
            try:
                from lib.models import Evidence, EvidenceMap
                evidences_models = [Evidence(**ev) for ev in evidences] if evidences else []
                evidence_map = EvidenceMap(
                    commentaire_scoring=evidence_map_data.get("commentaire_scoring", []),
                    appreciation_globale=evidence_map_data.get("appreciation_globale", [])
                ) if evidence_map_data else None
            except:
                evidences_models = evidences
                evidence_map = evidence_map_data

            enriched_result.append({
                "cv": cv_name,
                "coefficient_qualite_experience": coefficient,
                "commentaire_scoring": reranked_cv.get("commentaire_scoring", ""),
                "appreciation_globale": reranked_cv.get("appreciation_globale", ""),
                "evidences": evidences_models,
                "evidence_map": evidence_map,
                "flags_raw": summary.get("flags_raw")  # Flags détectés automatiquement
            })

        print(f"✅ Re-ranking xAI (Grok): {len(enriched_result)} CVs retournés (validés)")
        return enriched_result

    except Exception as e:
        print(f"❌ Exception rerank xAI: {e}")
        raise  # Remonter l'exception pour déclencher le fallback


# === MODIFICATION DE rerank_with_llm ===
# Au début de la méthode rerank_with_llm, ajouter le routing:

"""
    def rerank_with_llm(self, top_cvs: List[Dict], job_description: str, progress_callback=None, top_n: int = None) -> List[Dict]:
        # ... (début existant avec préparation des CVs et construction du prompt) ...

        # === ROUTING PROVIDER (AJOUTER APRÈS LA CONSTRUCTION DU PROMPT) ===
        provider = self.scoring_config.get("reranking_provider", "openai").lower()

        print(f"🔀 Provider reranking: {provider}")

        try:
            if provider == "xai":
                return self._rerank_with_xai(
                    cvs_to_rerank=cvs_to_rerank,
                    cv_summaries=cv_summaries,
                    prompt=prompt,
                    cv_names=cv_names,
                    progress_callback=progress_callback
                )
            else:  # default: openai
                return self._rerank_with_openai(
                    cvs_to_rerank=cvs_to_rerank,
                    cv_summaries=cv_summaries,
                    prompt=prompt,
                    cv_names=cv_names,
                    progress_callback=progress_callback
                )

        except Exception as e:
            # Le fallback existant se déclenchera ici
            raise
"""
