# -*- coding: utf-8 -*-
"""
Module de parsing de CVs - Logique pure sans dépendances Streamlit
Extraction texte (PDF/DOCX) + Parsing LLM + Nettoyage JSON
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import fitz  # PyMuPDF
import docx2txt
from openai import OpenAI
from dotenv import load_dotenv
import logging

from lib.models import CV, CVParseResult

# Charger variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# ==================== PROMPTS ====================

PROMPT_CV_EXTRACTION = """
Tu es un expert en ressources humaines avec une attention méticuleuse aux détails. Tu reçois un CV sous forme de texte brut.

**PROCESSUS EN 3 ÉTAPES OBLIGATOIRES :**

1. **EXTRACTION EXHAUSTIVE** : Lis attentivement TOUT le CV et identifie TOUTES les informations pertinentes, sans rien omettre. N'oublie aucun détail, même mineur.

2. **VÉRIFICATION APPROFONDIE** : Relis le CV une seconde fois pour t'assurer que :
   - Toutes les compétences techniques mentionnées sont bien extraites (frameworks, langages, outils, technologies)
   - Toutes les expériences professionnelles sont complètes avec leurs missions détaillées
   - Tous les diplômes et certifications sont capturés
   - Toutes les langues mentionnées sont incluses
   - Aucune information importante n'a été oubliée

3. **STRUCTURATION JSON** : Génère un JSON strictement valide avec les informations vérifiées.

Ta tâche est d'extraire uniquement les informations suivantes et de répondre uniquement avec un JSON strictement valide, sans aucune explication ou texte supplémentaire.

Structure à respecter :

{
  "identite": {
    "nom": "",
    "prenom": "",
    "email": "",
    "telephone": "",
    "adresse": "",
    "linkedin": "",
    "autres_reseaux": []
  },
  "titre": "",
  "resume_professionnel": "",
  "competences_techniques": [],
  "competences_transversales": [],
  "langues":[],
  "experiences_professionnelles": [
    {
      "poste": "",
      "entreprise": "",
      "lieu": "",
      "date_debut": "",
      "date_fin": "",
      "durée": "",
      "missions": []
    }
  ],
  "formations": [
    {
      "diplome": "",
      "ecole": "",
      "annee_obtention": "",
      "niveau": "",
      "specialite": ""
    }
    ],
  "certifications": [
    {
      "nom": "",
      "organisme": "",
      "annee": ""
    }
  ],
  "projets": [
    {
      "titre": "",
      "description": "",
      "technologies": []
    }
  ],
  "mobilite": {
    "permis_conduire": false,
    "disponibilite_geographique": ""
  },
  "autres": {
    "loisirs": [],
    "engagements": []
  }
}

**RÈGLES D'EXTRACTION STRICTES :**
- Respecte strictement cette structure, et n'ajoute rien.
- Pour des langues, seule la langue a mentionnee sans avoir plus de details.
- Pour les formations, seul le dernier diplôme (le plus récent) doit inclure les champs "niveau" (ex. : Bac+3, Bac+5) et "specialite" (ex. : Informatique, Gestion...).
- Si une information n'est pas trouvée, laisse la chaîne vide ("") ou une liste vide ([]), mais ne supprime aucun champ.
- La durée d'une expérience doit être indiquée dans le champ "durée", par exemple : "2 mois", "1 an et demi", etc.
- La réponse doit être *strictement du JSON*, sans aucun texte avant ni après.

**RAPPEL FINAL** : Avant de répondre, vérifie une dernière fois que tu as extrait TOUTES les informations du CV, sans aucune omission. L'exhaustivité est cruciale.
"""

# ==================== EXTRACTION TEXTE ====================

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrait le texte d'un fichier PDF avec PyMuPDF

    Args:
        pdf_path: Chemin vers le fichier PDF

    Returns:
        Texte extrait du PDF
    """
    import logging
    logger = logging.getLogger(__name__)
    
    pdf_path = str(pdf_path)
    logger.info(f"📄 Extraction PDF: {Path(pdf_path).name}")
    
    if not Path(pdf_path).exists():
        logger.error(f"❌ Fichier PDF introuvable: {pdf_path}")
        raise FileNotFoundError(f"Fichier PDF introuvable: {pdf_path}")
    
    file_size = Path(pdf_path).stat().st_size
    logger.info(f"  📏 Taille: {file_size} bytes")

    try:
        # Charger le PDF en mémoire pour éviter les problèmes de handle fermé
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        logger.info(f"  ✅ {len(pdf_bytes)} bytes lus en mémoire")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        logger.info(f"  📖 PDF ouvert: {doc.page_count} pages")
        
        try:
            text = "".join(page.get_text() for page in doc)
            logger.info(f"  ✅ {len(text)} caractères extraits")
            return text
        finally:
            doc.close()
    except Exception as e:
        logger.error(f"  ❌ Erreur: {type(e).__name__}: {str(e)}")
        raise


def extract_text_from_docx(docx_path: str) -> str:
    """
    Extrait le texte d'un fichier DOCX

    Args:
        docx_path: Chemin vers le fichier DOCX

    Returns:
        Texte extrait du DOCX
    """
    return docx2txt.process(docx_path)


def extract_text_from_file(file_path: str) -> str:
    """
    Extrait le texte d'un fichier (PDF ou DOCX)

    Args:
        file_path: Chemin vers le fichier

    Returns:
        Texte extrait

    Raises:
        ValueError: Si le format de fichier n'est pas supporté
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Format de fichier non supporté: {ext}. Accepté: .pdf, .docx")


# ==================== NETTOYAGE JSON ====================

def clean_json_text(text: str) -> str:
    """
    Nettoie le texte JSON généré par le LLM
    Supprime les balises markdown et normalise les guillemets

    Args:
        text: Texte JSON brut du LLM

    Returns:
        Texte JSON nettoyé
    """
    # Supprime les balises de code Markdown (```json ... ```)
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```", "", text)

    # Remplace les guillemets typographiques par des guillemets standards
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")

    return text.strip()


# ==================== PARSING LLM ====================

def parse_cv_with_llm(
    cv_text: str,
    model: str = "gpt-5-mini",
    openai_client: Optional[OpenAI] = None
) -> Dict[str, Any]:
    """
    Parse un CV avec le LLM

    Args:
        cv_text: Texte brut du CV
        model: Modèle LLM à utiliser
        openai_client: Client OpenAI (créé automatiquement si None)

    Returns:
        Dict contenant les données structurées du CV

    Raises:
        ValueError: Si la réponse LLM n'est pas un JSON valide
    """
    # Créer client si non fourni
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")
        # PAS DE TIMEOUT - laissons l'API prendre son temps
        openai_client = OpenAI(api_key=api_key)

    # Appel LLM avec logs détaillés
    import time
    api_call_start = time.time()
    logger.info(f"[DEBUG] Appel API OpenAI démarré à {time.strftime('%H:%M:%S')}")
    logger.info(f"[DEBUG] Modèle: {model}")
    logger.info(f"[DEBUG] Input tokens estimés: {(len(PROMPT_CV_EXTRACTION) + len(cv_text)) // 4}")

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant qui analyse des CV. Tu réponds UNIQUEMENT en JSON valide."
            },
            {
                "role": "user",
                "content": f"{PROMPT_CV_EXTRACTION}\n\n{cv_text}"
            }
        ],
        response_format={"type": "json_object"}
        # Pas de temperature pour GPT-5-mini (valeur par défaut 1.0)
    )

    api_call_end = time.time()
    api_duration = api_call_end - api_call_start

    # Extraire les métadonnées de la réponse
    usage = response.usage if hasattr(response, 'usage') else None

    logger.info(f"[DEBUG] Réponse reçue après {api_duration:.3f}s")
    if usage:
        logger.info(f"[DEBUG] Usage tokens: input={usage.prompt_tokens}, output={usage.completion_tokens}, total={usage.total_tokens}")

    # Extraire et nettoyer la réponse
    result_text = response.choices[0].message.content
    logger.info(f"[DEBUG] Longueur réponse: {len(result_text)} caractères")
    cleaned_result = clean_json_text(result_text)

    # Parser JSON
    try:
        parsed_data = json.loads(cleaned_result)
        return parsed_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse LLM n'est pas un JSON valide: {str(e)}\nRéponse brute: {cleaned_result[:500]}")


# ==================== FONCTION PRINCIPALE ====================

def parse_cv_from_file(
    file_path: str,
    model: str = "gpt-5-mini",
    openai_client: Optional[OpenAI] = None
) -> CVParseResult:
    """
    Parse un CV complet (extraction texte + LLM + validation)

    Args:
        file_path: Chemin vers le fichier CV (PDF ou DOCX)
        model: Modèle LLM à utiliser
        openai_client: Client OpenAI (créé automatiquement si None)

    Returns:
        CVParseResult avec succès/échec et données
    """
    import time

    filename = Path(file_path).name
    start_time = time.time()

    try:
        # Étape 1: Extraction texte
        extraction_start = time.time()
        cv_text = extract_text_from_file(file_path)
        extraction_duration = time.time() - extraction_start

        # Étape 2: Parsing LLM
        parsing_start = time.time()
        parsed_data = parse_cv_with_llm(cv_text, model, openai_client)
        parsing_duration = time.time() - parsing_start

        # Étape 3: Validation avec Pydantic
        cv_data = CV(cv=filename, **parsed_data)

        total_duration = time.time() - start_time

        return CVParseResult(
            filename=filename,
            success=True,
            data=cv_data,
            error=None,
            timings={
                "extraction": round(extraction_duration, 3),
                "parsing": round(parsing_duration, 3),
                "total": round(total_duration, 3)
            }
        )

    except Exception as e:
        total_duration = time.time() - start_time

        return CVParseResult(
            filename=filename,
            success=False,
            data=None,
            error=str(e),
            timings={
                "total": round(total_duration, 3),
                "error": True
            }
        )


# ==================== UTILITAIRES ====================

def get_openai_client() -> OpenAI:
    """
    Crée et retourne un client OpenAI configuré

    Returns:
        Client OpenAI

    Raises:
        ValueError: Si OPENAI_API_KEY n'est pas définie
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")

    # PAS DE TIMEOUT - le timeout est géré par asyncio.wait_for() dans parallel_engine
    return OpenAI(api_key=api_key)
