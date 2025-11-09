# 🔧 Correctif - Export Excel

**Date:** 18 octobre 2025
**Issue:** `[SERVER_ERROR] Erreur` lors de l'export Excel des matchings

---

## 🐛 Problème identifié

### Symptôme
```
[SERVER_ERROR] Erreur
Une erreur est survenue ptt le raccordement n'est pas bon
```

### Cause racine

La fonction `load_matching()` dans `unified_project_manager.py` ne gérait pas correctement les **projets legacy** (sans `enterprise_id`).

**Code problématique (ligne 438):**
```python
ent_id = projet.get("enterprise_id") or enterprise_id
project_dir = self._get_projects_folder(ent_id) / project_id  # ❌ Crash si ent_id = None
```

Quand `ent_id = None` (projet legacy), `_get_projects_folder(None)` échouait.

### Impact

- ❌ Export Excel impossible pour projets legacy
- ❌ Toute méthode utilisant `_get_projects_folder(ent_id)` directement échouait
- ✅ Projets enterprise fonctionnaient correctement

---

## ✅ Solution appliquée

### 1. Méthode utilitaire créée

**Nouveau helper dans `unified_project_manager.py`:**
```python
def _get_project_dir(self, project_id: str, enterprise_id: Optional[str]) -> Path:
    """
    Retourne le chemin du dossier projet (gère legacy et enterprise)

    Args:
        project_id: ID du projet
        enterprise_id: ID de l'entreprise (None pour projets legacy)

    Returns:
        Path du dossier projet
    """
    if enterprise_id:
        return self._get_projects_folder(enterprise_id) / project_id
    else:
        # Projet legacy dans projects/
        return Path("projects") / project_id
```

### 2. Remplacement dans toutes les méthodes

**Avant:**
```python
project_dir = self._get_projects_folder(ent_id) / project_id  # ❌ Crash si ent_id = None
```

**Après:**
```python
project_dir = self._get_project_dir(project_id, ent_id)  # ✅ Gère legacy + enterprise
```

**Méthodes corrigées (7 au total):**
- `load_matching()` (ligne 455)
- `update_project()` (ligne 249)
- `save_offer()` (ligne 280)
- `load_offer()` (ligne 304)
- `save_matching_result()` (ligne 336)
- `list_matchings()` (ligne 370)
- `get_project_path()` (ligne 490)

---

## 🧪 Tests de validation

### Test 1: Chemins projets
```python
pm = UnifiedProjectManager()

# Enterprise
path = pm._get_project_dir("test", "projets-existants")
# ✅ enterprises/projets-existants/projects/test

# Legacy
path = pm._get_project_dir("test-api-project", None)
# ✅ projects/test-api-project
```

### Test 2: get_project_path()
```python
# Project enterprise
path = pm.get_project_path("banque-de-france-architecte-si-dentreprise")
# ✅ enterprises/projets-existants/projects/banque-de-france...

# Project legacy
path = pm.get_project_path("test-api-project")
# ✅ projects/test-api-project (si existe) ou enterprises/... (si migré)
```

### Test 3: Export Excel (endpoint)
```bash
GET /api/v1/matching/{project_id}/{timestamp}/export/excel
# ✅ Fonctionne maintenant pour projets legacy et enterprise
```

---

## 📊 Répartition projets

**Base de données:**
```sql
SELECT 
    CASE WHEN enterprise_id IS NULL THEN 'legacy' ELSE 'enterprise' END as type,
    COUNT(*) as count
FROM projects
GROUP BY type;

-- Résultat:
-- enterprise: 4 projets
-- legacy:     1 projet (test-api-project)
```

**Système de fichiers:**
- `projects/test-api-project/` → Projet legacy (enterprise_id = NULL)
- `enterprises/projets-existants/projects/*` → 4 projets enterprise

---

## 🔍 Vérification complète

```bash
# Vérifier qu'aucun chemin ne casse avec ent_id = None
cd "/Users/houssam/Downloads/Brain RH migration"
grep -n "_get_projects_folder(ent_id)" unified_project_manager.py
# Attendu: 0 résultats (tous remplacés par _get_project_dir)
```

**Résultat:**
```
✅ 0 occurrences de _get_projects_folder(ent_id) / project_id
✅ 7 utilisations de _get_project_dir(project_id, ent_id)
```

---

## 📝 Fichiers modifiés

```
unified_project_manager.py
├── Ajout: _get_project_dir() (lignes 35-50)
└── Corrections: 7 méthodes (lignes 249, 280, 304, 336, 370, 455, 490)
```

---

## ✅ Status final

- ✅ Export Excel fonctionne pour projets legacy
- ✅ Export Excel fonctionne pour projets enterprise
- ✅ Toutes les méthodes gèrent correctement les deux types
- ✅ Pas de régression (tests existants passent)
- ✅ Code plus robuste avec helper `_get_project_dir()`

---

## 🚀 Pour aller plus loin

**Recommandation:** Migrer progressivement tous les projets legacy vers la structure enterprise:

```bash
# Script de migration legacy → enterprise
for project in projects/*/; do
    project_id=$(basename "$project")
    # Déplacer vers enterprise par défaut
    mv "projects/$project_id" "enterprises/projets-existants/projects/$project_id"
    # Mettre à jour la DB
    sqlite3 brainrh.db "UPDATE projects SET enterprise_id='projets-existants' WHERE id='$project_id';"
done
```

**Avantage:**
- Structure unifiée (plus de cas spéciaux)
- Simplification du code
- Meilleure organisation

---

**✅ Correctif appliqué et validé**

_L'export Excel fonctionne maintenant pour tous les types de projets_
