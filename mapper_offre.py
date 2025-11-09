"""
Module de mapping pour normaliser les formats d'offres d'emploi
Convertit différents formats d'offres vers le schéma unifié sections{}
"""

from typing import Dict, Any, List


def map_offre_to_sections(offre_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mappe une offre d'emploi vers le format standardisé sections{}

    Args:
        offre_data: Données de l'offre (peut être au format ParserOffre_Final ou autre)

    Returns:
        Offre au format standardisé avec clé "sections"

    Example:
        Input (format ParserOffre_Final):
        {
            "titre_cv": "Data Scientist",
            "resume_professionnel": "...",
            "competences_techniques": [...]
        }

        Output (format standardisé):
        {
            "sections": {
                "titre": "Data Scientist",
                "resume_professionnel": "...",
                "competences_techniques": [...]
            }
        }
    """

    # Cas 1: L'offre a déjà le format sections{} correct
    if "sections" in offre_data:
        return _normalize_sections(offre_data)

    # Cas 2: L'offre a le format de ParserOffre_Final (avec titre_cv, resume_professionnel, etc.)
    if "titre_cv" in offre_data or "resume_professionnel" in offre_data:
        return _map_from_parser_offre_final(offre_data)

    # Cas 3: Format inconnu - essayer de détecter et mapper
    return _map_generic_offre(offre_data)


def _normalize_sections(offre_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise un format qui a déjà une clé sections

    Args:
        offre_data: Offre avec clé "sections"

    Returns:
        Offre normalisée
    """
    sections = offre_data["sections"]

    # S'assurer que tous les champs requis existent
    normalized = {
        "sections": {
            "titre": sections.get("titre", ""),
            "resume_professionnel": sections.get("resume_professionnel", ""),
            "competences_techniques": sections.get("competences_techniques", []),
            "competences_transversales": sections.get("competences_transversales", []),
            "langues": sections.get("langues", []),
            "experiences_professionnelles": sections.get("experiences_professionnelles", []),
            "formations": sections.get("formations", []),
            "certifications": sections.get("certifications", []),
            "projets": sections.get("projets", []),
            "mobilite": sections.get("mobilite", {
                "permis_conduire": False,
                "disponibilite_geographique": ""
            })
        }
    }

    return normalized


def _map_from_parser_offre_final(offre_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mappe le format de ParserOffre_Final vers le format standardisé

    Args:
        offre_data: Offre au format ParserOffre_Final

    Returns:
        Offre au format standardisé sections{}
    """

    # Mapping direct des champs
    mapped = {
        "sections": {
            "titre": offre_data.get("titre_cv", ""),
            "resume_professionnel": offre_data.get("resume_professionnel", ""),
            "competences_techniques": offre_data.get("competences_techniques", []),
            "competences_transversales": offre_data.get("competences_transversales", []),
            "langues": offre_data.get("langues", []),
            "experiences_professionnelles": _normalize_experiences(
                offre_data.get("experiences_professionnelles", [])
            ),
            "formations": _normalize_formations(
                offre_data.get("formations", [])
            ),
            "certifications": offre_data.get("certifications", []),
            "projets": offre_data.get("projets", []),
            "mobilite": offre_data.get("mobilite", {
                "permis_conduire": False,
                "disponibilite_geographique": ""
            })
        }
    }

    return mapped


def _map_generic_offre(offre_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tente de mapper un format d'offre générique

    Args:
        offre_data: Offre au format inconnu

    Returns:
        Offre au format standardisé (best effort)
    """

    # Liste de mappings possibles pour les clés
    key_mappings = {
        "titre": ["titre", "titre_cv", "intitule", "poste", "title"],
        "resume_professionnel": ["resume_professionnel", "resume", "description", "profil"],
        "competences_techniques": ["competences_techniques", "skills", "technical_skills"],
        "competences_transversales": ["competences_transversales", "soft_skills"],
        "langues": ["langues", "languages"],
        "experiences_professionnelles": ["experiences_professionnelles", "experiences", "experience"],
        "formations": ["formations", "education"],
        "certifications": ["certifications", "certificats"],
        "projets": ["projets", "projects"]
    }

    sections = {}

    # Tenter de trouver les bonnes clés
    for standard_key, possible_keys in key_mappings.items():
        for possible_key in possible_keys:
            if possible_key in offre_data:
                sections[standard_key] = offre_data[possible_key]
                break
        else:
            # Valeur par défaut si non trouvé
            if standard_key in ["competences_techniques", "competences_transversales",
                                "langues", "experiences_professionnelles", "formations",
                                "certifications", "projets"]:
                sections[standard_key] = []
            else:
                sections[standard_key] = ""

    # Mobilité par défaut
    sections["mobilite"] = offre_data.get("mobilite", {
        "permis_conduire": False,
        "disponibilite_geographique": ""
    })

    return {"sections": sections}


def _normalize_experiences(experiences: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalise la liste des expériences professionnelles

    Args:
        experiences: Liste d'expériences (peut avoir différents formats)

    Returns:
        Liste d'expériences normalisées
    """
    if not experiences:
        return []

    normalized = []

    for exp in experiences:
        if isinstance(exp, dict):
            normalized_exp = {
                "poste": exp.get("poste", ""),
                "entreprise": exp.get("entreprise", ""),
                "lieu": exp.get("lieu", ""),
                "date_debut": exp.get("date_debut", ""),
                "date_fin": exp.get("date_fin", ""),
                "duree": exp.get("duree", exp.get("durée", "")),  # Support des deux orthographes
                "missions": exp.get("missions", [])
            }
            normalized.append(normalized_exp)
        elif isinstance(exp, str):
            # Si c'est une chaîne, essayer de la parser
            normalized.append({
                "poste": exp,
                "entreprise": "",
                "lieu": "",
                "date_debut": "",
                "date_fin": "",
                "duree": "",
                "missions": []
            })

    return normalized


def _normalize_formations(formations: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalise la liste des formations

    Args:
        formations: Liste de formations (peut avoir différents formats)

    Returns:
        Liste de formations normalisées
    """
    if not formations:
        return []

    normalized = []

    for formation in formations:
        if isinstance(formation, dict):
            normalized_formation = {
                "diplome": formation.get("diplome", ""),
                "ecole": formation.get("ecole", ""),
                "annee_obtention": formation.get("annee_obtention", ""),
                "niveau": formation.get("niveau", ""),
                "specialite": formation.get("specialite", "")
            }
            normalized.append(normalized_formation)
        elif isinstance(formation, str):
            # Si c'est une chaîne, essayer de la parser
            normalized.append({
                "diplome": formation,
                "ecole": "",
                "annee_obtention": "",
                "niveau": "",
                "specialite": ""
            })

    return normalized


def validate_offre_schema(offre_data: Dict[str, Any]) -> bool:
    """
    Valide qu'une offre a bien le bon schéma sections{}

    Args:
        offre_data: Offre à valider

    Returns:
        True si le schéma est valide, False sinon
    """
    if "sections" not in offre_data:
        return False

    sections = offre_data["sections"]
    required_keys = [
        "titre", "competences_techniques", "competences_transversales",
        "langues", "experiences_professionnelles", "formations"
    ]

    return all(key in sections for key in required_keys)


# Fonction helper pour usage direct
def convert_offre(offre_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Charge une offre depuis un fichier JSON et la convertit au format standardisé

    Args:
        offre_path: Chemin vers le fichier JSON d'offre
        output_path: Chemin de sortie optionnel pour sauvegarder

    Returns:
        Offre au format standardisé
    """
    import json

    with open(offre_path, 'r', encoding='utf-8') as f:
        offre_data = json.load(f)

    converted = map_offre_to_sections(offre_data)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted, f, ensure_ascii=False, indent=4)
        print(f"✅ Offre convertie et sauvegardée dans: {output_path}")

    return converted


if __name__ == "__main__":
    # Test du mapper
    import json

    # Exemple de test avec format ParserOffre_Final
    test_offre = {
        "titre_cv": "Data Scientist Junior",
        "resume_professionnel": "Recherche d'un profil junior en data science",
        "competences_techniques": ["Python", "SQL", "Machine Learning"],
        "competences_transversales": ["Esprit analytique", "Travail en équipe"],
        "langues": ["Français", "Anglais"],
        "experiences_professionnelles": [],
        "formations": [{"niveau": "Bac+5", "specialite": "Data Science"}],
        "certifications": [],
        "projets": [],
        "mobilite": {"permis_conduire": False, "disponibilite_geographique": ""}
    }

    print("📝 Test du mapper:")
    converted = map_offre_to_sections(test_offre)
    print(json.dumps(converted, indent=2, ensure_ascii=False))

    print(f"\n✅ Schéma valide: {validate_offre_schema(converted)}")
