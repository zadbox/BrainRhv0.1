"""
Module de validation et normalisation des sorties LLM
Implémente des checks non-IA (regex, jsonschema, normalisation)
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from jsonschema import validate, ValidationError, Draft7Validator
from datetime import datetime


# ==================== SCHÉMAS JSON ====================

SCHEMA_CV = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "object",
            "required": ["titre", "resume_professionnel", "competences_techniques",
                        "competences_transversales", "experiences_professionnelles"],
            "properties": {
                "titre": {"type": "string", "minLength": 1, "maxLength": 200},
                "resume_professionnel": {"type": "string", "maxLength": 2000},
                "competences_techniques": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 100}
                },
                "competences_transversales": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 100}
                },
                "langues": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 50}
                },
                "experiences_professionnelles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["poste"],
                        "properties": {
                            "poste": {"type": "string", "minLength": 1},
                            "entreprise": {"type": "string"},
                            "duree": {"type": "string"},
                            "description": {"type": "string", "maxLength": 1000}
                        }
                    }
                },
                "formations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "diplome": {"type": "string"},
                            "etablissement": {"type": "string"},
                            "annee": {"type": ["string", "integer"]}
                        }
                    }
                },
                "certifications": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "projets": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "mobilite": {
                    "type": "object",
                    "properties": {
                        "permis_conduire": {"type": "boolean"},
                        "disponibilite_geographique": {"type": "string"}
                    }
                }
            }
        }
    },
    "required": ["sections"]
}

SCHEMA_MUST_HAVE = {
    "type": "object",
    "properties": {
        "must_have": {
            "type": "array",
            "items": {"type": "string", "minLength": 3, "maxLength": 200},
            "minItems": 1,
            "maxItems": 15
        }
    },
    "required": ["must_have"]
}

SCHEMA_RERANKING = {
    "type": "object",
    "properties": {
        "ranked_cvs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["cv_id", "score", "justification"],
                "properties": {
                    "cv_id": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "justification": {"type": "string", "minLength": 10, "maxLength": 500}
                }
            }
        }
    },
    "required": ["ranked_cvs"]
}


# ==================== PATTERNS REGEX ====================

PATTERNS = {
    "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    "phone_fr": re.compile(r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$'),
    "annee": re.compile(r'^(19|20)\d{2}$'),
    "duree": re.compile(r'^\d+\s*(an|année|années|ans|mois|m)s?', re.IGNORECASE),
    "code_rome": re.compile(r'^[A-N]\d{4}$'),
    "url": re.compile(r'^https?://[^\s]+$')
}


# ==================== FONCTIONS DE NORMALISATION ====================

def normalize_text(text: str) -> str:
    """Normalise un texte (strip, espaces multiples, casse)"""
    if not isinstance(text, str):
        return ""

    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text.strip())

    return text


def normalize_competence(comp: str) -> str:
    """Normalise une compétence (majuscule initiale, acronymes en maj)"""
    comp = normalize_text(comp)

    # Acronymes connus (garder en majuscules)
    acronymes = ["SQL", "API", "AWS", "GCP", "ETL", "ML", "AI", "CI/CD", "DevOps",
                 "REST", "GraphQL", "NoSQL", "HTML", "CSS", "JS", "TS", "PHP"]

    for acronyme in acronymes:
        if comp.upper() == acronyme.upper():
            return acronyme

    # Majuscule initiale
    return comp.capitalize() if comp else ""


def normalize_langue(langue: str) -> str:
    """Normalise une langue (majuscule initiale)"""
    langue = normalize_text(langue)

    # Mapping langues courantes
    langues_mapping = {
        "anglais": "Anglais",
        "français": "Français",
        "francais": "Français",
        "espagnol": "Espagnol",
        "allemand": "Allemand",
        "italien": "Italien",
        "chinois": "Chinois",
        "arabe": "Arabe"
    }

    return langues_mapping.get(langue.lower(), langue.capitalize())


def coerce_boolean(value: Any) -> bool:
    """Convertit une valeur en booléen"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "oui", "yes", "1", "vrai"]
    if isinstance(value, (int, float)):
        return value != 0
    return False


def coerce_annee(value: Any) -> Optional[str]:
    """Convertit une année en string YYYY"""
    if isinstance(value, str):
        match = PATTERNS["annee"].match(value)
        if match:
            return value
        # Extraire l'année si présente
        match = re.search(r'(19|20)\d{2}', value)
        if match:
            return match.group(0)
    elif isinstance(value, int):
        if 1900 <= value <= 2100:
            return str(value)
    return None


# ==================== VALIDATION AVEC RÉPARATION ====================

class ValidationResult:
    """Résultat d'une validation"""

    def __init__(self, valid: bool, data: Any = None, errors: List[str] = None,
                 warnings: List[str] = None, repaired: bool = False):
        self.valid = valid
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.repaired = repaired

    def __bool__(self):
        return self.valid


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
    """Valide un JSON contre un schéma jsonschema"""
    try:
        validate(instance=data, schema=schema)
        return ValidationResult(valid=True, data=data)
    except ValidationError as e:
        return ValidationResult(valid=False, data=data, errors=[str(e)])


def repair_cv_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Répare et normalise les données d'un CV

    Returns:
        (data_réparée, liste_warnings)
    """
    warnings = []

    if "sections" not in data:
        data = {"sections": data}
        warnings.append("Structure ajoutée: sections{}")

    sections = data["sections"]

    # Normaliser les champs texte
    for field in ["titre", "resume_professionnel"]:
        if field in sections and isinstance(sections[field], str):
            sections[field] = normalize_text(sections[field])

    # Normaliser compétences
    for comp_type in ["competences_techniques", "competences_transversales"]:
        if comp_type in sections and isinstance(sections[comp_type], list):
            normalized = []
            for comp in sections[comp_type]:
                if isinstance(comp, str):
                    norm = normalize_competence(comp)
                    if norm and norm not in normalized:  # Dédupliquer
                        normalized.append(norm)
            sections[comp_type] = normalized
        else:
            sections[comp_type] = []
            warnings.append(f"Champ {comp_type} initialisé à []")

    # Normaliser langues
    if "langues" in sections and isinstance(sections["langues"], list):
        sections["langues"] = [normalize_langue(l) for l in sections["langues"] if l]
    else:
        sections["langues"] = []

    # Valider et réparer expériences
    if "experiences_professionnelles" in sections:
        exps_valides = []
        for exp in sections["experiences_professionnelles"]:
            if not isinstance(exp, dict):
                continue

            # Poste obligatoire
            if "poste" not in exp or not exp["poste"]:
                warnings.append(f"Expérience sans poste ignorée: {exp}")
                continue

            exp["poste"] = normalize_text(exp["poste"])

            # Normaliser durée
            if "duree" in exp and exp["duree"]:
                exp["duree"] = normalize_text(exp["duree"])

            # Limiter description
            if "description" in exp and len(exp.get("description", "")) > 1000:
                exp["description"] = exp["description"][:1000] + "..."
                warnings.append(f"Description tronquée pour {exp['poste']}")

            exps_valides.append(exp)

        sections["experiences_professionnelles"] = exps_valides
    else:
        sections["experiences_professionnelles"] = []

    # Valider et réparer formations
    if "formations" in sections:
        formations_valides = []
        for form in sections["formations"]:
            if not isinstance(form, dict):
                continue

            # Coercer l'année
            if "annee" in form:
                annee = coerce_annee(form["annee"])
                if annee:
                    form["annee"] = annee
                else:
                    warnings.append(f"Année invalide ignorée: {form['annee']}")
                    del form["annee"]

            formations_valides.append(form)

        sections["formations"] = formations_valides
    else:
        sections["formations"] = []

    # Autres listes
    for field in ["certifications", "projets"]:
        if field not in sections or not isinstance(sections[field], list):
            sections[field] = []

    # Mobilité
    if "mobilite" not in sections or not isinstance(sections["mobilite"], dict):
        sections["mobilite"] = {
            "permis_conduire": False,
            "disponibilite_geographique": ""
        }
    else:
        mob = sections["mobilite"]
        if "permis_conduire" in mob:
            mob["permis_conduire"] = coerce_boolean(mob["permis_conduire"])
        else:
            mob["permis_conduire"] = False

        if "disponibilite_geographique" not in mob:
            mob["disponibilite_geographique"] = ""

    return data, warnings


def repair_must_have_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Répare les données must-have

    Returns:
        (data_réparée, liste_warnings)
    """
    warnings = []

    if "must_have" not in data:
        # Essayer de deviner la structure
        if isinstance(data, list):
            data = {"must_have": data}
            warnings.append("Structure list → dict{must_have}")
        else:
            data = {"must_have": []}
            warnings.append("must_have manquant, initialisé à []")

    must_have = data["must_have"]

    if not isinstance(must_have, list):
        warnings.append(f"must_have n'est pas une liste: {type(must_have)}")
        data["must_have"] = []
        return data, warnings

    # Normaliser et filtrer
    cleaned = []
    for item in must_have:
        if not isinstance(item, str):
            continue

        item = normalize_text(item)

        # Filtrer trop courts/longs
        if len(item) < 3:
            warnings.append(f"Critère trop court ignoré: '{item}'")
            continue

        if len(item) > 200:
            item = item[:200]
            warnings.append(f"Critère tronqué à 200 caractères")

        if item not in cleaned:  # Dédupliquer
            cleaned.append(item)

    data["must_have"] = cleaned[:15]  # Max 15 critères

    if len(must_have) > 15:
        warnings.append(f"Trop de critères ({len(must_have)}), limité à 15")

    return data, warnings


def repair_reranking_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Répare les données de re-ranking

    Returns:
        (data_réparée, liste_warnings)
    """
    warnings = []

    if "ranked_cvs" not in data:
        # Essayer de deviner
        if isinstance(data, list):
            data = {"ranked_cvs": data}
            warnings.append("Structure list → dict{ranked_cvs}")
        else:
            data = {"ranked_cvs": []}
            warnings.append("ranked_cvs manquant")

    ranked = data["ranked_cvs"]

    if not isinstance(ranked, list):
        warnings.append(f"ranked_cvs n'est pas une liste: {type(ranked)}")
        data["ranked_cvs"] = []
        return data, warnings

    # Valider chaque CV
    cleaned = []
    for cv in ranked:
        if not isinstance(cv, dict):
            continue

        # Champs obligatoires
        if "cv_id" not in cv or not cv["cv_id"]:
            warnings.append(f"CV sans cv_id ignoré: {cv}")
            continue

        if "score" not in cv:
            warnings.append(f"CV {cv['cv_id']} sans score, mis à 0.5")
            cv["score"] = 0.5

        # Normaliser score
        try:
            score = float(cv["score"])
            cv["score"] = max(0.0, min(1.0, score))  # Capping
        except (ValueError, TypeError):
            warnings.append(f"Score invalide pour {cv['cv_id']}: {cv['score']}")
            cv["score"] = 0.5

        # Justification
        if "justification" not in cv or not cv["justification"]:
            cv["justification"] = "Pas de justification fournie"
            warnings.append(f"Justification manquante pour {cv['cv_id']}")
        else:
            cv["justification"] = normalize_text(cv["justification"])
            # Limiter taille
            if len(cv["justification"]) > 500:
                cv["justification"] = cv["justification"][:500] + "..."
                warnings.append(f"Justification tronquée pour {cv['cv_id']}")

        cleaned.append(cv)

    data["ranked_cvs"] = cleaned

    return data, warnings


# ==================== FONCTION PRINCIPALE ====================

def validate_and_repair(
    data: Any,
    schema_type: str,
    max_attempts: int = 3
) -> ValidationResult:
    """
    Valide et répare les données contre un schéma

    Args:
        data: Données à valider (dict ou JSON string)
        schema_type: "cv", "must_have", ou "reranking"
        max_attempts: Nombre max de tentatives de réparation

    Returns:
        ValidationResult
    """
    # Parser JSON si string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                data=None,
                errors=[f"JSON invalide: {str(e)}"]
            )

    # Sélectionner schéma et fonction de réparation
    schemas = {
        "cv": (SCHEMA_CV, repair_cv_data),
        "must_have": (SCHEMA_MUST_HAVE, repair_must_have_data),
        "reranking": (SCHEMA_RERANKING, repair_reranking_data)
    }

    if schema_type not in schemas:
        return ValidationResult(
            valid=False,
            data=None,
            errors=[f"Type de schéma inconnu: {schema_type}"]
        )

    schema, repair_fn = schemas[schema_type]

    # Tentative de validation directe
    result = validate_json_schema(data, schema)
    if result.valid:
        return ValidationResult(valid=True, data=data)

    # Tentatives de réparation
    warnings = []
    for attempt in range(max_attempts):
        data, repair_warnings = repair_fn(data)
        warnings.extend(repair_warnings)

        # Re-valider
        result = validate_json_schema(data, schema)
        if result.valid:
            return ValidationResult(
                valid=True,
                data=data,
                warnings=warnings,
                repaired=True
            )

    # Échec après max_attempts
    return ValidationResult(
        valid=False,
        data=data,
        errors=result.errors,
        warnings=warnings
    )


# ==================== CHECKS NON-IA ====================

def check_cv_size(cv_text: str, max_size_kb: int = 500) -> Tuple[bool, Optional[str]]:
    """Vérifie la taille d'un CV (limite spam/abus)"""
    size_kb = len(cv_text.encode('utf-8')) / 1024
    if size_kb > max_size_kb:
        return False, f"CV trop volumineux: {size_kb:.1f} KB (max {max_size_kb} KB)"
    return True, None


def check_offre_size(offre_text: str, max_size_kb: int = 200) -> Tuple[bool, Optional[str]]:
    """Vérifie la taille d'une offre"""
    size_kb = len(offre_text.encode('utf-8')) / 1024
    if size_kb > max_size_kb:
        return False, f"Offre trop volumineuse: {size_kb:.1f} KB (max {max_size_kb} KB)"
    return True, None


def check_min_content(text: str, min_words: int = 50) -> Tuple[bool, Optional[str]]:
    """Vérifie qu'il y a un minimum de contenu"""
    words = len(text.split())
    if words < min_words:
        return False, f"Contenu insuffisant: {words} mots (min {min_words})"
    return True, None


def check_email_valid(email: str) -> bool:
    """Vérifie si un email est valide"""
    return bool(PATTERNS["email"].match(email))


def check_phone_valid(phone: str) -> bool:
    """Vérifie si un téléphone français est valide"""
    return bool(PATTERNS["phone_fr"].match(phone))


def check_code_rome_valid(code: str) -> bool:
    """Vérifie si un code ROME est valide"""
    return bool(PATTERNS["code_rome"].match(code))


# ==================== TESTS ====================

if __name__ == "__main__":
    print("🧪 Tests du module de validation\n")
    print("=" * 60)

    # Test 1: Validation CV valide
    print("\n📋 Test 1: CV valide")
    cv_data = {
        "sections": {
            "titre": "Data Scientist",
            "resume_professionnel": "Expert en ML",
            "competences_techniques": ["Python", "SQL"],
            "competences_transversales": ["Leadership"],
            "langues": ["Anglais"],
            "experiences_professionnelles": [
                {"poste": "Data Scientist", "duree": "3 ans"}
            ],
            "formations": [],
            "certifications": [],
            "projets": [],
            "mobilite": {"permis_conduire": True, "disponibilite_geographique": "IDF"}
        }
    }
    result = validate_and_repair(cv_data, "cv")
    print(f"✅ Valide: {result.valid}" if result else f"❌ Invalide: {result.errors}")

    # Test 2: CV avec réparation
    print("\n🔧 Test 2: CV nécessitant réparation")
    cv_broken = {
        "titre": "Data Scientist",  # Manque wrapper "sections"
        "competences_techniques": ["python", "sql", "python"],  # Doublons + casse
        "experiences_professionnelles": [
            {"poste": "Data Scientist"}
        ]
    }
    result = validate_and_repair(cv_broken, "cv")
    print(f"✅ Réparé: {result.valid}, Warnings: {len(result.warnings)}" if result else f"❌ Échec")
    if result.warnings:
        for w in result.warnings[:3]:
            print(f"  ⚠️ {w}")

    # Test 3: Must-have
    print("\n🎯 Test 3: Must-have")
    must_have = {"must_have": ["Python", "SQL", "3 ans d'expérience"]}
    result = validate_and_repair(must_have, "must_have")
    print(f"✅ Valide: {result.valid}" if result else f"❌ Invalide")

    # Test 4: Checks non-IA
    print("\n🔍 Test 4: Checks non-IA")
    print(f"  Email valide: {check_email_valid('test@example.com')}")
    print(f"  Email invalide: {check_email_valid('invalid-email')}")
    print(f"  Code ROME valide: {check_code_rome_valid('M1805')}")
    print(f"  Code ROME invalide: {check_code_rome_valid('Z9999')}")

    cv_text = "CV " * 100
    ok, msg = check_cv_size(cv_text)
    print(f"  CV size check: {ok}")

    ok, msg = check_min_content("Trop court")
    print(f"  Min content check: {ok} - {msg}")

    print("\n✅ Tests terminés!")
