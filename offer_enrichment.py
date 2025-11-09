"""
Module d'enrichissement intelligent des offres d'emploi
Utilise GPT-4o mini pour proposer des compléments pertinents
"""

import json
from typing import Dict, Any
from jsonschema import validate, ValidationError
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialiser le client OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_ENRICHISSEMENT = """Tu es un expert en recrutement tech avec une connaissance approfondie du marché français.

🎯 MISSION: Analyser l'offre d'emploi fournie et PROPOSER des compléments intelligents pour la rendre plus complète et attractive.

📋 CONTEXTE:
- Métier cible: {metier_label}
- Offre d'emploi actuelle (JSON):
{offre_json}

🔍 ANALYSE REQUISE:
1. Examine ATTENTIVEMENT tous les éléments déjà présents dans l'offre (compétences techniques, outils, langages, certifications, missions, formations, expériences)
2. Identifie les MANQUES ou zones d'amélioration par rapport aux standards du marché pour ce type de poste
3. Évalue le niveau de séniorité attendu (junior/confirmé/senior) basé sur l'expérience requise et les responsabilités
4. Prends en compte l'écosystème technologique cohérent (ex: si Python → proposer Django/Flask, pandas, pytest, etc.)

💡 PROPOSITIONS À GÉNÉRER:

**Compétences techniques:**
- Type "must": compétences ESSENTIELLES manquantes pour le poste (ex: pour un Dev Python senior → architecture, design patterns)
- Type "nice": compétences qui renforcent le profil mais pas bloquantes (ex: connaissance d'un cloud spécifique)
- Justification: Explique POURQUOI cette compétence est pertinente pour CE poste spécifique

**Outils:**
- Outils techniques cohérents avec l'écosystème déjà mentionné (IDE, CI/CD, monitoring, etc.)
- Privilégie les outils standards du marché français
- Justification: Lien avec les missions et technologies mentionnées

**Langages de programmation:**
- Langages complémentaires pertinents (ex: si backend Python → SQL, si data science → R)
- Ne propose QUE si vraiment utile pour les missions décrites
- Justification: Usage concret dans le contexte du poste

**Certifications:**
- Certifications reconnues et valorisées sur le marché français
- Alignées avec les technologies mentionnées (ex: AWS Certified si cloud AWS, PSM si méthodes agiles)
- Justification: Valeur ajoutée concrète pour le poste

**Missions complémentaires:**
- Missions/responsabilités manquantes typiques pour ce niveau de séniorité
- Alignées avec les compétences et outils déjà mentionnés
- Formulation claire et actionnable
- Justification: Pourquoi cette mission enrichit le périmètre du poste

**Questions de clarification:**
- 3-5 questions précises pour aider le RH à affiner l'offre
- Focus sur les zones d'ambiguïté ou informations manquantes importantes
- Ex: "Quelle est la taille de l'équipe tech?", "Quel est le niveau d'autonomie attendu?", "Y a-t-il une astreinte?"

📊 COVERAGE SCORE (0-100):
Estime le degré de complétude de l'offre AVANT tes propositions:
- 90-100: Offre très complète, peu de manques
- 70-89: Offre correcte, quelques améliorations possibles
- 50-69: Offre incomplète, plusieurs éléments manquants
- 0-49: Offre très lacunaire, beaucoup d'éléments à ajouter

⚠️ RÈGLES STRICTES:
- Retourne UNIQUEMENT un JSON valide (pas de texte avant/après)
- Ne JAMAIS supprimer ou modifier les éléments déjà présents
- Chaque proposition doit avoir une justification ("rationale") de minimum 20 caractères
- Reste RÉALISTE: pas de technologies obscures ou trop rares
- Adapte tes propositions au NIVEAU DE SÉNIORITÉ du poste
- Si l'offre est déjà très complète, propose peu de choses (qualité > quantité)
- Utilise la terminologie française (ex: "conception", "développement", "déploiement")

🎯 TON OBJECTIF: Aider le RH à créer une offre claire, complète et attractive qui attirera les bons candidats tout en restant réaliste.
"""

ENRICH_SCHEMA = {
    "type": "object",
    "required": ["propositions", "coverage_score"],
    "properties": {
        "coverage_score": {"type": "number", "minimum": 0, "maximum": 100},
        "propositions": {
            "type": "object",
            "required": [
                "competences", "outils", "langages",
                "certifications", "missions", "questions_clarification"
            ],
            "properties": {
                "competences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type", "source", "rationale"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "type": {"type": "string", "enum": ["must", "nice"]},
                            "source": {"type": "string"},
                            "rationale": {"type": "string", "minLength": 10}
                        }
                    }
                },
                "outils": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "rationale"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "rationale": {"type": "string", "minLength": 10}
                        }
                    }
                },
                "langages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "rationale"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "rationale": {"type": "string", "minLength": 10}
                        }
                    }
                },
                "certifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "rationale"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "rationale": {"type": "string", "minLength": 10}
                        }
                    }
                },
                "missions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["text", "rationale"],
                        "properties": {
                            "text": {"type": "string", "minLength": 10},
                            "rationale": {"type": "string", "minLength": 10}
                        }
                    }
                },
                "questions_clarification": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 10}
                }
            }
        }
    },
    "additionalProperties": False
}


async def enrich_offer_intelligently(offre_json: Dict[str, Any], metier_label: str) -> Dict[str, Any]:
    """
    Enrichit une offre d'emploi avec des propositions IA

    Args:
        offre_json: Offre d'emploi parsée (dict)
        metier_label: Libellé du métier cible

    Returns:
        Dict avec propositions et coverage_score

    Raises:
        ValueError: Si validation échoue après 3 tentatives
    """
    user_content = PROMPT_ENRICHISSEMENT.format(
        metier_label=metier_label,
        offre_json=json.dumps(offre_json, ensure_ascii=False, indent=2)
    )

    # Première tentative
    # GPT-5 mini ne supporte PAS le paramètre temperature (erreur 400 si fourni)
    try:
        response = await client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Tu réponds UNIQUEMENT en JSON valide conforme au schéma demandé."},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )

        txt = response.choices[0].message.content
        print(f"📥 Réponse LLM (aperçu 200 chars): {txt[:200]}...")

        # Tentatives de validation avec réparation
        for attempt in range(3):
            try:
                data = json.loads(txt)
                validate(instance=data, schema=ENRICH_SCHEMA)
                print(f"✅ Validation réussie (tentative {attempt + 1})")
                return data
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"⚠️ Tentative {attempt + 1}/3 échouée: {str(e)[:100]}")

                if attempt < 2:  # Pas de réparation au 3e essai
                    # Demander une réparation
                    repair_response = await client.chat.completions.create(
                        model="gpt-5-mini",
                        messages=[
                            {"role": "system", "content": "Tu réponds UNIQUEMENT en JSON valide conforme au schéma demandé."},
                            {"role": "user", "content": f"""Corrige ce JSON pour respecter STRICTEMENT le schéma, sans changer le fond:

JSON à corriger:
{txt}

Erreur:
{str(e)}

Schéma attendu:
{json.dumps(ENRICH_SCHEMA, indent=2)}

Retourne UNIQUEMENT le JSON corrigé, sans texte additionnel."""}
                        ],
                        response_format={"type": "json_object"}
                    )
                    txt = repair_response.choices[0].message.content
                    print(f"🔧 Réparation tentée (aperçu): {txt[:150]}...")

        raise ValueError("Enrichissement: JSON non conforme après 3 tentatives")

    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement: {e}")
        raise


def merge_enrichment(offre_json: Dict[str, Any], enrichment: Dict[str, Any], selections: Dict[str, list]) -> Dict[str, Any]:
    """
    Fusionne les propositions acceptées dans l'offre

    Args:
        offre_json: Offre originale
        enrichment: Résultat de enrich_offer_intelligently
        selections: Dict des propositions acceptées par type
            Ex: {"competences": [0, 2], "outils": [1], ...}

    Returns:
        Offre enrichie
    """
    import copy
    offre_enrichie = copy.deepcopy(offre_json)  # Deep copy pour éviter mutations
    propositions = enrichment["propositions"]

    # Fusionner les compétences (MUST ET NICE)
    if "competences" in selections and "sections" in offre_enrichie:
        if "competences_techniques" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["competences_techniques"] = []

        for idx in selections["competences"]:
            comp = propositions["competences"][idx]
            comp_name = comp["name"]

            # Ajouter si pas déjà présent (éviter doublons)
            if comp_name not in offre_enrichie["sections"]["competences_techniques"]:
                offre_enrichie["sections"]["competences_techniques"].append(comp_name)
                print(f"✅ Compétence ajoutée: {comp_name} ({comp['type']})")

    # Fusionner les outils
    if "outils" in selections and "sections" in offre_enrichie:
        if "outils" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["outils"] = []

        for idx in selections["outils"]:
            outil = propositions["outils"][idx]
            outil_name = outil["name"]

            if outil_name not in offre_enrichie["sections"]["outils"]:
                offre_enrichie["sections"]["outils"].append(outil_name)
                print(f"✅ Outil ajouté: {outil_name}")

    # Fusionner les langages
    if "langages" in selections and "sections" in offre_enrichie:
        if "langages" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["langages"] = []

        for idx in selections["langages"]:
            lang = propositions["langages"][idx]
            lang_name = lang["name"]

            if lang_name not in offre_enrichie["sections"]["langages"]:
                offre_enrichie["sections"]["langages"].append(lang_name)
                print(f"✅ Langage ajouté: {lang_name}")

    # Fusionner les certifications
    if "certifications" in selections and "sections" in offre_enrichie:
        if "certifications" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["certifications"] = []

        for idx in selections["certifications"]:
            cert = propositions["certifications"][idx]
            cert_name = cert["name"]

            if cert_name not in offre_enrichie["sections"]["certifications"]:
                offre_enrichie["sections"]["certifications"].append(cert_name)
                print(f"✅ Certification ajoutée: {cert_name}")

    # Fusionner les missions
    if "missions" in selections and "sections" in offre_enrichie:
        if "responsabilites" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["responsabilites"] = []

        for idx in selections["missions"]:
            mission = propositions["missions"][idx]
            mission_text = mission["text"]

            if mission_text not in offre_enrichie["sections"]["responsabilites"]:
                offre_enrichie["sections"]["responsabilites"].append(mission_text)
                print(f"✅ Mission ajoutée: {mission_text[:50]}...")

    return offre_enrichie


def integrate_question_responses(offre_data: Dict[str, Any], questions_responses: Dict[str, str]) -> Dict[str, Any]:
    """
    Intègre les réponses aux questions de clarification dans l'offre JSON

    Args:
        offre_data: Données de l'offre actuelle
        questions_responses: Dictionnaire {question: réponse}

    Returns:
        Offre enrichie avec les réponses intégrées
    """
    import copy
    offre_enrichie = copy.deepcopy(offre_data)

    # Créer une section "informations_complementaires" si elle n'existe pas
    if "sections" in offre_enrichie:
        if "informations_complementaires" not in offre_enrichie["sections"]:
            offre_enrichie["sections"]["informations_complementaires"] = {}

        # Intégrer chaque réponse
        for question, response in questions_responses.items():
            if response and response.strip():  # Ignorer les réponses vides
                # Créer une clé normalisée à partir de la question
                # Ex: "Quelle est la taille de l'équipe ?" -> "taille_equipe"
                key = question.lower().replace("?", "").replace("'", "").replace(" ", "_")
                key = key[:50]  # Limiter la longueur

                offre_enrichie["sections"]["informations_complementaires"][key] = {
                    "question": question,
                    "reponse": response.strip()
                }
                print(f"✅ Réponse intégrée: {question[:50]}... -> {response[:50]}...")

    return offre_enrichie


# Test simple si exécuté directement
if __name__ == "__main__":
    import asyncio

    async def test():
        offre_test = {
            "sections": {
                "titre": "Développeur Python Junior",
                "competences_techniques": ["Python", "SQL"],
                "experiences_requises": "1 an minimum"
            }
        }

        result = await enrich_offer_intelligently(offre_test, "Développeur Python")
        print("\n✅ Résultat de l'enrichissement:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())
