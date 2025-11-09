# 🚀 Migration Base de Données - Documentation Complète

**Date:** 18 octobre 2025
**Stratégie:** Architecture hybride (Index SQLite + JSON complets)

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Procédure de migration](#procédure-de-migration)
4. [Validation](#validation)
5. [Rollback](#rollback)
6. [Maintenance](#maintenance)

---

## Vue d'ensemble

### Objectif

Améliorer les performances et la scalabilité du système Brain RH en introduisant une base SQLite pour indexer les entreprises et projets, tout en conservant les JSON comme source de vérité.

### Principe hybride

```
┌─────────────────────────────────────────────┐
│          ARCHITECTURE HYBRIDE               │
├─────────────────────────────────────────────┤
│                                             │
│  SQLite (brainrh.db)        JSON Files      │
│  ├─ enterprises             enterprises/    │
│  │  ├─ id                   ├─ */enterprise.json
│  │  ├─ nom                  └─ */projects/  │
│  │  ├─ secteur                  ├─ */projet.json
│  │  └─ json_path ───────────────┘           │
│  │                                           │
│  └─ projects                projects/       │
│     ├─ id                   └─ */projet.json│
│     ├─ nom                                   │
│     ├─ enterprise_id                         │
│     └─ json_path ────────────────────────────┘
│                                             │
│  INDEX RAPIDE              SOURCE DE VÉRITÉ │
│  (search, filter, FK)      (données complètes)
└─────────────────────────────────────────────┘
```

### Avantages

- ✅ **Performance**: Recherche/filtrage rapide via index SQL
- ✅ **Relations**: Foreign keys (enterprise_id)
- ✅ **Rollback simple**: Supprimer la DB, les JSON restent intacts
- ✅ **Migration sûre**: Dry-run obligatoire avant apply
- ✅ **ISO fonctionnel**: Aucun breaking change pour l'API

---

## Architecture

### Structure des fichiers

```
brainrh/
├── __init__.py              # Package principal
├── paths.py                 # Gestion PROJECT_ROOT
├── database.py              # Connexion SQLite
├── models/
│   ├── __init__.py
│   ├── enterprise.py        # EnterpriseDB (SQLModel)
│   ├── project.py           # ProjectDB (SQLModel)
│   └── cv.py                # CVMetaDB (future indexation)
└── services/
    ├── __init__.py
    ├── file_storage.py      # Helper JSON
    ├── enterprise_service.py # CRUD entreprises
    └── project_service.py    # CRUD projets

scripts/
└── migrate_index.py         # Script migration avec --dry-run

brainrh.db                   # Base SQLite (52 KB)
```

### Modèles DB

**EnterpriseDB** (`brainrh/models/enterprise.py`)
```python
class EnterpriseDB(SQLModel, table=True):
    __tablename__ = "enterprises"

    id: str = Field(primary_key=True)
    nom: str = Field(index=True)
    secteur: Optional[str] = None
    created_at: datetime
    last_modified: datetime
    json_path: str  # Chemin relatif vers JSON complet
```

**ProjectDB** (`brainrh/models/project.py`)
```python
class ProjectDB(SQLModel, table=True):
    __tablename__ = "projects"

    id: str = Field(primary_key=True)
    nom: str = Field(index=True)
    enterprise_id: Optional[str] = Field(
        foreign_key="enterprises.id",
        index=True
    )
    status: str = Field(default="actif", index=True)
    description: Optional[str] = None
    created_at: datetime
    last_modified: datetime
    json_path: str  # Chemin relatif vers JSON complet
```

### Services

Les services implémentent le pattern **DB + JSON synchronisé**:

```python
class EnterpriseService:
    @staticmethod
    def create_enterprise(data: Dict) -> Dict:
        # 1. Sauvegarder JSON complet
        FileStorage.save_json(json_path, full_data)

        # 2. Insérer index en DB
        with get_session() as session:
            db_ent = EnterpriseDB(...)
            session.add(db_ent)
            session.commit()

        return full_data
```

---

## Procédure de migration

### 1. Pré-requis

```bash
# Installer dépendances
pip install sqlmodel alembic

# Vérifier l'état actuel
ls -la enterprises/_index.json
ls -la projects/_index.json
```

### 2. Dry-run (OBLIGATOIRE)

```bash
# Simulation sans écriture
python scripts/migrate_index.py

# Vérifier la sortie:
# - 4 entreprises à migrer
# - 5 projets à migrer
# - Aucun warning "JSON manquant"
# - Tous les json_path loggés
```

**Sortie attendue:**
```
============================================================
🚀 MIGRATION JSON → SQLite
============================================================

🔍 MODE: DRY-RUN (aucune écriture en DB)

📂 Lecture: enterprises/_index.json
   Trouvé: 4 entreprises
   [DRY-RUN] Insérer enterprise: projets-existants (Banque de France)
             JSON: enterprises/projets-existants/enterprise.json
   ...

📂 Lecture: projects/_index.json
   Trouvé: 4 projets dans index
   [DRY-RUN] Insérer project (enterprise): banque-de-france...
             JSON: enterprises/projets-existants/projects/.../projet.json
   ...

📂 Scan: enterprises/*/projects/
   [DRY-RUN] Insérer project (scan): test2 (test2)
             JSON: enterprises/projets-existants/projects/test2/projet.json

============================================================
📊 DRY-RUN TERMINÉ
   4 entreprises à migrer
   5 projets à migrer
============================================================
```

### 3. Backup (RECOMMANDÉ)

```bash
# Backup des données JSON
cp -r enterprises/ enterprises.backup/
cp -r projects/ projects.backup/

# Backup DB existante (si elle existe)
cp brainrh.db brainrh.db.backup 2>/dev/null || true
```

### 4. Migration réelle

```bash
# Lancer la migration
python scripts/migrate_index.py --apply

# Répondre "yes" à la confirmation
```

**Sortie attendue:**
```
============================================================
🚀 MIGRATION JSON → SQLite
============================================================

⚠️  MODE: APPLY (écriture en DB)
   Backup conseillé: cp -r enterprises/ enterprises.backup/
   Backup conseillé: cp -r projects/ projects.backup/

   Continuer? (yes/no): yes

📊 Initialisation base de données...
[DB] Base de données initialisée: brainrh.db
   ✅ Tables créées

📂 Lecture: enterprises/_index.json
   Trouvé: 4 entreprises
   ✅ Inséré: projets-existants
   ✅ Inséré: bnp
   ✅ Inséré: toto
   ✅ Inséré: sg

📂 Lecture: projects/_index.json
   Trouvé: 4 projets dans index
   ✅ Inséré: banque-de-france-architecte-si-dentreprise
   ✅ Inséré: bnp
   ✅ Inséré: test
   ✅ Inséré: test-api-project

📂 Scan: enterprises/*/projects/
   ✅ Inséré: test2

============================================================
✅ MIGRATION TERMINÉE
   4 entreprises migrées
   5 projets migrés

   BD créée: brainrh.db
   Rollback: rm brainrh.db (JSON intacts)
============================================================
```

---

## Validation

### 1. Vérifier la DB

```bash
# Vérifier que la DB existe
ls -lh brainrh.db
# Attendu: ~52 KB

# Compter les tables
sqlite3 brainrh.db "SELECT count(*) FROM sqlite_master WHERE type='table';"
# Attendu: 3 (enterprises, projects, cv_meta)

# Lister les entreprises
sqlite3 brainrh.db "SELECT id, nom, json_path FROM enterprises;"
# Attendu: 4 lignes

# Lister les projets
sqlite3 brainrh.db "SELECT id, nom, enterprise_id, json_path FROM projects;"
# Attendu: 5 lignes
```

### 2. Vérifier que les JSON existent

```python
# Script de validation
python - <<'PY'
import sqlite3
from pathlib import Path

base_dir = Path.cwd()
conn = sqlite3.connect("brainrh.db")
cursor = conn.cursor()

# Vérifier enterprises
cursor.execute("SELECT id, json_path FROM enterprises")
for ent_id, json_path in cursor.fetchall():
    full_path = base_dir / json_path
    assert full_path.exists(), f"JSON manquant: {json_path}"
    print(f"✅ {ent_id}: {json_path}")

# Vérifier projects
cursor.execute("SELECT id, json_path FROM projects")
for proj_id, json_path in cursor.fetchall():
    full_path = base_dir / json_path
    assert full_path.exists(), f"JSON manquant: {json_path}"
    print(f"✅ {proj_id}: {json_path}")

conn.close()
print("\n✅ Tous les fichiers JSON existent")
PY
```

### 3. Tester l'API

```bash
# Tests unitaires
python3 -m pytest tests/test_migration_e2e.py -v
# Attendu: 6/6 tests passés

# Test manuel (API en marche)
curl http://localhost:8000/api/v1/enterprises
# Attendu: 4 entreprises

curl http://localhost:8000/api/v1/projects
# Attendu: 5 projets
```

### 4. Comparer données Service vs JSON

```python
python - <<'PY'
from brainrh.services.enterprise_service import EnterpriseService
from brainrh.services.project_service import ProjectService
import json
from pathlib import Path

# Tester entreprise
service = EnterpriseService()
ent = service.get_enterprise("projets-existants")

json_file = Path("enterprises/projets-existants/enterprise.json")
with open(json_file, 'r') as f:
    json_data = json.load(f)

# Comparer champs clés
assert ent['id'] == json_data['id']
assert ent['nom'] == json_data['nom']
assert ent['secteur'] == json_data['secteur']

print("✅ Service ↔ JSON: 100% correspondance")
PY
```

---

## Rollback

### Scénario 1: Rollback immédiat (pendant la migration)

Si un problème survient **pendant** la migration:

```bash
# 1. Arrêter le script (Ctrl+C)

# 2. Supprimer la DB partielle
rm brainrh.db

# 3. Restaurer les backups (si modifiés)
rm -rf enterprises/ projects/
mv enterprises.backup/ enterprises/
mv projects.backup/ projects/

# 4. Vérifier l'état
ls -la enterprises/_index.json
ls -la projects/_index.json
```

### Scénario 2: Rollback après migration complète

Si un problème est détecté **après** une migration complète:

```bash
# 1. Supprimer la DB
rm brainrh.db

# Effet: Les managers/services retournent à la lecture directe des JSON
# Les JSON n'ont JAMAIS été modifiés par la migration
```

**Important:** Les managers sont conçus pour fonctionner même sans DB:

```python
# enterprise_service.py fallback
try:
    json_data = FileStorage.load_json(db_ent.json_path)
except FileNotFoundError:
    # Reconstruire depuis DB
    json_data = {...}  # Données minimales depuis DB
```

### Scénario 3: Rollback Git (complet)

Pour revenir complètement à l'état pré-migration:

```bash
# 1. Identifier le commit pré-migration
git log --oneline | grep "avant migration"

# 2. Créer une branche de sauvegarde
git branch backup-post-migration

# 3. Revenir au commit pré-migration
git reset --hard <commit-id>

# 4. Supprimer les fichiers de migration
rm -rf brainrh/
rm brainrh.db
rm scripts/migrate_index.py

# 5. Vérifier que tout fonctionne
python3 -m pytest tests/
```

### Régénérer la DB

Si vous avez supprimé `brainrh.db` et voulez la recréer:

```bash
# Nettoyer
rm -f brainrh.db

# Relancer la migration
python scripts/migrate_index.py --apply
```

---

## Maintenance

### Ajouter une nouvelle entreprise

Le code gère automatiquement la synchronisation DB + JSON:

```python
from enterprise_manager import EnterpriseManager

manager = EnterpriseManager()
enterprise = manager.create_enterprise(
    nom="Nouvelle Entreprise",
    secteur="Tech",
    site_web="https://example.com"
)

# Effet:
# 1. JSON créé: enterprises/nouvelle-entreprise/enterprise.json
# 2. Index DB: INSERT INTO enterprises (...)
```

### Ajouter un nouveau projet

```python
from project_manager import ProjectManager

manager = ProjectManager()
project = manager.create_project(
    nom="Nouveau Projet",
    description="Description",
    enterprise_id="projets-existants"  # Optionnel
)

# Effet:
# 1. JSON créé: enterprises/projets-existants/projects/nouveau-projet/projet.json
#    OU projects/nouveau-projet/projet.json (si pas d'enterprise_id)
# 2. Index DB: INSERT INTO projects (...)
```

### Corriger une incohérence DB ↔ JSON

Si la DB et les JSON divergent:

```bash
# Solution 1: Régénérer la DB depuis les JSON
rm brainrh.db
python scripts/migrate_index.py --apply

# Solution 2: Corriger manuellement la DB
sqlite3 brainrh.db
> UPDATE enterprises SET nom = 'Nouveau Nom' WHERE id = 'projets-existants';
> .quit

# Solution 3: Corriger le JSON (recommandé)
# Éditer le JSON manuellement, puis:
rm brainrh.db
python scripts/migrate_index.py --apply
```

### Nettoyage des dossiers legacy

Après normalisation complète de la structure (migration de `projects/` vers `enterprises/`), les dossiers legacy doivent être supprimés pour éviter toute confusion.

#### 1. Vérifier que tous les projets sont normalisés

```bash
# Dry-run pour voir ce qui reste à migrer
python scripts/normalize_project_layout.py

# Attendu: "Aucun projet legacy à migrer!"
```

#### 2. Vérifier que tous les JSON ont enterprise_id

```bash
# Vérifier les fichiers JSON
for f in enterprises/*/projects/*/projet.json; do
    grep '"enterprise_id"' "$f" || echo "❌ MANQUANT: $f"
done

# Vérifier la DB
sqlite3 brainrh.db "
  SELECT id, enterprise_id
  FROM projects
  WHERE enterprise_id IS NULL;"
# Attendu: aucune ligne
```

#### 3. Supprimer les dossiers legacy vides

```bash
# Supprimer les dossiers projets legacy (après backup!)
rm -rf projects/bnp projects/test projects/test-api-project

# Vérifier
ls projects/
# Attendu: seulement _index.json
```

#### 4. Note importante

⚠️ **Ne jamais supprimer les dossiers legacy avant d'avoir confirmé:**
- Tous les projets sont dans `enterprises/*/projects/`
- Tous les `projet.json` ont le champ `enterprise_id`
- Tous les projets sont indexés en DB avec `enterprise_id` non NULL
- Les tests pytest passent: `pytest tests/test_migration_e2e.py -v`

### Monitoring

#### Vérifications de routine

**À exécuter régulièrement** (après tout changement de données):

```bash
# 1. Dry-run pour détecter artefacts/incohérences
python scripts/migrate_index.py
# Attendu: 4 entreprises, 5 projets, aucun warning

# 2. Vérifier l'intégrité des foreign keys
sqlite3 brainrh.db 'PRAGMA foreign_key_check;'
# Attendu: aucune sortie (= pas d'erreur)

# 3. Lister les projets orphelins
sqlite3 brainrh.db "
  SELECT p.id, p.nom, p.enterprise_id
  FROM projects p
  LEFT JOIN enterprises e ON p.enterprise_id = e.id
  WHERE p.enterprise_id IS NOT NULL AND e.id IS NULL;"
# Attendu: aucune ligne

# 4. Vérifier la cohérence des compteurs
sqlite3 brainrh.db "
  SELECT
    CASE
      WHEN enterprise_id IS NULL THEN 'legacy'
      ELSE 'enterprise'
    END as type,
    COUNT(*) as count
  FROM projects
  GROUP BY type;"
# Attendu: 4 enterprise, 1 legacy
```

#### Monitoring système

```bash
# Vérifier la taille de la DB
ls -lh brainrh.db

# Compter les entrées
sqlite3 brainrh.db "SELECT
  (SELECT count(*) FROM enterprises) as ent_count,
  (SELECT count(*) FROM projects) as proj_count;"

# Vérifier l'intégrité générale
sqlite3 brainrh.db "PRAGMA integrity_check;"
# Attendu: ok

# Analyser les index
sqlite3 brainrh.db "ANALYZE; PRAGMA optimize;"
```

---

## Troubleshooting

### Erreur: `ModuleNotFoundError: No module named 'brainrh'`

```bash
# Solution: Ajouter le projet au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ou dans le script:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

### Erreur: `sqlite3.OperationalError: database is locked`

```bash
# Cause: Processus concurrent accède à la DB
# Solution: Arrêter tous les processus Python/uvicorn

pkill -f uvicorn
pkill -f python.*brainrh

# Puis relancer
```

### Erreur: `FileNotFoundError: ... /projet.json`

```bash
# Cause: json_path incorrect ou fichier supprimé
# Solution: Vérifier l'intégrité

python - <<'PY'
import sqlite3
from pathlib import Path

conn = sqlite3.connect("brainrh.db")
cursor = conn.cursor()
cursor.execute("SELECT id, json_path FROM projects")

for proj_id, json_path in cursor.fetchall():
    if not Path(json_path).exists():
        print(f"❌ Manquant: {proj_id} -> {json_path}")
        # Supprimer de la DB
        # cursor.execute("DELETE FROM projects WHERE id = ?", (proj_id,))

conn.close()
PY
```

---

## Références

- **Code source**: `brainrh/`, `scripts/migrate_index.py`
- **Tests**: `tests/test_migration_e2e.py`
- **Status**: `MIGRATION_STATUS.md`
- **Règles coding**: `CODING_RULES.md`

---

**Version:** 1.0
**Dernière MAJ:** 18 octobre 2025
**Statut:** ✅ Production ready
