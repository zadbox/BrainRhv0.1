# -*- coding: utf-8 -*-
"""
Module de matching core - Fonctions pures de calcul
Vectorisation, similarité, scoring, formules de calcul
ATTENTION: Ne pas modifier les formules (risque de régression)
"""

import re
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer

from lib.models import CV, Offre, ResultatMatching


# ==================== NETTOYAGE TEXTE ====================

def clean_text(text: str) -> str:
    """
    Nettoie et normalise le texte

    Args:
        text: Texte brut

    Returns:
        Texte nettoyé (minuscules, espaces normalisés)
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().replace("\xa0", " ").strip())


# ==================== VECTORISATION ====================

def vectorize_text_list(
    text_list: List[str],
    embedding_model: SentenceTransformer,
    cache_folder: Optional[Path] = None
) -> np.ndarray:
    """
    Vectorise une liste de textes (avec cache optionnel)

    Args:
        text_list: Liste de strings à vectoriser
        embedding_model: Modèle SentenceTransformer
        cache_folder: Dossier de cache (None = pas de cache)

    Returns:
        np.ndarray de shape (1, d)
    """
    if not text_list:
        return np.zeros((1, embedding_model.get_sentence_embedding_dimension()))

    joined = " ".join(text_list)

    # Cache optionnel
    if cache_folder:
        cache_key = hashlib.sha256(joined.encode()).hexdigest()
        cache_file = cache_folder / f"emb_{cache_key}.npy"

        if cache_file.exists():
            return np.load(cache_file)

        # Calculer et cacher
        embedding = embedding_model.encode([joined])
        np.save(cache_file, embedding)
        return embedding

    return embedding_model.encode([joined])


def vectorize_many_docs(
    docs_as_lists: List[List[str]],
    embedding_model: SentenceTransformer,
    batch_size: int = 32,
    normalize: bool = True
) -> np.ndarray:
    """
    Vectorise plusieurs documents en batch (optimisé)

    Args:
        docs_as_lists: Liste de listes de strings (sections de CV aplaties)
        embedding_model: Modèle SentenceTransformer
        batch_size: Taille du batch
        normalize: Normaliser les embeddings (True pour cosine via dot product)

    Returns:
        np.ndarray de shape (N, d) en float32 normalisé
    """
    if not docs_as_lists:
        dim = embedding_model.get_sentence_embedding_dimension()
        return np.zeros((0, dim), dtype=np.float32)

    # Concaténer chaque liste en une chaîne
    texts = [" ".join(parts) for parts in docs_as_lists]

    # Encoder en batch
    embeddings = embedding_model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False
    )

    # Assurer float32
    return embeddings.astype(np.float32)


# ==================== SIMILARITÉ ====================

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs

    Args:
        vec_a: Vecteur A (shape: (1, d) ou (d,))
        vec_b: Vecteur B (shape: (1, d) ou (d,))

    Returns:
        Score de similarité entre 0 et 1
    """
    # Aplatir si nécessaire
    if vec_a.ndim > 1:
        vec_a = vec_a.flatten()
    if vec_b.ndim > 1:
        vec_b = vec_b.flatten()

    # Calcul cosinus
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)

    # Clamper entre 0 et 1
    return float(max(0.0, min(1.0, similarity)))


def compute_section_similarities(
    cv_embedding: np.ndarray,
    offre_embedding: np.ndarray,
    section_weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Calcule les similarités par section (DEPRECATED - utilise embedding global maintenant)

    Args:
        cv_embedding: Embedding du CV
        offre_embedding: Embedding de l'offre
        section_weights: Poids par section (non utilisé dans version actuelle)

    Returns:
        Dict avec score global uniquement
    """
    similarity = cosine_similarity(cv_embedding, offre_embedding)

    return {
        "score_global": similarity
    }


# ==================== FORMULES DE SCORING ====================

def calculate_nice_have_malus(
    nb_manquants: int,
    malus_factor: float = 0.95
) -> float:
    """
    Calcule le malus nice-have selon la formule: malus_factor^nb_manquants

    ATTENTION: Ne pas modifier cette formule (validée par utilisateur)

    Args:
        nb_manquants: Nombre de nice-have manquants
        malus_factor: Facteur de malus (défaut: 0.95)

    Returns:
        Multiplicateur entre 0 et 1 (1 = aucun malus)
    """
    if nb_manquants <= 0:
        return 1.0

    malus = malus_factor ** nb_manquants

    # Clamper entre 0 et 1
    return max(0.0, min(1.0, malus))


def calculate_final_score(
    score_base: float,
    bonus_nice_have: float,
    coefficient_experience: float
) -> float:
    """
    Calcule le score final selon la formule:
    Score Final = Score Base × Malus Nice-Have × Coefficient Qualité XP

    ATTENTION: Ne pas modifier cette formule (validée par utilisateur)

    Args:
        score_base: Score de similarité base (0-1)
        bonus_nice_have: Multiplicateur nice-have (0-1)
        coefficient_experience: Coefficient qualité expérience (1.0-1.4)

    Returns:
        Score final entre 0 et 1
    """
    score = score_base * bonus_nice_have * coefficient_experience

    # Clamper entre 0 et 1
    return max(0.0, min(1.0, score))


def validate_coefficient_experience(coef: float) -> float:
    """
    Valide et clamp le coefficient d'expérience entre 1.0 et 1.4

    Args:
        coef: Coefficient brut

    Returns:
        Coefficient validé entre 1.0 et 1.4
    """
    try:
        coef_float = float(coef)
        return max(1.0, min(1.4, coef_float))
    except (ValueError, TypeError):
        return 1.0


# ==================== UTILITAIRES CV ====================

def flatten_cv_sections(cv: CV) -> List[str]:
    """
    Aplatit les sections d'un CV en liste de strings

    Args:
        cv: CV structuré

    Returns:
        Liste de strings (compétences, expériences, formations, etc.)
    """
    parts = []

    # Titre
    if cv.titre:
        parts.append(cv.titre)

    # Résumé
    if cv.resume_professionnel:
        parts.append(cv.resume_professionnel)

    # Compétences techniques
    parts.extend(cv.competences_techniques)

    # Compétences transversales
    parts.extend(cv.competences_transversales)

    # Langues
    parts.extend(cv.langues)

    # Expériences (missions)
    for exp in cv.experiences_professionnelles:
        if exp.poste:
            parts.append(exp.poste)
        if exp.entreprise:
            parts.append(exp.entreprise)
        parts.extend(exp.missions)

    # Formations
    for formation in cv.formations:
        if isinstance(formation, dict):
            for key, value in formation.items():
                if value and isinstance(value, str):
                    parts.append(value)

    # Certifications
    parts.extend(cv.certifications)

    # Projets
    parts.extend(cv.projets)

    return parts


def flatten_offre_sections(offre: Offre) -> List[str]:
    """
    Aplatit les sections d'une offre en liste de strings

    Args:
        offre: Offre structurée

    Returns:
        Liste de strings
    """
    parts = []

    sections = offre.sections

    # Titre
    if sections.titre:
        parts.append(sections.titre)

    # Résumé
    if sections.resume_professionnel:
        parts.append(sections.resume_professionnel)

    # Compétences techniques
    parts.extend(sections.competences_techniques)

    # Compétences transversales
    parts.extend(sections.competences_transversales)

    # Langues
    parts.extend(sections.langues)

    # Expériences
    for exp in sections.experiences_professionnelles:
        if isinstance(exp, dict):
            for key, value in exp.items():
                if value and isinstance(value, str):
                    parts.append(value)

    # Formations
    for formation in sections.formations:
        if isinstance(formation, dict):
            for key, value in formation.items():
                if value and isinstance(value, str):
                    parts.append(value)

    # Certifications
    parts.extend(sections.certifications)

    # Projets
    parts.extend(sections.projets)

    return parts


# ==================== CONSTRUCTION RÉSULTAT ====================

def build_matching_result(
    cv: CV,
    score_base: float,
    nice_have_manquants: List[str],
    malus_factor: float = 0.95,
    coefficient_experience: float = 1.0,
    commentaire_scoring: Optional[str] = None,
    appreciation_globale: Optional[str] = None
) -> ResultatMatching:
    """
    Construit un résultat de matching complet

    Args:
        cv: CV analysé
        score_base: Score de similarité base
        nice_have_manquants: Liste des nice-have manquants
        malus_factor: Facteur de malus (défaut: 0.95)
        coefficient_experience: Coefficient qualité expérience (1.0-1.4)
        commentaire_scoring: Commentaire LLM (optionnel)
        appreciation_globale: Appréciation LLM (optionnelle)

    Returns:
        ResultatMatching complet avec score final calculé
    """
    # Calculer bonus nice-have
    bonus_nice_have = calculate_nice_have_malus(
        nb_manquants=len(nice_have_manquants),
        malus_factor=malus_factor
    )

    # Valider coefficient
    coefficient_experience = validate_coefficient_experience(coefficient_experience)

    # Calculer score final
    score_final = calculate_final_score(
        score_base=score_base,
        bonus_nice_have=bonus_nice_have,
        coefficient_experience=coefficient_experience
    )

    return ResultatMatching(
        cv=cv.cv,
        score_final=score_final,
        score_base=score_base,
        bonus_nice_have_multiplicateur=bonus_nice_have,
        coefficient_qualite_experience=coefficient_experience,
        nice_have_manquants=nice_have_manquants,
        commentaire_scoring=commentaire_scoring,
        appreciation_globale=appreciation_globale
    )
