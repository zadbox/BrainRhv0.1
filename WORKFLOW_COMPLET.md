# 🔄 WORKFLOW COMPLET BRAIN RH+ (Backend)

**Date:** 11 octobre 2025
**Version:** Post-migration FastAPI + React
**Modèle LLM par défaut:** `gpt-4o-mini`

---

## 📋 Vue d'ensemble du pipeline

```
1. CRÉATION OFFRE
   ↓
2. ENRICHISSEMENT OFFRE (IA/ROME)
   ↓
3. GÉNÉRATION MUST-HAVE / NICE-HAVE
   ↓
4. UPLOAD & PARSING CVs
   ↓
5. FILTRAGE PAR MUST-HAVE (éliminatoire)
   ↓
6. SCORING NICE-HAVE + SIMILARITÉ
   ↓
7. RE-RANKING LLM (Top N)
   ↓
8. RÉSULTATS FINAUX
```

---

## 🎯 ÉTAPE 1: Création de l'offre

**API Endpoint:** `POST /api/v1/offres`

**Payload minimal:**
```json
{
  "titre": "Développeur Backend Senior",
  "metier_label": "Développeur Python",
  "sections": {
    "competences_techniques": ["Python", "Django", "PostgreSQL"],
    "experiences_requises": "5 ans minimum",
    "formations": ["Bac+5 informatique"]
  }
}
```

**Ce qui se passe:**
- Offre stockée dans `projects/{project_id}/offre.json`
- État initial: brute, non enrichie

---

## 🌟 ÉTAPE 2: Enrichissement de l'offre

**Fichier:** `offer_enrichment.py`
**Fonction:** `enrich_offer_intelligently(offre_json, metier_label)`
**Modèle:** `gpt-4o-mini`

**Options d'enrichissement:**

### 2.1 Enrichissement IA (GPT-4o-mini)

**Prompt:** Analyse l'offre et propose des compléments intelligents

**Résultat:**
```json
{
  "coverage_score": 75,
  "propositions": {
    "competences": [
      {"name": "Docker", "type": "nice", "rationale": "..."},
      {"name": "Kubernetes", "type": "nice", "rationale": "..."}
    ],
    "outils": [
      {"name": "Git", "rationale": "..."}
    ],
    "langages": [
      {"name": "SQL", "rationale": "..."}
    ],
    "certifications": [],
    "missions": [
      {"text": "Conception architecture microservices", "rationale": "..."}
    ],
    "questions_clarification": [
      "Quelle est la taille de l'équipe backend ?",
      "Y a-t-il une astreinte ?"
    ]
  }
}
```

**UI:** Propositions affichées, RH sélectionne ce qu'il accepte

**Fusion:** `merge_enrichment(offre_json, enrichment, selections)`
- Ajoute les propositions acceptées à l'offre
- Évite les doublons
- Deep copy pour préserver l'original

### 2.2 Enrichissement ROME (API Pôle Emploi)

**Optionnel:** Active si code ROME fourni (ex: M1805)

**Récupère:**
- Compétences professionnelles
- Compétences transverses
- Savoir-faire
- Contextes de travail

**Fusion:** Même logique que IA, propositions + sélection manuelle

### 2.3 Combinaison IA + ROME

**Workflow:**
1. Enrichissement IA → propositions V1
2. Enrichissement ROME → propositions V2
3. Fusion et déduplication
4. RH valide/ajuste
5. Offre enrichie finale

---

## 📝 ÉTAPE 3: Génération Must-Have / Nice-Have

**Fichier:** `matching_engine.py`
**Fonction:** `extract_must_have_with_llm(job_description)`
**Modèle:** `gpt-4o-mini`

### 3.1 Extraction Must-Have (critères éliminatoires)

**Prompt stratégie:**
- Cherche vocabulaire impératif: "requis", "obligatoire", "minimum"
- Conserve les durées/niveaux chiffrés: "10+ ans", "Bac+5"
- Ignore localisation, type contrat, soft skills vagues
- **Target:** Extraire 10-15 critères minimum

**Format de sortie:**
```json
{
  "must_haves": [
    "Minimum 5 ans développement Python",
    "Bac+5 informatique ou équivalent",
    "Anglais courant exigé",
    "Django et FastAPI"
  ]
}
```

**Post-processing:**
- Nettoyage (trim, lowercase pour dédup)
- Déduplication
- Filtrage critères trop longs (>100 chars)
- Filtrage localisation/contrat si >30% du texte

### 3.2 Génération Nice-Have

**Logique:**
- Tous les critères **NON must-have** deviennent nice-have
- Compétences "souhaitées", "appréciées", "atout"
- Pas d'extraction LLM séparée, déduit par différence

**Usage:**
- Bonus multiplicateur dans le scoring: `0.95^(nb_manquants)`
- Si 0 manquants → multiplicateur 1.0 (aucun malus)
- Si 2 manquants → multiplicateur 0.9025

---

## 📄 ÉTAPE 4: Upload & Parsing CVs

**API Endpoint:** `POST /api/v1/cvs/parse/stream` (SSE)

**Parsing engine:** Extraction structurée avec LLM

**Format de sortie:**
```json
{
  "cv": "candidat_123.pdf",
  "sections": {
    "identite": {"nom": "...", "prenom": "..."},
    "competences_techniques": ["Python", "Django", "Docker"],
    "experiences_professionnelles": [
      {
        "poste": "Développeur Backend",
        "entreprise": "TechCorp",
        "duree": "3 ans",
        "debut": "2020",
        "fin": "2023",
        "missions": [...]
      }
    ],
    "formations": ["Master Informatique"],
    "langues": [{"langue": "Anglais", "niveau": "Courant"}]
  }
}
```

**Stockage:** `projects/{project_id}/cvs_parsed/{cv_id}.json`

---

## 🔍 ÉTAPE 5: Filtrage par Must-Have (éliminatoire)

**Fichier:** `matching_engine.py`
**Fonction:** `filter_cvs_by_must_have(cvs, indispensables, job_description)`
**Modèle:** `gpt-4o-mini`

**Modes:**
- **Séquentiel:** 1 CV à la fois (lent, fiable)
- **Parallèle:** Jusqu'à 500 CVs concurrents (rapide, optimisé)

### 5.1 Vérification par CV

**Fonction:** `check_single_cv_must_have(cv, indispensables, job_description)`

**Prompt stratégie:**
- **STRICT:** UN SEUL critère manquant = ÉLIMINATION
- **INTELLIGENT:** Cherche concepts, pas mots exacts
  - "Python" inclut pandas, Django, Flask, FastAPI
  - "SQL" inclut MySQL, PostgreSQL, Oracle
  - "Bac+5" = Master = MSc = Ingénieur
- **FLEXIBILITÉ EXPÉRIENCE:** Marge de 15% sur les années
  - Demandé: 5 ans → Accepté dès 4.25 ans (85% de 5)
  - Justification requise dans le commentaire
- **ADDITION DOMAINES:** Additionne toutes les expériences pertinentes
  - Ex: 2 ans Data Analyst + 2.5 ans Data Scientist = 4.5 ans total

**Format de sortie:**
```json
{
  "decision": "ACCEPTÉ" | "ÉLIMINÉ",
  "criteres_verifies": [
    {
      "critere": "Minimum 5 ans développement Python",
      "present": true,
      "commentaire": "Critère satisfait avec flexibilité (15%). Calcul: Dev Backend Python 3 ans (Startup X) + Dev Fullstack Python 1.5 ans (Agence Y) = 4.5 ans total. Légèrement sous les 5 ans requis mais au-dessus du seuil minimal de 4.25 ans (85%)."
    }
  ],
  "rationale": "Synthèse en 1 phrase",
  "element_declencheur": "Critère bloquant" | null
}
```

**Résultat:** Liste de CVs acceptés (passed) / rejetés (failed)

---

## 📊 ÉTAPE 6: Scoring Similarité + Nice-Have

**Fichier:** `matching_engine.py`
**Fonction:** `compute_similarity_with_scoring(job_text, cvs, nice_have_list, job_description)`

### 6.1 Calcul similarité (embeddings)

**Modèle:** `sentence-transformers/all-MiniLM-L6-v2`

**Pipeline:**
1. Encoder offre → vecteur normalisé (1 fois)
2. Encoder tous les CVs en batch → matrice normalisée (N CVs)
3. Calcul cosine similarity vectorisé: `cv_matrix @ job_vec.T`
4. Résultat: scores de similarité 0.0 à 1.0

**Optimisation:**
- Cache embeddings (hash SHA256)
- Batch processing (batch_size=32 par défaut)
- Normalisation pour dot product = cosine

### 6.2 Détection nice-have manquants

**Fonction:** `_find_nice_have_missing(cv, nice_have_list, job_description)`
**Modèle:** `gpt-4o-mini`

**Prompt:** Recherche sémantique des nice-have présents/absents dans le CV

**Modes:**
- **Parallèle:** Jusqu'à 500 CVs concurrents (QPS=10.0)
- **Fallback séquentiel** si module parallèle non disponible

**Format:**
```json
{
  "nice_have_presents": ["Docker", "Git"],
  "nice_have_manquants": ["Kubernetes", "CI/CD avancé"]
}
```

### 6.3 Score final

**Formule:**
```python
nombre_manquants = len(nice_have_manquants)
bonus_factor = 0.95  # Config: nice_have_malus_factor
bonus_multiplicateur = bonus_factor ** nombre_manquants

score_final = score_base * bonus_multiplicateur
score_final = clamp(score_final, 0.0, 1.0)
```

**Exemple:**
- Score base: 0.75 (similarité embeddings)
- Nice-have: 2 manquants → bonus = 0.95² = 0.9025
- Score final: 0.75 × 0.9025 = **0.677**

**Résultat:** Liste triée par score_final (tous les CVs, pas de limite top_k ici)

---

## 🏆 ÉTAPE 7: Re-Ranking LLM (Top N)

**Fichier:** `matching_engine.py`
**Fonction:** `rerank_with_llm(top_cvs, job_description)`
**Modèle:** `gpt-4o-mini`

**Scope:** Top 10 CVs par défaut (configurable: `top_rerank`)

### 7.1 Prompt stratégie

**Mission:** Re-classer les CVs du meilleur au moins bon

**Analyse qualitative:**
1. Durée et pertinence des expériences
2. Qualité des environnements (startup, grande entreprise, international)
3. Cohérence et progression du parcours
4. Missions et responsabilités en lien avec l'offre

**Coefficient qualité expérience:** 1.0 à 1.4
- 1.4 : EXCEPTIONNELLE (leadership, projets majeurs, environnement identique)
- 1.3 : TRÈS FORTE (senior, projets complexes, très pertinent)
- 1.2 : FORTE (confirmé, bonne pertinence)
- 1.1 : PERTINENTE (standard, domaine connexe)
- 1.0 : CORRECTE (junior ou peu pertinent)

### 7.2 Format de sortie

**Deux commentaires distincts:**

1. **`commentaire_scoring`** (2-3 lignes, technique):
   - Explique score base + bonus nice-have
   - **CRITIQUE:** Liste EXPLICITEMENT les nice-have MANQUANTS
   - Calcul du multiplicateur

2. **`appreciation_globale`** (4-5 lignes, qualitatif):
   - Analyse EN PROFONDEUR les expériences
   - Justifie le coefficient attribué
   - Compare aux autres candidats
   - Forces + vigilances + recommandation RH

**Structure:**
```json
{
  "ranked_cvs": [
    {
      "cv": "candidat_123.json",
      "coefficient_qualite_experience": 1.3,
      "commentaire_scoring": "Score base de 0.75 reflétant une bonne adéquation technique. Multiplicateur de 0.9025 (×0.95²) appliqué en raison de 2 nice-have manquants : Kubernetes et CI/CD avancé. Score final: 0.68.",
      "appreciation_globale": "Profil très fort pour ce poste de Développeur Backend Senior (coefficient: 1.3). Le candidat possède 6 ans d'expérience progressive en Python/Django avec 2 ans en tant que lead technique. Expérience de leadership dans un environnement agile similaire. Seule vigilance : Kubernetes manquant mais compensable par formation rapide vu son expertise Docker. Fortement recommandé pour entretien technique."
    }
  ]
}
```

### 7.3 Validation

**Contrôles:**
- Vérification noms de fichiers (doivent matcher exactement)
- Coefficient entre 1.0 et 1.4
- Tous les CVs présents (ajout auto si manquants)
- Fallback si JSON invalide: tri par score_final

---

## 📈 ÉTAPE 8: Calcul scores finaux et résultats

**Formule globale:**
```python
score_embedding = similarité cosine (0.0 à 1.0)
bonus_nice_have = 0.95^(nb_manquants)
score_intermediate = score_embedding × bonus_nice_have

coefficient_experience = 1.0 à 1.4 (du re-ranking LLM)
score_final = score_intermediate × coefficient_experience

# Clamp à [0.0, 1.0]
score_final = clamp(score_final, 0.0, 1.0)
```

**Exemple complet:**
```
CV: candidat_123.json

1. Similarité embeddings: 0.75
2. Nice-have: 2 manquants → 0.95² = 0.9025
3. Score intermédiaire: 0.75 × 0.9025 = 0.677
4. Coefficient expérience: 1.3 (profil très fort)
5. Score final: 0.677 × 1.3 = 0.880

Classement: 1er sur 50 CVs
```

**Stockage:** `projects/{project_id}/results/{matching_id}_results.json`

---

## ⚙️ Configuration LLM par défaut

### Modèle principal

**Fichier:** `config_loader.py`, `matching_engine.py`, `offer_enrichment.py`, `api/routers/matching.py`

```python
DEFAULT_MODEL = "gpt-4o-mini"
```

**Températures:**
- Extraction must-have: `1.0` (défaut gpt-4o-mini, créativité controlée)
- Filtrage must-have: `1.0` (défaut)
- Nice-have detection: `1.0` (défaut)
- Re-ranking: `1.0` (défaut)
- Enrichissement offre: `1.0` (défaut)

### Fallback

**Si `gpt-4o-mini` échoue:**
```python
fallback_models = ["gpt-4.1-mini", "gpt-4o-mini"]
```

---

## 📊 Métriques clés

**Performance:**
- Parsing 1 CV: ~5-10s (LLM)
- Filtrage must-have 100 CVs: ~60s (parallèle 500 concurrent)
- Scoring 100 CVs: ~30s (embeddings batch + nice-have parallèle)
- Re-ranking 10 CVs: ~10s (1 appel LLM)

**Parallélisation:**
- Max concurrent: 500 CVs (must-have + nice-have)
- QPS: 10.0 (limite OpenAI)
- Timeout: 300s (5 minutes)
- Retries: 1

**Cache:**
- Embeddings: Hash SHA256, stocké dans `cache/`
- Durée: Permanent (jusqu'à suppression manuelle)

---

## 🚀 Endpoints API clés

### Offres
- `POST /api/v1/offres` - Créer offre
- `GET /api/v1/offres/{project_id}` - Récupérer offre
- `POST /api/v1/offres/{project_id}/enrich` - Enrichir (IA/ROME)

### CVs
- `POST /api/v1/cvs/parse/stream` - Parser CVs (SSE)
- `GET /api/v1/cvs/projects/{project_id}/cvs` - Liste CVs parsés

### Matching
- `POST /api/v1/matching/run` - Lancer matching complet
- `POST /api/v1/matching/stream` - Lancer matching (SSE)
- `GET /api/v1/matching/{matching_id}/results` - Résultats

---

## 🔧 Modifications nécessaires

✅ **Complété:**
1. Uniformisation modèle: `gpt-5-mini` → `gpt-4o-mini`
2. Documentation workflow complet
3. Vérification température = 1.0 par défaut

📝 **À documenter dans frontend:**
- UI pour sélection enrichissement IA/ROME
- Affichage propositions avec rationales
- Validation manuelle avant fusion
- Workflow complet depuis création offre → résultats

---

**Documentation validée ✅**
**Prêt pour intégration frontend Palier 5**
