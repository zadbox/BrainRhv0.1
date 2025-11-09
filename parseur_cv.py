"""
⚠️ WARNING - SCRIPT LEGACY
Ce script est conservé pour compatibilité mais ne devrait plus être utilisé directement.
Les fonctions utilitaires (extract_text_from_pdf, analyze_text, etc.) restent utilisables.

Pour le parsing de CVs dans la nouvelle architecture, utilisez:
- API: POST /api/v1/projects/{project_id}/cvs/upload
- Service: brainrh.services.cv_service.CVService

Les CVs sont maintenant stockés dans: enterprises/{id}/projects/{id}/cvs_parsed/
"""

import os
import json
import fitz # PyMuPDF
import re
import docx2txt
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# 1. Configuration de l'API
from openai import OpenAI

# Récupérer la clé API depuis les variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY non trouvée dans les variables d'environnement")

client = OpenAI(api_key=OPENAI_API_KEY)

# 2. Prompt global pour extraire toutes les infos du CV
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

# 3.1. Extraire le texte brut du PDF
def extract_text_from_pdf(pdf_path):
    #la librairie PyMuPDF (fitz) pour extraire le texte de toutes les pages du PDF
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text
# 3.2. Extraction texte du DOCX
def extract_text_from_docx(docx_path):
    return docx2txt.process(docx_path)

# 4. Analyse d'un texte avec le prompt global
def analyze_text(text, prompt_text, model_name="gpt-5-mini"):
    """Analyse un texte avec OpenAI en utilisant response_format JSON"""
    import time

    api_call_start = time.time()
    print(f"[DEBUG] Appel API OpenAI démarré à {time.strftime('%H:%M:%S')}")
    print(f"[DEBUG] Modèle: {model_name}")
    print(f"[DEBUG] Input tokens estimés: {(len(prompt_text) + len(text)) // 4}")

    # Charger le seed depuis la config pour le déterminisme
    from config_loader import get_config
    seed = get_config().get("llm", {}).get("seed", 42)
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Tu es un assistant qui analyse des CV. Tu réponds UNIQUEMENT en JSON valide."},
            {"role": "user", "content": f"{prompt_text}\n\n{text}"}
        ],
        response_format={"type": "json_object"},
        seed=seed  # Déterminisme: même seed = mêmes résultats
        # GPT-5 mini: pas de paramètre temperature (erreur 400 si fourni)
        # PAS DE TIMEOUT - laissons l'API prendre son temps pour diagnostiquer
    )

    api_call_end = time.time()
    api_duration = api_call_end - api_call_start

    # Extraire les métadonnées de la réponse
    usage = response.usage if hasattr(response, 'usage') else None

    print(f"[DEBUG] Réponse reçue après {api_duration:.3f}s")
    if usage:
        print(f"[DEBUG] Usage tokens: input={usage.prompt_tokens}, output={usage.completion_tokens}, total={usage.total_tokens}")

    content = response.choices[0].message.content
    print(f"[DEBUG] Longueur réponse: {len(content)} caractères")

    return content


# 5. Nettoyage json
# ce script ajoute pour corriger la generation d'une output sous forme json
# consiste a nettoyer le texte avent de le convertir en objet json
def clean_json_text(text):
    # Supprime les balises de code Markdown éventuelles (```json ... ```)
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```", "", text)
    # Optionnel : remplace les guillemets typographiques par des guillemets simples
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return text.strip()

#offre to json
job_text = """
Titre du poste : Data Scientist Junior
Expérience requise : 1 an minimum
Formation : Bac+5 en Data Science

Compétences techniques :
Python (Pandas, NumPy, Scikit-learn)
SQL
Machine Learning (régression, classification)
Visualisation de données (Matplotlib, Seaborn)
Utilisation de Jupyter Notebook

Compétences transversales :
Esprit analytique
Capacité à vulgariser des concepts techniques
Travail en équipe
Autonomie

Langues :
Français 
Anglais 
"""
PROMPT_JOB_EXTRACTION = """
Tu es un expert en ressources humaines avec une attention méticuleuse aux détails. Tu reçois une offre d'emploi sous forme de texte brut.

**PROCESSUS EN 3 ÉTAPES OBLIGATOIRES :**

1. **EXTRACTION EXHAUSTIVE** : Lis attentivement TOUTE l'offre d'emploi et identifie TOUTES les informations pertinentes, sans rien omettre. N'oublie aucun détail, même mineur (compétences techniques, soft skills, exigences de formation, expérience requise, langues, certifications, etc.).

2. **VÉRIFICATION APPROFONDIE** : Relis l'offre une seconde fois pour t'assurer que :
   - Toutes les compétences techniques requises sont bien extraites (technologies, outils, frameworks, logiciels)
   - Toutes les compétences transversales (soft skills) sont capturées
   - Les exigences d'expérience (poste et durée) sont complètes
   - Les exigences de formation (niveau et spécialité) sont détaillées
   - Toutes les langues requises sont incluses
   - Toutes les certifications souhaitées sont mentionnées
   - Les éléments de mobilité (permis, localisation) sont notés
   - Aucune information importante n'a été oubliée

3. **STRUCTURATION JSON** : Génère un JSON strictement valide avec les informations vérifiées.

**STRUCTURE JSON À RESPECTER :**

{
    "sections":{
      "titre": "",
      "competences_techniques": [],
      "competences_transversales":[],
      "langues": [],

    "experiences_professionnelles": [
        {
          "poste": "",
          "duree": ""                    // Exemple : "3 ans minimum", "2-5 ans"
        }
      ],

      "formations": [
        {
          "niveau": "",                   // Ex : Bac+5, Master, Licence
          "specialite": ""                // Ex : Data Science, Informatique
        }
      ],

      "certifications": [],              // Noms de certifications éventuelles (ex: PMP, AWS, ITIL)
      "projets": [],                     // Domaines ou types de projets mentionnés

      "mobilite": {
        "permis_conduire": false,
        "disponibilite_geographique": ""
      }
    }
}

**RÈGLES D'EXTRACTION STRICTES :**
- Le titre de l'offre est lui-même le poste de l'expérience professionnelle
- Respecte strictement cette structure, et n'ajoute rien
- Si une information n'est pas trouvée, laisse la chaîne vide ("") ou une liste vide ([]), mais ne supprime aucun champ
- Ne rajoute aucun commentaire autour du JSON
- La réponse doit être *strictement du JSON*, sans aucun texte avant ni après

**RAPPEL FINAL** : Avant de répondre, vérifie une dernière fois que tu as extrait TOUTES les informations de l'offre d'emploi, sans aucune omission. L'exhaustivité est cruciale pour un matching précis.
"""

#   Script principal
def main():
    """
    ⚠️ DEPRECATED - Ce script écrit dans cv_json/ (structure legacy)

    Pour la nouvelle architecture, utilisez l'API:
    POST /api/v1/projects/{project_id}/cvs/upload

    Ce script est conservé uniquement pour tests/développement.
    """
    print("⚠️  WARNING: Script legacy - Les CVs devraient être uploadés via l'API")
    print("   Nouvelle structure: enterprises/{id}/projects/{id}/cvs_parsed/")
    print()

    # Configuration des répertoires via variables d'environnement
    cv_folder = os.getenv("CV_INPUT_FOLDER", "cv_input")
    json_output_folder = os.getenv("CV_JSON_FOLDER", "cv_json")
    offre_output_folder = os.getenv("OFFRES_FOLDER", "offres")

    # Créer les dossiers s'ils n'existent pas
    Path(json_output_folder).mkdir(parents=True, exist_ok=True)
    Path(offre_output_folder).mkdir(parents=True, exist_ok=True)

    # Analyse de l'offre d'emploi avec OpenAI
    print("📄 Analyse de l'offre d'emploi avec OpenAI...")
    job_raw_result = analyze_text(job_text, PROMPT_JOB_EXTRACTION)
    job_cleaned = clean_json_text(job_raw_result)

    try:
        job_data = json.loads(job_cleaned)
        print("✅ Offre extraite avec succès")

        # Sauvegarde de l'offre au format JSON
        offre_output_path = os.path.join(offre_output_folder, "offre_extrait.json")
        with open(offre_output_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, ensure_ascii=False, indent=4)
        print(f"💾 Offre sauvegardée dans : {offre_output_path}")

    except json.JSONDecodeError:
        print("❌ Erreur JSON dans l'extraction de l'offre. Résultat brut:")
        print(job_cleaned)
        job_data = {}  # Pour éviter le crash si le JSON est invalide

    # Vérifier que le dossier de CVs existe
    if not os.path.exists(cv_folder):
        print(f"⚠️ Le dossier {cv_folder} n'existe pas. Création...")
        Path(cv_folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Dossier {cv_folder} créé. Veuillez y placer vos CVs.")
        return

    cv_files = [f for f in os.listdir(cv_folder) if os.path.splitext(f)[-1].lower() in [".pdf", ".docx"]]

    if not cv_files:
        print(f"⚠️ Aucun CV trouvé dans {cv_folder}")
        return

    print(f"\n📁 Traitement de {len(cv_files)} CV(s)...")

    for filename in cv_files:
        file_path = os.path.join(cv_folder, filename)
        ext = os.path.splitext(filename)[-1].lower()

        print(f"\n📄 Traitement de : {filename}")
        print(f"  └─ Extraction du texte...")

        if ext == ".pdf":
            cv_text = extract_text_from_pdf(file_path)
        elif ext == ".docx":
            cv_text = extract_text_from_docx(file_path)

        print(f"  └─ Analyse du CV avec OpenAI...")
        result = analyze_text(cv_text, PROMPT_CV_EXTRACTION)
        cleaned_result = clean_json_text(result)

        try:
            extracted_data = json.loads(cleaned_result)
        except json.JSONDecodeError:
            print(f"  └─ ❌ JSON invalide pour {filename}. Résultat brut sauvegardé.")
            raw_output_path = os.path.join(json_output_folder, f"{filename}_raw.txt")
            with open(raw_output_path, "w", encoding="utf-8") as f:
                f.write(result)
            continue

        json_filename = os.path.splitext(filename)[0] + ".json"
        json_path = os.path.join(json_output_folder, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"  └─ ✅ Sauvegardé dans {json_path}")

    print(f"\n✅ Traitement terminé : {len(cv_files)} CV(s) traités")

if __name__ == "__main__":
    main()