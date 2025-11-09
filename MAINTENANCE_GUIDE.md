# 🔧 BRAIN RH - GUIDE DE MAINTENANCE DES FICHIERS DE RÉFÉRENCE

**Pour:** Claude Code (et développeurs)
**Usage:** Règles de maintenance des fichiers `REFERENCE_COMPLETE.md` et `CODING_RULES.md`

> ⚠️ **RÈGLE ABSOLUE:** Ces fichiers DOIVENT être maintenus à jour pour rester utiles
> 📘 **RÈGLE:** Mettre à jour IMMÉDIATEMENT après toute modification significative

---

## 🎯 OBJECTIF

Les fichiers de référence (`REFERENCE_COMPLETE.md`, `CODING_RULES.md`) servent de **"GPS du projet"** pour Claude Code.

**Sans maintenance :**
- ❌ Claude cherche au mauvais endroit
- ❌ Applique des patterns obsolètes
- ❌ Fait les mêmes erreurs répétées
- ❌ Perd du temps à explorer le code

**Avec maintenance :**
- ✅ Claude trouve instantanément le bon fichier
- ✅ Applique les bons patterns
- ✅ Évite les erreurs connues
- ✅ Gain de temps 80%

---

## 📋 FICHIERS À MAINTENIR

### 1. REFERENCE_COMPLETE.md (Carte du projet)

**Rôle:** Localiser rapidement n'importe quelle fonctionnalité

**Contenu:**
- Structure projet (dossiers, fichiers)
- Mapping fonctionnalité → fichier:ligne
- Endpoints API disponibles
- Schemas Pydantic
- Configuration

**Fréquence MAJ:** À chaque changement de structure

---

### 2. CODING_RULES.md (Règles & patterns)

**Rôle:** Éviter les erreurs récurrentes, appliquer les bons patterns

**Contenu:**
- Règles critiques (chemins, SSE, imports)
- Patterns obligatoires (routes API, SSE, chargement données)
- Exemples ❌ AVANT / ✅ APRÈS
- Checklist avant commit

**Fréquence MAJ:** À chaque nouveau pattern ou règle identifiée

---

### 3. MAINTENANCE_GUIDE.md (Ce fichier)

**Rôle:** Expliquer comment maintenir les 2 fichiers ci-dessus

**Contenu:**
- Quand mettre à jour
- Comment mettre à jour
- Exemples de mises à jour

**Fréquence MAJ:** Rarement (règles de maintenance stables)

---

## ⚡ QUAND METTRE À JOUR

### ✅ REFERENCE_COMPLETE.md

**Mettre à jour IMMÉDIATEMENT si :**

| Changement | Action dans REFERENCE_COMPLETE.md | Exemple |
|-----------|----------------------------------|---------|
| **Ajout route API** | Ajouter ligne dans tableau "API REST" | Nouvelle route `/api/v1/matchings/history` |
| **Ajout fichier Python important** | Ajouter dans section "Structure Projet" | Nouveau `lib/scoring.py` |
| **Modification signature fonction clé** | Mettre à jour ligne du tableau "Fonctionnalité" | `get_project_path()` prend un nouveau param |
| **Ajout schema Pydantic** | Ajouter dans section "Schemas Pydantic" | Nouveau `MatchingHistory` |
| **Changement config.yaml** | Mettre à jour section "Configuration" | Nouvelle clé `scoring.malus_experience` |
| **Déplacement fichier** | Mettre à jour tous les chemins/lignes | `matching_engine.py` → `lib/matching.py` |
| **Ajout commande utile** | Ajouter dans section "Commandes utiles" | Nouveau script `python export_data.py` |
| **Nouveau diagnostic erreur** | Ajouter dans section "Diagnostics" | "Export JSON vide" → cause + solution |

**NE PAS mettre à jour pour :**
- Corrections typos
- Refactoring interne sans changement d'interface
- Ajout de commentaires
- Modifications de logs/prints

---

### ✅ CODING_RULES.md

**Mettre à jour IMMÉDIATEMENT si :**

| Changement | Action dans CODING_RULES.md | Exemple |
|-----------|------------------------------|---------|
| **Nouvelle règle critique** | Ajouter section "Règle X" avec ❌/✅ | "Ne jamais utiliser `os.path.join()` pour projets" |
| **Nouveau pattern obligatoire** | Ajouter dans "Patterns obligatoires" | Pattern "Route WebSocket" |
| **Erreur récurrente identifiée** | Ajouter dans "Exemples d'erreurs fréquentes" | Bug sur `score_map` vide |
| **Changement de convention** | Mettre à jour règle existante | Format erreur SSE change |
| **Nouvelle fonction utilitaire critique** | Ajouter règle "Utiliser X" | Nouveau helper `validate_cv_format()` |
| **Pattern obsolète** | ~~Barrer~~ ou supprimer et noter "OBSOLÈTE" | Ancien format `titre_cv` supprimé |

**NE PAS mettre à jour pour :**
- Ajout de fonctionnalités (sauf si nouveau pattern)
- Corrections de bugs ponctuels
- Optimisations internes
- Modifications de documentation secondaire

---

## 🔧 COMMENT METTRE À JOUR

### Processus standard

```bash
# 1. Ouvrir le fichier à modifier
open REFERENCE_COMPLETE.md  # ou CODING_RULES.md

# 2. Identifier la section concernée
# Ex: "API REST" pour une nouvelle route

# 3. Ajouter/modifier le contenu
# Suivre le format existant (tableaux, exemples)

# 4. Mettre à jour la date en haut du fichier
**Dernière MAJ:** JJ/MM/AAAA

# 5. (Optionnel) Ajouter un commentaire en haut si changement majeur
<!-- MAJ 18/10/2025: Ajout routes WebSocket -->

# 6. Commit
git add REFERENCE_COMPLETE.md
git commit -m "docs: add new API routes for matching history"
```

---

## 📝 EXEMPLES DE MISES À JOUR

### Exemple 1 : Ajout d'une route API

**Changement:** Nouvelle route `/api/v1/matching/{id}/history`

**MAJ REFERENCE_COMPLETE.md:**

```diff
### Endpoints disponibles

| Endpoint | Méthode | Description | Fichier | Lignes |
|----------|---------|-------------|---------|--------|
| **Matching** |
| `/api/v1/matching/run` | POST | Lancer matching (batch) | `api/routers/matching.py` | 45-120 |
| `/api/v1/matching/run/stream` | POST | Matching (SSE) | `api/routers/matching.py` | 130-350 |
+ | `/api/v1/matching/{id}/history` | GET | Historique matching | `api/routers/matching.py` | 400-430 |
```

**MAJ date en haut:**
```diff
- **Dernière MAJ:** 17 octobre 2025
+ **Dernière MAJ:** 18 octobre 2025
```

---

### Exemple 2 : Nouvelle règle critique (erreur récurrente)

**Changement:** On découvre que Claude oublie souvent de valider l'existence de `offre.json`

**MAJ CODING_RULES.md:**

```markdown
### 7. 🚨 Validation offre : TOUJOURS vérifier existence

#### ❌ INTERDIT - Charger offre sans vérifier

```python
# ❌ NE JAMAIS FAIRE ÇA
offre_path = project_path / "offre.json"
with open(offre_path) as f:  # FileNotFoundError si absent
    offre = json.load(f)
```

#### ✅ OBLIGATOIRE - Vérifier puis charger

```python
# ✅ TOUJOURS FAIRE ÇA
offre_path = project_path / "offre.json"

if not offre_path.exists():
    raise HTTPException(400, "Aucune offre définie pour ce projet")

with open(offre_path, 'r', encoding='utf-8') as f:
    offre_data = json.load(f)
    offre = Offre(**offre_data)  # Validation Pydantic
```

**Fichiers concernés:**
- `api/routers/matching.py` (toutes routes matching)
```

**MAJ checklist:**
```diff
### ✅ Code quality
- [ ] Types Pydantic pour payloads API
- [ ] Validation existence ressources (fichiers, projets)
+ - [ ] Vérification existence offre.json avant chargement
```

---

### Exemple 3 : Déplacement de fichier

**Changement:** `matching_engine.py` déplacé vers `lib/matching.py`

**MAJ REFERENCE_COMPLETE.md:**

```diff
### Backend (Python)

```
📦 Root
- ├── matching_engine.py             # ⭐ Moteur matching principal (classe MatchingEngine)
├── parseur_cv.py                  # Parsing CVs PDF/DOCX via OpenAI LLM
[...]
│
├── 📁 lib/                        # ⭐ Logique métier pure (prioritaire)
│   ├── __init__.py
│   ├── models.py                  # ⭐ Pydantic schemas (CV, Offre, ResultatMatching)
│   ├── cv_parsing.py              # Fonctions parsing pures
+   ├── matching.py                 # ⭐ Moteur matching (classe MatchingEngine)
│   ├── matching_core.py           # Fonctions matching pures
```

**MAJ tous les tableaux "Fonctionnalité":**

```diff
| **Filtrage Must-have** | Fichier | Lignes clés | Notes |
|---------|---------|-------------|-------|
- | **Analyse LLM contextuelle** | `matching_engine.py` | 450-580 | Méthode `filter_must_have()` |
+ | **Analyse LLM contextuelle** | `lib/matching.py` | 450-580 | Méthode `filter_must_have()` |
```

**MAJ CODING_RULES.md:**

```diff
#### ✅ OBLIGATOIRE - Importer depuis `lib/`

```python
# ✅ TOUJOURS FAIRE ÇA
- from lib.matching_core import run_matching_pipeline
+ from lib.matching import MatchingEngine
+ from lib.matching_core import run_matching_pipeline  # Fonctions pures
```

---

### Exemple 4 : Nouveau diagnostic erreur

**Changement:** Erreur fréquente "Timeout SSE après 2 min"

**MAJ REFERENCE_COMPLETE.md - Section "Diagnostics":**

```diff
| Symptôme | Cause probable | Fichier à vérifier | Action |
|----------|----------------|-------------------|--------|
| **SSE se déconnecte** | Timeout backend ou client | `api/routers/*.py` | Vérifier keep-alive |
+ | **Timeout SSE après 2 min** | Nginx/proxy timeout par défaut | `nginx.conf`, routes SSE | Augmenter `proxy_read_timeout 600s` |
```

---

## 🤖 INSTRUCTIONS POUR CLAUDE CODE

### Règle automatique à appliquer

**Après CHAQUE modification de code, Claude DOIT se demander :**

1. "Est-ce que j'ai ajouté/modifié une route API ?"
   → Si oui : MAJ `REFERENCE_COMPLETE.md` section "API REST"

2. "Est-ce que j'ai créé un nouveau fichier Python important ?"
   → Si oui : MAJ `REFERENCE_COMPLETE.md` section "Structure Projet"

3. "Est-ce que j'ai rencontré une erreur récurrente ?"
   → Si oui : MAJ `CODING_RULES.md` section "Règles critiques"

4. "Est-ce que j'ai créé un nouveau pattern de code ?"
   → Si oui : MAJ `CODING_RULES.md` section "Patterns obligatoires"

5. "Est-ce que j'ai déplacé/renommé un fichier ?"
   → Si oui : MAJ `REFERENCE_COMPLETE.md` PARTOUT où le fichier est mentionné

### Phrase à ajouter dans le prompt système de Claude

```markdown
RÈGLE MAINTENANCE DOCS :
Après chaque modification significative (route API, fichier important, pattern, règle),
tu DOIS mettre à jour REFERENCE_COMPLETE.md ou CODING_RULES.md selon le cas.

Checklist automatique :
- [ ] Nouvelle route API → MAJ REFERENCE_COMPLETE.md
- [ ] Nouveau fichier important → MAJ REFERENCE_COMPLETE.md
- [ ] Erreur récurrente → MAJ CODING_RULES.md
- [ ] Nouveau pattern → MAJ CODING_RULES.md
- [ ] Déplacement fichier → MAJ REFERENCE_COMPLETE.md (tous les chemins)

Ne PAS demander confirmation, faire la MAJ directement.
```

---

## 📊 TEMPLATE DE MISE À JOUR

### Pour ajouter une route API (REFERENCE_COMPLETE.md)

```markdown
<!-- Dans la section "API REST" → tableau "Endpoints disponibles" -->

| `/api/v1/[resource]/[action]` | [METHOD] | [Description] | `api/routers/[file].py` | [start]-[end] |

<!-- Exemple -->
| `/api/v1/matching/{id}/history` | GET | Historique matching | `api/routers/matching.py` | 400-430 |
```

### Pour ajouter une règle critique (CODING_RULES.md)

```markdown
### [N]. 🚨 [Titre de la règle]

#### ❌ INTERDIT - [Description du mauvais pattern]

```python
# ❌ NE JAMAIS FAIRE ÇA
[code incorrect]
```

**Pourquoi ?**
[Explication des risques]

#### ✅ OBLIGATOIRE - [Description du bon pattern]

```python
# ✅ TOUJOURS FAIRE ÇA
[code correct]
```

**Fichiers concernés:**
- `[fichier1.py]` ([description])
- `[fichier2.py]` ([description])

**Fonction de référence:**
- **Fichier:** `[fichier.py]`
- **Fonction:** `[nom_fonction]`
- **Lignes:** [start]-[end]
```

### Pour ajouter un diagnostic (REFERENCE_COMPLETE.md)

```markdown
<!-- Dans la section "Diagnostics" -->

| **[Symptôme]** | [Cause probable] | `[fichier.py]:[lignes]` | [Action recommandée] |

<!-- Exemple -->
| **Export CSV vide** | score_map manquant | `matching_engine.py:1350-1450` | Vérifier génération score_map |
```

---

## 📅 FRÉQUENCE DE REVUE

### Revue hebdomadaire (recommandée)

**Chaque semaine, vérifier :**
- [ ] Tous les chemins de fichiers sont corrects
- [ ] Toutes les lignes référencées sont à jour
- [ ] Aucune section obsolète
- [ ] Les exemples fonctionnent toujours

**Outils:**
```bash
# Vérifier que tous les fichiers référencés existent
grep -o '\`[a-zA-Z_/]*\.py\`' REFERENCE_COMPLETE.md | sort -u | while read f; do
    f=${f//\`/}
    [ -f "$f" ] || echo "❌ Fichier manquant: $f"
done

# Vérifier que les routes API existent
grep -o '/api/v1/[a-z/{}]*' REFERENCE_COMPLETE.md | sort -u
# Comparer avec : grep -r "@router\." api/routers/
```

### Revue mensuelle (critique)

**Chaque mois, faire un audit complet :**
1. Relire REFERENCE_COMPLETE.md de bout en bout
2. Vérifier chaque tableau (routes API, fonctionnalités, schemas)
3. Tester quelques commandes de la section "Commandes utiles"
4. Valider les diagnostics avec des tests réels

---

## ⚠️ RISQUES SI PAS MAINTENU

| Fichier non maintenu | Conséquence | Impact |
|---------------------|-------------|---------|
| `REFERENCE_COMPLETE.md` | Claude cherche au mauvais endroit | ⏱️ Perte temps 5-10 min/tâche |
| `REFERENCE_COMPLETE.md` | Lignes de code incorrectes | 🐛 Mauvaises modifications |
| `CODING_RULES.md` | Répétition des mêmes erreurs | 🔄 Bugs récurrents |
| `CODING_RULES.md` | Patterns obsolètes appliqués | 🚨 Code legacy créé |
| Les deux | Claude perd confiance dans les docs | ❌ Arrête de les consulter |

---

## ✅ BÉNÉFICES D'UNE BONNE MAINTENANCE

| Bénéfice | Gain estimé |
|----------|-------------|
| **Localisation instantanée** | 80% temps recherche |
| **Zéro erreur de pattern** | 90% bugs évités |
| **Code cohérent** | 100% patterns uniformes |
| **Onboarding rapide** | Nouveau dev opérationnel en 1h |
| **Confiance de Claude** | Consulte docs systématiquement |

---

## 🎯 OBJECTIF FINAL

**Ces fichiers doivent être :**
1. **À jour** (< 1 semaine de décalage max)
2. **Précis** (chemins, lignes correctes)
3. **Complets** (toutes les fonctionnalités majeures)
4. **Concis** (pas de bruit, info utile seulement)

**Si ces critères sont respectés :**
→ Claude devient **10x plus efficace**
→ Zéro perte de temps en recherche
→ Code toujours conforme aux patterns

---

## 📞 CONTACT & QUESTIONS

**En cas de doute sur la maintenance :**
1. Consulter les exemples ci-dessus
2. S'inspirer du format existant
3. En cas d'hésitation : **mettre à jour** (mieux trop que pas assez)

**Règle d'or :** En cas de doute, **TOUJOURS mettre à jour**. Un fichier sur-documenté est mieux qu'un fichier obsolète.

---

**🔄 La maintenance de ces fichiers est CRITIQUE pour l'efficacité du projet**
**📖 Suivre ce guide SYSTÉMATIQUEMENT**

---

_Dernière modification: 18 octobre 2025 - Version 1.0_
