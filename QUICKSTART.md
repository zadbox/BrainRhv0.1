# 🚀 Guide de Démarrage Rapide

## Installation en 5 minutes

### 1. Installer les dépendances

```bash
cd brain-rh
pip install -r requirements.txt
```

### 2. Vérifier le fichier .env

Le fichier `.env` est déjà configuré avec vos clés API:

```bash
cat .env
```

Vous devriez voir:
```
OPENAI_API_KEY=sk-proj-...
ROME_CLIENT_ID=PAR_test_...
ROME_CLIENT_SECRET=2a25df...
```

✅ Tout est déjà configuré!

### 3. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à `http://localhost:8501`

## 🎯 Premier Matching en 3 étapes

### Étape 1: Parser l'offre d'emploi

1. Aller dans l'onglet **"📄 1. Parser l'offre"**
2. Coller le texte de votre offre d'emploi
3. (Optionnel) Activer l'enrichissement ROME dans la sidebar
4. Cliquer sur **"🚀 Parser l'offre"**

**Exemple d'offre:**
```
Titre du poste : Data Scientist Junior
Expérience requise : 1 an minimum en Data Science
Formation : Bac+5 en Data Science, Statistiques ou équivalent

Compétences techniques :
- Python (Pandas, NumPy, Scikit-learn)
- SQL (PostgreSQL, MySQL)
- Machine Learning (régression, classification)
- Visualisation de données (Matplotlib, Seaborn)
- Jupyter Notebook

Compétences transversales :
- Esprit analytique
- Capacité à vulgariser des concepts techniques
- Travail en équipe
- Autonomie

Langues :
- Français (courant)
- Anglais (professionnel)
```

### Étape 2: Parser les CVs

1. Aller dans l'onglet **"📁 2. Parser les CVs"**
2. Cliquer sur **"Browse files"** et sélectionner vos CVs (PDF ou DOCX)
3. Cliquer sur **"🚀 Parser tous les CVs"**
4. Attendre la fin du parsing (barre de progression)

### Étape 3: Lancer le matching

1. Aller dans l'onglet **"🎯 3. Matching"**
2. Cliquer sur **"🤖 Extraire automatiquement les must-have avec IA"**
3. Sélectionner les critères **INDISPENSABLES** (éliminatoires) avec les checkboxes 🔥
4. Les autres critères deviennent automatiquement des **nice-to-have** (bonus)
5. Cliquer sur **"🚀 LANCER LE MATCHING"**
6. Consulter les résultats classés par ordre de pertinence

### Étape 4: Exporter les résultats

1. Cliquer sur **"💾 Exporter les résultats (CSV)"**
2. Télécharger le fichier `resultats_matching.csv`

## 📊 Comprendre les résultats

### Scores affichés

- **Score final** : Score global après tous les calculs (0-1)
- **Score base** : Similarité sémantique brute (cosinus)
- **Bonus exp** : Bonus pour expériences pertinentes (+0.05 à +0.15)
- **Malus** : Facteur multiplicatif pour nice-have manquants (0.9^n)

### Interprétation

- **Score ≥ 0.7** : Candidat très pertinent ⭐⭐⭐
- **Score 0.5-0.7** : Candidat pertinent ⭐⭐
- **Score 0.3-0.5** : Candidat potentiel ⭐
- **Score < 0.3** : Candidat moins adapté

### Commentaires RH

Chaque CV a un commentaire généré par l'IA expliquant:
- Points forts du candidat
- Adéquation avec le poste
- Éventuelles lacunes
- Recommandations

## 🔧 Personnalisation rapide

### Changer le modèle LLM

Éditer `config.yaml`:
```yaml
llm:
  model: "gpt-4o-mini"  # ou "gpt-5-nano" si disponible
```

### Ajuster le nombre de résultats

Dans la **sidebar** de l'application:
- **Top K (pré-tri)** : 50 par défaut (CVs analysés en détail)
- **Top N (re-ranking)** : 10 par défaut (CVs avec commentaires RH)

### Activer/désactiver ROME

Dans la **sidebar**, cocher/décocher:
```
☑️ Enrichir avec ROME (France Travail)
```

## 🐛 Problèmes courants

### "OPENAI_API_KEY non trouvée"

Le fichier `.env` est déjà configuré, mais si vous avez cette erreur:

```bash
# Vérifier que le fichier existe
ls -la .env

# Vérifier le contenu
cat .env
```

Si le fichier est vide ou manquant, recréer avec:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### "gpt-5-nano not found"

Le modèle `gpt-5-nano` n'existe peut-être pas encore sur votre compte OpenAI.

**Solution:** Éditer `config.yaml`:
```yaml
llm:
  model: "gpt-4o-mini"
```

Puis relancer l'application.

### Streamlit ne se lance pas

```bash
# Vérifier l'installation
pip show streamlit

# Réinstaller si nécessaire
pip install --upgrade streamlit
```

### CVs non parsés correctement

- Les PDFs scannés (images) ne sont pas encore supportés → utilisez des PDFs avec texte sélectionnable
- Les DOCX très formatés peuvent causer des problèmes → simplifier la mise en forme

## 📁 Où sont mes fichiers?

```
brain-rh/
├── enterprises/       → Structure hiérarchique projets/entreprises
│   └── {id}/
│       ├── enterprise.json
│       └── projects/{id}/
│           ├── projet.json
│           ├── cvs_raw/       → CVs bruts (PDF/DOCX)
│           ├── cvs_parsed/    → CVs parsés (JSON)
│           ├── matchings/     → Résultats matching
│           └── historique/    → Anciens matchings
├── cv_input/          → Dossier temporaire pour uploads (legacy)
├── offres/            → Offres parsées (legacy)
├── output/            → Résultats exportés
├── cache/             → Cache des embeddings (accélère les calculs)
└── logs/              → Logs d'audit
```

## 🎓 Conseils pour de meilleurs résultats

### Pour l'offre d'emploi

- Soyez **précis** sur les compétences techniques
- Indiquez les **années d'expérience** requises
- Mentionnez le **niveau de diplôme** attendu
- Listez les **langues** nécessaires

### Pour les must-have

- **Indispensables** = critères éliminatoires stricts (ex: "Bac+5", "3 ans d'expérience Python")
- **Nice-to-have** = critères bonus appréciés (ex: "Docker", "Kubernetes")
- Soyez **raisonnable** : trop de must-have = aucun CV accepté

### Pour les CVs

- Préférez des **PDFs avec texte** (pas des scans)
- Structure claire : expériences, formations, compétences
- Évitez les CVs trop graphiques ou avec trop d'images

## 🚀 Workflow recommandé

1. **Préparer l'offre** : Texte clair avec toutes les infos
2. **Parser l'offre** : Vérifier le JSON généré
3. **Uploader les CVs** : Tous les CVs en une seule fois
4. **Parser les CVs** : Attendre la fin du parsing
5. **Extraire must-have** : IA ou manuel
6. **Sélectionner indispensables** : Maximum 5-7 critères
7. **Lancer matching** : Attendre les résultats
8. **Analyser le top 10** : Lire les commentaires RH
9. **Exporter** : CSV pour analyse externe

## 📞 Besoin d'aide?

- Lire le `README.md` complet
- Vérifier les logs dans la console
- Tester les modules individuellement (voir README)

Bon matching! 🎯
