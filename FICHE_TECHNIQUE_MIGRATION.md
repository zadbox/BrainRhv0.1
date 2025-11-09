# FICHE TECHNIQUE - Brain RH - Migration Frontend

**Date:** 11 octobre 2025
**Version actuelle:** v2.6.5 (Streamlit)
**Objectif:** Migration vers architecture moderne (FastAPI + React ou Django + HTMX)

---

## 1️⃣ STRUCTURE ET FONCTIONNEMENT ACTUEL

### Architecture générale
**Framework actuel:** Streamlit 1.45.1
**Structure:** Application monolithique avec routing multi-niveaux
**Fichiers Python:** 23 fichiers (10 112 lignes de code total)
**Taille projet:** ~51MB (incluant cache et données)

### Fichiers principaux et leur rôle

#### **Core Business Logic (NE PAS CASSER)**
1. **`matching_engine.py`** (58 442 lignes) - **CRITIQUE**
   - Moteur de matching CV/Offre avec scoring intelligent
   - Embeddings (SentenceTransformer all-MiniLM-L6-v2)
   - Filtrage must-have avec parallélisation (500 CVs max/batch)
   - Détection nice-have avec malus multiplicateur
   - Re-ranking LLM (top N CVs avec commentaires)
   - Calcul coefficient qualité expérience (×1.0 à ×1.4)
   - Validation jsonschema + réparation auto

2. **`parseur_cv.py`** (12 831 lignes)
   - Extraction texte de PDF (PyPDF2) et DOCX (python-docx)
   - Prompt LLM pour structuration JSON
   - Nettoyage et validation des données

3. **`parallel_cv_parsing.py`** (13 758 lignes)
   - Parsing parallélisé de CVs (asyncio + Semaphore)
   - Max 500 CVs simultanés avec rate limiting (QPS)
   - Performance tracking détaillé (logs avec timestamps ms)
   - Timeout 300s par CV, 1 retry

4. **`must_have_parallel.py`** (7 574 lignes)
   - Filtrage parallélisé des must-have
   - Concurrence: min(len(cvs), 500)
   - QPS: 10.0, timeout: 300s, retries: 1

5. **`nice_have_parallel.py`** (7 212 lignes)
   - Détection parallélisée des nice-have manquants
   - Même architecture que must_have_parallel
   - Malus: 0.95^(nb_manquants)

#### **UI et Navigation**
6. **`app.py`** (86 443 lignes) - **INTERFACE PRINCIPALE**
   - Point d'entrée Streamlit
   - Routing multi-niveaux: Entreprises > Projets > Détail matching
   - Gestion session_state (current_enterprise, current_project)
   - 3 onglets principaux: Préparer l'offre / Charger CVs / Matching
   - Affichage résultats avec métriques (score final, score base, malus nice-have, qualité XP)
   - Export CSV des résultats

7. **`pages_ui.py`** (44 804 lignes)
   - Pages de gestion Entreprises et Projets
   - CSS personnalisé avec dark mode
   - Formulaires de création/modification
   - Cartes UI avec Material Symbols

#### **Gestion de données**
8. **`project_manager.py`** (11 206 lignes)
   - CRUD projets de recrutement
   - Stockage JSON dans `projects/`
   - Historique des matchings

9. **`enterprise_manager.py`** (8 214 lignes)
   - CRUD entreprises clientes
   - Stockage JSON dans `enterprises/`
   - Compteur de projets

10. **`offer_enrichment.py`** (15 784 lignes)
    - Enrichissement d'offres via LLM
    - Extraction critères must-have et nice-have
    - Appel API France Travail / ROME

11. **`mapper_offre.py`** (10 556 lignes)
    - Mapping offre vers sections standardisées
    - Format compatible avec matching engine

12. **`rome_api.py`** (13 493 lignes)
    - Client API France Travail (codes ROME)
    - OAuth2 + refresh token
    - Enrichissement compétences métier

#### **Configuration et validation**
13. **`config_loader.py`** (7 198 lignes)
    - Chargement `config.yaml`
    - Classe ConfigLoader avec getters typés

14. **`validation.py`** (20 742 lignes)
    - Validation jsonschema pour CVs et offres
    - Réparation auto des données invalides
    - Checks non-IA (taille, contenu, format)

15. **`parallel_processing.py`** (13 030 lignes)
    - Pipeline de parallélisation générique
    - asyncio + ThreadPoolExecutor

### Fonctionnalités principales

#### **1. Gestion Entreprises/Projets**
- Créer/modifier/supprimer des entreprises clientes
- Créer des projets de recrutement par entreprise
- Archiver/restaurer des projets
- Navigation breadcrumb cliquable

#### **2. Préparation d'offre**
- Saisie manuelle de l'offre d'emploi
- Enrichissement automatique via LLM (GPT-5-mini)
- Enrichissement via API France Travail (codes ROME)
- Classification des critères: Must-have / Nice-to-have / N/A
- Sélection via selectbox unique (remplace anciens checkboxes)

#### **3. Parsing de CVs**
- Upload fichiers PDF/DOCX (batch ou individuel)
- Parsing parallélisé automatique (lots de 500 max)
- Extraction texte + structuration LLM
- Validation et réparation JSON
- Stockage dans `cv_json/`

#### **4. Matching CV/Offre (PIPELINE COMPLET)**

**Étape 1: Vectorisation**
- Offre vectorisée une seule fois
- Tous les CVs vectorisés en batch (32)
- Calcul cosine similarity par section

**Étape 2: Filtrage Must-Have (PARALLÈLE)**
- Appels LLM parallèles (500 max simultanés)
- QPS: 10.0, timeout: 300s, retries: 1
- Élimination des CVs ne satisfaisant pas les critères éliminatoires
- Rate limiting pour éviter throttling OpenAI

**Étape 3: Détection Nice-Have (PARALLÈLE)**
- Appels LLM parallèles (500 max simultanés)
- Identification des nice-have manquants
- Application malus: 0.95^(nb_manquants)

**Étape 4: Scoring Base**
- Calcul score par section (pondérations config.yaml)
- Score base = moyenne pondérée des similarités

**Étape 5: Re-ranking LLM (Top N)**
- Top N CVs (slider 5-20, défaut 10)
- LLM analyse qualité expériences professionnelles
- Attribution coefficient qualité XP (×1.0 à ×1.4):
  - 1.4: Expérience EXCEPTIONNELLE
  - 1.3: Expérience TRÈS FORTE
  - 1.2: Expérience FORTE
  - 1.1: Expérience PERTINENTE
  - 1.0: Expérience CORRECTE
- Commentaire détaillé par CV
- Appréciation globale

**Étape 6: Score Final**
```
Score Final = Score Base × Malus Nice-Have × Coefficient Qualité XP
```
- Score cappé entre 0.0 et 1.0

#### **5. Affichage et Export**
- Tableau trié par score final décroissant
- Carte détaillée par CV avec:
  - 4 métriques: Score final, Score base, Malus nice-have, Qualité XP
  - Commentaire du re-ranking (si top N)
  - Nice-have manquants avec badges
  - Détails du CV (identité, expériences, compétences)
- Export CSV avec toutes les colonnes
- Légende explicative du scoring

### Flux utilisateur complet
1. **Lancement:** `streamlit run app.py` (port 8501)
2. **Sélection entreprise** (ou création si première fois)
3. **Sélection projet** (ou création)
4. **Onglet 1: Préparer l'offre**
   - Saisir offre manuellement
   - OU enrichir via LLM/ROME
   - Classifier critères (Must-have/Nice-to-have/N/A)
5. **Onglet 2: Charger CVs**
   - Upload PDFs/DOCX
   - Parsing automatique (parallèle)
   - Voir liste des CVs parsés
6. **Onglet 3: Matching**
   - Configurer Top N (slider)
   - Lancer matching (automatiquement parallélisé)
   - Consulter résultats
   - Exporter CSV
7. **Retour projets/entreprises** via breadcrumb

---

## 2️⃣ DONNÉES ET TRAITEMENT

### Sources de données
1. **Fichiers locaux** (prioritaire)
   - CVs: `cv_input/` (PDF, DOCX)
   - CVs parsés: `cv_json/` (JSON structurés)
   - Offres: `offres/` (JSON par projet)
   - Projets: `projects/` (JSON hiérarchique)
   - Entreprises: `enterprises/` (JSON plat)

2. **APIs externes**
   - OpenAI GPT-5-mini (parsing, matching, re-ranking)
   - France Travail / ROME (enrichissement offres)

3. **Cache** (facultatif mais conseillé)
   - Embeddings: `cache/` (hash SHA256)
   - TTL: 24h

### Taille des données
- **CVs individuels:** 50-500 KB (PDF/DOCX)
- **CVs JSON:** 5-50 KB par CV
- **Offre:** 5-20 KB
- **Batch typique:** 20-100 CVs par matching
- **Batch max supporté:** Pas de limite technique (lots de 500)
- **Volume total produit:** Quelques centaines de CVs/jour estimé

### Type d'opérations
1. **Lecture/écriture fichiers** (synchrone)
   - Extraction texte PDF/DOCX
   - Sérialisation/désérialisation JSON

2. **Appels LLM** (asynchrone parallélisé)
   - Parsing CVs (response_format: json_object)
   - Filtrage must-have (response_format: json_object)
   - Détection nice-have (response_format: json_object)
   - Re-ranking (response_format: json_object)

3. **Calculs CPU** (synchrone)
   - Embeddings (SentenceTransformer sur CPU)
   - Cosine similarity (numpy)
   - Scoring (formules simples)

4. **I/O réseau**
   - OpenAI API (gpt-5-mini)
   - France Travail API (OAuth2 + endpoints ROME)

### Temps de traitement
**Exemple réel: 32 CVs**
- Extraction texte: ~15s total (I/O bound)
- Parsing LLM parallèle: ~2 min (network bound)
- Filtrage must-have: ~1-2 min (network bound)
- Détection nice-have: ~1-2 min (network bound)
- Embeddings: ~5s (CPU bound)
- Re-ranking top 10: ~30-60s (network bound)
- **Total: ~5-8 minutes pour 32 CVs**

**Goulot d'étranglement:**
- Latence OpenAI (90-120s par CV, d'où parallélisation nécessaire)
- QPS rate limiting (10 req/s configuré)

### Résultats exportables
- **CSV:** `scorecard_results.csv` (score, métadonnées, commentaires)
- **JSON:** `scorecard_results.json` (structure complète)
- Historique sauvegardé dans `projects/{project_id}/historique/`

### Historique
- Conservation de tous les matchings par projet
- Horodatage (ISO 8601)
- Pas de limite de rétention configurée

---

## 3️⃣ PARTIE LLM

### Modèles utilisés
**Principal:** OpenAI GPT-5-mini (`gpt-5-mini`)
**Fallbacks:** `gpt-4.1-mini`, `gpt-4o-mini`

**Contraintes techniques GPT-5-mini:**
- Temperature: 1.0 uniquement (pas d'override possible)
- Response format: `json_object` obligatoire pour parsing structuré
- Latence: 90-120s par appel (anormalement lent, confirme need parallélisation)

### Usage LLM par fonctionnalité

#### **1. Parsing CVs** (`parseur_cv.py`)
- **Prompt:** `PROMPT_CV_EXTRACTION` (~500 tokens)
- **Input:** Texte brut du CV (1000-5000 tokens)
- **Output:** JSON structuré (identité, compétences, expériences, formations, etc.)
- **Temperature:** 1.0 (défaut GPT-5-mini)
- **Mode:** Appels parallèles (max 500 simultanés, QPS 10)

#### **2. Filtrage Must-Have** (`must_have_parallel.py`)
- **Prompt:** Contexte offre + critères must-have + CV
- **Input:** ~2000-4000 tokens
- **Output:** JSON `{"manquants": ["critère1", ...], "raison": "..."}`
- **Mode:** Parallèle (500 max, QPS 10, timeout 300s, 1 retry)

#### **3. Détection Nice-Have** (`nice_have_parallel.py`)
- **Prompt:** Contexte offre + critères nice-have + CV
- **Input:** ~2000-4000 tokens
- **Output:** JSON `{"manquants": ["critère1", ...]}`
- **Mode:** Parallèle (500 max, QPS 10, timeout 300s, 1 retry)

#### **4. Re-ranking** (`matching_engine.py`)
- **Prompt:** Offre complète + liste Top N CVs + instructions détaillées
- **Input:** ~5000-10000 tokens (dépend du Top N)
- **Output:** JSON structuré:
  ```json
  {
    "ranked_cvs": [
      {
        "cv": "filename.json",
        "coefficient_qualite_experience": 1.2,
        "commentaire_scoring": "...",
        "appreciation_globale": "..."
      }
    ]
  }
  ```
- **Temperature:** 1.0
- **Mode:** Appel unique (pas parallélisé, reçoit tous les Top N d'un coup)

#### **5. Enrichissement Offre** (`offer_enrichment.py`)
- **Prompt:** Description offre brute
- **Output:** JSON avec sections enrichies
- **Temperature:** 1.0
- **Mode:** Appel unique

### Streaming vs Batch
**Mode actuel:** Batch uniquement (pas de streaming)
**Justification:** Besoin de JSON complet pour validation

**Besoin futur (migration):**
- Streaming souhaitable pour UX (feedback progressif)
- Mais nécessite parser JSON incrémental

### Paramètres dynamiques
- **Top N re-ranking:** Slider 5-20 (défaut 10)
- **QPS:** 10.0 (config.yaml, non exposé UI)
- **Timeout:** 300s (config.yaml, non exposé UI)
- **Retries:** 1 (config.yaml, non exposé UI)
- **Concurrency:** min(len(cvs), 500) (automatique)

### Personnalisation
**Par utilisateur:** Non (pas d'authentification actuellement)
**Par projet:** Oui (chaque projet a son offre et critères)
**Par entreprise:** Oui (isolation des données)

---

## 4️⃣ INTERFACE ACTUELLE

### Structure multi-page Streamlit
**Routing:**
```
/ (root)
├── Accueil Entreprises (si aucune entreprise sélectionnée)
│   ├── Liste des entreprises (cartes)
│   └── Formulaire de création
├── Accueil Projets (si entreprise sélectionnée, pas de projet)
│   ├── Liste des projets (cartes)
│   └── Formulaire de création
└── Détail Projet (si entreprise + projet sélectionnés)
    ├── Breadcrumb: Entreprises > Projets > Nom Projet
    ├── Onglet 1: Préparer l'offre
    ├── Onglet 2: Charger CVs
    └── Onglet 3: Matching
```

### Navigation
**Méthode:** `st.session_state` + `st.rerun()`
**État partagé:**
- `current_enterprise` (ID entreprise)
- `current_project` (ID projet)
- `top_rerank` (slider Top N)
- `critere_classification` (dict classification critères)

**Breadcrumb cliquable:**
- Clic "Entreprises" → reset `current_enterprise` + rerun
- Clic "Projets" → reset `current_project` + rerun
- Nom projet → pas d'action (déjà sur la page)

### Composants principaux par page

#### **Accueil Entreprises**
- Cartes entreprises (HTML/CSS custom)
- Boutons: Voir projets, Modifier, Supprimer
- Formulaire création (inputs + submit)
- Dark mode adaptatif (CSS variables)

#### **Accueil Projets**
- Cartes projets (actifs + archivés)
- Badges status (actif/archivé)
- Boutons: Ouvrir, Modifier, Archiver/Restaurer
- Formulaire création

#### **Onglet 1: Préparer l'offre**
- `st.text_area` (offre brute)
- Boutons: Enrichir via LLM, Enrichir via ROME, Merger
- Affichage critères extraits
- **Selectbox unique** par critère: N/A / Must-have / Nice-to-have
- Badges: [Manuel] ou [IA]
- Sauvegarde automatique dans `offres/offre_parsed.json`

#### **Onglet 2: Charger CVs**
- `st.file_uploader` (multiple, accept PDF/DOCX)
- Bouton "Préparer/Charger" (lance parsing parallèle)
- Progress bar pendant parsing
- Liste CVs parsés (expander par CV)
- Détails CV (identité, compétences, expériences)

#### **Onglet 3: Matching**
- Slider "Top N" (5-20)
- Bouton "Lancer matching"
- Progress bar multi-étapes:
  - Vectorisation
  - Filtrage must-have
  - Détection nice-have
  - Scoring
  - Re-ranking
- **Tableau résultats:**
  - Tri par score final décroissant
  - Colonnes: CV, Score final, Score base, Malus, Qualité XP
- **Cartes détaillées par CV:**
  - 4 métriques (st.metric)
  - Nice-have manquants (badges rouges)
  - Commentaire re-ranking (si top N)
  - Expander identité
  - Expander expériences
  - Expander compétences
- Bouton "Exporter CSV"
- Légende scoring (expander)

### États partagés (session_state)
```python
st.session_state = {
    'current_enterprise': str,  # ID entreprise
    'current_project': str,     # ID projet
    'top_rerank': int,          # Top N slider (5-20)
    'critere_classification': dict,  # {idx: "Must-have"/"Nice-to-have"/"N/A"}
    # ... autres états internes Streamlit
}
```

### Interactions principales
**Form submit:**
- Création entreprise/projet
- Sauvegarde offre
- Upload CVs

**Callbacks:**
- Clic bouton "Enrichir" → appel LLM → mise à jour offre
- Clic bouton "Lancer matching" → pipeline complet → affichage résultats
- Clic bouton "Exporter" → génération CSV → download

**Reruns:**
- Changement de page (entreprise/projet)
- Après création/suppression
- Après upload CVs
- Après matching

### Aspect visuel
**Doit-il être reproduit à l'identique?**
**Réponse:** NON, modernisation souhaitée
**Raison:** CSS custom complexe pour contourner limites Streamlit

**Style actuel:**
- Logo personnalisé (header)
- CSS variables pour dark mode
- Material Symbols icons
- Cartes avec ombres et hover effects
- Couleurs: Bleu (#4A90E2), Cyan (#5BC0DE)
- Typographie: Roboto (Google Fonts)

**Améliorations UX souhaitées:**
- Drag & drop CVs (actuellement upload basique)
- Tableaux triables/filtrables (actuellement tri fixe)
- Pagination (actuellement scroll infini)
- Notifications toast (actuellement st.success/error)
- Loading skeletons (actuellement spinners basiques)

---

## 5️⃣ CONTEXTE TECHNIQUE

### Environnement Python
**Version:** Python 3.9.6
**OS:** macOS Darwin 24.6.0

### Dépendances principales
```
streamlit==1.45.1
openai==1.63.2
sentence-transformers==5.1.1
jsonschema==4.23.0
pyyaml>=6.0
PyPDF2==3.0.1
python-docx==1.1.0
pandas==2.3.3
python-dotenv==1.0.0
pytest>=7.0
pytest-asyncio>=0.21.0
```

**Packages système:**
- Aucune dépendance système critique (pas de C extensions custom)

### Déploiement actuel
**Mode:** Local uniquement (`streamlit run app.py`)
**Port:** 8501 (config.yaml)
**Processus:** Single-threaded Streamlit server + asyncio pour parallélisation

**Pas de déploiement production actuellement**

### Taille du code
- **23 fichiers Python:** 10 112 lignes totales
- **Fichier le plus volumineux:** `app.py` (86 443 lignes)
- **Fichiers critiques:** `matching_engine.py`, `parallel_cv_parsing.py`, `parseur_cv.py`

### Configuration
**Fichiers:**
1. **`.env`** (secrets)
   ```
   OPENAI_API_KEY=***
   ROME_CLIENT_ID=***
   ROME_CLIENT_SECRET=***
   ```

2. **`config.yaml`** (159 lignes, paramètres)
   - Modèles LLM
   - Timeouts et retries
   - Poids scoring
   - Chemins fichiers
   - Parallélisation
   - Validation

3. **`.env.example`** (template)

### Environnement cible souhaité
**Besoin:**
- Déploiement cloud (pas spécifié, mais inféré)
- Scalabilité horizontale (si volume augmente)
- CI/CD basique (tests automatiques)

**Stack envisagée:**
- Docker (conteneurisation)
- Option 1: VM simple (OVH, DigitalOcean)
- Option 2: Cloud managed (GCP Cloud Run, AWS ECS, Azure Container Apps)

**Pas besoin de Kubernetes** (complexité excessive pour ce use case)

---

## 6️⃣ CONTRAINTES ET ATTENTES

### Contraintes techniques

#### **Réseau**
- OpenAI API: Rate limiting 10 req/s (configurable)
- France Travail API: Rate limit inconnu (non documenté dans code)
- Latence OpenAI: 90-120s par appel (bottleneck identifié)

#### **Stockage**
- Volumes actuels: ~51MB projet
- Croissance estimée: 100-500 MB/mois (CVs + cache)
- Pas de base de données relationnelle nécessaire (JSON suffit)

#### **RAM**
- Embeddings model: ~100MB en mémoire
- Batch 500 CVs: ~500MB RAM estimé
- Total besoin: 2GB RAM recommandé

#### **CPU**
- Embeddings: CPU-bound (SentenceTransformer)
- Scoring: négligeable
- Pas de GPU nécessaire

#### **Quotas API**
- OpenAI: Dépend du compte (non spécifié)
- Risque throttling si > 10 req/s
- Besoin monitoring usage

### Contraintes de sécurité

#### **Données sensibles**
- **CVs:** Oui (identité, email, téléphone, adresse)
- **RGPD:** Applicable (France)
- **Audit:** Logging activé (config.yaml), mais pas de chiffrement

**Besoins futurs:**
- Authentification utilisateurs (actuellement aucune)
- Chiffrement données au repos (CVs, offres)
- Logs d'accès et traçabilité
- Retention policy (actuellement illimitée)

#### **Secrets**
- Actuellement: `.env` local (non versionné)
- Besoin futur: Vault ou secrets manager

### Attentes de la migration

#### **1. Meilleure UI** (Priorité HAUTE)
- Design moderne et responsive
- Dark mode natif (pas de hacks CSS)
- Composants riches:
  - Drag & drop fichiers
  - Tableaux triables/filtrables/paginés
  - Progress bars élégantes
  - Notifications toast
  - Loading skeletons
- Moins de reruns (fluidité)

#### **2. Meilleure performance** (Priorité HAUTE)
- Conserver parallélisation (500 CVs simultanés)
- Optimiser latence perçue:
  - Streaming LLM (feedback progressif)
  - Chargement lazy des CVs
  - Cache navigateur
- Monitoring temps de traitement

#### **3. Modularité du code** (Priorité MOYENNE)
- Séparation backend/frontend propre
- API REST documentée (OpenAPI/Swagger)
- Tests unitaires et d'intégration
- Faciliter ajout de nouvelles fonctionnalités

#### **4. Préparation à l'échelle** (Priorité MOYENNE)
- Architecture stateless (pour scaling horizontal)
- Queue système pour jobs longs (matching de 1000+ CVs)
- Monitoring et alerting
- Logs centralisés

#### **5. Authentification** (Priorité BASSE pour MVP)
- Multi-utilisateurs
- Isolation des données par compte
- Gestion des permissions (admin/user)

### Fonctionnalités à conserver absolument
- ✅ Parsing parallélisé des CVs (500 max)
- ✅ Filtrage must-have parallélisé
- ✅ Détection nice-have parallélisée
- ✅ Re-ranking LLM avec coefficient qualité XP
- ✅ Export CSV
- ✅ Gestion entreprises/projets
- ✅ Historique des matchings
- ✅ Classification critères (Must-have/Nice-to-have/N/A)

### Fonctionnalités à améliorer
- 🔧 Upload CVs (remplacer par drag & drop)
- 🔧 Affichage résultats (tableaux modernes)
- 🔧 Navigation (moins de reruns, plus fluide)
- 🔧 Feedback progressif (streaming LLM)

### Fonctionnalités nouvelles (nice-to-have)
- 📝 Comparaison de CVs côte à côte
- 📝 Annotations manuelles sur CVs
- 📝 Templates d'offres pré-remplis
- 📝 Dashboard analytics (stats matchings)
- 📝 Notifications email (fin de matching)

---

## 7️⃣ POINTS D'ATTENTION POUR L'ARCHITECTE

### ⚠️ Fonctions critiques (NE PAS MODIFIER LA LOGIQUE)
1. **`matching_engine.match_cvs_with_job()`**
   - Cœur du système
   - Pipeline complet de matching
   - Formule scoring validée par utilisateur

2. **Prompts LLM**
   - Tous les prompts ont été optimisés et validés
   - Ne pas modifier sans tests exhaustifs
   - Localisation: `parseur_cv.py`, `matching_engine.py`, `offer_enrichment.py`

3. **Parallélisation**
   - Architecture asyncio + Semaphore validée
   - Performances 16x vs séquentiel
   - Ne pas casser la logique de batching

### 🔍 Zones à investiguer
1. **Latence OpenAI anormalement haute (90-120s/CV)**
   - Vérifier si reproductible en production
   - Potentiellement lié au compte dev
   - Monitoring nécessaire

2. **Validation JSON**
   - Taux de réparation actuel inconnu
   - À logger et monitorer

3. **Cache embeddings**
   - Efficacité réelle inconnue
   - Mesurer hit rate

### 📊 Métriques à collecter (post-migration)
- Temps de traitement par étape
- Taux d'erreur LLM
- Taux de réparation JSON
- Nombre de CVs traités/jour
- Hit rate cache
- Coût API OpenAI

### 🏗️ Recommandations architecture

**Backend:**
- FastAPI (async natif, compatible avec code actuel)
- Pydantic pour validation (remplace jsonschema)
- SQLAlchemy + PostgreSQL (optionnel, JSON suffit pour MVP)
- Celery + Redis pour queue jobs (si > 100 CVs/matching)

**Frontend:**
- React + TypeScript (contrôle total, écosystème mature)
- TanStack Query (cache et état serveur)
- TanStack Table (tableaux riches)
- shadcn/ui ou MUI (composants)
- React Dropzone (drag & drop)

**Déploiement:**
- Docker + docker-compose (dev)
- Cloud Run ou ECS (production)
- GitHub Actions (CI/CD)
- Sentry (monitoring erreurs)

**Migration par phases:**
1. **Phase 1:** Extraire backend en FastAPI (APIs REST)
2. **Phase 2:** Frontend React (pages simples d'abord)
3. **Phase 3:** Migration pages complexes (matching)
4. **Phase 4:** Features avancées (streaming, queue)

---

## 8️⃣ FICHIERS ANNEXES

### Documentation existante
- `README.md` (7 884 lignes) - Guide utilisateur
- `QUICKSTART.md` (6 337 lignes) - Installation rapide
- `SUIVI_PROJET.md` (12 913 lignes) - Historique des versions
- `INDEX.md` (10 133 lignes) - Index de la doc
- Nombreux fichiers `*.md` de fixes et features

### Tests existants
- `test_2cv_matching.py` (6 369 lignes)
- `test_batch_similarity.py` (4 276 lignes)
- `test_matching_complet.py` (6 266 lignes)
- `test_negation_must_have.py` (5 566 lignes)
- `test_parite_seq_parallel.py` (7 672 lignes)
- `test_parsing_performance.py` (1 891 lignes)
- `test_v2_integration.py` (12 957 lignes)

**Couverture:** Partielle (tests fonctionnels principalement)

### Scripts utilitaires
- `launch_app.sh` (260 lignes) - Lancement simplifié
- `migrate_to_enterprises.py` (2 921 lignes) - Migration données

---

## 9️⃣ RÉSUMÉ EXÉCUTIF

### Projet actuel
- **Nom:** Brain RH - Système de Matching CV/RH
- **Version:** 2.6.5
- **Framework:** Streamlit (Python)
- **Lignes de code:** 10 112 (23 fichiers)
- **Statut:** Fonctionnel, optimisé, mais UI limitée

### Raison de la migration
- Streamlit trop limitant pour UI riche
- Reruns complets à chaque interaction
- Difficile de customiser l'apparence
- Pas adapté pour scaling

### Forces à conserver
- ✅ Logique métier solide (matching engine)
- ✅ Parallélisation performante (16x speedup)
- ✅ Prompts LLM optimisés
- ✅ Pipeline validé par utilisateur

### Points faibles à corriger
- ❌ UI peu flexible (Streamlit)
- ❌ Pas d'authentification
- ❌ Pas de queue pour jobs longs
- ❌ Données sensibles non chiffrées
- ❌ Monitoring absent

### Stack recommandée
- **Backend:** FastAPI + Pydantic + asyncio
- **Frontend:** React + TypeScript + TanStack
- **Déploiement:** Docker + Cloud Run/ECS
- **Base de données:** JSON → PostgreSQL (optionnel)
- **Queue:** Celery + Redis (si besoin)

### Prochaines étapes
1. ChatGPT génère plan de migration détaillé
2. Création squelette FastAPI + React
3. Migration progressive par fonctionnalité
4. Tests de parité avec version Streamlit
5. Déploiement progressif (canary)

---

**Fin de la fiche technique**
**Document généré le:** 11 octobre 2025
**Contact:** houssam@brain-rh.com (exemple)
